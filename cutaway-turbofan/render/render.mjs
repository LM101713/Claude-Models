// Headless renderer for the Cutaway Turbofan (three.js in Chromium via Playwright).
//
//   cd render && npm install
//   node render.mjs ../models/CutawayTurbofan_assembly.glb out.png --view hero
//   node render.mjs ../models/CutawayTurbofan_assembly.glb out.gif --view flow --frames 36
//
// Views: hero | side | front | rear | top | flow (flow arrows and labels).
// The matching *_parts.json must sit next to the .glb (the generator writes both).
import http from "node:http";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf("--" + k); return i >= 0 ? args[i + 1] : d; };
const [glb, out] = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
if (!glb || !out) { console.error("usage: node render.mjs model.glb out.png|out.gif [--view hero] [--frames 36] [--w 1600 --h 1200]"); process.exit(2); }
const W = +opt("w", 1600), H = +opt("h", 1200), frames = +opt("frames", 0);

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
const q = new URLSearchParams({ glb: "/model.glb", parts: "/parts.json", view: opt("view", "hero"),
  angle: opt("angle", "0"), w: W, h: H, labels: opt("labels", "1"), flow: opt("flow", "0") });
await page.goto(`http://localhost:${port}/studio.html?${q}`);
await page.waitForFunction(() => document.title === "done" || document.title.startsWith("error"), null, { timeout: 300000 });
const title = await page.title();
if (title !== "done") { console.error(title); process.exit(1); }
if (!frames) {
  await page.screenshot({ path: out });
} else {
  // one full flow step per frame cycle; the rotor turns one blade pitch of the fan per loop
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "turbofan-"));
  const turn = +opt("turn", 40);
  for (let i = 0; i < frames; i++) {
    await page.evaluate(([a, p]) => window.frame(a, p), [turn * i / frames, +opt("cycles", 1) * i / frames]);
    await page.screenshot({ path: path.join(dir, `f${String(i).padStart(3, "0")}.png`) });
  }
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-framerate", opt("fps", "15"), "-i", path.join(dir, "f%03d.png"),
    "-vf", `scale=${opt("gw", "960")}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=192[p];[b][p]paletteuse=dither=sierra2_4a`,
    "-loop", "0", out]);
  fs.rmSync(dir, { recursive: true });
}
await browser.close();
server.close();
console.log("wrote", out);
