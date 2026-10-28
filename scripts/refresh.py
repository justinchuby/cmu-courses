#!/usr/bin/env python3
"""Fetch CMU public SOC + official catalog. Python 3.11+, no dependencies."""
import argparse
import hashlib
import html
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SOC = 'https://enr-apps.as.cmu.edu/assets/SOC/sched_layout_{}.htm'
CATALOG = 'https://coursecatalog.web.cmu.edu'

class TableParser(HTMLParser):
    # CMU's generated HTML omits some opening TR tags. Flush on closing TR.
    def __init__(self):
        super().__init__(); self.rows = []; self.row = []; self.cell = None
    def handle_starttag(self, tag, attrs):
        if tag in ('td', 'th'): self.cell = []
        elif tag == 'br' and self.cell is not None: self.cell.append(' ')
    def handle_data(self, text):
        if self.cell is not None: self.cell.append(text)
    def handle_endtag(self, tag):
        if tag in ('td', 'th') and self.cell is not None:
            self.row.append(' '.join(''.join(self.cell).split())); self.cell = None
        elif tag == 'tr':
            if self.row: self.rows.append(self.row)
            self.row = []

def text(fragment):
    return ' '.join(html.unescape(re.sub('<[^>]+>', ' ', fragment)).split())

def minutes(value):
    value = value.replace(' ', '').upper()
    if not re.fullmatch(r'\d{1,2}:\d{2}[AP]M', value): return None
    dt = datetime.strptime(value, '%I:%M%p')
    return dt.hour * 60 + dt.minute

def parse_schedule(raw, source):
    term = re.search(r'Semester:\s*(Spring|Summer|Fall)\s+(\d{4})', text(raw))
    if not term: raise ValueError('Missing semester: source may be a login or error page')
    name = ' '.join(term.groups()); term_id = f'{term[2]}-{term[1].lower()}'
    run = re.search(r'Run Date:\s*([\w-]+)', text(raw))
    parser = TableParser(); parser.feed(raw)
    courses = {}; meetings = []; department = ''; current = None; section = ''; cols = None
    for row in parser.rows:
        if row and row[0].lower() == 'course':
            cols = [c.lower().replace(' ', '') for c in row]; continue
        if not cols: continue
        if row[0] and not re.fullmatch(r'\d{2}-?\d{3}', row[0]):
            if all(not x for x in row[1:]): department = row[0]; current = None; section = ''
            continue
        if row[0]:
            code = row[0].replace('-', ''); current = code; section = ''
            courses[code] = dict(id=code, code=code[:2]+'-'+code[2:], title=row[1], units=row[2], department=department)
        if not current or len(row) < 8: continue
        r = dict(zip(cols, row))
        section = r.get('lec/sec', r.get('sec', '')) or section
        if not section: continue
        days = r.get('days', '')
        start = minutes(r.get('begin', '')); end = minutes(r.get('end', ''))
        room = next((r[k] for k in ('bldg/room','room','classroom') if r.get(k)), None)
        instructor = next((r[k] for k in ('instructor','instructors') if r.get(k)), '')
        instructors = [n.strip() for n in re.split(r';|\s+&\s+|\s+and\s+', instructor) if n.strip() and n.strip().upper() != 'TBA']
        topic = row[1] if not row[0] and row[1] else None
        key = [current, section, days, start, end, room, instructor, topic, r.get('location', '')]
        meetings.append(dict(id=hashlib.sha256(json.dumps(key).encode()).hexdigest()[:16], courseId=current, section=section,
            topic=topic, days=days, start=start, end=end, location=r.get('location', r.get('teachinglocation','')),
            room=room, instructors=instructors, mini=r.get('mini') or (section[-1] if section[-1:] in '1234' else None)))
    # Deduplicate repeated source rows, without merging distinct topics/campuses.
    meetings = list({m['id']:m for m in meetings}.values())
    if len(courses) < 1 or not meetings: raise ValueError('No course meetings found; refusing replacement')
    return dict(id=term_id, name=name, source=source, sourceRunDate=run[1] if run else None,
        fetchedAt=datetime.now(timezone.utc).isoformat(), courses=list(courses.values()), meetings=meetings,
        coverage=dict(rooms=sum(bool(m['room']) for m in meetings), instructors=sum(bool(m['instructors']) for m in meetings)))

def parse_catalog(raw, source):
    result = {}
    for block in re.findall(r'<dl\b[^>]*class=[\"\']courseblock[\"\'][^>]*>(.*?)</dl>', raw, re.S|re.I):
        title = re.search(r'<dt\b[^>]*>(.*?)</dt>', block, re.S|re.I)
        body = re.search(r'<dd\b[^>]*>(.*?)</dd>', block, re.S|re.I)
        if not title or not body: continue
        m = re.match(r'(\d{2})-(\d{3})\s+(.+)', text(title[1]))
        if m: result[m[1]+m[2]] = dict(title=m[3], description=text(body[1]), source=source)
    return result

def fetch(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url, headers={'User-Agent':'CMU-Campus-Explorer/0.1 (public academic schedule index)'}), timeout=45) as response:
                return response.read().decode('utf-8', errors='replace')
        except Exception:
            if attempt == 2: raise
            time.sleep(2 ** attempt)

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':'))+'\n')
    temporary.replace(path)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--terms', nargs='+', default=['fall','spring','summer'], choices=['fall','spring','summer'])
    p.add_argument('--catalog', action='store_true', help='Refresh official catalog descriptions (about 30 requests)')
    p.add_argument('--input', type=Path, help='Parse a saved official SOC HTML file instead of fetching')
    p.add_argument('--output', type=Path, default=ROOT/'web/data')
    args = p.parse_args(); output = args.output
    schedules = [parse_schedule(args.input.read_text(), 'local-import')] if args.input else [parse_schedule(fetch(SOC.format(t)), SOC.format(t)) for t in args.terms]
    # All requested schedule sources must parse before any replacement.
    for schedule in schedules:
        write_json(output/(schedule['id']+'.json'), schedule)
        print(schedule['name'], len(schedule['courses']), 'courses;', len(schedule['meetings']), 'meetings;', schedule['coverage'])
    files = sorted(output.glob('20*-*.json'))
    terms = []
    for file in files:
        d = json.loads(file.read_text()); terms.append({k:d[k] for k in ('id','name','source','sourceRunDate','fetchedAt','coverage')})
    write_json(output/'terms.json', terms)
    if args.catalog:
        index = fetch(CATALOG+'/coursedescriptions/')
        urls = sorted(set(re.findall(r'href="(/schools-colleges/[^"#]+/courses/)"', index)))
        if not urls: raise ValueError('Catalog index changed; refusing empty refresh')
        descriptions = {}
        for path in urls:
            url = CATALOG+path; found = parse_catalog(fetch(url), url)
            if not found: raise ValueError(f'No descriptions parsed from {url}; preserving previous catalog')
            descriptions.update(found); time.sleep(.3)
        write_json(output/'descriptions.json', dict(fetchedAt=datetime.now(timezone.utc).isoformat(), courses=descriptions))
        print(len(descriptions), 'official catalog descriptions')

if __name__ == '__main__': main()
