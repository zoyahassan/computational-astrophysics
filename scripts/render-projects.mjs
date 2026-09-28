#!/usr/bin/env node
/**
 * Render published project notebooks with Quarto and extract article HTML.
 * Requires: quarto on PATH, Python deps for notebook execution.
 */
import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const PROJECTS_DIR = join(ROOT, "projects");
const OUTPUT_ROOT = join(ROOT, "website", ".quarto-output");
const ARTICLES_DIR = join(ROOT, "website", "src", "content", "articles");
const PUBLIC_PROJECTS = join(ROOT, "website", "public", "projects");

function loadProjects() {
  return readdirSync(PROJECTS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => {
      const metaPath = join(PROJECTS_DIR, d.name, "meta.json");
      if (!existsSync(metaPath)) return null;
      return JSON.parse(readFileSync(metaPath, "utf8"));
    })
    .filter(Boolean);
}

function quartoAvailable() {
  const check = spawnSync("quarto", ["--version"], { stdio: "ignore" });
  return check.status === 0;
}

function renderWithQuarto(meta) {
  const notebookPath = join(ROOT, meta.notebook);
  const outDir = join(OUTPUT_ROOT, meta.slug);
  mkdirSync(outDir, { recursive: true });

  const result = spawnSync(
    "quarto",
    [
      "render",
      notebookPath,
      "--to",
      "html",
      "--output-dir",
      outDir,
      "--execute",
      "--metadata-file",
      join(ROOT, "quarto", "scientific-portfolio.yml"),
    ],
    { cwd: ROOT, stdio: "inherit", env: { ...process.env, PYTHONPATH: ROOT } },
  );

  if (result.status !== 0) {
    throw new Error(`Quarto failed for ${meta.slug}`);
  }
  return "quarto";
}

function renderWithPython(meta) {
  const python = join(ROOT, ".venv", "bin", "python");
  const interpreter = existsSync(python) ? python : "python3";
  const publicDir = join(PUBLIC_PROJECTS, meta.slug);
  const articleOut = join(ARTICLES_DIR, `${meta.slug}.html`);
  mkdirSync(publicDir, { recursive: true });
  mkdirSync(ARTICLES_DIR, { recursive: true });

  const result = spawnSync(
    interpreter,
    [
      join(ROOT, "scripts", "render_notebook.py"),
      join(ROOT, meta.notebook),
      "--slug",
      meta.slug,
      "--repo-root",
      ROOT,
      "--public-dir",
      publicDir,
      "--article-out",
      articleOut,
    ],
    { cwd: ROOT, stdio: "inherit", env: { ...process.env, PYTHONPATH: ROOT } },
  );

  if (result.status !== 0) {
    throw new Error(`Python notebook render failed for ${meta.slug}`);
  }
  return "python";
}

function renderNotebook(meta) {
  if (quartoAvailable()) {
    return renderWithQuarto(meta);
  }
  console.log("Quarto not found — using scripts/render_notebook.py");
  return renderWithPython(meta);
}

function extractBody(html) {
  const main = html.match(/<main[^>]*>([\s\S]*?)<\/main>/i);
  let body = main ? main[1] : html;
  body = body.replace(/<script[\s\S]*?<\/script>/gi, "");
  body = body.replace(/<link[^>]*>/gi, "");
  return body.trim();
}

function rewriteAssetPaths(html, slug) {
  return html.replace(
    /(src|href)="([^"]+\.(?:png|jpg|jpeg|svg|gif|webp))"/gi,
    (_, attr, path) => {
      const file = path.split("/").pop();
      return `${attr}="/projects/${slug}/${file}"`;
    },
  );
}

function publishAssets(slug) {
  const outDir = join(OUTPUT_ROOT, slug);
  const dest = join(PUBLIC_PROJECTS, slug);
  mkdirSync(dest, { recursive: true });

  const htmlFiles = readdirSync(outDir).filter((f) => f.endsWith(".html"));
  if (htmlFiles.length === 0) {
    throw new Error(`No HTML output for ${slug}`);
  }

  const htmlPath = join(outDir, htmlFiles[0]);
  let html = readFileSync(htmlPath, "utf8");

  const filesDir = readdirSync(outDir).find((f) => f.endsWith("_files"));
  if (filesDir) {
    const figures = join(outDir, filesDir, "figure-html");
    if (existsSync(figures)) {
      for (const fig of readdirSync(figures)) {
        cpSync(join(figures, fig), join(dest, fig));
      }
    }
  }

  html = rewriteAssetPaths(html, slug);
  const body = extractBody(html);
  mkdirSync(ARTICLES_DIR, { recursive: true });
  writeFileSync(join(ARTICLES_DIR, `${slug}.html`), body);
  console.log(`Wrote article fragment: ${relative(ROOT, join(ARTICLES_DIR, `${slug}.html`))}`);
}

function main() {
  const projects = loadProjects().filter((p) => p.status === "published" && p.notebook);
  if (projects.length === 0) {
    console.log("No published notebooks to render.");
    return;
  }

  for (const meta of projects) {
    console.log(`Rendering ${meta.slug}...`);
    const engine = renderNotebook(meta);
    if (engine === "quarto") {
      publishAssets(meta.slug);
    }
  }
}

main();
