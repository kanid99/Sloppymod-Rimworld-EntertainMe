// Renders preview.html to About/Preview.png at 1280x720.
//
//   NODE_PATH=$(npm root -g) node Source/Promo/render_preview.js
//
// Needs Playwright and a Chromium. The page's "T/" is served from the mod's
// Buildings textures, and the pinball cabinets are cropped to their opaque
// bounds here, since their textures are padded to a square.
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '..', '..');
const tex = path.join(root, 'Textures', 'EntertainingIdeas', 'Buildings');
const out = process.argv[2] || path.join(root, 'About', 'Preview.png');

(async () => {
  const browser = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium')
    ? { executablePath: '/opt/pw-browsers/chromium' } : {});
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  // The title face comes from Google Fonts. Chromium here may not go through
  // the proxy the shell does, so the stylesheet and font files are fetched
  // with curl and handed to the page.
  await page.route(/fonts\.(googleapis|gstatic)\.com/, route => {
    const url = route.request().url();
    try {
      const body = execFileSync('curl', ['-sSL', '-A', 'Mozilla/5.0 Chrome/120', url]);
      const type = url.includes('googleapis') ? 'text/css' : 'font/woff2';
      route.fulfill({ body, contentType: type, headers: { 'Access-Control-Allow-Origin': '*' } });
    } catch (e) {
      route.abort();
    }
  });
  await page.route('**/T/*', route => {
    const file = path.join(tex, path.basename(new URL(route.request().url()).pathname));
    route.fulfill({ path: file, contentType: 'image/png' });
  });
  await page.goto('file://' + path.join(__dirname, 'preview.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const font = await page.evaluate(async () => {
    const faces = await document.fonts.load('900 76px Archivo');
    return faces.length > 0;
  });
  if (!font) console.log('warning: Archivo did not load; the title falls back to Liberation Sans');
  const titleRight = await page.evaluate(() => document.querySelector('.title .a').getBoundingClientRect().right);
  console.log('title ends at x=' + Math.round(titleRight));
  await page.evaluate(async () => {
    for (const img of document.querySelectorAll('img[data-crop]')) {
      await img.decode();
      const c = document.createElement('canvas');
      c.width = img.naturalWidth; c.height = img.naturalHeight;
      const g = c.getContext('2d');
      g.drawImage(img, 0, 0);
      const d = g.getImageData(0, 0, c.width, c.height).data;
      let x0 = c.width, x1 = 0, y0 = c.height, y1 = 0;
      for (let y = 0; y < c.height; y++) for (let x = 0; x < c.width; x++) {
        if (d[(y * c.width + x) * 4 + 3] > 8) {
          if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        }
      }
      const o = document.createElement('canvas');
      o.width = x1 - x0 + 1; o.height = y1 - y0 + 1;
      o.getContext('2d').drawImage(c, x0, y0, o.width, o.height, 0, 0, o.width, o.height);
      img.src = o.toDataURL();
      await img.decode();
    }
  });
  await page.waitForTimeout(300);
  await page.screenshot({ path: out });
  await browser.close();
  console.log('wrote ' + out);
})();
