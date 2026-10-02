// Headless renderer for the Gemscale Flexi Bat (three.js in Chromium via Playwright).
//
//   cd render && npm install
//   node render.mjs ../models/GemscaleBat_standard_seed7.glb out.png --view hero --scheme midnight
//
// The matching *_parts.json must sit next to the .glb (the generator writes both).
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
const [glb, out] = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
if (!glb || !out) { console.error("usage: node render.mjs model.glb out.png [--view hero|top|face|plate] [--scheme midnight] [--w 1600 --h 1200]"); process.exit(2); }
const W = +opt("w", 1600), H = +opt("h", 1200);

const glbAbs = path.resolve(glb);
const partsAbs = glbAbs.replace(/\.glb$/, "_parts.json");
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".glb": "model/gltf-binary" };
const server = http.createServer((req, res) => {
  const u = decodeURIComponent(req.url.split("?")[0]);
  let f;
  if (u === "/model.glb") f = glbAbs;
  else if (u === "/parts.json") f = partsAbs;
  else if (u.startsWith("/three/")) f = path.join(here, "node_modules", u);
  else f = path.join(here, u);
  fs.readFile(f, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" });
    res.end(data);
  });
}).listen(0);
const port = server.address().port;

const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium",
  args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"],
});
const page = await browser.newPage({ viewport: { width: W, height: H } });
page.on("console", m => { if (m.type() === "error") console.error("page:", m.text()); });
const q = new URLSearchParams({ glb: "/model.glb", parts: "/parts.json", view: opt("view", "hero"), scheme: opt("scheme", "midnight"), w: W, h: H });
await page.goto(`http://localhost:${port}/studio.html?${q}`);
await page.waitForFunction(() => document.title === "done" || document.title.startsWith("error"), null, { timeout: 180000 });
const title = await page.title();
if (title !== "done") { console.error(title); process.exit(1); }
await page.screenshot({ path: out });
await browser.close();
server.close();
console.log("wrote", out);
