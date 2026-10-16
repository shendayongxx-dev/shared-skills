#!/usr/bin/env node

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function parseArgs(argv) {
  const args = {};
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i];
    if (!key?.startsWith("--") || argv[i + 1] === undefined) throw new Error(`invalid argument sequence near ${key ?? "<end>"}`);
    args[key.slice(2)] = argv[i + 1];
  }
  return args;
}

function sha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function loadSharp(moduleRef) {
  return require(moduleRef || process.env.SHARP_MODULE_PATH || "sharp");
}

export async function applyLogoAsset({ poster, logo, output, manifest, left, top, width, sharpModule }) {
  const sharp = loadSharp(sharpModule);
  const posterPath = path.resolve(poster);
  const logoPath = path.resolve(logo);
  const outputPath = path.resolve(output);
  const manifestPath = path.resolve(manifest);
  const x = Number(left);
  const y = Number(top);
  const targetWidth = Number(width);
  if (![x, y, targetWidth].every(Number.isInteger) || x < 0 || y < 0 || targetWidth < 32) {
    throw new Error("left, top and width must be non-negative integers; width must be at least 32");
  }
  const posterMeta = await sharp(posterPath).metadata();
  const logoMeta = await sharp(logoPath).metadata();
  if (logoMeta.format !== "png" || !(logoMeta.width > 0 && logoMeta.height > 0)) throw new Error("prepared logo must be a readable PNG");
  const targetHeight = Math.round(targetWidth * logoMeta.height / logoMeta.width);
  if (x + targetWidth > posterMeta.width || y + targetHeight > posterMeta.height) throw new Error("logo placement exceeds poster bounds");

  const overlay = await sharp(logoPath).resize(targetWidth, targetHeight, { fit: "fill", kernel: "lanczos3" }).png().toBuffer();
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  await sharp(posterPath).composite([{ input: overlay, left: x, top: y, blend: "over" }]).png({ compressionLevel: 9 }).toFile(outputPath);
  const outputMeta = await sharp(outputPath).metadata();
  if (outputMeta.width !== posterMeta.width || outputMeta.height !== posterMeta.height) throw new Error("poster dimensions changed during logo application");

  const record = {
    schema_version: "logo-application/1.0",
    base_poster: { path: posterPath, sha256: sha256(posterPath), width: posterMeta.width, height: posterMeta.height },
    prepared_logo: { path: logoPath, sha256: sha256(logoPath), source_width: logoMeta.width, source_height: logoMeta.height },
    output: { path: outputPath, sha256: sha256(outputPath), width: outputMeta.width, height: outputMeta.height },
    placement: { left: x, top: y, width: targetWidth, height: targetHeight },
    transformation: { rotation: 0, recolor: false, crop: false, aspect_ratio_preserved: true, blend: "over" }
  };
  fs.writeFileSync(manifestPath, `${JSON.stringify(record, null, 2)}\n`, "utf8");
  return record;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const result = await applyLogoAsset({
      poster: args.poster,
      logo: args.logo,
      output: args.output,
      manifest: args.manifest,
      left: args.left,
      top: args.top,
      width: args.width,
      sharpModule: args["sharp-module"]
    });
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}
