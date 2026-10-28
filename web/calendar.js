// Standard Pittsburgh academic calendar, reviewed from the official 2026–27 PDF.
// Programs with separate calendars must confirm their departmental schedule.
export const calendarSource='https://www.cmu.edu/hub/calendar/docs/2627-academic-calendar.pdf';
const calendars={
 '2026-fall':{start:'2026-08-24',end:'2026-12-04',minis:{'1':['2026-08-24','2026-10-09'],'2':['2026-10-19','2026-12-04']},breaks:[['2026-09-07','2026-09-07'],['2026-10-12','2026-10-16'],['2026-11-25','2026-11-27']],lateOnly:{'2026-11-03':1020}},
 '2027-spring':{start:'2027-01-19',end:'2027-04-30',minis:{'3':['2027-01-19','2027-03-05'],'4':['2027-03-15','2027-04-30']},breaks:[['2027-03-08','2027-03-12'],['2027-04-15','2027-04-17']],lateOnly:{}}
};
export function calendarKnown(id){return Boolean(calendars[id]);}
export function onTeachingDate(m,termId,date){
 const c=calendars[termId];if(!c||date<c.start||date>c.end||c.breaks.some(([a,b])=>date>=a&&date<=b))return false;
 if(m.mini){const range=c.minis[m.mini];if(!range||date<range[0]||date>range[1])return false;}
 if(c.lateOnly[date]&&m.start<c.lateOnly[date])return false;
 return true;
}
