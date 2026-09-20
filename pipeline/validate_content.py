"""Check that companion content is internally consistent (plan Phase 2).

- every Codex `related` id and image exists
- every hotspot's page exists and every target resolves (codex:<id> for now)
- every firstSeen (override or computed) points at a real page
- manual hotspot removals refer to real automatic hotspots
Exits non-zero on any error, so it can gate the build.
Usage: python validate_content.py
"""
import json
import sys

import yaml

from common import ASSETS, BOOKS, SITE

CONTENT = SITE / "src" / "content"


def main() -> int:
    errors: list[str] = []
    pages = {f"{m['slug']}-p{n:03d}" for m in BOOKS.values() for n in range(1, m["pages"] + 1)}
    art = {p.stem for p in (ASSETS / "art").glob("*.webp")}

    entries = {}
    for path in sorted((CONTENT / "codex").glob("*.md")):
        front = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
        entries[path.stem] = front
        for field in ("title", "summary", "source"):
            if not front.get(field):
                errors.append(f"codex/{path.name}: missing {field}")

    for eid, e in entries.items():
        for r in e.get("related", []):
            if r not in entries:
                errors.append(f"codex/{eid}: related '{r}' does not exist")
        for img in e.get("images", []):
            if img not in art:
                errors.append(f"codex/{eid}: image '{img}' not in site-assets/art")
        fs = e.get("firstSeen")
        if fs and f"b{fs['book']}-p{fs['page']:03d}" not in pages:
            errors.append(f"codex/{eid}: firstSeen {fs} is not a real page")

    links = json.loads((CONTENT / "generated" / "codex-links.json").read_text())
    for eid in entries:
        if eid not in links:
            errors.append(f"codex/{eid}: not linked yet (run link_codex.py)")
        elif not (entries[eid].get("firstSeen") or links[eid]["firstSeen"]):
            errors.append(f"codex/{eid}: no firstSeen (not mentioned in the lettering and no anchor match)")

    voices = {}
    for path in sorted((CONTENT / "voices").glob("*.md")):
        front = yaml.safe_load(path.read_text(encoding="utf-8").split("---", 2)[1])
        voices[path.stem] = front
        for c in front.get("codex", []):
            if c not in entries:
                errors.append(f"voices/{path.stem}: codex '{c}' does not exist")
        if front["portrait"]["page"] not in pages:
            errors.append(f"voices/{path.stem}: portrait page {front['portrait']['page']} does not exist")
    voice_links = json.loads((CONTENT / "generated" / "voices.json").read_text(encoding="utf-8"))
    for vid in voices:
        if vid not in voice_links:
            errors.append(f"voices/{vid}: not linked yet (run link_companions.py)")

    rail = json.loads((CONTENT / "generated" / "rail.json").read_text(encoding="utf-8"))
    for node in rail["nodes"]:
        if node.get("at") and node["at"]["pageId"] not in pages:
            errors.append(f"rail {node['id']}: page {node['at']['pageId']} does not exist")
        if node.get("teacher") and node["teacher"]["voice"] not in voices:
            errors.append(f"rail {node['id']}: teacher '{node['teacher']['voice']}' is not a voice")
        if node.get("codex") and node["codex"] not in entries:
            errors.append(f"rail {node['id']}: codex '{node['codex']}' does not exist")

    frags = {f["id"]: f for f in json.loads((CONTENT / "generated" / "fragments.json").read_text(encoding="utf-8"))}
    for fid, f in frags.items():
        if f["page"] not in pages:
            errors.append(f"fragment {fid}: page {f['page']} does not exist")

    companion_hs = json.loads((CONTENT / "hotspots" / "companions.json").read_text(encoding="utf-8"))
    auto = json.loads((CONTENT / "hotspots" / "auto.json").read_text(encoding="utf-8"))
    puzzle_hs = json.loads((CONTENT / "hotspots" / "puzzles.json").read_text(encoding="utf-8"))
    parchment = json.loads((CONTENT / "generated" / "parchment.json").read_text(encoding="utf-8"))
    puzzle_ids = {p["id"] for p in parchment["puzzles"]} | {"caves"}
    for p in parchment["puzzles"]:
        for key in ("available", "solved"):
            if p[key]["pageId"] not in pages:
                errors.append(f"parchment {p['id']}: {key} page {p[key]['pageId']} does not exist")
        for i, st in enumerate(p["stages"], 1):
            if st["answer"] not in st["choices"]:
                errors.append(f"parchment {p['id']} stage {i}: answer not among choices")
            if st.get("codex") and st["codex"] not in entries:
                errors.append(f"parchment {p['id']} stage {i}: codex '{st['codex']}' does not exist")
        if p["crop"] not in art:
            errors.append(f"parchment {p['id']}: crop '{p['crop']}' not in site-assets/art")
    manual = json.loads((CONTENT / "hotspots" / "manual.json").read_text(encoding="utf-8"))
    auto_ids = {h["id"] for h in auto + puzzle_hs + companion_hs}
    for rid in manual.get("remove", []):
        if rid not in auto_ids:
            errors.append(f"hotspots/manual.json: removes unknown hotspot '{rid}'")
    for h in auto + puzzle_hs + companion_hs + manual.get("add", []):
        if h["page"] not in pages:
            errors.append(f"hotspot {h['id']}: page {h['page']} does not exist")
        x0, y0, x1, y1 = h["rect"]
        if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
            errors.append(f"hotspot {h['id']}: bad rect {h['rect']}")
        for t in h["targets"]:
            kind, _, ref = t.partition(":")
            if kind == "codex" and ref not in entries:
                errors.append(f"hotspot {h['id']}: target {t} does not exist")
            elif kind == "puzzle" and ref not in puzzle_ids:
                errors.append(f"hotspot {h['id']}: target {t} does not exist")
            elif kind == "voice" and ref not in voices:
                errors.append(f"hotspot {h['id']}: target {t} does not exist")
            elif kind == "fragment" and ref not in frags:
                errors.append(f"hotspot {h['id']}: target {t} does not exist")
            elif kind not in ("codex", "puzzle", "voice", "place", "fragment"):
                errors.append(f"hotspot {h['id']}: unknown target kind '{kind}'")

    total = len(auto) + len(puzzle_hs) + len(companion_hs) - len(manual.get("remove", [])) + len(manual.get("add", []))
    if errors:
        print(f"{len(errors)} problem(s):")
        for e in errors:
            print("  -", e)
        return 1
    print(f"OK: {len(entries)} codex entries, {len(parchment['puzzles'])} puzzles, {len(voices)} voices, "
          f"{len(rail['nodes'])} rail beats, {len(frags)} fragments, {total} hotspots, all references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
