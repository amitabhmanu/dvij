# The Twice Born — website

Static Astro site for Netlify that publishes the comic (design:
`../twice-born-website-design.md`). Page images, art and PDFs are generated from
`../book/` into `../site-assets/` and are never committed.

## Layout

| Path | What |
|---|---|
| `pipeline/` | Content pipeline (Python + one Node script), run locally |
| `src/content/manifests/` | Per-book manifests the site reads (generated, committed) |
| `src/content/corrections/` | Your review edits: panel boxes, alt text, chapter starts (committed) |
| `src/content/codex/` | Codex (glossary) entries, one Markdown file each |
| `src/content/generated/codex-links.json` | Where each Codex entry appears in the comic (generated) |
| `src/content/hotspots/` | `auto.json` (generated links from the lettering), `manual.json` (your additions/removals) |
| `src/islands/` | Interactive components (reader, dev review tool) |
| `integrations/local-assets.mjs` | Serves `../site-assets` at `/_assets` in dev; bundles it on `build:local` |

## Setup

```bash
npm install
pip install -r requirements.txt
```

## Content pipeline

```bash
npm run pipeline          # everything, in order (slow steps skip finished work)
python pipeline/run_all.py --from text   # resume from a later step
```

Steps (see each script's docstring):

1. `compress.py` — compresses `book/B*.pdf` (JPEG q80, 4:2:0) into `site-assets/pdf/` and checks page counts, identical text and visual similarity (SSIM ≥ 0.97). Report: `pipeline/reports/compress.json`.
2. `render_pages.py` — 2× PNG masters of every page (local only).
3. `make_variants.mjs` — AVIF + WebP at 2115/1400/900/240 px, content-hashed (≈1.5 h on a 4-core laptop).
4. `extract_text.py` — captions, balloons and sound effects with positions.
5. `detect_panels.py` — draft panel boxes (paint-order aware).
6. `map_chapters.py` — chapter start pages from the breakdown quotes.
7. `prepare_art.py` — publishes only the allow-listed working images + parchment puzzle crops.
8. `extract_endnotes.py` — manuscript endnotes → draft glossary entries.
9. `build_manifests.py` — merges all of the above plus `src/content/corrections/`.
10. `link_codex.py` — finds every balloon/caption that mentions a Codex entry (by its `aliases`) and makes it a hotspot; the earliest mention becomes the entry's spoiler position (`firstSeen`).
11. `link_parchment.py` — resolves each puzzle's "starts" and "solved" quotes (in `src/content/parchment.yaml`) to comic pages, and adds a "Puzzle" badge hotspot where each puzzle begins.
12. `link_companions.py` — locates the Journey rail beats, crops each Voice's portrait from the panel where they speak, and places the `voice:` and hidden `fragment:` hotspots. `--sheet` also writes a portrait contact sheet.
13. `validate_content.py` — checks every Codex link, image, hotspot, puzzle answer, voice, rail beat, fragment and page reference resolves (`npm run validate`).

Helper: `python pipeline/find_page.py "a manuscript quote"` → book, page and chapter where it appears in the comic.

## Reviewing panels, alt text and chapters

```bash
npm run dev               # then open http://localhost:4321/dev/review
```

- Drag on empty space to draw a panel; drag a box to move it; drag its corner to resize; Delete removes it.
- List order = reading order (↑/↓ to reorder).
- Write alt text describing what is **drawn** in each panel.
- "Set as start of" fixes a chapter's first page (16 low-confidence starts are flagged `?`).
- Ctrl+S saves the page to `src/content/corrections/`; `[` and `]` move between pages.

Afterwards run `npm run manifests` to fold the corrections into the manifests.

**Hotspots mode** (same page, "Hotspots" button): orange boxes are automatic links from the lettering;
click one to switch it off. To add a link (e.g. on a drawn symbol rather than a word), pick a Codex entry
and drag a box. Changes save to `src/content/hotspots/manual.json` immediately.

## Codex entries

Each entry is `src/content/codex/<id>.md` with frontmatter: `title`, `aliases` (words that
auto-link it in the comic), `summary` (shown in the reader's drawer), `related`, `images`
(names in `site-assets/art`), `source`, and optionally `firstSeen: {book, page}` to override the
computed spoiler position. After adding or editing aliases, run `npm run codex` then `npm run validate`.

Spoilers: an entry is blurred for readers who haven't reached its `firstSeen` page, unless they
choose "Show everything". Progress lives in the reader's browser only.

## Puzzles

`src/content/parchment.yaml` holds the five parchment puzzles and the caves settings. Each puzzle is a
chain of multiple-choice `stages` (prompt, choices, answer, hint, explanation, optional Codex link),
transcribed from the characters' reasoning in the manuscript. After editing it, run
`python pipeline/link_parchment.py` then `npm run validate`. A puzzle opens for readers at its
`availableQuote` page; the guided walkthrough opens at its `solvedQuote` page.

## Companion layers

| Content | File | Notes |
|---|---|---|
| Journey rail | `src/content/rail.yaml` | Each beat's `quote` locates it in the comic; lenses are `chakra`, `party`, `teacher`, `epic` |
| Council of Voices | `src/content/voices/*.md` | `quote` (and optional `firstQuote`) set where they appear; `portrait: {page, match}` picks the panel, or `portrait: {page, box}` for a hand-picked crop |
| Charvaka fragments | `src/content/fragments.yaml` | Five hidden marks; finding all five opens `/charvaka/` |

`python pipeline/author_voices.py` regenerates the Voice entries from scratch (it overwrites hand edits).
After editing any of these, run `python pipeline/link_companions.py` then `npm run validate`.

## Build, test, deploy

```bash
npm run build             # production build (assets served from PUBLIC_ASSET_BASE)
npm run build:local       # same, with site-assets bundled into dist/_assets
npm run test:e2e          # Playwright tests against dist/ (run build:local first)
```

Environment variables:

| Variable | Purpose |
|---|---|
| `PUBLIC_ASSET_BASE` | Where page images, art and PDFs are served from. Default `/_assets` (bundled). Set to the CDN URL for hosting option A. |
| `SITE_URL` | Canonical site URL (once the domain is chosen). |
| `BUNDLE_ASSETS=1` | Copy `site-assets` into the build (option B). `build:local` sets it. |
