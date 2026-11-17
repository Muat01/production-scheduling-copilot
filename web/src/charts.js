/* ===== Chart engine (hand-built SVG, theme-aware, animated) ===== */
function niceStep(range,n){const r=range/n,e=Math.pow(10,Math.floor(Math.log10(r||1))),f=r/e;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*e}
function ticks(lo,hi,n=4){const s=niceStep(hi-lo,n),a=Math.floor(lo/s)*s,out=[];for(let v=a;;v+=s){out.push(+v.toFixed(10));if(v>=hi-s*1e-6||out.length>20)break}return{t:out,lo:out[0],hi:out[out.length-1]}}
function tipAt(host,html,x,y){let tp=host.querySelector(".tip");if(!tp){tp=document.createElement("div");tp.className="tip";host.appendChild(tp)}tp.dir=st.lang=="ar"?"rtl":"ltr";tp.innerHTML=html;tp.classList.add("on");
  const w=tp.offsetWidth,h=tp.offsetHeight,W=host.clientWidth;let l=x+16;if(l+w>W)l=x-w-16;tp.style.left=Math.max(0,l)+"px";tp.style.top=Math.max(-8,Math.min(y-h/2,host.clientHeight-h))+"px"}
function tipOff(host){const tp=host.querySelector(".tip");if(tp)tp.classList.remove("on")}
const trow=(c,n,v)=>`<div class="tr"><span><i style="background:${c}"></i>${n}</span><b>${v}</b></div>`;
function xTickStep(n,W,labelW){return Math.max(1,Math.ceil(n/Math.max(2,Math.floor(W/labelW))))}
/* line chart */
function lineChart(host,o){
  const W=host.clientWidth||600,H=o.h||280,m={l:o.ml||50,r:o.mr||14,t:o.mt||14,b:28},iw=W-m.l-m.r,ih=H-m.t-m.b,n=o.x.length;
  let all=[];o.series.forEach(s=>s.vals.forEach(v=>v!=null&&!isNaN(v)&&all.push(v)));if(o.hline)all.push(o.hline.y);
  const T=o.ymax!=null?{t:ticks(o.ymin??0,o.ymax,4).t,lo:o.ymin??0,hi:o.ymax}:ticks(o.ymin??0,Math.max(...all)*1.06,4),lo=T.lo,hi=T.hi;
  const X=i=>m.l+(n<2?iw/2:i*iw/(n-1)),Y=v=>m.t+ih-(v-lo)/(hi-lo)*ih;
  let g="";
  T.t.forEach((v,k)=>{const y=Y(v);g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${m.l-10}" y="${y+3.5}" text-anchor="end">${o.yfmt(v)}</text>`});
  const lw=o.xw||(st.lang=="ar"?62:50),step=xTickStep(n,iw,lw);
  for(let i=0;i<n;i+=step)g+=`<text x="${X(i)}" y="${H-8}" text-anchor="middle" class="${o.xui?"lbl-ui":""}">${o.xl?o.xl(o.x[i]):o.x[i]}</text>`;
  (o.bands||[]).forEach((b,bi)=>{const hw=iw/Math.max(1,n-1)/2,a=Math.max(m.l,X(b[0])-hw),c=Math.min(W-m.r,X(b[1])+hw);g+=`<rect x="${a}" y="${m.t}" width="${c-a}" height="${ih}" fill="var(--gold2)" opacity=".10"/>`;
    if(o.bandLabel&&bi==0)g+=`<text class="ann" x="${(a+c)/2}" y="${m.t+12}" text-anchor="middle" fill="var(--gold)" style="fill:var(--gold)">${o.bandLabel}</text>`});
  if(o.zone){const y=Y(o.zone.y);g+=`<rect x="${m.l}" y="${m.t}" width="${iw}" height="${Math.max(0,y-m.t)}" fill="var(--bad)" opacity=".07"/><line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--bad)" stroke-width="1.2" stroke-dasharray="4 4" opacity=".8"/>`;
    if(o.zone.label)g+=`<text class="ann" x="${m.l+8}" y="${y-6}" style="fill:var(--bad)">${o.zone.label}</text>`}
  const anim=st.anim&&!reduced();
  o.series.forEach((s,si)=>{let d="",pen=false;s.vals.forEach((v,i)=>{if(v==null||isNaN(v)){pen=false;return}d+=(pen?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1);pen=true});
    if(s.area){const gid="g"+Math.random().toString(36).slice(2,8);g+=`<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" style="stop-color:${s.color};stop-opacity:.28"/><stop offset="1" style="stop-color:${s.color};stop-opacity:0"/></linearGradient></defs><path class="${anim?"fadein":""}" d="${d}L${X(n-1)} ${Y(lo)}L${X(0)} ${Y(lo)}Z" fill="url(#${gid})"/>`}
    const pc=anim?(s.dash?'class="fadein"':'class="draw" pathLength="1"'):"";
    g+=`<path ${pc} style="${anim?`animation-delay:${si*.12}s`:""}" d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.w||2}" stroke-linejoin="round" stroke-linecap="round" ${s.dash?`stroke-dasharray="${s.dash}"`:""} ${s.op?`opacity="${s.op}"`:""}/>`});
  (o.marks||[]).forEach(p=>{g+=`<circle cx="${X(p.i)}" cy="${Y(p.v)}" r="${p.r||3}" fill="${p.c}" stroke="var(--card)" stroke-width="1.5" ${anim?'class="fadein"':""}/>`});
  (o.ann||[]).forEach(a=>{const x=X(a.i),y=Y(a.v);g+=`<g class="${anim?"fadein":""}"><line x1="${x}" x2="${x}" y1="${y-6}" y2="${m.t+20}" stroke="var(--mut)" stroke-dasharray="2 3"/><circle cx="${x}" cy="${y}" r="4" fill="none" stroke="var(--ink)" stroke-width="1.5"/><text class="ann" x="${x}" y="${m.t+14}" text-anchor="${x>W-120?"end":x<120?"start":"middle"}" style="fill:var(--soft)">${a.text}</text></g>`});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}<line class="cx" y1="${m.t}" y2="${m.t+ih}" stroke="var(--line2)" opacity="0"/>${o.series.map(s=>`<circle class="hd" r="4.5" fill="${s.color}" stroke="var(--card)" stroke-width="2.5" opacity="0" pointer-events="none"/>`).join("")}<rect class="hit" x="${m.l}" y="${m.t}" width="${iw}" height="${ih}" fill="transparent"/></svg>`;
  const svg=host.querySelector("svg"),cx=svg.querySelector(".cx"),hds=svg.querySelectorAll(".hd");
  const move=e=>{const r=svg.getBoundingClientRect(),px=(e.clientX-r.left)*(W/r.width);let i=Math.round((px-m.l)/iw*(n-1));i=Math.max(0,Math.min(n-1,i));
    cx.setAttribute("x1",X(i));cx.setAttribute("x2",X(i));cx.setAttribute("opacity",1);
    hds.forEach((c,j)=>{const v=o.series[j].vals[i];if(v==null||isNaN(v)){c.setAttribute("opacity",0);return}c.setAttribute("cx",X(i));c.setAttribute("cy",Y(v));c.setAttribute("opacity",1)});
    tipAt(host,`<div class="th">${o.tl?o.tl(o.x[i],i):o.x[i]}</div>`+o.series.filter(s=>!s.notip).map(s=>s.vals[i]==null||isNaN(s.vals[i])?"":trow(s.color,s.name,o.yfmt(s.vals[i],1))).join("")+(o.tipx?o.tipx(i):""),X(i)*(r.width/W),(e.clientY-r.top))};
  svg.addEventListener("pointermove",move);svg.addEventListener("pointerleave",()=>{cx.setAttribute("opacity",0);hds.forEach(c=>c.setAttribute("opacity",0));tipOff(host)});
}
/* bar chart (grouped), rounded tops, value labels */
function barPath(x,y,w,h,r){r=Math.min(r,w/2,h);if(h<=0)return"";return `M${x} ${y+h}V${y+r}Q${x} ${y} ${x+r} ${y}H${x+w-r}Q${x+w} ${y} ${x+w} ${y+r}V${y+h}Z`}
function barChart(host,o){
  const W=host.clientWidth||400,H=o.h||260,m={l:o.ml||46,r:8,t:o.labels?24:14,b:o.mb||38},iw=W-m.l-m.r,ih=H-m.t-m.b,nc=o.cats.length,ns=o.series.length;
  const T=o.ymax!=null?{t:ticks(0,o.ymax,4).t,hi:o.ymax}:ticks(0,Math.max(...o.series.flatMap(s=>s.vals))*1.08,4),hi=T.hi,Y=v=>m.t+ih-v/hi*ih,gw=iw/nc,bw=Math.min(o.bmax||52,gw*.7/ns);
  let g="";const anim=st.anim&&!reduced();
  T.t.forEach((v,k)=>{const y=Y(v);g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${m.l-10}" y="${y+3.5}" text-anchor="end">${o.yfmt(v)}</text>`});
  if(o.vline!=null){const x=m.l+gw*o.vline;g+=`<line x1="${x}" x2="${x}" y1="${m.t-6}" y2="${m.t+ih}" stroke="var(--bad)" stroke-width="1.5" stroke-dasharray="4 4"/>${o.vlabel?`<text class="ann" x="${x+6}" y="${m.t+4}" style="fill:var(--bad)">${o.vlabel}</text>`:""}`}
  o.cats.forEach((c,i)=>{const cx=m.l+gw*(i+.5);const [l1,l2]=wrapLbl(c,Math.max(5,Math.floor(gw/(st.lang=="ar"?5.4:6.4))));
    g+=`<text class="lbl-ui" x="${cx}" y="${H-m.b+16}" text-anchor="middle" style="font-size:11px"><tspan x="${cx}">${esc(l1)}</tspan>${l2?`<tspan x="${cx}" dy="13">${esc(l2)}</tspan>`:""}</text>`;
    o.series.forEach((s,j)=>{const x=cx-bw*ns/2+j*bw+1.5,v=s.vals[i],y=Y(v),col=s.colors?s.colors[i]:s.color;
      g+=`<path class="b ${anim?"grow":""}" style="animation-delay:${(i*ns+j)*.04}s" data-i="${i}" data-j="${j}" d="${barPath(x,y,bw-3,m.t+ih-y,5)}" fill="${col}"/>`;
      if(o.labels)g+=`<text x="${x+(bw-3)/2}" y="${y-7}" text-anchor="middle" class="${anim?"fadein":""}" style="fill:var(--ink);font-weight:600;font-size:11px">${(o.lfmt||o.yfmt)(v)}</text>`})});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}</svg>`;
  host.querySelectorAll(".b").forEach(r=>{r.addEventListener("pointermove",e=>{const i=+r.dataset.i,j=+r.dataset.j,s=o.series[j],hr=host.getBoundingClientRect();r.style.opacity=.82;
    tipAt(host,`<div class="th">${esc(o.cats[i])}</div>${trow(s.colors?s.colors[i]:s.color,s.name,(o.tfmt||o.yfmt)(s.vals[i]))}${o.tipx?o.tipx(i,j):""}`,e.clientX-hr.left,e.clientY-hr.top)});r.addEventListener("pointerleave",()=>{r.style.opacity=1;tipOff(host)})});
}
function wrapLbl(c,mx){let l1="",l2="";String(c).split(" ").forEach(x=>{if(!l2&&(l1+" "+x).trim().length<=mx)l1=(l1+" "+x).trim();else l2=(l2+" "+x).trim()});if(l2.length>mx)l2=l2.slice(0,mx-1)+"…";if(!l1){l1=l2.slice(0,mx);l2=""}return[l1,l2]}
/* waterfall */
function waterfall(host,o){
  const W=host.clientWidth||400,H=o.h||260,m={l:46,r:8,t:26,b:44},iw=W-m.l-m.r,ih=H-m.t-m.b,n=o.steps.length;
  let run=0;const bars=o.steps.map(s=>{if(s.total){const b={y0:0,y1:s.v,s};run=s.v;return b}const b={y0:run,y1:run+s.v,s};run+=s.v;return b});
  const T=ticks(0,Math.max(...bars.map(b=>Math.max(b.y0,b.y1)))*1.12,4),hi=T.hi,Y=v=>m.t+ih-v/hi*ih,gw=iw/n,bw=Math.min(64,gw*.62);
  let g="";const anim=st.anim&&!reduced();
  T.t.forEach((v,k)=>{const y=Y(v);g+=`<line x1="${m.l}" x2="${W-m.r}" y1="${y}" y2="${y}" stroke="var(--grid)" ${k?'stroke-dasharray="2 6"':""}/><text x="${m.l-10}" y="${y+3.5}" text-anchor="end">${o.yfmt(v)}</text>`});
  bars.forEach((b,i)=>{const cx=m.l+gw*(i+.5),x=cx-bw/2,top=Y(Math.max(b.y0,b.y1)),h=Math.abs(Y(b.y0)-Y(b.y1)),col=b.s.total?(i==0?C.mut:C.em):(b.s.v<0?C.em:C.gold);
    g+=`<path class="${anim?"grow":""}" style="animation-delay:${i*.1}s;${b.s.total?"":"opacity:.9"}" d="${barPath(x,top,bw,Math.max(1.5,h),b.s.total?6:3)}" fill="${col}"/>`;
    if(i<n-1){const yn=Y(b.y1);g+=`<line x1="${x+bw}" x2="${x+gw}" y1="${yn}" y2="${yn}" stroke="var(--line2)" stroke-dasharray="3 3"/>`}
    g+=`<text x="${cx}" y="${top-8}" text-anchor="middle" style="fill:var(--ink);font-weight:600;font-size:11.5px">${b.s.total?"":(b.s.v>0?"+":"−")}${o.yfmt(Math.abs(b.s.total?b.y1:b.s.v))}</text>`;
    const [l1,l2]=wrapLbl(b.s.label,Math.max(6,Math.floor(gw/(st.lang=="ar"?5.4:6.4))));g+=`<text class="lbl-ui" x="${cx}" y="${H-m.b+16}" text-anchor="middle" style="font-size:11px"><tspan x="${cx}">${esc(l1)}</tspan>${l2?`<tspan x="${cx}" dy="13">${esc(l2)}</tspan>`:""}</text>`});
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" role="img">${g}</svg>`;
}
/* sparkline */
function spark(ss){const all=ss.flatMap(s=>s.v),lo=Math.min(...all),hi=Math.max(...all),W=200,H=34,n=ss[0].v.length,X=i=>i*W/(n-1),Y=v=>H-3-(v-lo)/(hi-lo||1)*(H-8);
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" dir="ltr">`+ss.map(s=>{const d=s.v.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join("");return (s.area?`<path d="${d}L${W} ${H}L0 ${H}Z" fill="${s.c}" opacity=".14"/>`:"")+`<path d="${d}" fill="none" stroke="${s.c}" stroke-width="1.6" vector-effect="non-scaling-stroke" ${s.dash?'stroke-dasharray="3 3" opacity=".7"':""}/>`}).join("")+"</svg>"}
/* brush: mini area chart with draggable selection */
function brush(host,o){
  const W=host.clientWidth||600,H=58,m={l:6,r:6,t:6,b:6},iw=W-m.l-m.r,ih=H-m.t-m.b,n=o.vals.length,hi=Math.max(...o.vals),X=i=>m.l+i*iw/(n-1),Y=v=>m.t+ih-v/hi*ih;
  const d=o.vals.map((v,i)=>(i?"L":"M")+X(i).toFixed(1)+" "+Y(v).toFixed(1)).join("");
  host.innerHTML=`<svg viewBox="0 0 ${W} ${H}" height="${H}" dir="ltr" style="cursor:crosshair;touch-action:none"><rect x="0" y="0" width="${W}" height="${H}" rx="10" fill="var(--card2)"/><path d="${d}L${X(n-1)} ${m.t+ih}L${X(0)} ${m.t+ih}Z" fill="var(--em2)" opacity=".18"/><path d="${d}" fill="none" stroke="var(--em2)" stroke-width="1.4"/>
    <rect class="sel" y="2" height="${H-4}" rx="8" fill="var(--em2)" fill-opacity=".14" stroke="var(--em2)" stroke-width="1.5"/></svg>`;
  const svg=host.querySelector("svg"),sel=svg.querySelector(".sel");
  const draw=(a,b)=>{const x0=X(Math.min(a,b))-iw/(n-1)/2,x1=X(Math.max(a,b))+iw/(n-1)/2;sel.setAttribute("x",Math.max(1,x0));sel.setAttribute("width",Math.min(W-1,x1)-Math.max(1,x0))};
  draw(o.from,o.to);
  const idx=e=>{const r=svg.getBoundingClientRect();return Math.max(0,Math.min(n-1,Math.round(((e.clientX-r.left)*(W/r.width)-m.l)/iw*(n-1))))};
  let a=null;svg.addEventListener("pointerdown",e=>{a=idx(e);svg.setPointerCapture(e.pointerId);draw(a,a)});
  svg.addEventListener("pointermove",e=>{if(a!=null)draw(a,idx(e))});
  svg.addEventListener("pointerup",e=>{if(a==null)return;let b=idx(e),f=Math.min(a,b),tt=Math.max(a,b);if(tt-f<3){f=Math.max(0,f-2);tt=Math.min(n-1,tt+2)}a=null;o.on(f,tt)});
}
/* dumbbell list (baseline -> AI), one scale per row */
function dumbbell(rows){return `<div class="dl">${rows.map(r=>{const mx=Math.max(r.b,r.a)*1.12,pb=r.b/mx*100,pa=r.a/mx*100,good=r.lower?r.a<r.b:r.a>r.b,lo=Math.min(pa,pb),hi=Math.max(pa,pb),side=st.lang=="ar"?"right":"left";
  return `<div class="row"><div class="k">${r.k}<small>${r.s||""}</small></div><div class="track"><div class="base" style="${side}:0;width:100%"></div><div class="seg2" style="${side}:${lo}%;width:${hi-lo}%;background:${good?"var(--em2)":"var(--bad)"};opacity:.5"></div>
  <div class="dot" style="${side}:${pb}%;background:var(--mut)" ></div><div class="dot" style="${side}:${pa}%;background:${good?"var(--em2)":"var(--bad)"}" ></div>
  <span class="lab" style="${side}:${pb}%">${r.fb}</span><span class="lab" style="${side}:${pa}%;color:var(--ink);${Math.abs(pa-pb)<14?"top:20px":""}">${r.fa}</span></div>
  <div class="delta"><span class="pill ${good?"ok":"bad"}">${B(r.d)}</span></div></div>`}).join("")}</div>`}
function legend(items){return `<div class="lg">${items.map(i=>`<span style="color:${i[1]}"><i class="${i[2]?"d":""}" style="background:${i[1]}"></i><span style="color:var(--soft)">${i[0]}</span></span>`).join("")}</div>`}
function mount(id,fn){const h=document.getElementById(id);if(!h)return;const f=()=>fn(h);f();redraw.push(f)}
function countUp(){if(!st.anim||reduced())return;$$("[data-cu]").forEach(el=>{const to=+el.dataset.cu,f=el.dataset.f,dec=+(el.dataset.d||1),t0=performance.now(),dur=1100;
  const fmt=v=>f=="p"?pct(v,dec):f=="h"?fh(v):f=="s"?sgn(v,dec):num(v,dec);
  const step=now=>{const k=Math.min(1,(now-t0)/dur),e=1-Math.pow(1-k,3);el.textContent=fmt(to*e);if(k<1)requestAnimationFrame(step);else el.textContent=fmt(to)};requestAnimationFrame(step)})}
const CU=(v,f,d=1)=>{const txt=f=="p"?pct(v,d):f=="h"?fh(v):f=="s"?sgn(v,d):num(v,d);return `<bdi class="n" data-cu="${v}" data-f="${f}" data-d="${d}">${txt}</bdi>`};

/* ===== Tables: search, sort, paginate, CSV ===== */
const TB={};
function tblInit(id,cols,rows,csvName,opt={}){const p=TB[id]||{};TB[id]={cols,rows,q:p.q||"",sort:p.sort??null,dir:p.dir||1,page:0,size:opt.size||12,csvName,best:opt.best}}
function tblRows(id){const T=TB[id];let r=T.rows.filter(x=>!T.q||T.cols.some(c=>String(c.f?c.f(x[c.k],x):x[c.k]).toLowerCase().includes(T.q.toLowerCase())));
  if(T.sort!=null){const c=T.cols[T.sort];r=[...r].sort((a,b)=>{const u=a[c.k],v=b[c.k];return (typeof u=="number"&&typeof v=="number"?u-v:String(u).localeCompare(String(v)))*T.dir})}return r}
function tblInner(id,csv,search){const T=TB[id],all=tblRows(id),pages=Math.max(1,Math.ceil(all.length/T.size));T.page=Math.min(T.page,pages-1);const r=all.slice(T.page*T.size,(T.page+1)*T.size);
  const body=r.length?r.map(x=>`<tr class="${T.best&&T.best(x)?"best":""}">`+T.cols.map(c=>`<td class="${c.n?"n":""}">${c.h?c.h(x[c.k],x):c.n?B(esc(c.f?c.f(x[c.k],x):x[c.k])):esc(c.f?c.f(x[c.k],x):x[c.k])}</td>`).join("")+"</tr>").join(""):`<tr><td colspan="${T.cols.length}" class="empty">${t("noRes")}</td></tr>`;
  return `${search||csv?`<div class="tools">${search?`<input type="search" data-q="${id}" placeholder="${t("search")}" value="${esc(T.q)}" aria-label="${t("search")}">`:""}${csv?`<button class="btn" data-csv="${id}">${ic("dl")}${t("csv")}</button>`:""}</div>`:""}
  <div class="tbl"><table><thead><tr>${T.cols.map((c,i)=>`<th class="${c.n?"n":""}" data-s="${id}:${i}" aria-sort="${T.sort===i?(T.dir>0?"ascending":"descending"):"none"}">${c.l}<span class="so">${T.sort===i?(T.dir>0?"▲":"▼"):"↕"}</span></th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>
  ${pages>1?`<div class="pager"><span>${t("rows",B(num(all.length)))}</span><span style="display:flex;gap:8px;align-items:center"><button class="btn" data-pg="${id}:-1" ${T.page==0?"disabled":""}>${t("pgPrev")}</button>${t("pg",B(T.page+1),B(pages))}<button class="btn" data-pg="${id}:1" ${T.page>=pages-1?"disabled":""}>${t("pgNext")}</button></span></div>`:""}`}
function tblHTML(id,csv=true,search=true){return `<div id="w_${id}" data-wc="${csv?1:0}" data-wq="${search?1:0}">${tblInner(id,csv,search)}</div>`}
function tblRefresh(id){const w=$("#w_"+id);if(!w)return;const f=document.activeElement&&document.activeElement.dataset&&document.activeElement.dataset.q==id,pos=f?document.activeElement.selectionStart:0;w.innerHTML=tblInner(id,w.dataset.wc=="1",w.dataset.wq=="1");if(f){const i=w.querySelector("input");i.focus();i.setSelectionRange(pos,pos)}}
function exportCSV(id){const T=TB[id],r=tblRows(id);if(!r.length){toast(t("noRes"));return}
  const q=v=>'"'+String(v).replace(/"/g,'""')+'"',raw=T.cols.map(c=>q(c.l)).join(",")+"\n"+r.map(x=>T.cols.map(c=>q(c.raw?c.raw(x[c.k],x):x[c.k])).join(",")).join("\n");
  const a=document.createElement("a");a.href=URL.createObjectURL(new Blob(["﻿"+raw],{type:"text/csv;charset=utf-8"}));a.download=T.csvName+".csv";document.body.appendChild(a);a.click();a.remove();toast(t("csvOk")+" · "+r.length)}
const cell=(v,max,col,txt)=>`<span class="cb"><span class="trk"><i style="width:${Math.max(3,Math.min(100,v/max*100)).toFixed(0)}%;background:${col}"></i></span>${B(txt)}</span>`;
let tmr;function toast(m){const e=$("#toast");e.textContent=m;e.classList.add("on");clearTimeout(tmr);tmr=setTimeout(()=>e.classList.remove("on"),1900)}

