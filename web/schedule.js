export const DAY_CODES = ['U','M','T','W','R','F','S'];
export function pittsburghNow(date = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(date).map(p=>[p.type,p.value]));
  return {date:`${parts.year}-${parts.month}-${parts.day}`,day:{Sun:'U',Mon:'M',Tue:'T',Wed:'W',Thu:'R',Fri:'F',Sat:'S'}[parts.weekday],minute:Number(parts.hour)*60+Number(parts.minute),clock:`${parts.hour}:${parts.minute}`};
}
export function atTime(m, day, minute) { return m.start !== null && m.end !== null && m.days.includes(day) && m.start <= minute && minute < m.end; }
export function formatTime(m) { return m == null ? 'TBA' : `${String(Math.floor(m/60)).padStart(2,'0')}:${String(m%60).padStart(2,'0')}`; }
export function matchesFollow(m, follows) { return follows.some(f=>f.kind==='courses'&&f.id===m.courseId||f.kind==='rooms'&&f.id===m.room||f.kind==='professors'&&m.instructors.includes(f.id)); }
export function followsKey(kind,id) {return `${kind}:${id}`;}
export function validateImport(d) {
  if(!d || !/^20\d{2}-(spring|summer|fall)$/.test(d.id) || typeof d.name!=='string' || !Array.isArray(d.courses) || !Array.isArray(d.meetings)) throw new Error('请导入由 refresh.py 生成的学期 JSON。');
  const ids=new Set();
  for(const c of d.courses) {if(!c||!['id','code','title','department'].every(k=>typeof c[k]==='string')||ids.has(c.id)) throw new Error('课程数据格式错误。');ids.add(c.id);}
  for(const m of d.meetings) {if(!m||!ids.has(m.courseId)||typeof m.id!=='string'||typeof m.section!=='string'||typeof m.days!=='string'||!Array.isArray(m.instructors)||m.instructors.some(n=>typeof n!=='string')||!['start','end'].every(k=>m[k]===null||Number.isInteger(m[k])&&m[k]>=0&&m[k]<1440)||!(m.room===null||typeof m.room==='string')||typeof m.location!=='string')throw new Error('排班数据格式错误。');}
  return d;
}
