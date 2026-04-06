#!/usr/bin/env python3
"""
regenerate.py — Regenerate CONTEXT.md from catalog.json.

Usage:
    python3 scripts/regenerate.py

Run this after any changes to catalog.json (adding books, editing entries,
merging new extractions) to keep CONTEXT.md in sync.

This script consolidates the logic from the original generate_context.py
and is the canonical way to regenerate the context file.
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = REPO_ROOT / "catalog.json"
CONTEXT_PATH = REPO_ROOT / "CONTEXT.md"

# Thematic groupings — each entry is assigned to the best-matching group
# based on keyword scoring across title, author, themes, and synopsis.
GROUPINGS = [
    {
        "name": "Video Art & Moving Image",
        "keywords": ["video", "moving image", "Paik", "Viola", "Gary Hill", "Joan Jonas",
                      "Videofreex", "Vostell", "Broken Screen", "Echo"],
    },
    {
        "name": "Film Theory & Cinema",
        "keywords": ["film", "cinema", "Godard", "Frampton", "Marker", "Lynch",
                      "La Jetée", "Film Art", "Circles of Confusion"],
    },
    {
        "name": "Performance Art & Body",
        "keywords": ["performance", "Acconci", "Yoko Ono", "body", "Artaud", "United States"],
    },
    {
        "name": "Fluxus, Neo-Dada & Experimental Art",
        "keywords": ["Fluxus", "Beuys", "Rauschenberg", "Dieter Roth",
                      "Niki de Saint Phalle", "Maciunas", "Neo-Dada"],
    },
    {
        "name": "Conceptual & Rule-Based Art",
        "keywords": ["conceptual", "rule-based", "Sophie Calle", "Glenn Ligon",
                      "David Diao", "Logical Conclusions", "Mechanism of Meaning"],
    },
    {
        "name": "Sculpture, Installation & Space",
        "keywords": ["sculpture", "installation", "Eva Hesse", "Nancy Graves", "Ruth Asawa",
                      "Boltanski", "Maya Lin", "Matta-Clark", "Richard Long", "Drawing",
                      "Architecture"],
    },
    {
        "name": "Painting, Abstraction & Color",
        "keywords": ["painting", "abstraction", "Jack Whitten", "Ninth Street Women",
                      "Terry Winters", "Richter", "Penck", "Bulatov"],
    },
    {
        "name": "Photography & Image",
        "keywords": ["photography", "photo", "Naked City", "Dirty Windows",
                      "Hidden Mother", "Women Photographers"],
    },
    {
        "name": "Digital Art, New Media & NFTs",
        "keywords": ["digital", "new media", "NFT", "Processing", "Rhizome",
                      "Collective Intelligence", "Surfing with Satoshi"],
    },
    {
        "name": "Typography, Design & Visual Language",
        "keywords": ["typography", "design", "typographic", "Tibor Kalman",
                      "Graphic Design", "2nd Sight", "Elements of Typographic"],
    },
    {
        "name": "Architecture, Urbanism & Built Environment",
        "keywords": ["architecture", "urban", "Rural Studio", "Off the Grid",
                      "building", "space", "dwelling"],
    },
    {
        "name": "Craft, Material Culture & Objects",
        "keywords": ["craft", "material", "Anni Albers", "Knit Like", "Art Deco",
                      "ceramic", "weaving"],
    },
    {
        "name": "Music: Experimental, Jazz & Sound Studies",
        "keywords": ["music", "jazz", "sound", "Coltrane", "Arcana", "Soundscape",
                      "Musician", "Ken Burns", "Voice in the Headphones", "Soloists"],
    },
    {
        "name": "Sacred Singing & Oral Tradition",
        "keywords": ["Sacred Harp", "shape-note", "Shenandoah", "Haida",
                      "Bringhurst", "oral"],
    },
    {
        "name": "Situationism, Spectacle & Everyday Life",
        "keywords": ["Situationism", "Debord", "SI", "Everyday Life",
                      "All That Is Solid", "spectacle", "Egress"],
    },
    {
        "name": "Critical Theory & Philosophy",
        "keywords": ["Benjamin", "Foucault", "Deleuze", "Wittgenstein", "Danto",
                      "Hickey", "Krauss", "Scarry", "Nagel", "DeLanda", "Rancière",
                      "theory", "philosophy"],
    },
    {
        "name": "Media Theory & Digital Culture",
        "keywords": ["media", "electronic", "digital", "Protocol", "Social Media",
                      "Body Invaders", "Flusser", "Commodity Aesthetics"],
    },
    {
        "name": "Political Philosophy & Radical Thought",
        "keywords": ["political", "Caliban", "Witch", "Art of Not Being Governed",
                      "Multitude", "Crypto", "Achieving Our Country", "Freedom",
                      "Detroit", "City of Quartz"],
    },
    {
        "name": "Feminism, Gender & Identity",
        "keywords": ["feminist", "feminism", "gender", "Room of One's Own",
                      "Xenofeminism", "Species Meet", "Woman Destroyed", "Women"],
    },
    {
        "name": "Literature: Beat Generation & Experimental Writing",
        "keywords": ["Burroughs", "Gysin", "Beat", "Letters"],
    },
    {
        "name": "Literature: American Canon",
        "keywords": ["Twain", "Saunders", "Carver", "Faulkner", "Lowell", "Sexton",
                      "Dickinson", "Bowles", "Delights", "Century of Fiction"],
    },
    {
        "name": "Literature: European & World Voices",
        "keywords": ["Woolf", "Kundera", "Brontë", "Celan", "Rilke", "Pavese",
                      "Coetzee", "Kazantzakis", "Erpenbeck"],
    },
    {
        "name": "Science Fiction & Speculative Imagination",
        "keywords": ["Ubik", "Software", "Lovecraft", "St. Clair", "Ministry for the Future",
                      "Ballard", "speculative", "fiction"],
    },
    {
        "name": "Drama, Theater & Narrative",
        "keywords": ["drama", "theater", "Macbeth", "Good Woman", "Setzuan",
                      "Idea of a Theater"],
    },
    {
        "name": "Myth, Religion & Spirituality",
        "keywords": ["myth", "religion", "Hero", "Thousand Faces", "Norse", "Saga",
                      "Temptation", "Augustine", "Meditation", "spiritual"],
    },
    {
        "name": "Psychology & Mind",
        "keywords": ["psychology", "Interpretation of Dreams", "dream", "unconscious"],
    },
    {
        "name": "Art World, Institutions & Discourse",
        "keywords": ["Best Art", "I Like Your Work", "Art School", "Art Spirit",
                      "Inside the Studio", "Biennial", "Museum", "Gallery"],
    },
    {
        "name": "Environmentalism, Nature & Land",
        "keywords": ["Wilderness", "American Mind", "Against the Machine", "This Land",
                      "Low Tech", "environment", "nature", "land"],
    },
    {
        "name": "Comics, Graphic Narrative & Visual Storytelling",
        "keywords": ["comics", "graphic", "Walking Dead", "Nat Turner", "narrative"],
    },
    {
        "name": "Miscellaneous & Reference",
        "keywords": ["self-help", "astrology", "health", "cooking", "industrial",
                      "counterculture", "Blueprint", "Sing Backwards"],
    },
]

INTRO = (
    "This collection spans the artistic, theoretical, and cultural territories that "
    "have shaped contemporary creative practice at the intersection of digital culture, "
    "visual art, and critical thought. Kevin McCoy, known as a pioneering digital artist "
    "and co-creator of the first NFT, has built a deeply curated library that moves "
    "fluidly across video art and cinema, performance and embodiment, theoretical "
    "philosophy and experimental literature, craft traditions and digital media. The "
    "library maps a landscape where Fluxus gestures meet algorithmic thinking, where "
    "Situationist critique encounters net culture, where the hand-made and the digital, "
    "the sacred and the profane, coexist in productive tension. It is a library that "
    "treats art history, media theory, radical politics, music, mythology, and material "
    "practice as interconnected dimensions of a single, evolving intellectual project."
)


def load_catalog() -> list[dict]:
    with open(CATALOG_PATH, "r") as f:
        return json.load(f)


def categorize(entry: dict) -> int:
    """Score entry against each grouping, return index of best match."""
    title = entry.get("title", "").lower()
    author = (entry.get("author") or "").lower()
    themes = [t.lower() for t in entry.get("themes", [])]
    synopsis = entry.get("synopsis", "").lower()
    combined = f"{title} {author} {' '.join(themes)} {synopsis}"

    best_score, best_idx = -1, len(GROUPINGS) - 1  # default to Misc

    for idx, group in enumerate(GROUPINGS):
        score = 0
        for kw in group["keywords"]:
            kw_lower = kw.lower()
            if kw_lower in title:
                score += 10
            elif kw_lower in author or kw_lower in themes:
                score += 8
            elif kw_lower in combined:
                score += 3
        if score > best_score:
            best_score = score
            best_idx = idx

    return best_idx


def format_entry(entry: dict, all_titles: set) -> list[str]:
    """Format a single catalog entry as markdown lines."""
    lines = []
    title = entry.get("title", "").strip()
    author = (entry.get("author") or "").strip()
    year = entry.get("year")
    synopsis = entry.get("synopsis", "").strip()
    themes = entry.get("themes", [])
    connections = entry.get("in_conversation_with", [])

    # Header
    parts = [f"**{title}**"]
    if author:
        parts[0] += f" — {author}"
    if year:
        parts[0] += f" ({year})"
    lines.append(parts[0])

    if synopsis:
        lines.append(synopsis)
    if themes:
        lines.append(f"**Themes:** {', '.join(themes)}")

    valid_conns = [c for c in connections if c in all_titles]
    if valid_conns:
        lines.append(f"**In conversation with:** {', '.join(valid_conns)}")

    lines.append("")
    return lines


def generate():
    catalog = load_catalog()
    all_titles = {e["title"] for e in catalog}

    # Categorize
    buckets: dict[int, list[dict]] = {i: [] for i in range(len(GROUPINGS))}
    for entry in catalog:
        buckets[categorize(entry)].append(entry)

    # Build markdown
    md = [
        "# Kevin McCoy's Library — Intellectual Context",
        "",
        INTRO,
        "",
        "## Catalog",
        "",
    ]

    entry_count = 0
    active_groups = 0

    for idx, group in enumerate(GROUPINGS):
        entries = sorted(buckets[idx], key=lambda e: e.get("title", "").lower())
        if not entries:
            continue
        active_groups += 1
        md.append(f"### {group['name']}")
        md.append("")
        for entry in entries:
            md.extend(format_entry(entry, all_titles))
            entry_count += 1

    # Write
    CONTEXT_PATH.write_text("\n".join(md))

    print(f"✓ Generated CONTEXT.md: {entry_count} entries across {active_groups} groupings")
    print(f"  Output: {CONTEXT_PATH}")
    return entry_count


if __name__ == "__main__":
    count = generate()
    catalog = load_catalog()
    expected = len(catalog)
    if count == expected:
        print(f"  Verification passed: all {expected} entries included")
    else:
        print(f"  Warning: expected {expected} entries, got {count}", file=sys.stderr)
        sys.exit(1)
