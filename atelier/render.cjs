// Rend chaque affiche de manifest.json en PDF prêt à imprimer (+ PNG d'aperçu).
// Usage : node atelier/render.cjs
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const fs = require('fs'); const path = require('path');
const HERE = __dirname;

(async () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(HERE, 'manifest.json')));
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const job of manifest) {
    const p = await b.newPage({ viewport: { width: 794, height: 1123 }, deviceScaleFactor: 2 });
    await p.goto('file://' + path.join(HERE, job.html), { waitUntil: 'networkidle' });
    await p.waitForTimeout(300);
    await p.pdf({
      path: path.join(HERE, job.out + '.pdf'),
      format: job.format, scale: job.scale, printBackground: true,
      margin: { top: 0, right: 0, bottom: 0, left: 0 },
    });
    await p.emulateMedia({ media: 'screen' });
    const el = await p.$('.page');
    await el.screenshot({ path: path.join(HERE, job.out + '.png') });
    console.log('rendu', job.out, '->', job.format, 'échelle', job.scale);
    await p.close();
  }
  await b.close();
  console.log('terminé');
})().catch(e => { console.error('FATAL', e); process.exit(1); });
