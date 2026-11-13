/* ===== Core utilities ===== */
const ICONS={ov:'<rect x="3" y="3" width="7" height="9" rx="1.5"/><rect x="14" y="3" width="7" height="5" rx="1.5"/><rect x="14" y="12" width="7" height="9" rx="1.5"/><rect x="3" y="16" width="7" height="5" rx="1.5"/>',
  pl:'<path d="M4 6h7M8 12h10M5 18h6"/><path d="M3 3v18"/><circle cx="18" cy="6" r="1.5"/>',ru:'<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',di:'<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',
  bm:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2"/>',mt:'<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5M9 13h7M9 17h5"/>',
  sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',moon:'<path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z"/>',sys:'<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
  search:'<circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/>',dl:'<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5h.01"/>',warn:'<path d="M12 3l9.5 17h-19z"/><path d="M12 10v4M12 17h.01"/>',
  print:'<path d="M7 9V3h10v6"/><rect x="3" y="9" width="18" height="8" rx="2"/><path d="M7 14h10v7H7z"/>',link:'<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',globe:'<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
  reset:'<path d="M4 4v6h6"/><path d="M20 12a8 8 0 1 0-2.3 5.7"/><path d="M4 10a8 8 0 0 1 1.3-2.7"/>',send:'<path d="M4 12l16-8-6 16-3-7z"/>',play:'<path d="M7 4l13 8-13 8z"/>',pause:'<path d="M7 4v16M17 4v16"/>',
  undo:'<path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',chat:'<path d="M4 5h16v11H9l-5 4z"/>',book:'<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',bolt:'<path d="M13 2L4 14h7l-1 8 9-12h-7z"/>',check:'<path d="M5 12l5 5 9-10"/>'};
const PAGES=["ov","pl","ru","di","bm","mt"];
const LANGS=["en","id","ar"],LOC={en:"en-US",id:"id-ID",ar:"ar-u-nu-latn"};
const st={page:"ov",lang:"en",theme:"system",book:1,base:"OPT",method:"stable",chg:true,events:[],msgs:[],story:0,playing:false,rbook:1,anim:true};
const li=()=>LANGS.indexOf(st.lang);
const t=(k,...a)=>{let s=(S[k]||[k,k,k])[li()];a.forEach((v,i)=>s=s.split("{"+i+"}").join(v));return s};
const tl=k=>S[k+(st.lang=="en"?"":"_"+st.lang)]||S[k];
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const NF={};const nf=d=>{const k=st.lang+d;return NF[k]||(NF[k]=new Intl.NumberFormat(LOC[st.lang],{minimumFractionDigits:d,maximumFractionDigits:d}))};
const num=(x,d=0)=>nf(d).format(x);
const pct=(x,d=1)=>num(x*100,d)+"%";
const sgn=(x,d=0)=>(x<0?"−":"+")+num(Math.abs(x),d);
const B=s=>`<bdi class="n">${s}</bdi>`;
const sum=a=>a.reduce((x,y)=>x+y,0),mean=a=>a.length?sum(a)/a.length:NaN;
const ic=k=>`<svg class="ic" viewBox="0 0 24 24">${ICONS[k]}</svg>`;
const reduced=()=>matchMedia("(prefers-reduced-motion: reduce)").matches;
const C={ink:"var(--ink)",mut:"var(--mut)",em:"var(--em2)",gold:"var(--gold2)",steel:"var(--steel2)",rose:"var(--rose)",lilac:"var(--lilac)",bad:"var(--bad)"};
const redraw=[];
function store(k,v){try{if(v===undefined)return localStorage.getItem("psc_"+k);localStorage.setItem("psc_"+k,v)}catch(e){return null}}
const fh=v=>num(v,0)+" "+t("min");
