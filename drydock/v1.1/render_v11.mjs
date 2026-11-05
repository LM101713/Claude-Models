// node render_v11.mjs  -> renders/v11_*.png  (studio and three.js from ../render)
import http from "node:http"; import fs from "node:fs"; import path from "node:path";
import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url));
const R = path.join(here, "..", "render");
const { chromium } = await import(path.join(R, "node_modules", "playwright-core", "index.mjs"));
const out = path.join(here, "renders"); fs.mkdirSync(out, { recursive: true });
const JOBS = [
  ["v11_01_cap_inside", "v11_cap_inside", { view: "capface", rotz: "0", sub: "V1.1 CAP FROM INSIDE · TWIST-LOCK WINDOW UNDER ITS LEDGE", labels: "0", w: 1200, h: 1200 }],
  ["v11_02_cap_section", "v11_cap_section", { view: "section", sub: "V1.1 CAP SECTION · WINDOW EARS UNDER THE 45° LEDGE", labels: "0", w: 1300, h: 1100 }],
  ["v11_03_window", "v11_window", { view: "capface", sub: "V1.1 WINDOW · 3 EARS + GRIP BAR", labels: "0", w: 1000, h: 1000 }],
  ["v11_04_body_tongues", "v11_body", { view: "label", rotz: "-35", sub: "V1.1 BODY · DETENT SPRING TONGUES, LOCK MARKS ON THE WEBS", labels: "0", dy: "-14", zoom: "1.25" }],
  ["v11_05_fit_plate", "v11_fitplate", { view: "adapters", sub: "V1.1 FIT-TEST PLATE", labels: "0", h: 1100 }],
];
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".glb": "model/gltf-binary" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  const f = u.startsWith("/three/") ? path.join(R, "node_modules", u) : path.join(R, u);
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" }); res.end(d); });
}).listen(0);
const port = server.address().port;
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium",
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [file, scene, o] of JOBS) {
  const W = o.w || 1600, H = o.h || 1100;
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  const qs = new URLSearchParams({ glb: `/out/${scene}.glb`, meta: `/out/${scene}.json`, w: W, h: H, ...o });
  await page.goto(`http://localhost:${port}/studio.html?${qs}`);
  await page.waitForFunction(() => document.title === "done" || document.title.startsWith("error"), null, { timeout: 600000 });
  if (await page.title() !== "done") { console.error(file, await page.title()); continue; }
  await page.screenshot({ path: path.join(out, file + ".png") }); await page.close(); console.log("wrote", file);
}
await browser.close(); server.close();
