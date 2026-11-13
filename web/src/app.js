/* ===== Domain ===== */
const BK=Object.fromEntries(D.books.map(b=>[b.seed,b])),NB=D.books.length,MN=D.books[0].inst.mach;
const baseInst=b=>({...BK[b].inst,down:[]});
const RV=Object.fromEntries(D.study.rv.map(r=>[r.objective+"|"+r.method,r]));
const rvMean=(o,m)=>RV[o+"|"+m].mean;
const RULES_WT=D.rules.map(r=>[r,rvMean("weighted_tardiness",r)]).sort((a,b)=>a[1]-b[1]);
const RULES_MK=D.rules.map(r=>[r,rvMean("makespan",r)]).sort((a,b)=>a[1]-b[1]);
const OPT_WT=rvMean("weighted_tardiness","CP-SAT"),OPT_MK=rvMean("makespan","CP-SAT");
const DIS=Object.fromEntries(D.study.dis.map(r=>[r.method,r])),PAIR=Object.fromEntries(D.study.pair.map(r=>[r.from+">"+r.to,r]));
const BENCH=D.study.bench.map(r=>{const best=Math.min(...D.rules.map(k=>r[k]));return{...r,best,bestRules:D.rules.filter(k=>r[k]==best).join(" · "),gap:best/r.optimum-1}});
const STORY={b:1,m:0,t0:120,d:60};
const MCOL=[C.em,C.steel,C.gold];

/* plan computation: base plan, then events applied in order */
function basePlan(b,base){const I=baseInst(b);return base=="OPT"?BK[b].opt.map(r=>r.slice()):dispatch(I,base)}
function gridKey(b,base,ev){if(base!="OPT"||!BK[b].sc)return null;let k=null;
  if(ev.kind=="breakdown")k=`b:${ev.machine}:${ev.time}:${ev.duration}`;else if(ev.kind=="rush"&&ev.time==60&&ev.due==null)k=`r:${ev.job}`;
  return k&&BK[b].sc[k]?k:null}
function computePlan(b,base,events,method){
  let I=baseInst(b),S=basePlan(b,base),prev=null,src=null,fz={},now=null,info=null;
  events.forEach((ev,i)=>{const J=applyEvent(I,ev),broken=ev.kind=="breakdown"?ev.machine:null;fz=frozenOps(J,S,ev.time,broken);
    const k=i==0&&events.length==1&&method!="right_shift"?gridKey(b,base,ev):null;let N;
    if(k){N=BK[b].sc[k][method].s.map(r=>r.slice());src="pre"}else{N=rightShift(J,S,ev.time,fz);src=method=="right_shift"?"rs":"fb"}
    info={before:kpis(I,S),dev:deviation(S,N,fz)};prev=S;S=N;I=J;now=ev.time});
  return{I,S,prev,src,fz,now,info,k:kpis(I,S),errs:check(I,S)}}

/* ===== Extra charts ===== */
function gantt(host,o){
  const I=o.I,S=o.S,nm=I.mach.length,W=Math.max(host.clientWidth||700,o.minW||620),rh=o.rh||34,m={l:70,r:16,t:o.now!=null?22:10,b:26},H=m.t+nm*rh+m.b,iw=W-m.l-m.r;
  const K=kpis(I,S),ends=[K.makespan,...(I.down||[]).map(d=>d.e),...(o.prev?o.prev.map((r,j)=>r.length?r[r.length-1]+I.routes[j][r.length-1][1]:0):[])];
  const T=ticks(0,Math.max(...ends)*1.02,6),X=v=>m.l+v/T.hi*iw,anim=st.anim&&!reduced();
  let g=`<defs><pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="6" height="6" fill="var(--bad)" opacity=".10"/><line x1="0" y1="0" x2="0" y2="6" stroke="var(--bad)" stroke-width="2" opacity=".55"/></pattern></defs>`;
  T.t.forEach((v,k)=>{const x=X(v);g+=`<line x1="${x}" x2="${x}" y1="${m.t}" y2="${m.t+nm*rh}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${x}" y="${H-8}" text-anchor="middle">${num(v)}</text>`});
  for(let r=0;r<nm;r++){const y=m.t+r*rh;g+=`<rect x="${m.l}" y="${y+2}" width="${iw}" height="${rh-4}" rx="6" fill="var(--card2)" opacity="${r%2?0.55:0.9}"/><text class="lbl-ui" x="${m.l-10}" y="${y+rh/2+4}" text-anchor="end" style="font-size:11.5px;fill:var(--soft);font-weight:600">${esc(I.mach[r])}</text>`}
  (I.down||[]).forEach(d=>{const y=m.t+d.m*rh;g+=`<rect x="${X(d.s)}" y="${y+1}" width="${X(d.e)-X(d.s)}" height="${rh-2}" rx="5" fill="url(#hatch)" stroke="var(--bad)" stroke-width="1" stroke-opacity=".5"/>`});
  const late=K.T.map(x=>x>0),chg=o.changed||new Set();
  if(o.prev&&o.showChg)o.prev.forEach((row,j)=>row.forEach((s,k)=>{if(s==null||!S[j]||S[j][k]===s)return;const [mm,p]=I.routes[j][k],y=m.t+mm*rh;
    g+=`<rect class="gh" x="${X(s)+.5}" y="${y+6.5}" width="${Math.max(2,X(s+p)-X(s)-1)}" height="${rh-13}" rx="4" fill="none" stroke="var(--mut)" stroke-dasharray="3 3" opacity=".8"/>`}));
  let bars="";
  S.forEach((row,j)=>row.forEach((s,k)=>{const [mm,p]=I.routes[j][k],y=m.t+mm*rh,x=X(s),w=Math.max(2,X(s+p)-x-1.5),col=late[j]?C.rose:chg.has(j)?C.gold:C.em,fr=(j+":"+k) in (o.fz||{});
    const ps=o.prev&&o.prev[j]&&o.prev[j][k]!=null?o.prev[j][k]:null,dx=ps!=null&&o.tween?X(ps)-x:0;
    bars+=`<g class="op${o.tween&&dx?" tw":""}" data-j="${j}" data-k="${k}" style="${dx?`transform:translateX(${dx.toFixed(1)}px)`:""}"><rect class="${anim&&!o.tween?"growx":""}" style="${anim&&!o.tween?`animation-delay:${(s/T.hi*.6).toFixed(2)}s`:""}" x="${x}" y="${y+5}" width="${w}" height="${rh-10}" rx="5" fill="${col}" ${fr?'opacity=".55"':""} ${late[j]&&chg.has(j)?'stroke="var(--gold)" stroke-width="2"':""}/>${w>24?`<text x="${x+w/2}" y="${y+rh/2+3.5}" text-anchor="middle" style="fill:${late[j]?"#fff":"#0B100E"};font-weight:700;font-size:10px;pointer-events:none">${esc(I.jobs[j])}</text>`:""}</g>`}));
  g+=bars;
  if(o.now!=null){const x=X(o.now);g+=`<line x1="${x}" x2="${x}" y1="${m.t-14}" y2="${m.t+nm*rh}" stroke="var(--gold)" stroke-width="1.6"/><rect x="${x-22}" y="${m.t-21}" width="44" height="15" rx="7" fill="var(--gold2)"/><text x="${x}" y="${m.t-10.5}" text-anchor="middle" style="fill:#0B100E;font-weight:700;font-size:9.5px">${esc(t("gNow"))} ${num(o.now)}</text>`}
  host.innerHTML=`<div class="gscroll"><svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" dir="ltr" role="img" style="min-width:${o.minW||620}px">${g}</svg></div>`;
  const svg=host.querySelector("svg");
  if(o.tween&&anim){requestAnimationFrame(()=>requestAnimationFrame(()=>svg.querySelectorAll(".op.tw").forEach(e=>e.style.transform="translateX(0)")))}else svg.querySelectorAll(".op.tw").forEach(e=>e.style.transform="none");
  svg.querySelectorAll(".op").forEach(el=>{const j=+el.dataset.j,k=+el.dataset.k;
    el.addEventListener("pointerenter",()=>{svg.classList.add("hl");svg.querySelectorAll(`.op[data-j="${j}"]`).forEach(e=>e.classList.add("on"))});
    el.addEventListener("pointermove",e=>{const hr=host.getBoundingClientRect(),[mm,p]=I.routes[j][k],s=S[j][k],tj=K.T[j];
      tipAt(host,`<div class="th">${esc(I.jobs[j])} · ${t("op")} ${B(k+1)}/${B(I.routes[j].length)}</div>${trow(C.mut,t("machine"),esc(I.mach[mm]))}${trow(C.em,t("start")+" → "+t("end"),num(s)+" → "+num(s+p))}${trow(C.gold,t("due")+" · "+t("weight"),num(I.due[j])+" · "+num(I.w[j]))}${trow(tj>0?C.rose:C.em,t("tard"),tj>0?"+"+num(tj)+" "+t("min"):t("onTime"))}${o.prev&&o.prev[j]&&o.prev[j][k]!=null&&o.prev[j][k]!==s?`<div class="tf">${t("gGhost")}: ${B(num(o.prev[j][k]))} → ${B(num(s))} (${B(sgn(s-o.prev[j][k]))} ${t("min")})</div>`:""}`,e.clientX-hr.left+host.querySelector(".gscroll").scrollLeft*0,e.clientY-hr.top)});
    el.addEventListener("pointerleave",()=>{svg.classList.remove("hl");svg.querySelectorAll(".op.on").forEach(e=>e.classList.remove("on"));tipOff(host)})});
}
function ganttLegend(o){return legend([[t("gOn"),C.em],[t("gLate"),C.rose],[t("gRush"),C.gold]].concat(o.down?[[t("gDown"),C.bad,1]]:[]).concat(o.ghost?[[t("gGhost"),C.mut,1]]:[]).concat(o.now?[[t("gNow"),"var(--gold)"],[t("gFrozen"),"color-mix(in srgb,var(--em2) 55%,transparent)"]]:[]))}
/* horizontal bars with 95% CI whiskers */
function hbarCI(host,o){const W=host.clientWidth||320,rh=40,m={l:o.ml||118,r:56,t:6,b:22},H=m.t+o.rows.length*rh+m.b,iw=W-m.l-m.r;
  const T=ticks(0,Math.max(...o.rows.map(r=>r.v+(r.ci||0)))*1.04,3),X=v=>m.l+v/T.hi*iw,anim=st.anim&&!reduced();let g="";
  T.t.forEach((v,k)=>{const x=X(v);g+=`<line x1="${x}" x2="${x}" y1="${m.t}" y2="${H-m.b}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${x}" y="${H-6}" text-anchor="middle">${o.fmt(v)}</text>`});
  o.rows.forEach((r,i)=>{const y=m.t+i*rh+8,h=rh-16;
    g+=`<text class="lbl-ui" x="${m.l-10}" y="${y+h/2+4}" text-anchor="end" style="font-size:11.5px;fill:var(--soft);font-weight:600">${esc(r.label)}</text><path class="${anim?"growx":""}" style="animation-delay:${i*.08}s" d="M${m.l} ${y}H${X(r.v)-5}Q${X(r.v)} ${y} ${X(r.v)} ${y+5}V${y+h-5}Q${X(r.v)} ${y+h} ${X(r.v)-5} ${y+h}H${m.l}Z" fill="${r.color}"/>`;
    if(r.ci)g+=`<g class="${anim?"fadein":""}" stroke="var(--ink)" stroke-width="1.4" opacity=".75"><line x1="${X(r.v-r.ci)}" x2="${X(r.v+r.ci)}" y1="${y+h/2}" y2="${y+h/2}"/><line x1="${X(r.v-r.ci)}" x2="${X(r.v-r.ci)}" y1="${y+h/2-5}" y2="${y+h/2+5}"/><line x1="${X(r.v+r.ci)}" x2="${X(r.v+r.ci)}" y1="${y+h/2-5}" y2="${y+h/2+5}"/></g>`;
    g+=`<text x="${X(r.v+(r.ci||0))+8}" y="${y+h/2+4}" style="fill:var(--ink);font-weight:600;font-size:11.5px">${o.fmt(r.v,1)}</text>`});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}</svg>`}
/* forest plot: paired differences with CI, zero line */
function forest(host,o){const W=host.clientWidth||320,rh=44,m={l:o.ml||150,r:20,t:8,b:24},H=m.t+o.rows.length*rh+m.b,iw=W-m.l-m.r;
  const lo=Math.min(0,...o.rows.map(r=>r.v-r.ci)),hi=Math.max(0,...o.rows.map(r=>r.v+r.ci)),sp=niceStep(hi-lo,4),a=Math.floor(lo/sp)*sp,b=Math.ceil(hi/sp)*sp,X=v=>m.l+(v-a)/(b-a)*iw;let g="";
  for(let v=a;v<=b+1e-9;v+=sp){const x=X(v);g+=`<line x1="${x}" x2="${x}" y1="${m.t}" y2="${H-m.b}" stroke="${Math.abs(v)<1e-9?"var(--line2)":"var(--grid)"}" ${Math.abs(v)<1e-9?'stroke-width="1.5"':'stroke-dasharray="2 6"'}/><text x="${x}" y="${H-6}" text-anchor="middle">${sgn(v)}</text>`}
  o.rows.forEach((r,i)=>{const y=m.t+i*rh+rh/2,good=r.v<0,col=good?C.em:C.rose;
    g+=`<text class="lbl-ui" x="${m.l-10}" y="${y+4}" text-anchor="end" style="font-size:11.5px;fill:var(--soft);font-weight:600">${esc(r.label)}</text><line x1="${X(r.v-r.ci)}" x2="${X(r.v+r.ci)}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="3" stroke-linecap="round" opacity=".55"/><circle cx="${X(r.v)}" cy="${y}" r="6" fill="${col}" stroke="var(--card)" stroke-width="2"/><text x="${X(r.v)}" y="${y-11}" text-anchor="middle" style="fill:var(--ink);font-weight:600;font-size:11px">${sgn(r.v)} ± ${num(r.ci)}</text>`});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}</svg>`}
/* connected scatter (trade-off frontier) */
function frontier(host,o){const W=host.clientWidth||520,H=o.h||280,m={l:56,r:22,t:18,b:40},iw=W-m.l-m.r,ih=H-m.t-m.b;
  const xs=o.pts.map(p=>p.x),ys=o.pts.map(p=>p.y),TX=ticks(Math.min(...xs)*.92,Math.max(...xs)*1.04,4),TY=ticks(Math.min(...ys)*.9,Math.max(...ys)*1.06,4);
  const X=v=>m.l+(v-TX.lo)/(TX.hi-TX.lo)*iw,Y=v=>m.t+ih-(v-TY.lo)/(TY.hi-TY.lo)*ih,anim=st.anim&&!reduced();let g="";
  TY.t.forEach((v,k)=>{const y=Y(v);g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${m.l-10}" y="${y+3.5}" text-anchor="end">${num(v)}</text>`});
  TX.t.forEach(v=>{g+=`<text x="${X(v)}" y="${H-22}" text-anchor="middle">${num(v)}</text>`});
  g+=`<text class="lbl-ui" x="${m.l+iw/2}" y="${H-4}" text-anchor="middle" style="font-size:11px">${esc(o.xl)}</text><text class="lbl-ui" x="${m.l}" y="${m.t-6}" style="font-size:11px">${esc(o.yl)}</text>`;
  const line=o.pts.filter(p=>!p.solo);g+=`<path class="${anim?"draw":""}" pathLength="1" d="${line.map((p,i)=>(i?"L":"M")+X(p.x)+" "+Y(p.y)).join("")}" fill="none" stroke="var(--em2)" stroke-width="2"/>`;
  o.pts.forEach((p,i)=>{const x=X(p.x),y=Y(p.y),c=p.solo?C.rose:p.hl?C.gold:C.em;g+=`<g class="${anim?"fadein":""}"><circle cx="${x}" cy="${y}" r="${p.hl?7:5}" fill="${c}" stroke="var(--card)" stroke-width="2"/><text x="${x+(p.dx||9)}" y="${y+(p.dy||-9)}" text-anchor="${p.anchor||"start"}" style="fill:var(--soft);font-weight:600;font-size:10.5px">${p.l}</text></g>`});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}</svg>`}
/* per-category dot range (min..max connector) */
function dotRange(host,o){const W=host.clientWidth||700,H=o.h||260,m={l:50,r:10,t:12,b:28},iw=W-m.l-m.r,ih=H-m.t-m.b,n=o.cats.length;
  const T=ticks(0,Math.max(...o.series.flatMap(s=>s.vals))*1.06,4),X=i=>m.l+(i+.5)*iw/n,Y=v=>m.t+ih-v/T.hi*ih,anim=st.anim&&!reduced();let g="";
  T.t.forEach((v,k)=>{const y=Y(v);g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${m.l-10}" y="${y+3.5}" text-anchor="end">${num(v)}</text>`});
  const step=xTickStep(n,iw,22);o.cats.forEach((c,i)=>{const vs=o.series.map(s=>s.vals[i]);g+=`<line x1="${X(i)}" x2="${X(i)}" y1="${Y(Math.min(...vs))}" y2="${Y(Math.max(...vs))}" stroke="var(--line2)" stroke-width="3" stroke-linecap="round"/>`;
    if(i%step==0)g+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle">${c}</text>`;
    o.series.forEach((s,j)=>{g+=`<circle class="${anim?"fadein":""}" style="animation-delay:${(i*.02).toFixed(2)}s" cx="${X(i)}" cy="${Y(s.vals[i])}" r="4.5" fill="${s.color}" stroke="var(--card)" stroke-width="1.5"/>`})});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}<line class="cx" y1="${m.t}" y2="${m.t+ih}" stroke="var(--line2)" opacity="0"/><rect class="hit" x="${m.l}" y="${m.t}" width="${iw}" height="${ih}" fill="transparent"/></svg>`;
  const svg=host.querySelector("svg"),cx=svg.querySelector(".cx");
  svg.addEventListener("pointermove",e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)*(W/r.width),i=Math.max(0,Math.min(n-1,Math.floor((px-m.l)/iw*n)));cx.setAttribute("x1",X(i));cx.setAttribute("x2",X(i));cx.setAttribute("opacity",1);
    tipAt(host,`<div class="th">${o.tl(o.cats[i])}</div>`+o.series.map(s=>trow(s.color,s.name,num(s.vals[i]))).join(""),X(i)*(r.width/W),e.clientY-r.top)});
  svg.addEventListener("pointerleave",()=>{cx.setAttribute("opacity",0);tipOff(host)})}

/* ===== Building blocks ===== */
const card=(ttl,sub,body,extra="",id="")=>`<div class="card" ${id?`id="${id}"`:""}><div class="card-h"><div><h3>${ttl}</h3>${sub?`<div class="sub">${sub}</div>`:""}</div>${extra}</div>${body}</div>`;
const kpi=(lbl,val,cmp,pill="",cls="")=>`<div class="kpi ${cls}"><div class="lbl"><span>${lbl}</span>${pill}</div><div class="val">${val}</div><div class="cmp">${cmp}</div></div>`;
const mName=m=>t("m_"+m);
const kstrip=(P,base)=>{const k=P.k,b=base||null,d=(a,c,low=true)=>b==null||a==c?"":`<span class="pill ${(a<c)==low?"ok":"bad"}">${B(sgn(a-c))}</span>`;
  return `<div class="kstrip">${[[t("wt"),k.wt,b&&b.wt],[t("late"),k.late,b&&b.late],[t("mk"),k.makespan,b&&b.makespan]].map(([l,v,c])=>`<div><span>${l}</span><b>${B(num(v))}</b>${c!=null?d(v,c):""}</div>`).join("")}
  <div><span>${t("movedOps")}</span><b>${B(P.info?num(P.info.dev.mv):"0")}</b></div><div><span>${t("moved")}</span><b>${B(P.info?num(P.info.dev.dev):"0")}</b></div>
  <div><span>${t("checker")}</span><b class="${P.errs.length?"bad":"okc"}">${P.errs.length?t("viol",B(P.errs.length)):`${ic("check")} ${t("feasible")}`}</b></div></div>`};

/* ===== Overview ===== */
function storyPlan(step){const b=STORY.b,ev={kind:"breakdown",machine:STORY.m,time:STORY.t0,duration:STORY.d};
  if(step==0){const I=baseInst(b),S=BK[b].opt;return{I,S,prev:null,now:null,fz:{},k:kpis(I,S),errs:check(I,S)}}
  const P=computePlan(b,"OPT",[ev],step==1?"right_shift":"stable");return P}
function pOverview(){
  const best=RULES_WT[0],red=1-OPT_WT/best[1],ok=BENCH.filter(r=>r.cpsat==r.optimum).length,mx=Math.max(...BENCH.map(r=>r.cpsat_seconds));
  const rs=DIS.right_shift,re=DIS.reoptimize,sp=PAIR["reoptimize>stable"];
  return `<section class="hero"><div class="lanes" aria-hidden="true">${[[90,C.em],[60,C.steel],[120,C.gold],[40,C.em],[75,C.rose]].map(([w,c],i)=>`<i style="width:${w}px;background:${c};margin-inline-start:${[0,30,12,70,20][i]}px"></i>`).join("")}</div>
    <div class="eyebrow">${t("ovEy")}</div><h2>${t("ovH",B(pct(red,0)))}</h2><p class="lead">${t("ovLead")}</p>
    <div class="kpis">${kpi(t("k1"),CU(-red*100,"s",0)+"<small>%</small>",t("k1c",B(num(best[1])+" ("+best[0]+")"),B(num(OPT_WT))),`<span class="pill ok">CP-SAT</span>`)}
    ${kpi(t("k2"),`${CU(ok,"n",0)}<small>/ ${B(num(BENCH.length))}</small>`,t("k2c",B(num(mx,1))),`<span class="pill mu">JSPLIB</span>`)}
    ${kpi(t("k3"),CU(-(1-re.weighted_tardiness/rs.weighted_tardiness)*100,"s",0)+"<small>%</small>",t("k3c",B(num(rs.weighted_tardiness)),B(num(re.weighted_tardiness))),`<span class="pill ok">n = ${B(30)}</span>`)}
    ${kpi(t("k4"),CU(sp.dev_diff/re.deviation_min*100,"s",0)+"<small>%</small>",t("k4c",B(sgn(sp.wt_diff/re.weighted_tardiness*100,0)+"%")),`<span class="pill wn">w = 0.2</span>`)}</div></section>
  ${card(t("stTitle"),t("stSub",MN[STORY.m],B(STORY.t0),B(STORY.d)),`<div class="steps">${[0,1,2].map(i=>`<button class="step ${i==st.story?"on":""}" data-story="${i}" aria-pressed="${i==st.story}"><span class="sn">${B(i+1)}</span><span><b>${t("st"+i)}</b><small>${t("st"+i+"d")}</small></span></button>`).join("")}</div>
    <div id="storyK"></div><div id="storyLg"></div><div class="chart" id="storyG"></div>`,`<div style="display:flex;gap:8px"><button class="btn" data-play>${ic(st.playing?"pause":"play")}${t(st.playing?"pause":"play")}</button><button class="btn pri" data-openstory>${ic("pl")}${t("openPl")}</button></div>`,"story")}
  <div class="grid g21">${card(t("pipeT"),t("pipeS"),`<ol class="pipe">${[1,2,3,4,5].map(i=>`<li><span class="pn">${B(i)}</span><b>${t("p"+i)}</b><small>${t("p"+i+"d")}</small></li>`).join("")}</ol>
    <div class="cmdex"><code>"${esc(t("q_bd"))}"</code><span>→</span><code>{"action":"breakdown","machine":"Mill","start":120,"duration":60}</code></div>`)}
  ${card(t("insT"),"",`<ul class="ins">${[t("ins1",B(num(best[1]/OPT_WT,1))),t("ins2",B(num(rs.deviation_min))),t("ins3",B(sgn(sp.dev_diff)),B(sgn(sp.wt_diff))),t("ins4")].map((x,i)=>`<li><i style="background:${[C.em,C.rose,C.gold,C.steel][i]}"></i><span>${x}</span></li>`).join("")}</ul>`)}</div>`}
let storyPrev=null,storyTimer=null;
function drawStory(tween){const P=storyPlan(st.story),k0=kpis(baseInst(STORY.b),BK[STORY.b].opt);
  $("#storyK").innerHTML=kstrip(P,st.story?k0:null);$("#storyLg").innerHTML=ganttLegend({down:st.story>0,ghost:st.story>0,now:st.story>0});
  const prev=storyPrev;mount("storyG",h=>gantt(h,{I:P.I,S:P.S,prev:st.story?BK[STORY.b].opt:null,showChg:st.story>0,fz:P.fz,now:P.now,tween:tween&&prev?1:0,minW:640}));storyPrev=P.S}
function afterOverview(){storyPrev=null;drawStory(false)}
function setStory(i){st.story=(i+3)%3;$$("[data-story]").forEach(b=>{const on=+b.dataset.story==st.story;b.classList.toggle("on",on);b.setAttribute("aria-pressed",on)});st.anim=true;redraw.length=0;drawStory(true);st.anim=false}
function togglePlay(){st.playing=!st.playing;clearInterval(storyTimer);if(st.playing)storyTimer=setInterval(()=>{if(st.page!="ov"){st.playing=false;clearInterval(storyTimer);return}setStory(st.story+1)},3200);const b=$("[data-play]");if(b)b.innerHTML=ic(st.playing?"pause":"play")+t(st.playing?"pause":"play")}

/* ===== Planner ===== */
const RUSH=P=>{const s=new Set();st.events.forEach(e=>{if(e.kind=="rush"||e.kind=="due_change")s.add(e.job);if(e.kind=="new_job")s.add(P.I.routes.length-1)});return s};
let PL=null;
function plan(){PL=computePlan(st.book,st.base,st.events,st.method);return PL}
function pPlanner(){plan();
  return `<div class="bar"><label class="ctl">${ic("book")}<span>${t("book")}</span><select id="selBook">${D.books.map(b=>`<option value="${b.seed}" ${b.seed==st.book?"selected":""}>${num(b.seed)}${b.sc?" ★":""}</option>`).join("")}</select></label>
    <label class="ctl"><span>${t("base")}</span><select id="selBase"><option value="OPT" ${st.base=="OPT"?"selected":""}>${t("optLbl")}</option>${D.rules.map(r=>`<option value="${r}" ${st.base==r?"selected":""}>${t("baseRule",r)}</option>`).join("")}</select></label>
    <div class="chips" role="group" aria-label="${t("repair")}">${["stable","reoptimize","right_shift"].map(m=>`<button class="${st.method==m?"on":""}" data-method="${m}">${mName(m)}</button>`).join("")}</div>
    <label class="tog"><input type="checkbox" id="chg" ${st.chg?"checked":""}><span>${t("showChg")}</span></label>
    <button class="btn" data-reset-plan>${ic("reset")}${t("reset")}</button></div>
  <div class="grid g21 pl"><div>${card(t("ganttT"),t("ganttS"),`<div id="plK"></div><div id="plSrc"></div><div id="plLg"></div><div class="chart" id="plG"></div>`)}
    ${card(t("jobsT"),t("jobsS"),`<div id="plJobs"></div>`)}</div>
    <div>${card(t("chatT"),t("chatS"),`<div class="chat" id="chat" aria-live="polite"></div><div class="qc">${["q_bd","q_bd2","q_rush","q_due","q_new","q_cmp","q_undo","q_help"].map(q=>`<button data-q="${q}">${esc(t(q))}</button>`).join("")}</div>
      <form class="chatin" id="chatF"><input id="chatI" autocomplete="off" placeholder="${esc(t("chatPh"))}" aria-label="${esc(t("chatPh"))}"><button class="btn pri" type="submit" aria-label="${t("send")}">${ic("send")}</button></form>
      <div class="note" style="margin-top:12px">${ic("info")}<span>${t("gridHint")}</span></div>`,"","chatCard")}
    ${card(t("evLog"),"",`<div id="plLog"></div>`)}</div></div>`}
function srcBadge(P){if(!P.src)return"";const pre=P.src=="pre";return `<div class="src ${pre?"pre":"live"}">${ic(pre?"check":"bolt")}<span>${pre?t("srcPre")+` · ${mName(st.method)}`:t("srcLive")}</span></div>${P.src=="fb"?`<div class="note w" style="margin:8px 0 4px">${ic("warn")}<span>${t("fbNote")}</span></div>`:""}`}
function evText(e,I){const J=n=>I.jobs[n]||"J"+(n+1);
  return e.kind=="breakdown"?t("ev_breakdown",MN[e.machine],B(num(e.time)),B(num(e.time+e.duration))):e.kind=="rush"?t("ev_rush",J(e.job),e.due!=null?", "+t("due")+" "+num(e.due):""):e.kind=="due_change"?t("ev_due",J(e.job),B(num(e.due))):t("ev_new",e.name,B(e.route.length),B(num(e.due)))}
function afterPlanner(tween=false){const P=PL;
  $("#plK").innerHTML=kstrip(P,P.info?P.info.before:null);$("#plSrc").innerHTML=srcBadge(P);$("#plLg").innerHTML=ganttLegend({down:(P.I.down||[]).length,ghost:P.prev&&st.chg,now:P.now!=null});
  mount("plG",h=>gantt(h,{I:P.I,S:P.S,prev:P.prev,showChg:st.chg,fz:P.fz,now:P.now,changed:RUSH(P),tween:tween?1:0,minW:600}));
  const rows=P.I.routes.map((r,j)=>({j:P.I.jobs[j],route:r.map(o=>MN[o[0]]).join(" → "),rel:P.I.rel[j],due:P.I.due[j],w:P.I.w[j],c:P.k.C[j],tt:P.k.T[j]}));
  tblInit("jobs",[{k:"j",l:t("job")},{k:"route",l:t("route"),h:v=>`<span class="rt">${esc(v)}</span>`},{k:"due",l:t("due"),n:1,f:v=>num(v)},{k:"w",l:t("weight"),n:1,f:v=>num(v)},{k:"c",l:t("compl"),n:1,f:v=>num(v)},
    {k:"tt",l:t("tard"),n:1,h:v=>v>0?`<span class="pill bad">${B("+"+num(v))}</span>`:`<span class="pill ok">${t("onTime")}</span>`,raw:v=>v}],rows,"plan_book"+st.book,{size:12});
  $("#plJobs").innerHTML=tblHTML("jobs",true,false);
  $("#plLog").innerHTML=st.events.length?`<ol class="evlog">${st.events.map((e,i)=>`<li><span class="pn">${B(i+1)}</span><span>${evText(e,P.I)}</span><small>t = ${B(num(e.time))}</small></li>`).join("")}</ol>`:`<div class="empty-st" style="min-height:90px">${t("noEv")}</div>`;
  drawChat()}
function drawChat(){const c=$("#chat");if(!c)return;c.innerHTML=[{a:1,kind:"hello"},...st.msgs].map(msgHTML).join("");c.scrollTop=c.scrollHeight}
function msgHTML(m){if(!m.a)return `<div class="msg u"><bdi>${esc(m.text)}</bdi></div>`;let h="";
  if(m.kind=="hello")h=t("hello");else if(m.kind=="help")h=t("help");else if(m.kind=="nu")h=t("notUnd");else if(m.kind=="err")h=m.errs.map(e=>t(e[0],...(e.slice(1)))).join(" ");
  else if(m.kind=="undo")h=t(m.ok?"undone":"nothing");else if(m.kind=="reset")h=t("resetDone");else if(m.kind=="method")h=t("mSwitch",`<b>${mName(m.m)}</b>`)+(m.res?resLine(m.res):"");
  else if(m.kind=="cmp"){const mx=Math.max(...m.rows.map(r=>r[1]));h=`${t("cmpRes",B(m.book))}<div class="mini">${m.rows.map(r=>`<div><span>${r[0]=="OPT"?"CP-SAT":r[0]}</span>${cell(r[1],mx,r[0]=="OPT"?C.em:r[1]==m.bestRule?C.gold:C.steel,num(r[1]))}</div>`).join("")}</div>`}
  else if(m.kind=="ev")h=`<div class="act">${m.acts.map(e=>`<code>${esc(JSON.stringify(e))}</code>`).join("")}</div>${(m.notes||[]).map(n=>`<div class="mn">${t(n[0],...(n.slice(1)))}</div>`).join("")}${resLine(m.res)}`;
  return `<div class="msg a"><span class="av"><b>MH</b></span><div>${h}</div></div>`}
function resLine(r){if(!r)return"";const ar=st.lang=="ar"?"←":"→",f=(a,b)=>`${B(num(a))} ${ar} ${B(num(b))}`;
  return `<div class="res"><div><span>${t("wt")}</span><b>${f(r.wt0,r.wt1)}</b></div><div><span>${t("late")}</span><b>${f(r.l0,r.l1)}</b></div><div><span>${t("movedOps")}</span><b>${B(num(r.mv))}</b></div><div><span>${t("moved")}</span><b>${B(num(r.dev))}</b></div>
   <div><span>${t("bott")}</span><b>${esc(r.bott)}</b></div><div><span>${t("checker")}</span><b class="${r.err?"bad":"okc"}">${r.err?t("viol",B(r.err)):t("feasible")}</b></div></div><div class="srcl ${r.src=="pre"?"pre":""}">${r.src=="pre"?t("srcPre"):t("srcLive")}</div>${r.src=="fb"?`<div class="mn">${t("fbNote")}</div>`:""}`}
function snapRes(){const P=PL;if(!P.info)return null;return{wt0:P.info.before.wt,wt1:P.k.wt,l0:P.info.before.late,l1:P.k.late,mv:P.info.dev.mv,dev:P.info.dev.dev,bott:P.k.bottleneck,err:P.errs.length,src:P.src}}

/* ===== Copilot parser (EN / ID / AR, rule-based, offline) ===== */
const AR_D="٠١٢٣٤٥٦٧٨٩",FA_D="۰۱۲۳۴۵۶۷۸۹";
function normCmd(s){return s.toLowerCase().replace(/[٠-٩]/g,c=>AR_D.indexOf(c)).replace(/[۰-۹]/g,c=>FA_D.indexOf(c)).replace(/،/g,",").replace(/[–—]/g,"-").replace(/\s+/g," ").trim()}
const TM="(\\d+(?:[.,]\\d+)?(?:\\s*(?:h|jam|hours?|ساعة|ساعات)(?:\\s*\\d+)?)?)(?:\\s*(?:min|mins|minutes|menit|mnt|m|دقيقة|دقائق|د)\\b)?";
function ptime(s){if(s==null)return null;s=s.trim().replace(",",".");const h=s.match(/^(\d+(?:\.\d+)?)\s*(?:h|jam|hours?|ساعة|ساعات)\s*(\d+)?$/);if(h)return Math.round(+h[1]*60)+(+(h[2]||0));const m=s.match(/^(\d+)/);return m?+m[1]:null}
function findMachines(s){const out=[];MALIAS.forEach((al,m)=>al.forEach(a=>{const re=/^[a-z]+$/.test(a)?new RegExp("\\b"+a+"\\b","g"):new RegExp(a,"g");let x;while((x=re.exec(s)))out.push({m,i:x.index,len:a.length})}));
  let x;const re=/\bm([1-9])\b/g;while((x=re.exec(s)))out.push({m:+x[1]-1,i:x.index,len:x[0].length,bad:+x[1]>MN.length});return out.sort((a,b)=>a.i-b.i)}
const kw=(s,list)=>{for(const k of list){const re=new RegExp("(?:^|[^a-z\\u0600-\\u06ff])(?:"+k+")\\s*"+TM,"i"),x=s.match(re);if(x)return ptime(x[1])}return null};
const K_START=["at","from","pada","jam","mulai","dari","sejak","عند","من","منذ","الساعة"],K_DUR=["for","selama","durasi","لمدة","مدة","مدته"],K_END=["to","until","till","sampai","hingga","إلى","الى","حتى","لغاية"],K_DUE=["due","due at","deadline","jatuh tempo","tenggat","batas","موعد","موعده","تسليم","بحلول"],K_W=["weight","bobot","وزن","الوزن"];
function parseCmd(raw,I,now){const s=normCmd(raw),acts=[],notes=[],errs=[];const has=re=>re.test(s);
  const jobs=[...s.matchAll(/\bj(?:ob)?\s*(\d+)\b/g)].map(x=>+x[1]);
  if(has(/^(help|bantuan|tolong|مساعدة|ساعدني|\?)$/)||has(/\b(help|bantuan)\b|مساعدة/))return{meta:"help"};
  if(has(/\bundo\b|\bbatal|تراجع/))return{meta:"undo"};
  if(has(/\breset\b|start over|mulai ulang|إعادة ضبط|ابدأ من جديد|من البداية/))return{meta:"reset"};
  if(has(/compare|bandingkan|banding|قارن|مقارنة/))return{meta:"cmp"};
  if(has(/new (?:job|order)|job baru|pesanan baru|order baru|أمر جديد|طلب جديد|امر جديد/)){
    const cut=s.search(/\bdue\b|jatuh tempo|tenggat|deadline|موعد|تسليم|\bweight\b|bobot|وزن/),body=cut>0?s.slice(0,cut):s,route=[];
    findMachines(body).forEach(f=>{const x=body.slice(f.i+f.len).match(/^\s*[:=]?\s*(\d+)/);if(x&&!f.bad)route.push([f.m,+x[1]])});
    if(!route.length){errs.push(["notUnd"]);return{errs}}
    const due=kw(s,K_DUE),w=kw(s,K_W),at=kw(s,["at","pada","عند"]),time=at!=null&&at!==due?at:now,work=sum(route.map(r=>r[1]));
    acts.push({kind:"new_job",route,due:due!=null?due:time+2*work,weight:w||1,time,name:"J"+(I.routes.length+1)});
  }else{
    const ms=findMachines(s),brk=has(/down|broke|break|fail|stop|rusak|mati|mogok|berhenti|macet|عطل|معطل|معطّل|متوقف|توقف|خرب|تعطل|تعطّل/);
    if(brk&&ms.length){const f=ms[0];if(f.bad)errs.push(["unkM"]);else{
      let st0=kw(s,K_START),du=kw(s,K_DUR),en=kw(s,K_END);const rg=s.match(new RegExp(TM+"\\s*-\\s*"+TM));if(rg&&st0==null&&en==null){st0=ptime(rg[1]);en=ptime(rg[2])}
      if(st0==null&&du==null&&en==null){const ns=[...s.replace(/\bm[1-9]\b/g,"").matchAll(/\d+/g)].map(x=>+x[0]);if(ns.length){st0=ns[0];du=ns[1]!=null?ns[1]:null}}
      if(st0==null){st0=now;notes.push(["asmNow",B(num(now))])}
      if(du==null&&en!=null)du=en-st0;if(du==null){du=60;notes.push(["asm60"])}
      if(!(st0>=0&&st0<=2000&&du>0&&du<=2000))errs.push(["badT"]);else acts.push({kind:"breakdown",machine:f.m,time:st0,duration:du})}}
    else if(has(/rush|prioriti|expedite|urgent|asap|percepat|prioritas|mendesak|segera|استعجل|استعجال|عاجل|أولوية|اولوية|سرّع|سرع/)&&jobs.length){
      jobs.forEach(n=>{if(n<1||n>I.routes.length)errs.push(["unkJ","J"+n]);else acts.push({kind:"rush",job:n-1,weight:5,due:kw(s,K_DUE),time:kw(s,["at","pada","عند"])??60})})}
    else if(has(/due|deadline|jatuh tempo|tenggat|موعد|تسليم|بحلول/)&&jobs.length){const due=kw(s,K_DUE)??(()=>{const x=s.replace(/\bj(?:ob)?\s*\d+\b/g,"").match(/\d+/);return x?+x[0]:null})();
      const n=jobs[0];if(n<1||n>I.routes.length)errs.push(["unkJ","J"+n]);else if(due==null||due<0||due>3000)errs.push(["badT"]);else acts.push({kind:"due_change",job:n-1,due,time:now})}
    else{const mth=has(/stab|nervous|minimi[sz]e changes|don.?t move|ثابت|استقرار|مستقر/)?"stable":has(/right.?shift|keep (?:the )?sequence|geser|إزاحة|ازاحة/)?"right_shift":has(/re.?opt|full|best possible|optimasi ulang|penuh|optimal|أمثلة|الأمثل|كاملة/)?"reoptimize":null;
      if(mth)return{meta:"method",m:mth};
      if(ms.length&&!brk)errs.push(["notUnd"])}}
  if(!acts.length&&!errs.length)errs.push(["notUnd"]);return{acts,notes,errs}}
function runCmd(text){if(!text.trim())return;st.msgs.push({text});const P0=plan(),now=st.events.length?st.events[st.events.length-1].time:60,r=parseCmd(text,P0.I,now);let tween=false;
  if(r.meta=="help")st.msgs.push({a:1,kind:"help"});
  else if(r.meta=="undo"){const ok=st.events.length>0;st.events.pop();st.msgs.push({a:1,kind:"undo",ok});tween=ok}
  else if(r.meta=="reset"){st.events=[];st.msgs.push({a:1,kind:"reset"});tween=true}
  else if(r.meta=="method"){st.method=r.m;plan();st.msgs.push({a:1,kind:"method",m:r.m,res:snapRes()});tween=true}
  else if(r.meta=="cmp"){const I=baseInst(st.book),rows=[["OPT",kpis(I,BK[st.book].opt).wt],...D.rules.map(k=>[k,kpis(I,dispatch(I,k)).wt])];st.msgs.push({a:1,kind:"cmp",book:st.book,rows,bestRule:Math.min(...rows.slice(1).map(x=>x[1]))})}
  else if(r.errs&&r.errs.length)st.msgs.push({a:1,kind:"err",errs:r.errs});
  else{r.acts.forEach(a=>st.events.push(a));plan();st.msgs.push({a:1,kind:"ev",acts:r.acts,notes:r.notes,res:snapRes()});tween=true}
  plan();st.anim=true;redraw.length=0;afterPlanner(tween);st.anim=false;writeHash()}

/* ===== Rules vs optimal ===== */
function pRules(){return `<div class="grid g2">${card(t("ruT"),t("ruS"),`<div class="chart" id="ruWT"></div>`,`<span class="pill ok">${t("optShare",B(Math.round(RV["weighted_tardiness|CP-SAT"].optimal_share*30)))}</span>`)}${card(t("ruT2"),t("ruS2"),`<div class="chart" id="ruMK"></div>`)}</div>
  <div class="note" style="margin-bottom:18px">${ic("info")}<span>${t("rDesc")}</span></div>
  ${card(t("ruT3"),t("ruS3"),legend([["CP-SAT",C.em],[RULES_WT[0][0],C.gold],["FIFO",C.steel]])+`<div class="chart" id="ruBook"></div>`)}
  <div class="grid g2">${card(t("ruLive"),t("ruLiveS"),`<div class="bar" style="margin:0 0 8px"><label class="ctl">${ic("book")}<span>${t("book")}</span><select id="selRB">${D.books.map(b=>`<option value="${b.seed}" ${b.seed==st.rbook?"selected":""}>${num(b.seed)}</option>`).join("")}</select></label></div><div class="chart" id="ruLive"></div>`)}
  ${card(t("ruT4"),t("ruS4"),`<div id="ruTbl"></div>`)}</div>`}
const methCols=m=>m=="CP-SAT"?C.em:C.steel;
function afterRules(){const ms=["CP-SAT",...RULES_WT.map(r=>r[0])],mk=["CP-SAT",...RULES_MK.map(r=>r[0])];
  mount("ruWT",h=>barChart(h,{cats:ms,labels:1,series:[{name:t("wt"),vals:ms.map(m=>rvMean("weighted_tardiness",m)),colors:ms.map((m,i)=>m=="CP-SAT"?C.em:i==1?C.gold:C.steel)}],yfmt:v=>num(v),h:260,bmax:46}));
  mount("ruMK",h=>barChart(h,{cats:mk,labels:1,series:[{name:t("mk"),vals:mk.map(m=>rvMean("makespan",m)),colors:mk.map((m,i)=>m=="CP-SAT"?C.em:i==1?C.gold:C.steel)}],yfmt:v=>num(v),h:260,bmax:46}));
  const by={};D.study.rvruns.forEach(([s,o,m,v])=>{if(o=="weighted_tardiness")(by[s]=by[s]||{})[m]=v});const seeds=Object.keys(by).map(Number).sort((a,b)=>a-b),br=RULES_WT[0][0];
  mount("ruBook",h=>dotRange(h,{cats:seeds,series:[{name:"FIFO",color:C.steel,vals:seeds.map(s=>by[s].FIFO)},{name:br,color:C.gold,vals:seeds.map(s=>by[s][br])},{name:"CP-SAT",color:C.em,vals:seeds.map(s=>by[s]["CP-SAT"])}],tl:c=>t("seed")+" "+num(c),h:250}));
  liveRules();
  tblInit("rv",[{k:"seed",l:t("seed"),n:1,f:v=>num(v)},...["CP-SAT",...D.rules].map(m=>({k:m,l:m,n:1,h:(v,x)=>{const mn=Math.min(...["CP-SAT",...D.rules].map(q=>x[q]));return v==mn?`<b class="okc">${B(num(v))}</b>`:B(num(v))},raw:v=>v}))],seeds.map(s=>({seed:s,...by[s]})),"rules_vs_optimal_wt",{size:10});
  $("#ruTbl").innerHTML=tblHTML("rv",true,false)}
function liveRules(){const I=baseInst(st.rbook),rows=[["CP-SAT",kpis(I,BK[st.rbook].opt).wt],...D.rules.map(k=>[k,kpis(I,dispatch(I,k)).wt])],o=rows[0][1];
  mount("ruLive",h=>barChart(h,{cats:rows.map(r=>r[0]),labels:1,series:[{name:t("wt"),vals:rows.map(r=>r[1]),colors:rows.map((r,i)=>i?C.steel:C.em)}],yfmt:v=>num(v),h:240,bmax:38,
    tipx:i=>i?`<div class="tf">${t("gapOpt")}: ${B("+"+num(rows[i][1]-o))}</div>`:""}))}

/* ===== Disruptions ===== */
const DM=["right_shift","reoptimize","stable"],DCOL={right_shift:C.rose,reoptimize:C.steel,stable:C.em};
function pDis(){const rs=DIS.right_shift,re=DIS.reoptimize,sb=DIS.stable;
  return `<div class="grid g4">${DM.map(m=>{const d=DIS[m];return kpi(mName(m),CU(d.weighted_tardiness,"n",0),`${t("late")} ${B(num(d.late_jobs,1))} · ${t("moved")} ${B(num(d.deviation_min))}`,`<span class="dotl" style="--c:${DCOL[m]}"></span>`,"std")}).join("")}
    ${kpi(t("pWt"),CU(PAIR["right_shift>reoptimize"].wt_diff,"s",0),`± ${B(num(PAIR["right_shift>reoptimize"].wt_ci))} · ${mName("reoptimize")} vs ${mName("right_shift")}`,`<span class="pill ok">95% CI</span>`,"std")}</div>
  ${card(t("diT"),t("diS"),`<div class="grid g3" style="margin:0">${[["wt","weighted_tardiness",0],["late","late_jobs",1],["moved","deviation_min",0]].map(([l,k,d])=>`<div><div class="sm-title">${t(l)}</div><div class="chart" id="di_${k}"></div></div>`).join("")}</div>`)}
  <div class="grid g2">${card(t("diP"),t("diPS"),`<div class="sm-title">${t("pWt")}</div><div class="chart" id="diPW"></div><div class="sm-title" style="margin-top:12px">${t("pDev")}</div><div class="chart" id="diPD"></div>`)}
  ${card(t("diStab"),t("diStabS"),`<div class="chart" id="diSt"></div><div class="note" style="margin-top:10px">${ic("info")}<span id="diInf"></span></div>`)}</div>
  ${card(t("diRuns"),t("diRunsS"),`<div id="diTbl"></div>`)}`}
function afterDis(){const nm=DM.map(mName),ml=st.lang=="ar"?130:st.lang=="id"?150:150;
  [["weighted_tardiness",0],["late_jobs",1],["deviation_min",0]].forEach(([k,d])=>mount("di_"+k,h=>hbarCI(h,{rows:DM.map((m,i)=>({label:nm[i],v:DIS[m][k],ci:DIS[m][k+"_ci"],color:DCOL[m]})),fmt:(v,x)=>num(v,x?d:0),ml:Math.min(ml,h.clientWidth*.42)})));
  const pr=D.study.pair.map(p=>({label:mName(p.to)+" − "+mName(p.from),v:p.wt_diff,ci:p.wt_ci})),pd=D.study.pair.map(p=>({label:mName(p.to)+" − "+mName(p.from),v:p.dev_diff,ci:p.dev_ci}));
  mount("diPW",h=>forest(h,{rows:pr,ml:Math.min(260,h.clientWidth*.48)}));mount("diPD",h=>forest(h,{rows:pd,ml:Math.min(260,h.clientWidth*.48)}));
  const S2=D.study.stab.filter(r=>r.stability<1e8),inf=D.study.stab.find(r=>r.stability>1e8),grp={};S2.forEach(r=>{const k=r.deviation_min+"|"+r.weighted_tardiness;(grp[k]=grp[k]||[]).push(r)});
  const pts=Object.values(grp).map(g=>({x:g[0].deviation_min,y:g[0].weighted_tardiness,l:"w = "+g.map(r=>num(r.stability,r.stability>0&&r.stability<.1?2:1)).join(" · "),hl:g.some(r=>r.stability==0.2)}));
  [...pts].sort((a,b)=>a.x-b.x).forEach((p,i)=>{if(i%2){p.dy=20;p.dx=6}});
  $("#diInf").innerHTML=t("frozenOnly",B(num(inf.weighted_tardiness)),B(num(inf.deviation_min)));
  mount("diSt",h=>frontier(h,{pts,xl:t("moved"),yl:t("wt"),h:300}));
  tblInit("dr",[{k:0,l:t("seed"),n:1,f:v=>num(v)},{k:1,l:t("method"),f:v=>mName(v),h:v=>`<span class="dotl" style="--c:${DCOL[v]}">${mName(v)}</span>`},{k:2,l:t("machine")},{k:3,l:t("start"),n:1,f:v=>num(v)},{k:4,l:t("dur"),n:1,f:v=>num(v)},
    {k:5,l:t("wt")+" · "+t("before"),n:1,f:v=>num(v)},{k:6,l:t("wt")+" · "+t("after"),n:1,f:v=>num(v)},{k:7,l:t("moved"),n:1,f:v=>num(v)},{k:8,l:t("movedOps"),n:1,f:v=>num(v)}],D.study.disruns,"disruption_runs",{size:12});
  $("#diTbl").innerHTML=tblHTML("dr")}

/* ===== Benchmarks ===== */
function pBench(){const ok=BENCH.filter(r=>r.cpsat==r.optimum).length,slow=BENCH.reduce((a,b)=>b.cpsat_seconds>a.cpsat_seconds?b:a),cnt={};BENCH.forEach(r=>r.bestRules.split(" · ").forEach(k=>cnt[k]=(cnt[k]||0)+1));const top=Object.entries(cnt).sort((a,b)=>b[1]-a[1]);
  return `<div class="grid g4">${kpi(t("bmK1"),`${CU(ok,"n",0)}<small>/ ${B(BENCH.length)}</small>`,"ft06 · ft10 · la01–05 · la16 · la19 · abz5",`<span class="pill ok">OPTIMAL</span>`,"std")}
   ${kpi(t("bmK2"),`${CU(slow.cpsat_seconds,"n",1)}<small>s</small>`,`${slow.instance} · ${slow.size}`,"","std")}
   ${kpi(t("bmK3"),`${CU(mean(BENCH.map(r=>r.gap))*100,"n",1)}<small>%</small>`,t("bestRule")+" vs "+t("optimum"),`<span class="pill wn">${t("bmG").split(",")[0]}</span>`,"std")}
   ${kpi(t("bmK4"),`${CU(mean(BENCH.map(r=>r.cpsat_seconds)),"n",1)}<small>s</small>`,t("secs")+" · ≤ 60 s",`<span class="pill mu">CP-SAT</span>`,"std")}</div>
  ${card(t("bmG"),t("bmGS"),`<div class="chart" id="bmGap"></div>`)}${card(t("bmT"),t("bmS"),`<div id="bmTbl"></div>`)}`}
function afterBench(){mount("bmGap",h=>barChart(h,{cats:BENCH.map(r=>r.instance),labels:1,series:[{name:t("bestRule"),vals:BENCH.map(r=>r.gap*100),colors:BENCH.map(()=>C.gold)}],yfmt:v=>num(v,0)+"%",lfmt:v=>num(v,1),h:270,bmax:48,
    tipx:i=>`<div class="tf">${esc(BENCH[i].bestRules)} · ${B(num(BENCH[i].best))} vs ${B(num(BENCH[i].optimum))}</div>`}));
  tblInit("bm",[{k:"instance",l:t("inst")},{k:"size",l:t("size")},{k:"optimum",l:t("optimum"),n:1,f:v=>num(v)},{k:"cpsat",l:"CP-SAT",n:1,h:(v,x)=>`<b class="${v==x.optimum?"okc":"bad"}">${B(num(v))}</b>`,raw:v=>v},{k:"cpsat_seconds",l:t("secs"),n:1,f:v=>num(v,2)},
    {k:"best",l:t("bestRule"),n:1,f:v=>num(v)},{k:"gap",l:"%",n:1,h:v=>cell(v,.3,C.gold,"+"+num(v*100,1)+"%"),raw:v=>(v*100).toFixed(1)},{k:"bestRules",l:t("method")}],BENCH,"benchmarks",{size:10});$("#bmTbl").innerHTML=tblHTML("bm",true,false)}

/* ===== Method & sources ===== */
const REFS=[["Giffler, B., & Thompson, G. L. (1960). Algorithms for solving production-scheduling problems. Operations Research, 8(4), 487–503.","https://doi.org/10.1287/opre.8.4.487"],
["Panwalkar, S. S., & Iskander, W. (1977). A survey of scheduling rules. Operations Research, 25(1), 45–61.","https://doi.org/10.1287/opre.25.1.45"],
["Baker, K. R. (1984). Sequencing rules and due-date assignments in a job shop. Management Science, 30(9), 1093–1104.","https://doi.org/10.1287/mnsc.30.9.1093"],
["Vieira, G. E., Herrmann, J. W., & Lin, E. (2003). Rescheduling manufacturing systems: A framework of strategies, policies, and methods. Journal of Scheduling, 6(1), 39–62.","https://doi.org/10.1023/A:1022235519958"],
["Ouelhadj, D., & Petrovic, S. (2009). A survey of dynamic scheduling in manufacturing systems. Journal of Scheduling, 12(4), 417–431.","https://doi.org/10.1007/s10951-008-0090-8"],
["Zhang, L., et al. (2026). DScheLLM: Enabling dynamic scheduling through a fine-tuned dual-system large language model. arXiv:2601.09100.","https://arxiv.org/abs/2601.09100"],
["Yan, J., & Ji, S. (2026). Industrial mechanism-aware multi-agent collaboration of large language models for job shop scheduling optimization. Computers & Industrial Engineering, 217, 112079.",""],
["Perron, L., & Didier, F. CP-SAT, Google OR-Tools (v9.15).","https://developers.google.com/optimization"],
["Fisher, H., & Thompson, G. L. (1963) in Muth & Thompson (Eds.), Industrial Scheduling; Lawrence, S. (1984); Adams, J., Balas, E., & Zawack, D. (1988), Management Science, 34(3), 391–401. Collected in JSPLIB.","https://github.com/tamy0612/JSPLIB"]];
function pMethod(){const ul=a=>`<ul>${a.map(x=>`<li>${x}</li>`).join("")}</ul>`;
  return `${card(t("pipeT"),t("pipeS"),`<ol class="pipe">${[1,2,3,4,5].map(i=>`<li><span class="pn">${B(i)}</span><b>${t("p"+i)}</b><small>${t("p"+i+"d")}</small></li>`).join("")}</ol>`)}
  <div class="grid g2"><div class="card prose"><h3>${ic("bolt")} ${t("mtLive")}</h3>${ul(tl("mtLiveL"))}</div><div class="card prose"><h3>${ic("check")} ${t("mtPre")}</h3>${ul(tl("mtPreL"))}</div></div>
  <div class="grid g2"><div class="card prose"><h3>${t("mtLim")}</h3>${ul(tl("mtLimL"))}</div><div class="card prose"><h3>${t("mtData")}</h3>${ul(tl("mtDataL"))}</div></div>
  <div class="card prose refs" dir="ltr"><h3>${t("mtRef")}</h3><ol>${REFS.map(r=>`<li>${esc(r[0])}${r[1]?` <a href="${r[1]}" target="_blank" rel="noopener">${esc(r[1].replace("https://",""))}</a>`:""}</li>`).join("")}</ol></div>`}

/* ===== Shell, router, URL state ===== */
const RENDER={ov:[pOverview,afterOverview],pl:[pPlanner,()=>afterPlanner(false)],ru:[pRules,afterRules],di:[pDis,afterDis],bm:[pBench,afterBench],mt:[pMethod,()=>{}]};
function shell(){
  const navBtns=PAGES.map(p=>`<button class="${p==st.page?"on":""}" data-p="${p}">${ic(p)}<span>${t("n_"+p)}</span>${p=="pl"&&st.events.length?`<span class="nb">${B(st.events.length)}</span>`:""}</button>`).join("");
  $("#side").innerHTML=`<div class="brand"><div class="mark"><b>MH</b></div><div><strong>SCHEDULING COPILOT</strong><span>${t("tag")}</span></div></div><div class="navlbl">${t("navLbl")}</div><nav class="nav">${navBtns}</nav>
    <div class="side-foot"><div class="simcard"><b>${t("simT")}</b><span>${t("simS")}</span></div><div class="byline">${t("builtBy")} <b>Muatasem Hadi</b><br>${t("role")}</div></div>`;
  $("#bnav").innerHTML=PAGES.map(p=>`<button class="${p==st.page?"on":""}" data-p="${p}">${ic(p)}<span>${t("n_"+p).split(" ")[0]}</span></button>`).join("");
  $("#top").innerHTML=`<div class="crumb"><small>${t("d_"+st.page)}</small><h1>${t("n_"+st.page)}</h1></div>
   <div class="tools-top"><span class="period">${t("book")} <b>${B(num(st.book))}</b> · ${B(num(NB))}</span>
   <button class="chipbtn" data-cmdk>${ic("search")}<span class="lbl">${t("cmdShort")}</span><kbd>Ctrl K</kbd></button>
   <div class="seg" role="group" aria-label="${t("cLang")}">${LANGS.map(l=>`<button data-lang="${l}" class="${l==st.lang?"on":""}" title="${S.langName[LANGS.indexOf(l)]}">${{en:"EN",id:"ID",ar:"ع"}[l]}</button>`).join("")}</div>
   <div class="seg" role="group" aria-label="${t("cTheme")}">${[["light","sun"],["dark","moon"],["system","sys"]].map(([k,i])=>`<button data-theme="${k}" class="${k==st.theme?"on":""}" title="${t(k)}" aria-label="${t(k)}">${ic(i)}</button>`).join("")}</div></div>`;
}
function writeHash(){const q=new URLSearchParams({p:st.page,l:st.lang,th:st.theme});if(st.book!=1)q.set("b",st.book);if(st.base!="OPT")q.set("base",st.base);if(st.method!="stable")q.set("m",st.method);
  if(st.events.length)q.set("ev",JSON.stringify(st.events));if(st.rbook!=1)q.set("rb",st.rbook);try{history.replaceState(null,"","#"+q.toString())}catch(e){}}
function readHash(){const q=new URLSearchParams(location.hash.slice(1)),g=k=>q.get(k);
  if(PAGES.includes(g("p")))st.page=g("p");if(LANGS.includes(g("l")))st.lang=g("l");else if(LANGS.includes(store("lang")))st.lang=store("lang");
  if(["light","dark","system"].includes(g("th")))st.theme=g("th");else if(["light","dark","system"].includes(store("theme")))st.theme=store("theme");
  if(BK[+g("b")])st.book=+g("b");if(D.rules.includes(g("base")))st.base=g("base");if(DM.includes(g("m")))st.method=g("m");if(BK[+g("rb")])st.rbook=+g("rb");
  if(g("ev")){try{const e=JSON.parse(g("ev"));if(Array.isArray(e)&&e.length<20&&e.every(x=>["breakdown","rush","due_change","new_job"].includes(x.kind)))st.events=e}catch(err){}}}
function render(anim=true){st.anim=anim;redraw.length=0;const H=document.documentElement;H.lang=st.lang;H.dir=st.lang=="ar"?"rtl":"ltr";
  document.title="Production Scheduling Copilot · "+t("n_"+st.page);shell();const [pg,after]=RENDER[st.page];
  $("#app").innerHTML=`<div class="page">${pg()}</div>`;after();countUp();writeHash();st.anim=false}
function rerender(){const y=scrollY;st.anim=false;redraw.length=0;const [pg,after]=RENDER[st.page];$("#app").innerHTML=`<div>${pg()}</div>`;after();shell();writeHash();scrollTo(0,y)}
function applyTheme(){const dark=st.theme=="dark"||(st.theme=="system"&&matchMedia("(prefers-color-scheme: dark)").matches);document.documentElement.dataset.theme=dark?"dark":"light"}

/* ===== Command palette ===== */
let cmdSel=0,cmdList=[];
function cmdItems(){return [...PAGES.map(p=>({ic:p,l:t("n_"+p),g:t("cPage"),run:()=>go(p)})),
  ...["q_bd","q_bd2","q_rush","q_due","q_cmp"].map(q=>({ic:"chat",l:t(q),kw:"copilot command perintah أمر",g:t("cCmd"),run:()=>{st.page="pl";render(true);setTimeout(()=>runCmd(t(q)),30)}})),
  ...D.books.map(b=>({ic:"book",l:t("book")+" "+num(b.seed)+(b.sc?" ★":""),kw:"book buku دفتر seed "+b.seed,g:t("cBook"),run:()=>{st.book=b.seed;st.events=[];st.msgs=[];go("pl")}})),
  ...LANGS.map((l,i)=>({ic:"globe",l:S.langName[i],kw:["english inggris إنجليزية","indonesian indonesia إندونيسية","arabic arab عربي"][i],g:t("cLang"),run:()=>setLang(l)})),
  ...[["light","sun"],["dark","moon"],["system","sys"]].map(([k,i])=>({ic:i,l:t(k),g:t("cTheme"),run:()=>setTheme(k)})),
  {ic:"link",l:t("copyLink"),g:t("cAct"),run:()=>{writeHash();(navigator.clipboard?navigator.clipboard.writeText(location.href):Promise.reject()).then(()=>toast(t("linkOk"))).catch(()=>toast(location.href))}},
  {ic:"print",l:t("print"),g:t("cAct"),run:()=>setTimeout(()=>print(),150)}]}
function cmdRender(){const q=$("#cmdq").value.trim().toLowerCase();cmdList=cmdItems().filter(x=>!q||(x.l+" "+(x.kw||"")+" "+x.g).toLowerCase().includes(q)).slice(0,40);cmdSel=Math.min(cmdSel,Math.max(0,cmdList.length-1));
  $("#cmdl").innerHTML=cmdList.map((x,i)=>`<li class="${i==cmdSel?"on":""}" data-ci="${i}">${ic(x.ic)}<span>${x.l}</span><small>${x.g}</small></li>`).join("")||`<li>${t("noRes")}</li>`}
function cmdOpen(){$("#cmdk").classList.add("on");$("#cmdq").placeholder=t("cmd");$("#cmdf").innerHTML=`<span><kbd>↑↓</kbd> ${t("cmdNav")}</span><span><kbd>↵</kbd> ${t("cmdOpen")}</span><span><kbd>Esc</kbd> ${t("cmdClose")}</span>`;$("#cmdq").value="";cmdSel=0;cmdRender();setTimeout(()=>$("#cmdq").focus(),10)}
function cmdClose(){$("#cmdk").classList.remove("on")}
function go(p){if(p!="ov"&&st.playing)togglePlay();st.page=p;render(true);scrollTo({top:0})}
function setLang(l){st.lang=l;store("lang",l);render(false)}
function setTheme(k){st.theme=k;store("theme",k);applyTheme();render(false)}

/* ===== Events ===== */
document.addEventListener("click",e=>{
  const n=e.target.closest("[data-p]");if(n){go(n.dataset.p);return}
  const L=e.target.closest("[data-lang]");if(L){setLang(L.dataset.lang);return}
  const Th=e.target.closest("[data-theme]");if(Th&&Th.tagName=="BUTTON"){setTheme(Th.dataset.theme);return}
  if(e.target.closest("[data-cmdk]")){cmdOpen();return}
  if(e.target.id=="cmdk"){cmdClose();return}
  const ci=e.target.closest("[data-ci]");if(ci){const x=cmdList[+ci.dataset.ci];cmdClose();x&&x.run();return}
  const sy=e.target.closest("[data-story]");if(sy){if(st.playing)togglePlay();setStory(+sy.dataset.story);return}
  if(e.target.closest("[data-play]")){togglePlay();return}
  if(e.target.closest("[data-openstory]")){st.book=STORY.b;st.base="OPT";st.method=st.story==1?"right_shift":"stable";st.events=st.story?[{kind:"breakdown",machine:STORY.m,time:STORY.t0,duration:STORY.d}]:[];st.msgs=[];go("pl");return}
  const mt=e.target.closest("[data-method]");if(mt){st.method=mt.dataset.method;$$("[data-method]").forEach(b=>b.classList.toggle("on",b==mt));plan();st.anim=true;redraw.length=0;afterPlanner(true);st.anim=false;writeHash();return}
  if(e.target.closest("[data-reset-plan]")){st.events=[];st.msgs=[];plan();st.anim=true;redraw.length=0;afterPlanner(true);st.anim=false;shell();writeHash();return}
  const qq=e.target.closest("[data-q]");if(qq&&qq.tagName=="BUTTON"&&qq.closest(".qc")){runCmd(t(qq.dataset.q));shell();return}
  const th=e.target.closest("[data-s]");if(th){const [id,i]=th.dataset.s.split(":"),T=TB[id];T.dir=T.sort==+i?-T.dir:1;T.sort=+i;T.page=0;tblRefresh(id);return}
  const pg=e.target.closest("[data-pg]");if(pg){const [id,d]=pg.dataset.pg.split(":");TB[id].page+=+d;tblRefresh(id);return}
  const c=e.target.closest("[data-csv]");if(c)exportCSV(c.dataset.csv);
});
document.addEventListener("submit",e=>{if(e.target.id=="chatF"){e.preventDefault();const i=$("#chatI");runCmd(i.value);i.value="";shell();i.focus()}});
document.addEventListener("change",e=>{
  if(e.target.id=="selBook"){st.book=+e.target.value;st.events=[];st.msgs=[];rerender();return}
  if(e.target.id=="selBase"){st.base=e.target.value;rerender();return}
  if(e.target.id=="chg"){st.chg=e.target.checked;redraw.length=0;afterPlanner(false);return}
  if(e.target.id=="selRB"){st.rbook=+e.target.value;st.anim=true;liveRules();st.anim=false;writeHash()}});
document.addEventListener("keydown",e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()=="k"){e.preventDefault();$("#cmdk").classList.contains("on")?cmdClose():cmdOpen();return}
  if($("#cmdk").classList.contains("on")){if(e.key=="Escape")cmdClose();else if(e.key=="ArrowDown"){cmdSel=Math.min(cmdList.length-1,cmdSel+1);cmdRender();e.preventDefault()}else if(e.key=="ArrowUp"){cmdSel=Math.max(0,cmdSel-1);cmdRender();e.preventDefault()}else if(e.key=="Enter"){const x=cmdList[cmdSel];cmdClose();x&&x.run()}return}});
document.addEventListener("input",e=>{if(e.target.id=="cmdq"){cmdSel=0;cmdRender();return}
  if(e.target.dataset.q&&TB[e.target.dataset.q]){const id=e.target.dataset.q;TB[id].q=e.target.value;TB[id].page=0;tblRefresh(id)}});
let rz,lastW=innerWidth;addEventListener("resize",()=>{clearTimeout(rz);rz=setTimeout(()=>{if(Math.abs(innerWidth-lastW)<2)return;lastW=innerWidth;st.anim=false;redraw.forEach(f=>f())},140)});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change",()=>{if(st.theme=="system")applyTheme()});
addEventListener("hashchange",()=>{const before=location.hash;readHash();applyTheme();if("#"+new URLSearchParams(location.hash.slice(1)).toString()!==before||true)render(true)});
readHash();applyTheme();render(true);
