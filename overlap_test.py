# Automated pop-up overlap test for Tam's Heavenly Hair Salon.
# Plays busy days with a bot and, every few game-ticks, checks rectangle intersections between:
#  request cards (bubbles+hearts+burden tags) x each other, station labels, HUD panels, on-screen buttons, screen/safe edges;
#  HUD panels x customer/Tam sprites (HUD must not cover gameplay).
import sys,asyncio,json
from playwright.async_api import async_playwright
URL=sys.argv[1] if len(sys.argv)>1 else 'http://localhost:8800/tams-heavenly-hair-salon/'
VIEWS=[(390,844,None),(375,667,None),(430,932,None),(390,844,{'t':47,'b':34})]  # last = iPhone notch PWA safe areas
DAYS=[1,3,6,10,14,18,21,24]
JS=r'''async (L)=>{const T=__T;const sv=T.save();for(const k of ["boots","tea","radio","couch","dryer2","style2","shears","spray"])sv.upg[k]=1;T.startLevel(L);
 const ov=(a,b)=>a.x<b.x+b.w-0.01&&b.x<a.x+a.w-0.01&&a.y<b.y+b.h-0.01&&b.y<a.y+a.h-0.01;let frames=0,maxC=0;const bad=[];const dt=1/30;let t=0;
 while(t<240){t+=dt;T.update(dt);const g=T.get();if(g.state!='play')break;const k=Math.round(t/dt);
  if(k%5==0){const cs=window.__cust();for(const c of [...cs].sort((a,b)=>a.pat-b.pat)){if(c.st=='wait'||c.st=='done'){const need=c.order[c.step];const s=T.stations().find(s=>s.type==need&&!s.occ);if(s&&Math.random()<.8)T.moveTo(c,s)}}
   if(g.queue==0&&!window.__tam().task){const pay=cs.find(c=>c.st=='pay');const rd=cs.filter(c=>c.st=='ready').sort((a,b)=>a.pat-b.pat)[0];if(pay&&(!rd||rd.pat>1.5))T.enqueue({k:'checkout',ref:pay});else if(rd)T.enqueue({k:'serve',ref:rd.stn});else if(pay)T.enqueue({k:'checkout',ref:pay})}}
  if(k%7)continue;frames++;const Ly=T.layout();const C=Ly.cards,S=Ly.statics;maxC=Math.max(maxC,C.length);
  // visible logical area (inside screen AND safe area)
  const vis={x0:Math.max(0,(Ly.SAFE.l-Ly.OXs)/Ly.SC),y0:Math.max(0,(Ly.SAFE.t-Ly.OYs)/Ly.SC),x1:Math.min(400,(Ly.VW-Ly.SAFE.r-Ly.OXs)/Ly.SC),y1:Math.min(720,(Ly.VH-Ly.SAFE.b-Ly.OYs)/Ly.SC)};
  for(let i=0;i<C.length;i++){const a=C[i];
   for(let j=i+1;j<C.length;j++)if(ov(a,C[j]))bad.push(['card-card',L,t.toFixed(1)]);
   for(const s of S)if(ov(a,s))bad.push(['card-'+s.k,L,t.toFixed(1),a,s]);
   if(a.x<vis.x0-.01||a.y<vis.y0-.01||a.x+a.w>vis.x1+.01||a.y+a.h>vis.y1+.01)bad.push(['card-edge',L,t.toFixed(1),a,vis])}
  const H=S.filter(s=>s.k=='hud'),B=S.filter(s=>s.k=='btn'),Lb=S.filter(s=>s.k=='label');
  for(const h of H){for(const sp of Ly.sprites)if(ov(h,sp))bad.push(['hud-sprite',L,t.toFixed(1),h,sp]);for(const b of B)if(ov(h,b))bad.push(['hud-button',L,t.toFixed(1)]);for(const l of Lb)if(ov(h,l))bad.push(['hud-label',L]);
   if(h.y<vis.y0-.01||h.x<vis.x0-.01||h.x+h.w>vis.x1+.01)bad.push(['hud-edge',L,h,vis])}}
 return{L,frames,maxCards:maxC,overlaps:bad.length,sample:bad.slice(0,3)}}'''
async def main():
  tot=0;fr=0
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for (w,h,safe) in VIEWS:
      pg=await b.new_page(viewport={'width':w,'height':h},device_scale_factor=2,is_mobile=True,has_touch=True)
      errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
      if safe:await pg.add_init_script('window.__SAFE='+json.dumps(safe))
      await pg.goto(URL);await pg.wait_for_timeout(700)
      for L in DAYS:
        r=await pg.evaluate(JS,L);tot+=r['overlaps'];fr+=r['frames']
        print(f"{w}x{h}{' safe'+str(safe) if safe else ''} day {L:2}: frames {r['frames']:3} max cards {r['maxCards']} overlaps {r['overlaps']}",r['sample'] if r['overlaps'] else '')
      if errs:print('PAGE ERRORS',errs);tot+=len(errs)
      await pg.close()
    await b.close()
  print(f'TOTAL frames {fr}  overlaps {tot}');sys.exit(1 if tot else 0)
asyncio.run(main())
