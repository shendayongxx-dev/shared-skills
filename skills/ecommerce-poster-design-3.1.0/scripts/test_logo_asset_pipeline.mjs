#!/usr/bin/env node

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { prepareLogoAsset } from "./prepare_logo_asset.mjs";
import { applyLogoAsset } from "./apply_logo_asset.mjs";

const require = createRequire(import.meta.url);
const sharpModule = process.argv[2] || process.env.SHARP_MODULE_PATH || "sharp";
const sharp = require(sharpModule);
const temp = fs.mkdtempSync(path.join(os.tmpdir(), "logo-pipeline-"));

try {
  const svg = path.join(temp, "logo.svg");
  const png = path.join(temp, "logo.png");
  const prepManifest = path.join(temp, "logo.preflight.json");
  fs.writeFileSync(svg, '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="180" viewBox="0 0 720 180"><rect width="720" height="180" rx="24" fill="#13233d"/><text x="360" y="116" text-anchor="middle" font-size="96" fill="#fff">AERIN</text></svg>');
  const prepared = await prepareLogoAsset({ input: svg, output: png, manifest: prepManifest, longEdge: 2048, sharpModule });
  assert.equal(prepared.generation_asset.width, 2048);
  assert.equal(prepared.generation_asset.height, 512);
  assert.equal(prepared.transformation.recolor, false);
  assert.equal(prepared.safety_checks.aspect_ratio_preserved, true);

  const poster = path.join(temp, "poster.png");
  const finalPoster = path.join(temp, "poster.final.png");
  const applyManifest = path.join(temp, "logo.application.json");
  await sharp({ create: { width: 1600, height: 1600, channels: 4, background: "#101820" } }).png().toFile(poster);
  const applied = await applyLogoAsset({ poster, logo: png, output: finalPoster, manifest: applyManifest, left: 96, top: 80, width: 320, sharpModule });
  assert.equal(applied.output.width, 1600);
  assert.equal(applied.output.height, 1600);
  assert.equal(applied.placement.height, 80);
  assert.equal(applied.transformation.aspect_ratio_preserved, true);

  const unsafe = path.join(temp, "unsafe.svg");
  fs.writeFileSync(unsafe, '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>alert(1)</script></svg>');
  await assert.rejects(() => prepareLogoAsset({ input: unsafe, output: path.join(temp, "unsafe.png"), manifest: path.join(temp, "unsafe.json"), sharpModule }), /blocked active/);
  process.stdout.write(JSON.stringify({ passed: 3, failed: 0, temp_dir: temp }) + "\n");
} catch (error) {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 1;
}
