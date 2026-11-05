// node render_thumb.mjs out.png [query string]   (three.js + playwright from ../../render/node_modules)
import http from "node:http"; import fs from "node:fs"; import path from "node:path"; import { fileURLToPath } from "node:url";
const here = path.dirname(fileURLToPath(import.meta.url)); const R = path.join(here, "..", "..", "render");
const { chromium } = await import(path.join(R, "node_modules", "playwright-core", "index.mjs"));
const [out, qs = ""] = process.argv.slice(2);
const p = new URLSearchParams(qs); const W = +(p.get("w") || 1920), H = +(p.get("h") || 1080);
const types = { ".html": "text/html", ".js": "text/javascript", ".json": "application/json", ".glb": "model/gltf-binary" };
const srv = http.createServer((req, res) => { const u = decodeURIComponent(req.url.split("?")[0]);
  const f = u.startsWith("/three/") ? path.join(R, "node_modules", u) : path.join(here, u);
  fs.readFile(f, (e, d) => { if (e) { res.writeHead(404); res.end(); return; } res.writeHead(200, { "content-type": types[path.extname(f)] || "application/octet-stream" }); res.end(d); }); }).listen(0);
const b = await chromium.launch({ executablePath: "/opt/pw-browsers/chromium", args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const pg = await b.newPage({ viewport: { width: W, height: H } });
pg.on("console", m => { if (m.type() === "error") console.error(m.text()); });
await pg.goto(`http://localhost:${srv.address().port}/thumb.html?${qs}`);
await pg.waitForFunction(() => document.title === "done" || document.title.startsWith("error"), null, { timeout: 600000 });
if (await pg.title() !== "done") { console.error(await pg.title()); process.exit(1); }
await pg.screenshot({ path: out, omitBackground: true }); await b.close(); srv.close(); console.log("wrote", out);
