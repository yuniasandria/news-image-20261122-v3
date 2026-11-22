// The Sunday Ledger v3 — entrypoint for make.fun news-image-20261122.
// Reads the entry.png rendered by render.py in this repo and copies it to
// the output directory the grader reads. Node 22, standard library only.
import { copyFileSync, existsSync, mkdirSync, statSync } from "node:fs";
import { join } from "node:path";

const repo = new URL(".", import.meta.url).pathname;
const src = join(repo, "entry.png");
if (!existsSync(src)) {
  throw new Error("entry.png is missing from the repository");
}
const size = statSync(src).size;
if (size > 1024 * 1024) {
  throw new Error("entry.png is larger than 1 MiB: " + size + " bytes");
}
const head = Buffer.alloc(8);
const fd = (await import("node:fs")).openSync(src, "r");
(await import("node:fs")).readSync(fd, head, 0, 8, 0);
(await import("node:fs")).closeSync(fd);
const pngSig = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
if (!head.equals(pngSig)) {
  throw new Error("entry.png is not a PNG file");
}
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";
mkdirSync(outDir, { recursive: true });
copyFileSync(src, join(outDir, "entry.png"));
console.log("entry.png (" + size + " bytes) copied to " + outDir);
