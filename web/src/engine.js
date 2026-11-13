/* ===== Job-shop engine in the browser (port of jobshop.py, rules.py, reschedule.py) ===== */
/* inst = {routes:[[[m,p],...],...], due:[], w:[], rel:[], jobs:[], mach:[], down:[{m,s,e}]}  sched = starts[j][k] */
const RULE_KEYS=["FIFO","SPT","EDD","MWKR","CR","WSPT"];
function nJobs(I){return I.routes.length}
function fit(I,m,start,p){let moved=true;while(moved){moved=false;for(const d of I.down||[]){if(d.m==m&&start<d.e&&start+p>d.s){start=d.e;moved=true}}}return start}
function dispatch(I,rule){
  const n=nJobs(I),nm=I.mach.length,nxt=Array(n).fill(0),jr=I.rel.slice(),mr=Array(nm).fill(0),rem=I.routes.map(r=>r.reduce((a,o)=>a+o[1],0)),S=I.routes.map(r=>Array(r.length).fill(null));
  const total=I.routes.reduce((a,r)=>a+r.length,0);let done=0;
  const key=(j,now)=>{const [m,p]=I.routes[j][nxt[j]],due=I.due[j];let v;
    if(rule=="FIFO")v=jr[j];else if(rule=="SPT")v=p;else if(rule=="EDD")v=due;else if(rule=="MWKR")v=-rem[j];else if(rule=="CR")v=(due-now)/Math.max(rem[j],1);else v=p/I.w[j];return [v,j]};
  while(done<total){
    const cand=[];for(let j=0;j<n;j++)if(nxt[j]<I.routes[j].length){const [m,p]=I.routes[j][nxt[j]],est=fit(I,m,Math.max(jr[j],mr[m]),p);cand.push([est+p,est,j,m])}
    cand.sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]||a[3]-b[3]);const cs=cand[0][0],ms=cand[0][3];
    const conf=cand.filter(c=>c[3]==ms&&c[1]<cs),now=Math.min(...conf.map(c=>c[1]));
    let best=null,bk=null;for(const c of conf){const k=key(c[2],now);if(!bk||k[0]<bk[0]||(k[0]==bk[0]&&k[1]<bk[1])){bk=k;best=c}}
    const j=best[2],est=best[1],[m,p]=I.routes[j][nxt[j]];S[j][nxt[j]]=est;jr[j]=mr[m]=est+p;rem[j]-=p;nxt[j]++;done++}
  return S}
function comp(I,S){return I.routes.map((r,j)=>S[j][r.length-1]+r[r.length-1][1])}
function kpis(I,S){const C=comp(I,S),T=C.map((c,j)=>Math.max(0,c-I.due[j])),cmax=Math.max(...C),busy=Array(I.mach.length).fill(0);
  I.routes.forEach(r=>r.forEach(([m,p])=>busy[m]+=p));const b=busy.indexOf(Math.max(...busy));
  return{makespan:cmax,wt:T.reduce((a,t,j)=>a+t*I.w[j],0),tt:T.reduce((a,b)=>a+b,0),late:T.filter(t=>t>0).length,maxT:Math.max(...T),T,C,util:busy.map(x=>x/cmax),bottleneck:I.mach[b],flow:C.reduce((a,c,j)=>a+c-I.rel[j],0)/C.length}}
function check(I,S){const errs=[];I.routes.forEach((r,j)=>r.forEach(([m,p],k)=>{const s=S[j]&&S[j][k];if(s==null){errs.push(`${I.jobs[j]} op ${k+1} not scheduled`);return}
    if(k==0&&s<I.rel[j])errs.push(`${I.jobs[j]} before release`);if(k>0&&s<S[j][k-1]+r[k-1][1])errs.push(`${I.jobs[j]} op ${k+1} before op ${k}`)}));
  const byM={};I.routes.forEach((r,j)=>r.forEach(([m,p],k)=>{(byM[m]=byM[m]||[]).push([S[j][k],S[j][k]+p,j])}));
  Object.entries(byM).forEach(([m,l])=>{l.sort((a,b)=>a[0]-b[0]);for(let i=1;i<l.length;i++)if(l[i][0]<l[i-1][1])errs.push(`${I.mach[m]}: ${I.jobs[l[i-1][2]]} and ${I.jobs[l[i][2]]} overlap`);
    (I.down||[]).forEach(d=>{if(d.m==+m)l.forEach(([s,e,j])=>{if(s<d.e&&e>d.s)errs.push(`${I.mach[m]}: ${I.jobs[j]} runs during downtime`)})})});return errs}
/* events */
function applyEvent(I,ev){const J=JSON.parse(JSON.stringify(I));J.down=(I.down||[]).map(d=>({...d}));
  if(ev.kind=="breakdown")J.down.push({m:ev.machine,s:ev.time,e:ev.time+ev.duration});
  else if(ev.kind=="rush"||ev.kind=="due_change"){if(ev.weight)J.w[ev.job]=ev.weight;if(ev.due!=null)J.due[ev.job]=ev.due}
  else if(ev.kind=="new_job"){const work=ev.route.reduce((a,o)=>a+o[1],0);J.routes.push(ev.route.map(o=>[o[0],o[1]]));J.due.push(ev.due!=null?ev.due:ev.time+2*work);J.w.push(ev.weight||1);J.rel.push(ev.time);J.jobs.push(ev.name||"J"+(J.routes.length))}
  return J}
function frozenOps(I,S,t0,broken){const fz={};S.forEach((row,j)=>{if(j>=nJobs(I))return;row.forEach((s,k)=>{if(s==null||s>=t0)return;const [m,p]=I.routes[j][k];if(broken!=null&&m==broken&&s+p>t0)return;fz[j+":"+k]=s})});
  let ch=true;while(ch){ch=false;for(const key of Object.keys(fz)){const [j,k]=key.split(":").map(Number);if(k>0&&!((j+":"+(k-1)) in fz)){delete fz[key];ch=true}}}return fz}
function rightShift(I,S,t0,fz){const order=[];S.forEach((row,j)=>{if(j<nJobs(I))row.forEach((s,k)=>order.push([s,j,k]))});order.sort((a,b)=>a[0]-b[0]||a[1]-b[1]||a[2]-b[2]);
  for(let j=0;j<nJobs(I);j++)for(let k=0;k<I.routes[j].length;k++)if(!S[j]||S[j][k]==null)order.push([null,j,k]);
  const N=I.routes.map(r=>Array(r.length).fill(null)),mf=Array(I.mach.length).fill(0),jf=I.rel.slice();
  for(const [so,j,k] of order){const [m,p]=I.routes[j][k];let s;if((j+":"+k) in fz)s=fz[j+":"+k];else{s=Math.max(so==null?0:so,jf[j],mf[m],t0);s=fit(I,m,s,p)}N[j][k]=s;jf[j]=s+p;mf[m]=Math.max(mf[m],s+p)}return N}
function deviation(old,nw,fz){let dev=0,mv=0;old.forEach((row,j)=>row.forEach((s,k)=>{if(nw[j]&&nw[j][k]!=null&&!((j+":"+k) in fz)){const d=Math.abs(nw[j][k]-s);dev+=d;if(d>0)mv++}}));return{dev,mv}}
