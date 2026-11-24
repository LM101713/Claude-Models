// Renders every scene JSON written by flurry.py.  node render.mjs
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { fileURLToPath } from "node:url"; import { createRequire } from "node:module";
const { chromium } = createRequire(import.meta.url)("playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  const f = u.startsWith("/three/") ? path.join(here, "node_modules", u) : path.join(here, u);
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" }); res.end(d); });
}).listen(0);
const port = server.address().port;
const shots = [
  ["01_hero", "scene=hero&hang=1&az=-14&el=8&zoom=1.15", 1600, 1200],
  ["02_full_set", "scene=set&el=89.9&zoom=1.02", 1600, 1200],
  ["03_set_spinning", "scene=set_spin&az=-18&el=48&zoom=1.0", 1600, 1200],
  ["04_as_printed", "scene=flat&az=-25&el=38&zoom=1.15", 1600, 1200],
  ["05_pivot_section", "scene=section&az=0&el=22&zoom=1.1&fov=20", 1600, 1200],
];
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
fs.mkdirSync(path.join(here, "../renders"), { recursive: true });
for (const [name, qs, w, h] of shots) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: 1 });
  page.on("pageerror", e => console.error(name, e.message));
  await page.goto(`http://127.0.0.1:${port}/studio.html?${qs}`);
  await page.waitForFunction("window.__done === true", null, { timeout: 120000 });
  await page.screenshot({ path: path.join(here, "../renders", name + ".png") });
  await page.close(); console.log(name);
}
await browser.close(); server.close();
