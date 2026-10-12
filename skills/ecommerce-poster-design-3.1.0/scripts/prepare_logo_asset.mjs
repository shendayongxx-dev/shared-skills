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
    if (!key?.startsWith("--") || argv[i + 1] === undefined) {
      throw new Error(`invalid argument sequence near ${key ?? "<end>"}`);
    }
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

function inspectSvg(svgText) {
  if (!/<svg\b/i.test(svgText)) throw new Error("input is not an SVG document");
  const blockedElements = /<(script|foreignObject|iframe|object|embed)\b/i;
  if (blockedElements.test(svgText)) throw new Error("SVG contains blocked active or embedded content");
  if (/\son[a-z]+\s*=/i.test(svgText)) throw new Error("SVG contains an event-handler attribute");

  const refs = [...svgText.matchAll(/(?:href|xlink:href)\s*=\s*["']([^"']+)["']/gi)].map((m) => m[1]);
  const unsafeRef = refs.find((ref) => !(ref.startsWith("#") || ref.startsWith("data:image/")));
  if (unsafeRef) throw new Error(`SVG contains an external reference: ${unsafeRef}`);
  if (/url\(\s*["']?(?:https?:|file:|\\\\|\/\/)/i.test(svgText)) {
    throw new Error("SVG contains an external CSS resource");
  }

  const openTag = svgText.match(/<svg\b[^>]*>/i)?.[0] || "";
  const getNumber = (name) => {
    const raw = openTag.match(new RegExp(`${name}\\s*=\\s*["']([0-9.]+)(?:px)?["']`, "i"))?.[1];
    return raw ? Number(raw) : null;
  };
  const viewBoxRaw = openTag.match(/viewBox\s*=\s*["']([^"']+)["']/i)?.[1] || null;
  const viewBox = viewBoxRaw ? viewBoxRaw.trim().split(/[\s,]+/).map(Number) : null;
  const width = getNumber("width");
  const height = getNumber("height");
  const vbWidth = viewBox?.length === 4 ? viewBox[2] : null;
  const vbHeight = viewBox?.length === 4 ? viewBox[3] : null;
  const ratioWidth = width || vbWidth;
  const ratioHeight = height || vbHeight;
  if (!(ratioWidth > 0 && ratioHeight > 0)) throw new Error("SVG needs a positive width/height or viewBox");
  return { width, height, viewBox, aspectRatio: ratioWidth / ratioHeight, embeddedReferences: refs.length };
}

export async function prepareLogoAsset({ input, output, manifest, longEdge = 2048, sharpModule }) {
  const inputPath = path.resolve(input);
  const outputPath = path.resolve(output);
  const manifestPath = path.resolve(manifest);
  if (path.extname(inputPath).toLowerCase() !== ".svg") throw new Error("prepare_logo_asset currently accepts authoritative .svg logo sources only");
  const svgText = fs.readFileSync(inputPath, "utf8");
  const svg = inspectSvg(svgText);
  const targetLongEdge = Number(longEdge);
  if (!Number.isInteger(targetLongEdge) || targetLongEdge < 1024 || targetLongEdge > 8192) {
    throw new Error("--long-edge must be an integer from 1024 to 8192");
  }

  const sharp = loadSharp(sharpModule);
  const sharpPkg = require(path.join(sharpModule || process.env.SHARP_MODULE_PATH || "sharp", "package.json"));
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });

  const width = svg.aspectRatio >= 1 ? targetLongEdge : Math.max(1, Math.round(targetLongEdge * svg.aspectRatio));
  const height = svg.aspectRatio >= 1 ? Math.max(1, Math.round(targetLongEdge / svg.aspectRatio)) : targetLongEdge;
  await sharp(Buffer.from(svgText), { density: 600 })
    .resize(width, height, { fit: "fill", kernel: "lanczos3" })
    .png({ compressionLevel: 9, adaptiveFiltering: true })
    .toFile(outputPath);

  const metadata = await sharp(outputPath).metadata();
  const stats = await sharp(outputPath).stats();
  const outputRatio = metadata.width / metadata.height;
  if (Math.abs(outputRatio / svg.aspectRatio - 1) > 0.002) throw new Error("rasterized logo aspect ratio drifted");
  const alpha = metadata.hasAlpha && stats.channels.length >= 4 ? stats.channels[3] : null;
  const transparencyClass = !metadata.hasAlpha
    ? "no_alpha_channel"
    : alpha.min < 255
      ? "has_transparent_pixels"
      : "alpha_channel_fully_opaque";

  const record = {
    schema_version: "logo-asset-preflight/1.1",
    authoritative_source: {
      path: inputPath,
      format: "svg",
      sha256: sha256(inputPath),
      declared_width: svg.width,
      declared_height: svg.height,
      view_box: svg.viewBox,
      aspect_ratio: svg.aspectRatio
    },
    generation_asset: {
      path: outputPath,
      format: "png",
      sha256: sha256(outputPath),
      width: metadata.width,
      height: metadata.height,
      has_alpha: metadata.hasAlpha,
      alpha_min: alpha?.min ?? null,
      alpha_max: alpha?.max ?? null,
      has_transparent_pixels: Boolean(alpha && alpha.min < 255),
      transparency_class: transparencyClass,
      aspect_ratio: outputRatio
    },
    transformation: {
      kind: "deterministic_svg_rasterization",
      long_edge: targetLongEdge,
      fit: "preserve_aspect_ratio",
      rotation: 0,
      recolor: false,
      crop: false,
      renderer: "sharp",
      renderer_version: sharpPkg.version
    },
    safety_checks: {
      active_content_absent: true,
      external_references_absent: true,
      embedded_reference_count: svg.embeddedReferences,
      aspect_ratio_preserved: true,
      transparency_inspected: true,
      visual_background_artifact_review_required: transparencyClass !== "has_transparent_pixels"
    }
  };
  fs.writeFileSync(manifestPath, `${JSON.stringify(record, null, 2)}\n`, "utf8");
  return record;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const result = await prepareLogoAsset({
      input: args.input,
      output: args.output,
      manifest: args.manifest,
      longEdge: args["long-edge"] || 2048,
      sharpModule: args["sharp-module"]
    });
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (error) {
    process.stderr.write(`${error.message}\n`);
    process.exitCode = 1;
  }
}
