import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

export type ProjectMeta = {
  slug: string;
  title: string;
  subtitle: string;
  description: string;
  topics: string[];
  tools: string[];
  status: "published" | "coming-soon";
  featured: boolean;
  notebook: string | null;
  sourceRepoPath?: string;
  learning?: string;
  published?: string;
};

const projectsRoot = join(process.cwd(), "..", "projects");

export function loadProjects(): ProjectMeta[] {
  return readdirSync(projectsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const raw = readFileSync(join(projectsRoot, entry.name, "meta.json"), "utf8");
      return JSON.parse(raw) as ProjectMeta;
    })
    .sort((a, b) => {
      if (a.status !== b.status) return a.status === "published" ? -1 : 1;
      return a.title.localeCompare(b.title);
    });
}

export function getProject(slug: string): ProjectMeta | undefined {
  return loadProjects().find((project) => project.slug === slug);
}

export function loadArticleHtml(slug: string): string | null {
  const path = join(process.cwd(), "src", "content", "articles", `${slug}.html`);
  try {
    return readFileSync(path, "utf8");
  } catch {
    return null;
  }
}
