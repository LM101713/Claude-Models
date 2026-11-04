// Headless renderer for DRYDOCK P001 (three.js in Chromium via Playwright).
//   python scenes.py && node render.mjs            -> ../renders/*.png
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(here, "..", "renders");
fs.mkdirSync(outDir, { recursive: true });
const JOBS = [
  ["01_hero", "hero", { sub: "PROTOTYPE 001  ·  DESICCANT CARTRIDGE", rotz: "124" }],
  ["08_wordmark", "hero", { sub: "RECESSED WORDMARK ON THE BODY", rotz: "124", view: "label", labels: "0" }],
  ["02_exploded", "exploded", { sub: "EXPLODED ASSEMBLY  ·  6 PRINTED PARTS, NO HARDWARE", h: 900 }],
  ["03_section", "section", { sub: "SECTION  ·  ~55 mL OF 2–5 mm SILICA BEADS", h: 1300, w: 1750 }],
  ["04_in_spool", "spool", { sub: "IN A 55 mm SPOOL BORE  ·  GENERIC SPOOL, SECTIONED", h: 1000 }],
  ["05_expansion", "expansion_exploded", { sub: "EXPANSION  ·  COUPLER + SECOND BODY", h: 800 }],
  ["06_adapters", "adapters", { sub: "SPOOL ADAPTERS  ·  52 – 60 mm BORES", h: 1100 }],
  ["07_cap_face", "capface", { sub: "CAP FACE  ·  WINDOW, VENTS, INDEX FLUTES", labels: "0", w: 1200, h: 1200 }],
];
const only = process.argv[2];
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".glb": "model/gltf-binary" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  const f = u.startsWith("/three/") ? path.join(here, "node_modules", u) : path.join(here, u);
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" }); res.end(data);
  });
}).listen(0);
const port = server.address().port;
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium",
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [file, scene, o] of JOBS) {
  const view = o.view || scene;
  if (only && !file.includes(only)) continue;
  const W = o.w || 1600, H = o.h || 1100;
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on("console", m => { if (m.type() === "error") console.error("page:", m.text()); });
  const qs = new URLSearchParams({ glb: `/out/${scene}.glb`, meta: `/out/${scene}.json`, w: W, h: H, ...o, view });
  await page.goto(`http://localhost:${port}/studio.html?${qs}`);
  await page.waitForFunction(() => document.title === "done" || document.title.startsWith("error"), null, { timeout: 600000 });
  const t = await page.title();
  if (t !== "done") { console.error(file, t); continue; }
  await page.screenshot({ path: path.join(outDir, file + ".png") });
  await page.close();
  console.log("wrote", file);
}
await browser.close(); server.close();
