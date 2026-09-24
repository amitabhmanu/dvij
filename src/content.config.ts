import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

// Codex entries (design §6.1). firstSeen is normally computed by
// pipeline/link_codex.py from the comic's lettering; set it here only to
// override that.
const codex = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/codex" }),
  schema: z.object({
    title: z.string(),
    aliases: z.array(z.string()).default([]),
    summary: z.string(),
    related: z.array(z.string()).default([]),
    images: z.array(z.string()).default([]), // names from site-assets/art (without .webp)
    diagram: z.string().optional(), // key in src/components/diagrams/index.ts
    source: z.string(), // endnote-N | manuscript | author
    firstSeen: z.object({ book: z.number().int(), page: z.number().int() }).optional(),
    manuscriptAnchor: z.string().optional(),
  }),
});

// Council of Voices (design §9). firstSeen and portraits are computed by
// pipeline/link_companions.py into generated/voices.json.
const voices = defineCollection({
  loader: glob({ pattern: "*.md", base: "./src/content/voices" }),
  schema: z.object({
    order: z.number().int(),
    name: z.string(),
    fullName: z.string().optional(),
    role: z.enum(["teacher", "guide", "antagonist", "survey"]),
    tradition: z.string(),
    setting: z.string(),
    quote: z.string(),
    firstQuote: z.string().optional(),
    firstSeen: z.object({ book: z.number().int(), page: z.number().int() }).optional(),
    portrait: z.object({ page: z.string(), match: z.string().optional(), box: z.array(z.number()).length(4).optional() }),
    excerpt: z.string(),
    codex: z.array(z.string()).default([]),
  }),
});

export const collections = { codex, voices };
