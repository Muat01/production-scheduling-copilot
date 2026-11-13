const fs=require('fs');eval(fs.readFileSync(process.argv[2],'utf8').replace('const D=','global.D='));eval(fs.readFileSync(require('path').join(__dirname,'src','engine.js'),'utf8')+';global.dispatch=dispatch;global.check=check;global.kpis=kpis;global.RULE_KEYS=RULE_KEYS;global.rightShift=rightShift;global.frozenOps=frozenOps;global.applyEvent=applyEvent');
let ok=0,bad=0;
for(const b of D.books){const I={...b.inst,down:[]};for(const r of RULE_KEYS){const S=dispatch(I,r),ref=D.ref[b.seed][r];if(JSON.stringify(S)==JSON.stringify(ref)&&check(I,S).length==0)ok++;else{bad++;console.log('MISMATCH',b.seed,r)}}
  if(check(I,b.opt).length)console.log('opt infeasible',b.seed);
  if(b.sc)for(const [k,v] of Object.entries(b.sc)){const p=k.split(':');const ev=p[0]=='b'?{kind:'breakdown',machine:+p[1],time:+p[2],duration:+p[3]}:{kind:'rush',job:+p[1],weight:5,time:60};const J=applyEvent(I,ev);
    for(const m of ['reoptimize','stable']){const e=check(J,v[m].s);if(e.length){bad++;console.log('scenario infeasible',b.seed,k,m,e[0])}}
    const rs=rightShift(J,b.opt,ev.time,frozenOps(J,b.opt,ev.time,ev.kind=='breakdown'?ev.machine:null));if(check(J,rs).length){bad++;console.log('rs infeasible',k)}}}
console.log('rule parity ok',ok,'bad',bad);
