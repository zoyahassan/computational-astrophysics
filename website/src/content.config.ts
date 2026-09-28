import { defineCollection } from "astro:content";

// Article HTML is loaded directly in project pages (not as Markdown content).
export const collections = {
  articles: defineCollection({ type: "data", schema: undefined as never }),
};
