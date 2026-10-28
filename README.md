# 课间 · CMU Campus Explorer

A campus discovery browser for Carnegie Mellon: explore courses, look up a classroom, follow an instructor, and see scheduled teaching at the current Pittsburgh time. Original interface; no ScottyLabs layout or application code is reused.

## Run locally

Requires Python 3.11+ and Node 18+ for tests. No package installation or database is required.

```sh
npm run dev
# http://127.0.0.1:4173
npm test
npm run refresh
```

## What works

- Search course numbers (with or without a hyphen) and titles; filter department, campus and semester.
- Read official catalog descriptions with source links.
- Open a course, room or professor to see all semester meeting records and a repeated weekly timetable. Entity links connect these three indexes.
- Follow courses, rooms and professors using browser localStorage; filter the feed to followed entities.
- Match the current Pittsburgh time, including daylight saving, against teaching meetings. Fall 2026 and Spring 2027 standard Pittsburgh calendars include semester boundaries, Mini 1–4 ranges, breaks and Democracy Day's evening exception. Other terms remain unavailable in the current-time view until a reviewed calendar is added.
- Import normalized complete schedule JSON into browser memory. It is never uploaded and disappears on reload. Local follow IDs remain on the device.
- Daily GitHub Actions refresh, data commits and GitHub Pages deployment.

## Important data limitation, verified 2026-10-28

The current public SOC files have **8 columns**: Course, Title, Units, Lec/Sec, Days, Begin, End, Location. Location is a teaching city/campus, **not a classroom**. Both Fall 2026 and Spring 2027 contain zero classroom or instructor records. The public course search also omits Bldg/Room and Instructor; its course-description modal does not restore those fields.

Consequently, public data alone cannot fulfill classroom lookup or professor scheduling today. The app shows that absence explicitly. Those indexes work when a complete dataset is imported. No historical instructor associations or fabricated classroom assignments are inserted.

The university SOC homepage says complete schedules are available to valid Andrew account holders. A working authenticated data export has **not** been verified in this project. No unattended Andrew authentication or credentials are configured. Finding an authorized complete source remains the main next step.

“此刻课表” is a calculation from the published schedule and standard calendar, not a live attendance, cancellation, room-occupancy or access signal. Doctoral sections, Heinz, Tepper MBA, MSCF and other special-calendar programs need their own calendar adapters. Only Pittsburgh meeting records are included in that view. Catalog descriptions are undergraduate catalog text and may omit graduate courses or differ from a semester's special-topic offering.

## Sources and scraper

- [CMU Schedule of Classes](https://enr-apps.as.cmu.edu/open/SOC/SOCServlet)
- [Official complete-schedule download page](https://enr-apps.as.cmu.edu/open/SOC/SOCServlet/completeSchedule): refreshed nightly, not instantaneously.
- [Public spring HTML](https://enr-apps.as.cmu.edu/assets/SOC/sched_layout_spring.htm), plus fall and summer equivalents. URLs roll forward; the script reads the semester and year from each document instead of assuming the year.
- [Official catalog description index](https://coursecatalog.web.cmu.edu/coursedescriptions/): discovers department inventory pages and parses course blocks in batches, rather than making a request per course.
- [Example ECE course page supplied by the project owner](https://courses.ece.cmu.edu/18300). Its description also appears in the catalog inventory used by the scraper.
- [2026–27 standard Pittsburgh calendar](https://www.cmu.edu/hub/calendar/docs/2627-academic-calendar.pdf), reviewed version dated 1 July 2026; calendar rules are maintained in `web/calendar.js`.
- [ScottyLabs/cmucourses](https://github.com/ScottyLabs/cmucourses): inspected README, repository tree and backend course controller. README mentions JS scrapers, but no scraper implementation was found in the current default-branch tree. No code was copied.

`scripts/refresh.py` uses the Python standard library. It handles the official generator's missing opening TR tags, inherited course/section cells, multi-meeting sections, topic continuations, TBA/null times and optional room/instructor headers. It retries fetch failures, validates semester markers and nonempty results, and writes each JSON atomically. Catalog failures preserve the prior catalog and fail the workflow rather than deploying an empty replacement. Source URLs, source run dates, fetch timestamps and field coverage travel with each semester.

```sh
python3 scripts/refresh.py --terms fall spring summer
python3 scripts/refresh.py --catalog
```

### Complete schedule import

If you have an authorized official complete SOC HTML export in the old table format, normalize it **outside the public data directory**:

```sh
mkdir -p .private
python3 scripts/refresh.py --input .private/complete-schedule.html --output .private/data
```

Use “导入完整课表” in the app to select the resulting `20xx-fall.json` (or spring/summer equivalent). The table should identify its semester, use Course/Title/Units/Lec/Sec/Days/Begin/End/Location headers and optionally Bldg/Room and Instructor. The parser also recognizes Sec, Teaching Location and Mini. Instructor lists support semicolons and spaced `&` / `and`; commas are preserved because names can be formatted “Last, First”. Do not commit restricted exports or credentials. The `.private/` folder is ignored by Git.

## GitHub deployment

The workflow in `.github/workflows/refresh-and-deploy.yml` runs on pushes to `main`, manual dispatch and daily at **11:35 UTC** (06:35 Pittsburgh winter / 07:35 summer), after CMU's stated nightly refresh. GitHub schedules may be delayed. GitHub Pages must use **GitHub Actions** as its source; repository settings must permit the workflow to push refreshed data.

Each run tests the parser and time logic, fetches the official data, saves the data commit, uploads `web/` and deploys it. A fetch or parser failure stops publication. No GitHub secrets or external database is needed for public sources. The browser recalculates current-time matching every minute while open; it loads the latest published dataset on page reload. Background push notifications, accounts and cross-device synchronization are not implemented.

## Tests

`npm test` covers malformed official HTML, continuation rows, optional complete fields, TBA, topic/Mini preservation, catalog extraction, DST, interval boundaries, entity follow matching, malformed imports, semester boundaries, holidays and Mini ranges. Browser QA additionally checks real course search, descriptions, following and unavailable-data states.
