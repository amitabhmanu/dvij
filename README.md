# The Twice Born — website

Static Astro site for Netlify that publishes the comic. Page images, art and PDFs
are generated from `../book/` into `../site-assets/` and are never committed; they
are served from a Cloudflare R2 bucket.

| Document | What it is |
|---|---|
| [docs/twice-born-website-design.md](docs/twice-born-website-design.md) | The design. What the site is, how the pipeline works, what every layer does, and what is still open. Kept in step with the code |
| [docs/real-india-pairings.md](docs/real-india-pairings.md) | Researched real-world counterparts for the valley's places, with confidence levels and sources. Awaiting your confirmation; blocks the Real India layer |
| [docs/twice-born-website-design-discussion.md](docs/twice-born-website-design-discussion.md) | The original brainstorm the design was drawn from. Superseded where the two disagree - see design §15 |

**State:** all five books are in — 171 pages, 1,712 panels, every panel described,
all 81 chapter starts confirmed. The companion layers are built: a Codex of 21
entries, the Parchment's 5 puzzles, the Bhoodara caves, a journey rail of 10 beats,
8 Council of Voices cards and 5 hidden Charvaka fragments, linked by 91 hotspots.
Still open: the valley map and Real India layer, which need the place pairings
confirmed, and the v2 AI features.

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
pip install -r pipeline/requirements.txt
```

The Python packages are for the content pipeline only, which runs on your
machine. `requirements.txt` is kept under `pipeline/` rather than at the repo
root so Netlify does not install them on every deploy.

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

## Reviewing panels, descriptions and chapters

**This pass is complete.** All 171 pages have been checked against the art: 1,712 panels,
every one with a description, and all 81 chapter starts confirmed. Use the tool below to
change any of it.

| | Draft from the pipeline | After review |
|---|---|---|
| Panel boxes | 1,686 | 1,712 |
| Panels described | 0 | 1,712 |
| Chapter starts confirmed | 65 of 81 | 81 of 81 |

Book 1 took almost all the corrections (20 pages of 42): its pages are montages with no
gutters, so detection merged two drawings into one box again and again. Books 2-5 are on
regular grids and needed five pages between them. Two pages also had their reading order
wrong - B1 p21 and B4 p18, where interleaved columns scrambled the dialogue.

```bash
npm run dev               # then open http://localhost:4321/dev/review
```

- Drag on empty space to draw a panel; drag a box to move it; drag its corner to resize; Delete removes it.
- List order = reading order (↑/↓ to reorder).
- Descriptions say what is **drawn**, not what is said - the page transcript already carries
  the lettering, and a screen reader reads both. They also keep the book's own withholding:
  he is "the young man" until the Professor names him Dvij on B1 p12.
- "Set as start of" fixes a chapter's first page.
- Ctrl+S saves the page to `src/content/corrections/`; `[` and `]` move between pages.

Afterwards run `npm run manifests` to fold the corrections into the manifests.

Corrections live in two files, both committed:

| File | Shape |
|---|---|
| `src/content/corrections/panels.json` | `{"b1-p004": {"panels": [[x0,y0,x1,y1], …], "alt": ["…", …]}}` - omit `panels` to keep the detected boxes and only set descriptions |
| `src/content/corrections/chapters.json` | `{"23": 39}` - chapter number to corrected start page |

**Hotspots mode** (same page, "Hotspots" button): orange boxes are automatic links from the lettering;
click one to switch it off. To add a link (e.g. on a drawn symbol rather than a word), pick a Codex entry
and drag a box. Changes save to `src/content/hotspots/manual.json` immediately.

## How companion content finds its page

Puzzle starts, rail beats, Voice `firstSeen` values and fragments are all pinned to a
comic page by `pipeline/find_page.py`: it locates a quoted passage in the manuscript,
reads off its chapter, and picks the page in that chapter whose lettering matches best.
Chapter ranges include the reviewed corrections from `corrections/chapters.json`.

Where the art never lettered the passage, nothing matches and the lookup falls back to
the chapter's first page - reported as `chapter-only`. That is usually close, but for a
`firstSeen` it lifts the spoiler veil early. Four anchors were wrong and are now pinned
explicitly, each with a comment saying what the art shows:

| Where | Field |
|---|---|
| `content/parchment.yaml` | `availablePage: b4-p016` |
| `content/rail.yaml` | `page: b5-p009` on the node |
| `content/voices/*.md` | `firstSeen: {book, page}` in the front matter |

An override resolves with confidence `reviewed`. Re-run `npm run codex`,
`python pipeline/link_parchment.py` and `python pipeline/link_companions.py` after
editing any of them, and they print each anchor's confidence.

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
| `PUBLIC_ASSET_BASE` | Where page images, art and PDFs are served from. Set to the R2 bucket in `netlify.toml`; unset locally, where the dev server serves `../site-assets` at `/_assets`. |
| `SITE_URL` | Canonical site URL (once the domain is chosen). |
| `BUNDLE_ASSETS=1` | Copy `site-assets` into the build (option B). `build:local` sets it. |

## Hosting the assets (Cloudflare R2)

The 742 MB of page images, art and PDFs are build output, not source, so they
are never in git. They live in a Cloudflare R2 bucket and the site reads them
from `PUBLIC_ASSET_BASE`. R2 charges nothing for egress, which is what makes it
a good fit for a comic: a reader going through all 171 pages pulls about 36 MB.

One-time setup:

1. Cloudflare dashboard -> R2 -> Create bucket, named `dvij-assets`, location
   Automatic.
2. That bucket -> Settings -> Public access. Either allow the `r2.dev` subdomain
   (fine to start; Cloudflare rate-limits it and asks you not to use it for
   production) or attach a custom domain such as `assets.yourdomain.com`, which
   is the better option once the domain exists.
3. R2 -> API -> Manage API tokens -> Create API token, permission **Object Read &
   Write**, scoped to this bucket only. Copy the access key id and secret; the
   secret is shown once.
4. `cp .env.example .env` and fill in `R2_ACCOUNT_ID`, `R2_BUCKET`,
   `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`. `.env` is gitignored.
5. Put the bucket's public URL in `netlify.toml` as `PUBLIC_ASSET_BASE`, with
   no trailing slash. It is public by design and shows up in every built page,
   so it belongs in the repo rather than in the Netlify UI. Astro inlines it at
   build time, so changing it needs a redeploy.

Then upload:

```bash
npm run upload -- --dry-run     # what it would send, and how much
npm run upload                  # ~742 MB the first time
npm run upload -- --only art    # just one folder
```

The script mirrors `site-assets/pages`, `art` and `pdf` into the bucket at the
same paths, sets each object's content type, and caches the content-hashed
images forever. It skips anything already in the bucket at the same size, so a
re-run after an interrupted upload picks up where it stopped, and re-running
after a partial re-encode only sends what changed. `--force` re-uploads
everything.
