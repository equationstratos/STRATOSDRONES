// Headless check of pcb3d_viewer.html: renders, part count, no errors, screenshots.
const {chromium} = require('/opt/node22/lib/node_modules/playwright');
const path = require('path');
(async () => {
  const b = await chromium.launch({executablePath:'/opt/pw-browsers/chromium',
    args:['--use-gl=angle','--use-angle=swiftshader','--ignore-gpu-blocklist','--no-sandbox']});
  const p = await b.newPage({viewport:{width:1280,height:860}, deviceScaleFactor:1.4});
  const errs=[]; p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
  p.on('pageerror',e=>errs.push('PAGEERR '+e.message));
  const f = 'file://'+path.resolve('hardware/pcb/viz/pcb3d_viewer.html');
  await p.goto(f,{waitUntil:'load'});
  await p.waitForTimeout(4000);
  const info = await p.evaluate(()=>({rendering:window.__vizRendering&&window.__vizRendering(),
     info:window.__pcbInfo&&window.__pcbInfo()}));
  console.log('rendering:', info.rendering);
  console.log('pcbInfo  :', JSON.stringify(info.info));
  console.log('errors   :', errs.length, errs.slice(0,5).join(' || '));
  // iso
  await p.screenshot({path:'/tmp/pcb_iso.png'});
  // top view
  await p.evaluate(()=>{ document.getElementById('vTop').click(); });
  await p.waitForTimeout(1500); await p.screenshot({path:'/tmp/pcb_top.png'});
  // bottom view
  await p.evaluate(()=>{ document.getElementById('vBot').click(); });
  await p.waitForTimeout(1500); await p.screenshot({path:'/tmp/pcb_bot.png'});
  // subsystem colour mode
  await p.evaluate(()=>{ document.getElementById('vIso').click(); document.getElementById('cSub').click(); });
  await p.waitForTimeout(1200); await p.screenshot({path:'/tmp/pcb_sub.png'});
  await b.close();
})().catch(e=>{console.error(e);process.exit(1)});
