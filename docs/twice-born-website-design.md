# The Twice Born — Website Design

Design for a static website, hosted on Netlify, that publishes the *Twice Born* comic and the interactive companion layers worked out in [twice-born-website-design-discussion.md](twice-born-website-design-discussion.md). This document supersedes the discussion record where they differ; §17 lists the corrections.

---

## 1. Decisions

| Area | Decision |
|---|---|
| Launch | **Public**, hosted on Netlify. Domain to be decided later |
| What the reader shows | The **final pages** from `book/B1.pdf`–`B5.pdf`, with a **panel-by-panel mode** derived from the PDFs |
| Source of published images | **Compressed** versions of the five book PDFs. They are compressed first and hosted as downloads, and all page images are extracted from them (§4.1) |
| Working material | **Not hosted.** Nothing from `images/` is published except the few files listed in §4.7 |
| Art | **Final as-is; nothing will be redrawn.** The site describes the art exactly as printed (§4.6) |
| Reading mode | **Hybrid** — two-page spreads on desktop, single page on phones, optional panel view |
| AI features | **Static v1**; codex Q&A and character chat designed now, built as **v2** |
| Hosting | Netlify, static output, auto-deploy on push |
| Site framework | Astro (static output, interactive "islands" for the reader and puzzles) |
| Build pipeline | Offline Python (PyMuPDF), run locally against `book/` — never on Netlify |

---

## 2. Source Material

Everything the site needs already exists in this folder. Facts below were measured from the files.

### 2.1 The comic — `book/`

| Book | Title | Pages | Parts | PDF size |
|---|---|---|---|---|
| 1 | Valley | 42 | 5 (12, 8, 6, 9, 7 pp) | 634 MB |
| 2 | Parchment | 34 | 5 (5, 7, 8, 6, 8) | 365 MB |
| 3 | Leaf | 34 | 5 (9, 7, 7, 6, 5) | 327 MB |
| 4 | Ascent | 32 | 4 (8, 9, 9, 6) | 336 MB |
| 5 | Discovery | 29 | 5 (6, 7, 6, 5, 5) | 323 MB |
| **Total** | | **171** | **24** | **1.9 GB** |

- Every page is portrait, **1058 × 1688 pt** (≈ 14.7 × 23.4 in), composed of multiple panels.
- Each book PDF is exactly the concatenation of its part PDFs in `images/book N/BNC1…C5.pdf`, so page → part mapping is known.
- **Captions and speech balloons are live text**, not baked into the art (e.g. B1 p2: *"Lost... I've been driving too long."*). They can be extracted with positions.
- **Each panel is a separate embedded image** with a known bounding box on the page (B2 p4 has 12). Boxes bleed past the page edge and overlap slightly under gutters.
- Only Book 1 has a front page (p1, no lettering). Books 2–5 start directly on story pages.
- The PDFs have **no chapter bookmarks** — their outlines are auto-generated from every text frame. Chapter → page mapping has to be derived (§4.4).
- **Known defect in the source: B1 p1.** The page holds two images — the valley map across the top half, and a 1536 × 1024 PNG across the bottom half that is pure black (brightest pixel 1 of 255). It is in `book/B1.pdf` itself, so it is in the printed book and is not something the pipeline introduced; no other page has anything like it. The site drops it from that page's panel list so panel mode does not step into a black rectangle, but the page still displays as the map above a black field. Cropping the page would change how a printed page is shown, so that decision is the author's (§18).

### 2.2 Companion material

| Source | Contents | Used for |
|---|---|---|
| `book/The Twice Born.docx` | Full prose manuscript, ~103k words, 80 chapters + prologue/epilogue | Rail beats, Council excerpts, v2 AI grounding |
| Manuscript **endnotes** (13) | Vaastu Purusha Mandala · Ashtadhyayi lesson · the Vedic-mathematics pi shloka · Dikpalas table · Lakshmi's symbol · Nakshatras table · stages of Shaivite renunciation · Chakra–tattva table · Kanchuka diagram · Bija mantras · Periodic Table of the Tattvas · Navagrahas & Navratnas · Gnomon | Seed content for the Codex |
| `images/artifacts/` | `map.jpg` (valley map); `parchment.png` (full parchment); **`parchment - mapped.png`** (the same parchment with the **5 puzzles boxed**); `first`–`sixth.jpg` (line-art crops); `one`–`five.png` (aged-parchment renders); `vaastu mandala`, `tattvas`, `nakshatra`, `gnomon`, `directions`, `hierarchy`, `lakshmis symbol`, `leaf` | Codex illustrations, parchment puzzle, valley map |
| `images/**/chapterN_panel_breakdown.md` (81) | Per-panel visual description, captions, character notes | Chapter mapping, alt-text starting point (build-time only; not published) |
| `images/references/characters/` | Dvij and Bhavi model/expression/costume sheets | Design reference only (not published) |
| [real-india-pairings.md](real-india-pairings.md) | Suggested real-world counterparts for 16 valley places | Real India layer (§10) |

---

## 3. Site Map & URLs

Deep-linkable URLs are built in from day one — cheap now, expensive to retrofit.

| URL | Page |
|---|---|
| `/` | Home — cover, synopsis, **Start reading** / **Continue reading**, entry points to the companion layers |
| `/read/` | Book picker (5 books, cover thumbnail, part list, progress per book) |
| `/read/b1/` | Book overview — parts, chapters, page thumbnails, **Download PDF** (the compressed book) |
| `/read/b1/7` | Reader at Book 1, page 7 |
| `/read/b1/7#p3` | Reader in panel mode at panel 3 of that page (a hash, so no extra static routes are needed) |
| `/read/b1/ch/12` | Redirect to the first page of chapter 12 |
| `/codex/` · `/codex/<slug>` | Codex index and entries |
| `/parchment/` | The Parchment of Puzzles (Guided / Hard) |
| `/caves/` | The Bhoodara caves pi puzzle |
| `/journey/` | The trek rail — chakra, party, and teacher lenses |
| `/voices/` · `/voices/<slug>` | Council of Voices |
| `/bestiary/` · `/bestiary/<slug>` | Bestiary — the book's mythological creatures (§11) |
| `/avadhana/` | The Memory Hall — the recitation technique Dvij learns (§12) |
| `/valley/` | Valley map, with the Real India layer |
| `/search/` | Full-text search across comic text and codex |
| `/about/` | About the book and author |

The Charvaka thread (§9.1) has no nav entry by design.

---

## 4. Content Pipeline (offline)

A set of Python scripts in `site/pipeline/`, run locally with PyMuPDF (already installed: 1.25.5). Input is `book/*.pdf`. Output is compressed PDFs, page images and JSON manifests. The pipeline runs once, and again only when a book PDF changes.

### 4.0 Compress the PDFs (first step)
Every published file comes from the compressed PDFs, never from the 1.9 GB originals.

- **Method (`site/pipeline/compress.py`):**
  - re-encode each embedded panel image from lossless PNG to JPEG. Every image is RGB with no transparency and at most 148 dpi at print size, so no downsampling is needed
  - leave all text, vectors and layout untouched

  Cropping images to their visible area, as the external tool behind the old `B1C1-compressed.pdf` benchmark did, would have saved only about 8 % more.
- **Result (built):** JPEG quality 80 with 4:2:0 chroma, chosen by side-by-side comparison. **202.5 MB for all five books**, versus 1.9 GB (Book 1: 66 MB; Books 2–5: 31–38 MB each). Every book passes the gate: identical text, worst-page SSIM 0.972–0.978. The existing benchmark reached 5 % only by visibly softening detail (SSIM 0.87).
- **Quality gate:**
  - render a sample page from each book at 2× from both the original and the compressed PDF, and compare side by side
  - JPEG quality is set where no difference is visible at reading size (q80 4:2:0 chosen over q85 4:4:4, q70 and the benchmark)
  - check that text extraction gives identical output
- **Output:** `site-assets/pdf/the-twice-born-b1.pdf` … `b5.pdf`. These are the downloadable books and the only source for §4.1–4.3.

### 4.1 Page images
- Render each page of the **compressed** PDFs at 2× (≈ 2116 × 3376 px) as the master.
- Emit widths **2116 / 1400 / 900 / 240 (thumb)** in **AVIF** with **WebP** fallback, served via `<picture>` + `srcset`.
- Filenames carry a content hash (`b1-p007.3f9a2c.avif`) so they can be cached forever.
- Size (built): 547 MB for all 1,368 files, most of it the full-width masters. A reader typically downloads the 900 or 1400 px AVIF: about 210 KB per page on a phone.

### 4.2 Text layer
- Extract every text span with its bounding box and font size, per page.
- Store per page: `[{text, bbox, kind}]`, where `kind` is heuristically `caption | balloon | sfx`. Large, isolated all-caps words such as RATTLE or CRASH are tagged `sfx`.
- Uses: a hidden, screen-reader-accessible transcript under each page; the search index; an optional "transcript" toggle for readers.

### 4.3 Panel boxes (reviewed: 171/171 pages, 1,712 panels)
`detect_panels.py` works from paint order rather than bounding boxes. The pages have no gutters and images overlap, so the draft is built by walking the page's drawing operations and letting the last painter win each cell of a grid; boxes are then clipped to the page, merged where they overlap heavily, and slivers dropped. Output is `panels: [[x0, y0, x1, y1]]`, normalised 0–1, in reading order.

**The review is done.** Every page was checked against the art, and corrections are stored in `src/content/corrections/panels.json`, which `build_manifests.py` merges over the draft. What it found:

| Book | Draft boxes | After review | Pages corrected |
|---|---|---|---|
| 1 | 357 | 383 | 20 of 42 |
| 2 | 364 | 364 | 1 of 34 |
| 3 | 372 | 372 | 1 of 34 |
| 4 | 296 | 296 | 1 of 32 |
| 5 | 297 | 297 | 2 of 29 |

Book 1 accounts for almost all of it: its pages are montages where drawings bleed into one another with no gutter, so the detector repeatedly merged two pictures into one box. Books 2–5 are laid out on regular grids and came through nearly clean.

Two pages had their **reading order** wrong rather than their boxes — B1 p21 and B4 p18, where two columns interleave and the stored order ran straight down each column, scrambling the dialogue. Both now follow the conversation.

The dev tool (`/dev/review`, dev builds only) remains the way to change any of this by hand.

### 4.4 Chapter mapping (confirmed: 81/81)
`map_chapters.py` takes the quoted captions and dialogue from each chapter's panel breakdown and fuzzy-matches them (RapidFuzz) against the lettering extracted in §4.2. The first page carrying a match gives the chapter start; matches with only one hit are flagged low-confidence. Output is `chapters: [{n, title, book, startPage}]`; `confirmed` is added at manifest time.

That heuristic is right most of the time but has a known failure: a short phrase two chapters share — a place name, a stock exclamation — pulls a start a page early. **All 81 starts have now been checked** by a stronger method: attribute *every* line of lettering on every page to whichever chapter's breakdown matches it best, then take a chapter's start to be the first page it owns a line on. A chapter that begins halfway down a page is still credited to that page, and a shared phrase goes to whichever chapter fits it better rather than to the first one over a threshold.

That agreed with the pipeline on 75 of 81. Five corrections, each then checked against the art and stored in `src/content/corrections/chapters.json`:

| | Was | Now | Why |
|---|---|---|---|
| B1 ch23 | p38 | **p39** | p38 is entirely the tunnel scene; p39 opens "Next day, the sky was overcast". "Kaal Bhairava temple" appears in both chapters and dragged it early |
| B3 ch38 | p3 | **p4** | p4 opens on the chapter's own first line |
| B4 ch51 | p4 | **p3** | it begins halfway down p3, at the Arjuna's-chariot exchange |
| B5 ch69 | p11 | **p10** | every line on p10 is its own; this also unpicks ch69 and ch70 both claiming p11 |
| B5 ch78 | p26 | **p25** | likewise for ch78 and ch79 |

Chapters are short, often 1–3 pages, so a page can still legitimately hold two chapter starts: B5 p11 carries ch70's opening after ch69 ends mid-page.

### 4.5 Manifests
One manifest per book, the single data source the reader consumes:

```json
{
  "book": 1, "slug": "b1", "title": "Valley",
  "cover": "b1-p001",
  "pdf": { "file": "pdf/the-twice-born-b1.pdf", "bytes": 66094228 },
  "parts": [{ "n": 1, "startPage": 1, "endPage": 12 }],
  "chapters": [{ "n": 0, "title": "Prologue", "startPage": 2, "confirmed": true }],
  "pages": [{
    "n": 7, "id": "b1-p007", "w": 2115, "h": 3375, "reviewed": true,
    "src": { "avif": { "2115": "…", "1400": "…", "900": "…", "240": "…" }, "webp": { "…": "…" } },
    "panels": [{ "box": [0.0, 0.0, 0.2913, 0.1896], "alt": "…" }],
    "text": [{ "t": "Splash! Splash!!", "bbox": [0.0577, 0.1012, 0.1472, 0.1488], "kind": "sfx", "panel": 0 }]
  }]
}
```

A panel's `box` is `[x0, y0, x1, y1]`, normalised 0–1. Each text unit carries the index of the panel it sits in, so the transcript reads in panel order. `reviewed` is true for pages with an entry in `corrections/panels.json`; `confirmed` is true for a chapter whose start is either high-confidence or fixed in `corrections/chapters.json`. Both are true for everything as of this pass.

Adding or correcting a book is a content update, not a code change.

### 4.6 Alt text (written: 1,712 of 1,712 panels)
The art is final and won't be redrawn, so **descriptions follow the printed panels exactly as they appear.** They were written from the rendered pages rather than from the panel breakdowns, because the breakdowns are the brief the art was drawn *from* and the two diverge in places.

Rules the pass followed:

- **Describe what is drawn, not what is said.** The lettering is already in the page transcript (§4.2) and is read out separately; repeating it would double every line for a screen-reader user. A description names speech only where the act of speaking is the picture — "the Mahant, snarling", "Bhavi shouts with a hand out".
- **Keep the book's own withholding.** He is "the young man" until the Professor names him Dvij on B1 p12, and she is "the young woman" until the same page. A description must not know something the page has not yet told the reader.
- **Read the diagram pages out.** Roughly forty pages are charts — the katapayadi tables (B2 p25–26), the eight directional lords (B3 p3), the four puzzle solutions (B4 p29–32), the vaastu purusha chain (B5 p22). For these the description states what the chart actually says, since that content exists nowhere else in the accessible text. These are also the descriptions most worth a second pair of eyes: a misread chart is now written into the site.
- **One sentence a panel**, median about 95 characters, longer only for the chart pages and full-page establishing shots.

**Continuity, as the art actually shows it** (this supersedes the earlier note taken from the breakdowns):

- **The cast is on the right arm.** B1 p4's caption says so and every panel that shows it agrees. The breakdowns disagree with each other about the side; the art does not.
- **He is bearded until B1 p23**, where he finds the crude razor and shaves; from there he is clean-shaven or lightly stubbled. B1 p4 shows "a bearded face under a heavily bandaged head".
- **The head bandage** gives way to a plaster on the brow around B1 p13, and the plaster persists for much of Book 1.

### 4.7 What gets published
| Published | Source |
|---|---|
| Compressed book PDFs (downloads) | §4.0 |
| Page images, thumbnails, panel crops (for Council portraits and share cards) | Rendered from the compressed PDFs |
| Valley map | `images/artifacts/map.jpg` |
| Parchment + per-puzzle crops | `images/artifacts/parchment.png`, cut using the boxes in `parchment - mapped.png` (§7.1) |
| Codex diagrams | Only the `images/artifacts/` diagrams a codex entry actually uses (e.g. `vaastu mandala.jpg`, `tattvas.jpg`, `nakshatra.jpg`, `gnomon.jpg`, `lakshmis symbol.jpg`) |
| Parchment texture for puzzle pages | One of `one`–`five.png`, as a background |

Nothing else from `images/` is published: no working panel PNGs, part PDFs, breakdowns or character sheets. Each file added to this list should be a deliberate choice.

### 4.8 Anchoring companion content to pages
Every companion item — a puzzle's start, a rail beat, a Voice's `firstSeen`, a fragment — is pinned to a comic page by `find_page.py`, which locates a quoted passage in the manuscript, reads off its chapter from the `_Toc` bookmarks, and then picks the page in that chapter whose lettering best matches. The chapter ranges come from the pipeline's `chapters.json` **with the reviewed corrections applied** (§4.4), so a lookup lands in the same chapter the reader sees.

The failure mode is specific and worth understanding: **the art abridges the manuscript.** Where a passage was never lettered, no page clears the match threshold and the lookup falls back to the chapter's first page, marked `chapter-only`. That is usually close enough, but not always — and for a `firstSeen` it leaks, because the spoiler veil lifts early.

A second, subtler trap: a quote can name a *place* where the entry is about a *person*. The tantric baba's `firstQuote` was the line introducing the Kaal Bhairava temple, which is two pages before he is on the page.

Anchors verified against the art during the review pass, with the errors it found:

| Anchor | Was | Now | Why |
|---|---|---|---|
| Puzzle 3 starts | B4 p15 | **B4 p16** | the art letters "The next clue on the parchment looked like a coiled serpent" on p16; p15 is the chapter's first page |
| Puzzle 4 starts | B5 p11 | **B5 p12** | "Nine green eyes" is on p12; p11 is where Dvij only tells her to work on it |
| Rail, svadhishthana | B4 p15 | **B4 p17** | p15 was the chapter's first page; p16 finds the temple, p17 is the moment - the kiss, then the dream of light rising from the base of the spine |
| Rail, Yogini's gift | B5 p8 | **B5 p9** | "And left you the mutt?" is on p9; on p8 she is still there |
| Yogini's `firstSeen` | B1 p40 | **B1 p42** | her line is narration the art never lettered; she first appears on p42, so her card was unveiling two pages early |
| Tantric baba's `firstSeen` | B1 p38 | **B1 p40** | his `firstQuote` names the temple, not the man. p38 is the tunnel, p39 the approach across the lake; he appears on p40, "emerged from Samadhi" |

Each override is an explicit page id in the content file, next to the quote and with a comment saying what the art shows: `availablePage` in `parchment.yaml`, `page` on a rail node, `firstSeen` in a Voice's front matter. They resolve with confidence `reviewed`.

**Still `chapter-only`, and checked to be right anyway:** puzzles 2 and 5 (B3 p24, B5 p21), and the rail's Kurup and Ponga beats (B4 p23, B5 p25).

Every chakra beat is now anchored the same way — on the page that draws the moment, not on the page where the manuscript narrates it. Muladhara, manipura, anahata, vishuddha and ajna each land where the art marks the rise; svadhishthana was the one exception and no longer is.

---

## 5. The Reader

### 5.1 Layout
| Viewport | Default | Options |
|---|---|---|
| Desktop / landscape tablet (≥ 1024 px) | Two-page spread (right-hand page first, as in print) | Single page |
| Portrait tablet / phone | Single page, fit to width | **Panel mode** |

Panel mode:
- Steps through `panels[]` one at a time.
- Animates a zoom from the page to each panel box, keeping the page visible dimmed behind it.
- Next/previous moves between panels, crossing page boundaries seamlessly.

### 5.2 Navigation
- **Page and panel navigation:** arrow keys, swipe, and tap zones (left third back, right third forward, centre toggles chrome). Page Up/Down and Home/End also work.
- **Header, auto-hiding:**
  - book / part / chapter breadcrumb
  - chapter jump menu
  - thumbnail strip
  - mode toggle (spread / single / panel)
  - transcript toggle
- **Book boundaries:** the last page of a book offers the next book directly.
- **URL:** updates on every page turn (`history.replaceState`), so any page can be shared.

### 5.3 Progress & state
- Stored in `localStorage` (wrapped in try/catch; the reader works without it):
  - `lastRead {book, page, panel}`
  - `furthestRead` per book
  - reading-mode preference
- `furthestRead` drives the **spoiler policy** (§5.5).

### 5.4 Performance
- Preload the current page plus the next two; prefetch thumbnails for the chapter.
- Target: largest contentful paint (LCP) under 2.5 s on 4G for the first page. The 900 px AVIF is the mobile default.
- The reader is a single island (Preact or vanilla TS). The surrounding page is static HTML, so it renders before the JavaScript loads.

### 5.5 Spoiler policy (site-wide)
Every companion layer reveals plot: Kurup's betrayal, puzzle answers, who leaves the trek. So every piece of companion content carries a **`firstSeen: {book, page}`** position.

| State | Behaviour |
|---|---|
| Before the reader reaches `firstSeen` | Entry is listed but **veiled**: title and silhouette only, with the note "appears in Book 3" |
| After | Fully visible |
| **Reveal all** toggle | For readers who have finished, or do not care |

A reader who arrives by deep link and has no progress gets a one-time prompt: "Hide spoilers beyond this page?"

### 5.6 Accessibility
- Hidden transcript per page (§4.2), plus panel alt text.
- Full keyboard operation.
- Visible focus rings and respect for `prefers-reduced-motion`: panel-mode zooms become cuts.
- Hotspot marks (§6.3) are real buttons, not just shapes on the image.

---

## 6. Codex & Hotspots (Layer 1)

### 6.1 Codex
A small wiki of the book's concepts. Entries are Markdown files in an Astro content collection, with schema-validated frontmatter:

```yaml
id: chakras
title: Chakras
aliases: [chakra, kundalini chakras]
summary: The seven energy centres along the spine…   # shown in the drawer
related: [kundalini, tattvas, samkhya, bija-mantras]
firstSeen: { book: 3, page: 12 }
source: endnote-8                                     # endnote-N | manuscript | author
images: [tattvas.jpg]
```

The body holds the long form: tables, diagrams, cross-links.

- **Seed content:** the manuscript's 13 endnotes (§2.2) become the first entries almost verbatim.
- **Illustrations:** the `images/artifacts/` diagrams illustrate them. The mapping of files like `hierarchy.jpg` and `directions.jpg` to specific entries is still to be confirmed.
- **Other entries:** names the Professor explains in-line (Mahavidyas, Ashtadikpalas, Kaula, Charvaka, Soma, Bhoodara caves…) become further entries, written from the manuscript.
- **Links:** cross-links make it a wiki rather than a flat glossary — for example, kundalini → chakras → tattvas → Samkhya.
- **Recurring symbols:** each entry lists the pages it appears on ("this glyph also appears on B2 p5, B3 p9"). This fits the book, whose plot runs on recognising symbols.
- **Script:** diacritics (IAST, e.g. *Bhārāti Kṛṣṇa*) and Devanagari must render, which affects the font choice (§13).

### 6.2 Presentation
| Trigger | Result |
|---|---|
| Tap a hotspot or codex link | **Drawer** with `summary` (bottom sheet on phones, side panel on desktop); the art stays visible |
| "Read more" in the drawer | Full entry at `/codex/<slug>` (dense tables such as the chakra table live here) |

### 6.3 Hotspots
Hotspots come from two sources, merged at build time:

- **Automatic** (`src/content/hotspots/auto.json`, from `pipeline/link_codex.py`): every caption or balloon whose text mentions a Codex entry's `aliases` becomes a hotspot over that lettering. The earliest mention also sets the entry's `firstSeen`, so spoiler positions follow the comic itself. The first run produced 72 hotspots on 41 pages.
- **Manual** (`src/content/hotspots/manual.json`, from the review tool's Hotspots mode): switch off unwanted automatic ones, and draw new ones, for example on a drawn symbol that no caption names.

```json
{ "id": "auto-b1-p007-3", "page": "b1-p007", "rect": [0.64, 0.08, 0.83, 0.15],
  "targets": ["codex:matrikas"], "terms": ["saptamatrikas"], "auto": true }
```

- **Rect:** `[x0, y0, x1, y1]`, normalised 0–1, the same as panel boxes.
- **Targets:** `codex:`, `puzzle:`, `voice:`, `place:`, `fragment:`. One mechanism serves every layer. Phase 2 uses `codex:`.
- **Visual cue:** a small gold dot at the hotspot's corner. The reader's **Notes** toggle (key `n`) shows or hides them.
- **Validation:** `pipeline/validate_content.py` fails the build if any target, page or image doesn't resolve.

---

## 7. The Parchment of Puzzles (Layer 2)

### 7.1 What the parchment actually is
The parchment holds **five puzzles**, one per row: "They form five rows... with each row a puzzle by itself. The 5 puzzles will lead to 5 different solutions. The solutions will eventually add up." The characters solve them **in row order**. The full chains below were transcribed from the manuscript and are built into `site/src/content/parchment.yaml`.

| # | Drawing | Solution chain | Chapters | Comic pages (start → solved) |
|---|---|---|---|---|
| 1 | Tree with a vertical eye | Vertical eye = Shiva's third eye → Shiva meditating under the Kalpataru = **Gyaneshwar** → there is no Gyaneshwar temple, so it must be Kaal Bhairava, whose linga bears a vertical eye → vaastu treats the whole temple as a tree, with the garbhagriha as its trunk → the idol's line of sight runs past the flagstaff and gopura to **Mount Dronagiri** | 42–43 | B3 p19 → p23 |
| 2 | Crescent moon + three serrated rings holding a yoni ("key"), a teardrop and a flute | Rings = **Sudarshan chakra** = Kaal Purusha, the band of rashis → the moon brings in the **nakshatras** → the three symbols = **Bharani, Aridra, Dhanishta** → one naming syllable from each spells **Ponga**, so the mendicant must join the expedition | 44–45 | B3 p24 → p27 |
| 3 | Coiled serpent, a seven-trunked elephant, eight small figures (last one underlined), a stopwatch | Serpent = **kundalini**, so the next three pictures are chakras → seven-trunked elephant = **muladhara** (an ordinary elephant would be vishuddha, the first wrong guess) → eight figures = **ashtamatrikas**; the eighth rules the vowels, which sit on the **vishuddha** lotus → stopwatch = **kaala** kanchuka → letter ज (ja) on the Periodic Table of the Tattvas → bija akshara of **svadhishthana** → the three chakra shapes (square, crescent, circle) as an inverted triangle form a **Vedic altar** → the ashram of Kritya Rishi | 56–63 | B4 p15 → p32 |
| 4 | Nine splotchy green "eyes" | Green beans (**moong**) → nine = **navagrahas** → moong belongs to **Budha** (Wednesday) → Budha's direction is **north**, taken from the Vedic altar and found precisely with a **gnomon**. Twist: Bhavi coloured the copies differently. Kurup's red beans point south, so the Mahant goes the wrong way | 70–74 | B5 p11 → p15 |
| 5 | A square man "digesting a fish" + a bull missing its two hind legs | Bull = **Dwapara** yuga → man = **Vaastu Purusha** → fish = **Mina**, which governs the feet → at the feet, vaastu places the library, and the hours **3–6 pm** → Dwapara also maps to the afternoon → lengthening shadows → the **trishul**'s shadow by the Hanuman temple points the way | 76–77 | B5 p21 → p23 |

Notes:
- **Crops** for the solve panels are cut from the line-art `parchment.png` using the boxes in `parchment - mapped.png`. The page itself shows the aged `parchment - 1.png`, with its own region boxes.
- **The "3 × 3 grid"** in the discussion doc is the **kalasha**: nine wrapped parchment pieces on nine mounds of grain, where Bhavi picks the one with the knot (B2 p33). The puzzle page opens with that scene.

### 7.2 Modes
| Mode | Behaviour |
|---|---|
| **Guided** | Walk through how the characters solved each puzzle, step by step. No way to fail. Hints delivered "in character" by the round-nosed man where the book uses him (puzzle 3) |
| **Hard** | You get the parchment and work out the iconography yourself |

### 7.3 Mechanics
- The full `parchment.png` has one hotspot per puzzle, using the §7.1 boxes. Tapping a puzzle opens its solve panel.
- **Answers:** multiple choice, which is more forgiving than free text for obscure iconography. Every puzzle is a **multi-stage chain** (see §7.1), so each stage is its own question.
- **Unlocking (built):** a puzzle opens when the reader reaches the page where the characters **start** it, so readers can try to beat them to the answer; solving it yourself isn't a spoiler. The **Guided** walkthrough of the characters' own reasoning is gated to the page where they **solve** it. Either lock can be lifted with a button.
- **Round-nosed man:** his hints appear for puzzle 3, the one the characters take to him in the book (Samkhya, the ashtamatrikas, the altar).
- **Hint ladder:**
  1. After a wrong answer, a soft nudge.
  2. After a second wrong answer, a pointer to the relevant codex entry.
  3. "Show me how they solved it", which links to the comic page.
- **Payoff:** each solved puzzle animates into its answer (Dronagiri → Kritya Rishi's ashram → north from the altar → the 3–6 pm shadow). With all five solved, the parchment "adds up" to the plant's location, as the book promises.
- **Where it appears:** embedded from the relevant comic pages via a `puzzle:` hotspot, and standalone at `/parchment/`.
- **Data:** `parchment.json`, one entry per puzzle: `{id, rect, storyOrder, stages:[{prompt, choices, answer, hint, codex}], unlockAt:{book,page}}`.
- **State:** a client-side state machine; progress stored in `localStorage`.

### 7.4 The Bhoodara caves (built: `/caves/`)
- **The book's rule (ch. 33):** in each chamber, count the exits "starting with the one on my left and going clockwise, and skipping the entrance", and take the exit numbered by the next digit of pi. Coming back, reverse the digits and count anticlockwise from the right.
- **The game:**
  1. Decode the shloka *gopī bhāgya madhuvrāta…* with a katapayadi table, giving 3 1 4 1 5 9 2 6.
  2. Go in through eight chambers.
  3. Reach the painted chamber, with the mesolithic hunting scenes.
  4. Find the way back out through the same eight chambers in reverse.
- **Modes:** in Guided mode the exits are numbered. In Hard mode you count them yourself.
- **Unlocking:** the page opens once the reader reaches B2 p26.
- **Where the verse comes from:** the decode step hands the reader the katapayadi table but not the technique that made the verse stick. That is §12, which unlocks earlier and links forward into this page.

---

## 8. The Journey Rail (Layers: kundalini + party + teachers)

One rail, several lenses, as the discussion concluded. The rail is the site's spine for the trek arc (mainly Books 4–5).

### 8.1 Nodes (built)
Ten beats, authored in `site/src/content/rail.yaml` and located in the comic by `pipeline/link_companions.py`.

| Beat | Comic | Kundalini | The party | Teacher |
|---|---|---|---|---|
| At the base of a bottomless pit | B3 p34 | **Muladhara** | | The tantric baba's teaching, recalled |
| The ancient temple of the forest | B4 p17 | **Svadhishthana** | | Kaula, "the left path" |
| A feast at Vidgati's shrine | B4 p23 | **Manipura** | | The round-nosed man: "live joyously" |
| Kurup is gone | B4 p23 | | **Kurup leaves** for the Mahant | |
| The field of fireflies | B5 p8 | **Anahata** | | |
| Yogini's gift | B5 p9 | | **Yogini leaves**; the dog passes to Dvij | |
| Chanting at the Vedic ashram | B5 p16 | **Vishuddha?** (only asked) | | The sage: "That you are" |
| Ponga's work is done | B5 p25 | | **Ponga sits down** | The monk: "You have to look within" |
| Towards infinity | B5 p29 | **Ajna** | **Bhavi stays**; the dog follows | |
| Sahasrara | — | **never lit** | | |

Each chakra beat sits on the page where the art marks the rise, not where the manuscript narrates it (§4.8). The pages above are generated from `rail.yaml`; if you move a beat, `link_companions.py` reprints them all.

### 8.2 Presentation
- **Rail (built):** a slim vertical rail beside the reader, off by default, behind a **Journey** button (or the `j` key) that appears from B3 p34 on. Chakra beats use the traditional chakra colours; other beats are small diamonds. Tapping a beat opens a card with all three lenses and a link to the page.
- **Nodes:** they light up as `furthestRead` passes them. Clicking one opens a card with the beat, a link to the page, the chakra codex entry, and the other lenses for that beat.
- **Sahasrara:** stays visibly unlit at the end. The book refuses to claim completion, and the site should too.
- **Vishuddha:** shown in a hesitant style (dotted outline), because the text frames it as a question.
- **Standalone page (built):** `/journey/` shows every beat as a timeline, with filter buttons for All / Kundalini / The party / Teachers. Beats beyond the reader's progress are blurred. Plotting the beats on the valley map is still a possible Phase 5 addition.

### 8.3 The Mahaprasthanika lens
- **The parallel:** the ending echoes the Pandavas' final journey — a solitary ascent into the mountains, with a dog who stands for Yama/Dharma, after the companions fall away.
- **Framing:** present it as an *interpretive* lens, with softer framing than the chakra lens, because the book never names it.
- **Where it matches the epic** (corrected from the discussion doc):
  - In the epic, companions fall for personal flaws. **Kurup** fits that pattern: he is dropped for greed and treachery.
  - **Yogini** and **Ponga** simply finish their parts.
  - **Bhavi**'s staying behind is a handover of the mission, not a punishment.
- **The dog:** it passes to Dvij when Yogini leaves (~85 %), not in the last line. The last line confirms a handover that happened earlier.

---

## 9. Council of Voices (Layer 3)

`/voices/` (built) is a gallery with one card per figure. Portraits are cropped automatically from the panel where the figure speaks their chosen line, and can be overridden per figure. Each card has:
- portrait (a crop from the comic)
- tradition / school
- the setting where Dvij meets them
- a curated excerpt of their teaching (a comic panel plus a short manuscript quote)
- linked codex entries
- `firstSeen`

| Figure | Tradition |
|---|---|
| Mahant (Mahapandit Sampoornand Swami) | Institutional Vedic-Puranic orthodoxy |
| Head pujari of the Mahavidya temples | Shakta, the ten Mahavidyas |
| Tantric baba (Keshav Bharan, Kaal Bhairava temple) | Aghora / Tantra, Bhairava-Shaivism |
| Great sage of the Vedic ashram | Orthodox Vedic ritualism |
| Monk under the Hanuman-temple tree | Advaita-flavoured renunciation |
| Yogini | Folk / liminal tantric figure |
| The round-nosed man (Vidgati's shrine) | Samkhya; Charvaka setting |
| The Professor (field-guide monologue) | Survey card: Vaishnavism, Shaivism, Shaktism, Naga/Dhumavati, Hanuman devotion, Charvaka, Anant Path, the jatadharis |

- **The Mahant's card** is visually distinct (red rule, "Antagonist" tag). It reads as *how institutional religion gets weaponised*, not as one more equally valid voice.
- **Hotspots:** each figure's line in the comic carries a `voice:` note that opens their card in the reader's drawer.
- **v2:** each card gains a "Talk to …" button (§15).

### 9.1 The Charvaka thread
- **Idea:** Charvaka is a hidden, **recurring thread**, not a card. Readers collect it rather than being handed it, which echoes the book's theme of suppressed knowledge.
- **Fragments:** `fragment:` hotspots placed at:
  1. the Professor's Charvaka manuscript in the prologue
  2. the Charvaka shrine on the valley map
  3. the round-nosed man's "While life is yours, live joyously"
  4. the Professor's "Do you think that puts me under grave peril?"
  5. the ashvamedha as "a work of fools"
- **Discovery (built):** fragments are marked with a faint ✦ rather than the usual note dot, and are recorded in `localStorage` when opened. Until all five are found, `/charvaka/` shows only a count and a hint; with all five it shows the collected fragments and what they add up to. It is never linked from the nav.
- **Where they are:** B1 p7 (the Professor's disguised manuscript, a corner mark), B4 p4 (×2: "a work of fools", and "Charvaka's texts were not destroyed"), B4 p20 (Vidgati's shrine) and B4 p22 ("While life is yours").

---

## 10. The Valley Map & Real India (Layer 4)

- **Base map:** `/valley/` uses `images/artifacts/map.jpg` with pan and zoom. Each location is a `place:` hotspot linking to its card and the comic pages where it appears.
- **Places:** fort ruins (mint, "royal gym", the math), two pushkarinis, the chain-gated stepwell, the Bhoodara caves, the rock-cut caves near Vidgati's shrine, and the temple clusters.
- **Real India toggle:** swaps the fictional labels for each place's real heritage-site inspiration: photo, short real history, and an optional external map link. It is the one layer that deliberately breaks the fiction. It answers the Professor's line: "it could have been anywhere… Thus it is nowhere."
- **Data:** `places.json` with fields `{id, name, mapRect, pages[], real: {name, region, lat, lng, photo, credit, note}}`.
- **Pairings:** [real-india-pairings.md](real-india-pairings.md) proposes real counterparts for 16 places, each with its reasoning, a confidence level and sources. Examples: Daundagarh → Daulatabad Fort, Gaumukh hill + Kamal Taal → Anjanadri hill + Pampa Sarovar, the Mahavidya temples → Kamakhya, Bhoodara → Bhimbetka's paintings in a Belum-like labyrinth, Dronagiri → Dronagiri Parvat, the final valley → the Valley of Flowers.
- **A second view:** the pairings span the whole country (Deccan, central India, Odisha, Assam, the Himalaya). So besides the label toggle, the layer gets a small **India map** with a line from each valley location to its real site, a visual form of the Professor's "it could have been anywhere."
- **Places left fictional:** Madangi Van, the tavern and bazaar, and the lodge stay fictional on purpose. Some of the valley should remain *nowhere*.
- **Still needed:** your confirmation of each pairing, plus photos with licences (your own, public domain, or CC with credit, recorded in `places.json`).

---

## 11. The Bestiary (Layer 5) — planned, not started

The valley is full of creatures. Most are spoken of rather than met: the cook warns of nagas and yakshas in the forest, Viraat reels off banmanus, pichhal peris, pishachas, kimpurushas and kinnars as the van climbs into the dark, Bhavi explains the boulder field with a rakshasa riding a mountain, and vyalas are carved on the temple steps. A section where a reader can browse them, see them, and read what tradition says about them is the last of the book-world layers.

### 11.1 What is in the book

Gathered from the lettering and the reviewed panel descriptions. "Named" means the word is in a caption or balloon; "drawn" means the art shows the creature, whether or not it is named.

| Creature | Named at | Drawn at | Note |
|---|---|---|---|
| **Vyala** | b1-p039 (×2) | b1-p039, b3-p022 | The strongest entry: the book defines them itself — "composite creatures controlling cosmic energy" — and draws them twice, as elephant-headed lions on high plinths, then in close-up as a lion-faced guardian with horns and a carved mane |
| **Naga** | b1-p011 | b2-p003 (a golden figure reclining on a serpent couch) | Three different things share the name in this book — see §11.5 |
| **Yaksha** | b1-p011 | b1-p011 (the painted forest scene behind the cook: a tiger, a lion and horned figures half hidden among the trees) | |
| **Rakshasa — Vraktaasura** | b1-p030 | b1-p030 (horned, riding a mountain through the sky as Indra looses the vajra) | Named, with his own myth, on the page |
| **Giants** | b1-p030 | b1-p030 (heaving boulders over the fort walls) | The scattered boulders are their work — or a meteor's. The page argues both |
| **Banmanus** | b1-p018 | b1-p018 (huge shaggy man-figures in the dark forest) | |
| **Pishacha** | b1-p018 | b1-p018 (crouching ghouls) | |
| **Kimpurusha / Kinnara** | b1-p018 | b1-p018 (a horse-headed being) | Two names in one breath; one entry or two is an authoring call |
| **Pichhal peri** | b1-p018 | — | The backwards-footed woman of North Indian folklore; the book only names her |
| **Bhoot / Pret** | b1-p036, b1-p039, b3-p034 | — | "Bhoots, prets prey on unsuspecting souls, not forlorn ones." The abandoned Forest Officer's bungalow is a *bhoot* bungalow, and the Kaal Bhairava temple floats on *Bhootnath* taal |
| **Gandharva** | b4-p017 | — | Bhavi's aside: "you are what my uncle would call 'a gandharva's incarnation'" |
| **Apsara** | b5-p028 | — | Bhavi recalls the stories of the apsara and the ascetic rishi |
| **Ashtomi** | b4-p019 | b4-p019 (the hillside ablaze with flowering trees that Kurup points at) | A race, not a beast: "they survive by smelling flowers… any unpleasant smell causes instant death" |

Thirteen entries, the same order of magnitude as the Codex's 21. More will surface while the entries are written; the table above is what a first pass over all 171 pages of lettering and panel descriptions found, and `pipeline/find_page.py` locates any further ones in the manuscript.

### 11.2 Editorial stance — the book debunks its own monsters

This layer cannot be a straight monster manual, because the book will not let it be one. The creature roll-call on b1-p018 is answered in the very next balloon:

> Age-old legends, fabricated to scare children from straying into forests. Now used by Mahant to scare peasants from escaping.

The same move happens on b1-p030, where the giants' boulders become an asteroid, and again on b3-p034, where the yogini's line about bhoots and prets is a correction rather than a warning. So each entry carries three registers, in this order:

1. **In the book** — the panel, the quote, the page link. What is actually on the page.
2. **In tradition** — where the creature comes from, what it is in the texts and in folk telling.
3. **And yet** — who in the book doubts it, and why. This is the Charvaka thread (§9.1) running through the bestiary, and it is what keeps the section honest with the story.

A reader who works through the bestiary should come away with the Professor's habit of mind, not with a list of monsters.

### 11.3 Mechanics

Reuses the Codex machinery end to end (§6) rather than inventing a parallel one:

- **Collection:** `src/content/bestiary/<id>.md`, a second Astro content collection with the Codex schema (`title`, `aliases`, `summary`, `related`, `images`, `source`, `firstSeen`) plus `class` (naga · yaksha-class · rakshasa-class · bhoot-class · composite-carving · race), `appearance` (what it looks like, for the gallery caption) and `alsoKnownAs`.
- **A separate collection, not a Codex flag.** The two differ in presentation — the Codex is a text wiki, the bestiary an image-first gallery — and keeping the aliases in their own namespace is what makes the disambiguation in §11.5 tractable. The cost is a second collection to author and validate. `related:` links cross the two freely, so a creature can point at `codex:kaula` and back.
- **Hotspot target:** a new `beast:` prefix in the existing scheme (§6.3). One mechanism still serves every layer.
- **Auto-linking:** a `link_bestiary.py` alongside `link_codex.py`, with a per-entry `exclude` list of contexts that must not fire (§11.5). The earliest mention sets `firstSeen`, so the same spoiler veil applies (§5.5).
- **Validation:** `validate_content.py` gains the collection, its images and its hotspot targets.

### 11.4 Images

Three sources, in order of preference:

1. **Crops from the comic itself.** Eight of the thirteen are drawn — everything above except pichhal peri, bhoot/pret, gandharva, apsara and the Ashtomis, whose panel shows the flowering hillside rather than the race itself — and every panel already has a reviewed box, so a `portrait: {page, box}` crop works exactly as the Voice portraits do (§9) — `link_companions.py` already has the cropping code. No licensing to chase, and the gallery then looks like the book instead of like a stock-photo wall.
2. **`images/artifacts/` diagrams**, where one illustrates an entry.
3. **Public-domain or CC photographs of the real carvings** for the "in tradition" register — vyalas and makaras on temple plinths are photographed everywhere. Licence and credit recorded per image, the same discipline the Real India layer needs (§10).

The five entries with no art (pichhal peri, bhoot/pret, gandharva, apsara, Ashtomi) get a typographic card rather than a placeholder image. A quiet gap is better than a stand-in that contradicts the book's own pictures.

### 11.5 Disambiguation — where auto-linking will go wrong

Every one of these is a real string in the manifests, and each would otherwise produce a false hotspot:

| Word | The trap |
|---|---|
| **Naga** | *Naga hill* (b1-p039), the *Naga tribesmen* in the smoky frames (b2-p002) and the serpent-being are three different things |
| **Makara, Simha, Mina, Vrishabha** | Zodiac signs on the star chart (b3-p025) and the zodiac-body table (b5-p022), not creatures |
| **Matsya** | One of the five M's — madya, matsya, mamsa, mudra, maithuna (b4-p017) — not the avatar |
| **Yogini** | A character in the party throughout, not the class of deity |
| **Varaha** | The *Varaha Purana* (b4-p030), cited as a text |
| **Nandi, Hanuman** | Deities and their images, not bestiary creatures. They belong in the Codex; the bestiary `related:` links across |

### 11.6 Site map

| URL | Page |
|---|---|
| `/bestiary/` | Gallery index — a card per creature, filterable by `class`, veiled by `firstSeen` |
| `/bestiary/<slug>` | One creature: the three registers, its panels, its Codex cross-links |

Whether it earns its own nav entry or sits under the Codex is a presentation call to make once the gallery exists.

---

## 12. The Memory Hall (Avadhana) — planned, not started

Dvij walks out of a labyrinth nobody returns from because of a party trick he watched at a foundation ceremony. That is the book's best argument for its own subject matter, and the site currently only shows the *end* of it: `/caves/` hands the reader the verse and the katapayadi table, and the technique that made the verse stick — the thing the Professor actually explained — is never taught. This section teaches it, and it is the most naturally interactive material in the book, because the technique *is* a procedure.

### 12.1 What the book shows

| Page | What is on it |
|---|---|
| **b2-p008** | The avadhan show at the ceremony. Caption: "numerous people throwing challenging questions at an expert who responded rapidly… The expert formed verses at will, tracking all questions." The Professor names it: "**Avadhan.** That's what this is called. Many people ask questions. Expert has to remember all of them, then respond to each in verses following rules of rasa and alankara." Then the technique: "**Techniques of memorization!** The entire Vedas handed down orally through millenniums! Students learned **forward sequence, backward, skipping syllables** — remember it forever!" |
| **b2-p008, drawn** | Two panels do the teaching. One shows the expert seated inside **a ring of ten numbered questioners**. The next is a held-up **chart**: *1. Forward sequence*, one to ten with arrows; *2. Backward sequence*, ten to one; *3. Skipping syllables*, with alternate numbers dropped |
| **b2-p025** | The payoff, three books' worth of setup later: "Professor explained their memorization technique to me. **I tried it on a shloka and it worked.**" — "This shloka gave you some magical powers?" — "**No**, but it did help me remember the value of pi" |
| **b2-p026** | The digits become the route through the caves (§7.4, built) |
| **b5-p009–p010** | The same thing in its own setting: the udgatrus' Samaveda chanting, and "they are shrauta texts, **preserved by oral recitation**" |

So the book supplies the technique, the drawn chart, the worked application and the reason to care — and the site already owns the last link in that chain.

### 12.2 The real technique, and why it is worth a section

The chart on b2-p008 is a simplified drawing of the Vedic **pāṭhas**: the recitation schemes that carried the Veda for millennia without writing. The ladder runs

| Pāṭha | Pattern over words 1 2 3 … |
|---|---|
| *saṃhitā* | the line as it is spoken |
| *pada* | 1 · 2 · 3 — each word alone |
| *krama* | 1‑2, 2‑3, 3‑4 |
| *jaṭā* | 1‑2 2‑1 1‑2, 2‑3 3‑2 2‑3 |
| *ghana* | 1‑2 2‑1 1‑2‑3 3‑2‑1 1‑2‑3, 2‑3 3‑2 2‑3‑4 4‑3‑2 2‑3‑4 |

The book's "forward, backward, skipping syllables" is exactly *krama*, *jaṭā* and the interleaving of *ghana*, drawn for a reader who is not going to be given the Sanskrit names.

The hook for a modern reader is that **this is an error-correcting code**. Every word is recited inside several different neighbourhoods, so a syllable that drifts in one pass contradicts itself in another and the mistake is audible. An oral tradition solved redundancy checking a long time before checksums, and a browser can demonstrate it in about fifteen seconds: corrupt one word and let the reader watch the *ghana* pattern light up in three places at once. That demonstration is the section's centrepiece, and nothing else on the site does it.

### 12.3 What the reader does

Three pieces, in the book's own order.

**a. The pāṭha ladder.** One verse, shown as word chips in Devanagari with IAST beneath. The reader builds each pattern by placing chips, climbing *pada → krama → jaṭā → ghana*; the app checks each utterance against the rule and shows where a wrong chip breaks the interlock. Patterns are **generated from the word list by rule**, not typed out per verse, so a verse is pure data and any verse can be dropped in. Then the corruption demo of §12.2.

**b. The avadhana ring.** The drawn panel, made playable: questioners around a circle, each handing over one short item, delivered out of order and interleaved with an interrupting task — because that interleaving is what makes it *avadhāna* and not a memory game. The reader then answers in the original order. Start at four, build to ten, which is the ring the book draws. (Eight is *aṣṭāvadhāna*; a hundred is *śatāvadhāna*. The book's ten sits between them, and the entry can say so.) The Professor being shushed mid-explanation on the same page is the obvious model for the interrupting task.

**c. The verse that pays off.** *gopī bhāgya madhuvrāta…* is already on the site, so the chain closes: drill it in the Hall, decode it with the katapayadi table, walk the caves on the digits. Note for whoever builds it — **the two halves read the verse differently.** The pāṭhas segment it into *words*; the katapayadi decode reads it by *consonant*. Same verse, two segmentations, and the UI has to keep them visibly apart or it will teach a muddle. The decode step stays where it is, in `Caves.tsx`; the Hall links to it rather than duplicating it.

### 12.4 Retention, claimed honestly

The manuscript's claim is strong — the shloka "got stuck in my mind permanently" — and the site can *test* it instead of repeating it. On a later visit, once at a day and once at a week, the Hall offers a single optional recall check and reports the plain result, including a failure. One interval, no streaks, no scores, no nagging.

This matters for the same reason §11.2 does: Dvij is asked point-blank whether the shloka gave him magical powers and says **no**. A memory section that oversells itself would be the one page on the site the book itself contradicts.

### 12.5 Mechanics

- **Page:** `/avadhana/`, a new island `src/islands/Memory.tsx`, in the shape of `Caves.tsx` — phases, `localStorage` progress (§5.3), Guided and Hard modes.
- **Content:** `src/content/memory.yaml` — `{id, title, verse: [{deva, iast, gloss}], source, note}`, plus the ring drill's item pools. Verses are data; the pāṭha generator is code.
- **Unlocking:** the existing `availableQuote` mechanism (§4.8) pinned to **b2-p008**, where the Professor explains it. That is earlier than the caves' b2-p026, so the site's order matches the book's: learn it, then use it.
- **Codex:** two entries to write — `avadhana` and `vedic-pathas` — with aliases (`avadhan`, `avadhana`, `krama`, `jata`, `ghana`, `patha`, `shrauta`). `link_codex.py` then auto-links the b2-p008 balloons and the b5-p010 caption, and `firstSeen` lands on b2-p008 by itself.
- **Validation:** `validate_content.py` gains the verse file and the new page reference.
- **Script:** Devanagari and IAST at chip size, side by side. §13 already flags the font requirement; here it becomes load-bearing rather than decorative.
- **Accessibility:** chip placement needs a keyboard path and sensible announcements, and the recall check must not be the only way through (§5.6).

### 12.6 Audio — the gap worth naming

This is an **oral** technique. A silent trainer teaches the permutation pattern but not the thing itself, which is a sound. Three options: ship v1 silent, with the patterns set in Devanagari and IAST; add CC-licensed recordings of ghanapāṭha recitation with credit recorded per file; or record a reciter. Speech synthesis is not an option — TTS mangles Sanskrit prosody and would teach a wrong reading, which is worse than silence.

Recommendation: silent v1, recordings as a follow-up, because the pattern is what carries the section and a bad reading would undermine it. This is an open question (§18).

### 12.7 Site map

| URL | Page |
|---|---|
| `/avadhana/` | The Memory Hall — the pāṭha ladder, the avadhana ring, the link into the caves |

---

## 13. Visual Design

- **Identity:** vintage 1950s–60s Indian adventure comic, the same style lock as the character manifest. The site should feel like the book's world, not a generic webcomic host.
- **Palette:** warm paper cream, sepia, terracotta, faded ink black, with a single saturated red-gold accent taken from Bhavi's costume. Define it as CSS custom properties, with a **night-reading theme** (deep ink background, softened paper) for the reader.
- **Texture:** subtle paper grain on chrome only, never over the art. Parchment texture for the puzzle pages (from `one`–`five.png`).
- **Type:**
  - a characterful display face for titles, echoing hand-lettered comic mastheads
  - a highly readable serif for codex prose
  - a Devanagari-capable face (e.g. Noto / Tiro Devanagari) for terms
  - all faces must cover IAST diacritics
- **Chrome:** the art is the hero. The reader UI is minimal, auto-hides, and never overlaps panels in panel mode.

---

## 14. Technical Architecture

### 14.1 Stack
- **Astro, static output.** It produces one HTML page per comic page and codex entry, which is good for sharing and search. Content collections validate codex / voices / places schemas at build time.
- **Islands:** reader, parchment, caves, journey rail, valley map. Preact or vanilla TypeScript; no heavy framework needed.
- **Search:** [Pagefind](https://pagefind.app) indexes the built HTML at build time, including the hidden page transcripts and codex. It runs fully client-side, with no search backend.

### 14.2 Repository layout
```
dvij/
├── book/                 final PDFs (source of truth; NOT in git)
├── images/               working material (NOT in git)
├── site/                 ← git repo, connected to Netlify
│   ├── docs/             this document, the Real India research,
│   │                     the original discussion record
│   ├── pipeline/         Python + one Node script: compress, render,
│   │                     text, panels, chapters, manifests, linking
│   ├── src/
│   │   ├── pages/        Astro routes (§3)
│   │   ├── components/   layout and veil components
│   │   ├── islands/      reader, drawer, parchment, caves, rail,
│   │   │                 dev review tool
│   │   ├── lib/          manifest, progress, spoilers, codex, companions
│   │   ├── layouts/      the one page shell
│   │   ├── styles/       tokens and global CSS
│   │   └── content/      codex/*.md, voices/*.md, parchment.yaml,
│   │                     rail.yaml, fragments.yaml, hotspots/*.json,
│   │                     corrections/*.json, generated/*.json,
│   │                     manifests/b1.json … b5.json
│   ├── public/           favicon and small static files
│   ├── tests/e2e/        Playwright
│   ├── netlify/functions/   (v2 only)
│   └── netlify.toml
└── site-assets/          pipeline output: compressed PDFs, page images,
                          art (NOT in git; uploaded to Cloudflare R2, §14.3)
```

The three documents in `site/docs/` are the only prose in the repo besides the
README. Paths named in this document — `book/`, `images/`, `site-assets/` — are
relative to `dvij/`, the project root, not to the repo root.

### 14.3 Where the PDFs and page images live
The published binaries are the compressed PDFs (202 MB) and the page images rendered from them (547 MB), about 750 MB in all. They don't belong in git.

| Option | How | Trade-off |
|---|---|---|
| **A. Object storage + CDN** (Recommended) | Upload `site-assets/` to a public bucket (e.g. Cloudflare R2 or S3 behind a CDN) on a subdomain such as `pages.<domain>`; manifests store an `assetBase` URL | The site repo stays small, Netlify auto-builds on push, and assets are uploaded once and cached forever. Large PDF downloads don't count against Netlify bandwidth |
| B. Netlify CLI deploy | Copy `site-assets/` into the build output locally and run `netlify deploy --prod` | One host, but every deploy happens from your machine and there's no deploy on push. Worth reconsidering if the measured total turns out small |

**Decided (20 Sep 2026): option A, on Cloudflare R2.** The measured total is 742 MB — 547 MB of page images across 1,369 files, 194 MB of PDFs, 1.2 MB of art. R2's free tier covers the storage and charges nothing for egress, which matters here: a reader working through all 171 pages pulls about 36 MB, so the same traffic on Netlify would eat its 100 GB monthly allowance roughly 2,800 read-throughs in.

`pipeline/upload_assets.mjs` (`npm run upload`) mirrors `site-assets/{pages,art,pdf}` into the bucket, sets each object's content type, caches the content-hashed images for a year and the PDFs for a week, and skips anything already there at the same size. The site reads `PUBLIC_ASSET_BASE`, set as a Netlify environment variable. Setup steps are in [the site README](../README.md#hosting-the-assets-cloudflare-r2).

Until the domain exists the bucket's `r2.dev` URL works; after that it moves to a custom domain such as `assets.<domain>`, which is one environment variable and a redeploy.

**jsDelivr was considered and rejected.** It would serve the page images — the largest is 1.7 MB, under its 20 MB per-file cap — but all five PDFs are 30–64 MB and exceed it, the files would have to live in a second GitHub repo as 547 MB of permanent history, and jsDelivr is a free service for open-source code rather than a host for a comic's artwork. If it throttled or blocked the repo, the art would go dark with no warning.

### 14.4 Netlify configuration
- **Build:** `astro build && pagefind --site dist`, publishing `dist/`.
- **Caching:** headers with `Cache-Control: public, max-age=31536000, immutable` for hashed assets.
- **Redirects:** `/read/b1/ch/:n` → the chapter's start page, generated at build time from the manifests into `_redirects`.
- **Previews:** deploy previews on pull requests, for reviewing content changes before they go live.
- **v2:** functions in `netlify/functions/`; secrets in Netlify environment variables.

---

## 15. v2 — AI Features

### 15.1 Architecture
- **Proxy:** a Netlify Function (TypeScript, official Anthropic SDK) sits between the site and the Claude API.
- **API key:** kept in a Netlify environment variable. It never appears in client JavaScript.
- **Streaming:** responses stream to the browser.

| Feature | Where | Grounding |
|---|---|---|
| **Ask the Codex** | Codex drawer and entry pages: "Ask about this" | Codex + manuscript |
| **Talk to a Voice** | Council cards | Codex + manuscript + that figure's character sheet (doctrine, speech style, what they refuse to discuss) |

### 15.2 Grounding & caching
- **Corpus:** the manuscript (~103k words) plus the codex fits comfortably in a single request's context window. Measure the exact size with the token-counting endpoint before committing.
- **Prompt order:** the stable corpus goes first in the system prompt, marked for **prompt caching**. The figure-specific sheet and the user's question go after the cache breakpoint. Repeat requests then read the corpus from cache instead of paying full input price each time.
- **Spoilers and caching:** trimming the corpus to the reader's exact progress would change the prompt prefix on every request and defeat caching. Instead, keep **five cache variants**, one per book boundary ("the text through the end of Book N"). Each reader gets the variant matching their `furthestRead`, which keeps spoiler safety without losing cache hits.
- **Voices:** each figure is instructed to answer only from their doctrine and on-page dialogue, to stay in voice, and to decline to drift. The Mahant stays manipulative, never wise.

### 15.3 Model
- **Default:** `claude-opus-5`.
- **Cost trade-off:** a cheaper model (e.g. `claude-sonnet-5` or `claude-haiku-4-5`) cuts cost for high-volume public chat, at some quality cost. That is your call once real traffic and a small evaluation set exist.
- **Refusals:** handle the `refusal` stop reason, and enable the API's server-side model fallbacks.

### 15.4 Cost & abuse controls
Because it is a public site, apply all of these:
- per-IP rate limit (stored in Netlify Blobs)
- maximum question length
- maximum turns per conversation
- a hard daily spend cap that turns the feature off gracefully
- CORS locked to the site origin
- logging of token usage per request, to see real cost before widening access

If per-question cost is too high even with caching, fall back to **retrieval**: send only the relevant chapters plus the codex entry instead of the whole manuscript.

---

## 16. Roadmap

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Pipeline: **PDF compression + quality gate**, page images, text layer, draft panels, chapter map, manifests; dev review tool; asset hosting | **Done.** 1.9 GB → 202.5 MB, all gates passed; 171 pages at 4 widths × 2 formats; assets on R2 (§14.3) |
| 1 | **Reader MVP**: home, book picker, hybrid reader, panel mode, progress, search, PDF downloads; deploy publicly | **Done.** Live on Netlify |
| — | **Review pass**: panel boxes checked, descriptions written from the art, chapter starts confirmed | **Done.** 171/171 pages, 1,712/1,712 panels, 81/81 chapters (§4.3, §4.4, §4.6) |
| 2 | Codex (21 entries), drawer, hotspot authoring, spoiler policy | **Done.** 91 hotspots |
| 3 | Parchment of Puzzles (Guided + Hard), Bhoodara caves | **Done.** 5 puzzles |
| 4 | Journey rail (three lenses), Council of Voices, Charvaka thread | **Done.** 10 beats, 8 voices, 5 fragments |
| 5 | Valley map + Real India layer | **Blocked** on pairings confirmed + photos ([real-india-pairings.md](real-india-pairings.md)) |
| 6 | **Bestiary** — 13 creature entries, gallery, `beast:` hotspots (§11) | **Not started.** Ready to author: the roll-call is gathered and 8 of 13 can be illustrated from the comic art |
| 7 | **Memory Hall** — pāṭha ladder, avadhana ring, recall check (§12) | **Not started.** The pattern generator is the whole build; verses are data. Audio undecided |
| 8 (v2) | Ask the Codex, Talk to a Voice | Not started; needs a cost review |

Phase 1 alone is a complete, shippable comic site. Each later phase adds a layer without reworking earlier ones, because they all share the manifest + hotspot + `firstSeen` pattern.

**Verification as of this pass:** `npm run build` and Pagefind succeed; `validate_content.py` resolves every hotspot target, codex link, `firstSeen` and companion reference; 45 Playwright tests pass (3 skipped by viewport).

---

## 17. Corrections to the Discussion Document

Verified against the manuscript and the PDFs:

1. **The parchment is not a 3 × 3 grid.** It holds **five puzzles** in uneven rows (boxed in `parchment - mapped.png`). The 3 × 3 arrangement is the kalasha's nine parchment pieces (§7.1).
2. **Kurup and Yogini are not separated in the ashram raid.** Kurup defects to the Mahant earlier, and Yogini leaves on her own the morning after the firefly night, before the ashram (§8.1).
3. **The dog passes to Dvij when Yogini leaves** (~85 %), not in the final line (§8.3).
4. **Vishuddha is posed as a question**, not stated like the other chakras (§8.1).
5. **Kurup does fit the epic's "fall through a flaw" pattern**, which strengthens the Mahabharata reading rather than weakening it (§8.3).
6. **The unit is book / part, not "issue".** There are 5 books and 24 parts (§2.1).
7. **Layer numbering:** the discussion's §10 mixes section and layer numbers. This document uses Layer 1 = Codex, 2 = Parchment, 3 = Voices, 4 = Real India, 5 = Bestiary, with the kundalini and Mahaprasthanika material as lenses on one rail.
8. **Paged vs. scroll is settled:** portrait multi-panel pages favour the hybrid paged reader (§1, §5).

---

## 18. Open Questions

**Settled:** public launch · no redraws · compressed PDFs are hosted and are the image source · working images unpublished except §4.7 · five parchment puzzles (§7.1) · assets on Cloudflare R2 (§14.3) · panel boxes, descriptions and chapter starts reviewed across all 171 pages (§4.3, §4.4, §4.6).

**For you:**

1. **Domain name** (you'll specify later). It also names the asset subdomain (§14.3), which is on the rate-limited `r2.dev` URL until then and should not carry launch traffic.
2. **Real India:** confirm or replace each pairing in [real-india-pairings.md](real-india-pairings.md), and source licensed photos. Blocks Phase 5.
3. **B1 p1's black half** (§2.1): leave the page as printed, crop it to the map, or fix the source PDF?
4. **Spot-check the chart pages.** The descriptions on the diagram pages state what each chart says, so a misreading is now in the site's accessible text. The ones worth checking: B2 p25–26, B3 p3–4, B4 p29–32, B5 p22.
5. **Review the authored companion text**: 21 Codex entries, 5 puzzle chains, 8 Voice cards, 10 rail beats. The quotes are the book's; the framing is not.
6. **Voice portraits.** Three of the eight are loose automatic crops — the Mahant's is visibly the wrong figure. Each can be replaced with a hand-picked `portrait: {page, box}`.
7. **Covers for Books 2–5**, for the book picker and share cards. Only Book 1 has a front page.
8. **Bestiary (§11).** Confirm the 13 creatures in §11.1 — add any the scan missed, drop any you do not want a page for — and say whether *kimpurusha* and *kinnara* are one entry or two. The "in tradition" register is written from outside the book, so it needs the same review as the Codex framing (item 5). Blocks Phase 6.
9. **Memory Hall audio (§12.6).** The technique is oral. Silent v1, CC-licensed ghanapatha recordings with credit, or a reciter you record? And which verse the ladder drills besides *gopī bhāgya* — one is enough to ship, but a second makes the pattern generator prove itself.

**Still to decide:**

10. **Spoiler default:** veil by default (current behaviour), or reveal by default with an opt-in veil?
11. **State the patterns or let readers discover them?** Should the kundalini / Mahabharata patterns be named up front, or left for readers to find via the rail?
12. **Analytics:** none, Netlify Analytics, or a privacy-friendly script?
13. **PDF downloads:** free and unrestricted, or behind a simple "read online first" flow? The site is public either way.
