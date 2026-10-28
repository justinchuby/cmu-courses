import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from refresh import parse_schedule, parse_catalog, minutes

class ParsingTests(unittest.TestCase):
    def schedule(self, rows, full=False):
        header='<tr>'+''.join('<td>'+v+'</td>' for v in ['Course','Title','Units','Lec/Sec','Days','Begin','End','Location']+(['Bldg/Room','Instructor'] if full else []))+'</tr>'
        return 'Semester: Fall 2026 Run Date: 28-oct-2026<table>'+header+rows+'</table>'
    def row(self, values, opening=True):return ('<tr>' if opening else '')+''.join('<td>'+v+'</td>' for v in values)+'</tr>'
    def test_malformed_rows_and_continuations(self):
        rows=self.row(['Computer Science']+['']*10)+self.row(['15112','Programming','12','A','MWF','12:00PM','12:50PM','Pittsburgh'],False)+self.row(['','','','','R','09:00AM','09:50AM','Pittsburgh'])
        d=parse_schedule(self.schedule(rows),'fixture')
        self.assertEqual(len(d['courses']),1);self.assertEqual(len(d['meetings']),2)
        self.assertEqual(d['meetings'][1]['section'],'A');self.assertIsNone(d['meetings'][0]['room'])
        self.assertEqual(d['courses'][0]['department'],'Computer Science');self.assertEqual(d['meetings'][0]['start'],720)
    def test_full_schedule_and_null_tba(self):
        rows=self.row(['18300','EM','12','A','TR','10:00AM','11:20AM','Pittsburgh','DH 2315','Professor One; Professor Two'])+self.row(['','','','B','TBA','','','Pittsburgh','',''])
        d=parse_schedule(self.schedule(rows,True),'fixture')
        self.assertEqual(d['coverage'],{'rooms':1,'instructors':1});self.assertEqual(d['meetings'][0]['instructors'],['Professor One','Professor Two']);self.assertIsNone(d['meetings'][1]['start'])
    def test_reject_error_page(self):
        with self.assertRaises(ValueError):parse_schedule('<html>login</html>','fixture')
    def test_topic_title_preserved(self):
        rows=self.row(['48314','New Pedagogies:','VAR','','','','',''])+self.row(['','Special topic','','A3','M','11:00AM','12:20PM','Pittsburgh'])
        m=parse_schedule(self.schedule(rows),'fixture')['meetings'][0]
        self.assertEqual(m['topic'],'Special topic');self.assertEqual(m['mini'],'3')
    def test_catalog(self):
        d=parse_catalog('<dl class="courseblock"><dt>18-300 Electromagnetics</dt><dd>Fall<br>Fields &amp; waves.</dd></dl>','fixture')
        self.assertEqual(d['18300']['description'],'Fall Fields & waves.')
    def test_times(self):
        self.assertEqual(minutes('12:00AM'),0);self.assertEqual(minutes('12:00PM'),720);self.assertIsNone(minutes('TBA'))
if __name__=='__main__':unittest.main()
