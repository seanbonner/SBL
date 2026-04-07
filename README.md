# llmbrary

Turn a physical media collection into a portable knowledge base for LLMs.

This repository is a template for building a structured catalog of books, films, and music extracted from photographs of shelves or imported from text lists. The catalog is designed to be loaded into LLM context windows, giving AI assistants awareness of the intellectual background behind a conversation — the books that shaped how you think, the films that informed your visual language, the music that soundtracks your practice.

Fork it, fill it with your own collection, and point an LLM at the generated context files.

## Why

LLMs are general-purpose by default. They don't know what you've read, watched, or listened to, what intellectual traditions matter to you, or what conceptual vocabulary you actually use. Giving a model access to your collection doesn't make it an expert — but it does let it recognize when a project intersects with something on your shelves, trace thematic connections you might not have articulated, and meet you closer to where you actually are.

## Multi-Media Support

The catalog supports three media types, each with shared core fields and type-specific metadata:

| Media Type | Creator Field | Type-Specific Fields |
|---|---|---|
| `book` | `author` | `publisher` |
| `film` | `director` | `cast`, `format` (DVD/Blu-ray/digital) |
| `music` | `artist` | `album`, `label`, `format` (CD/vinyl/digital) |

All entries share: `title`, `media_type`, `year`, `synopsis`, `themes`, `confidence`, `needs_review`, `in_conversation_with`, and `source_image`. The `in_conversation_with` field supports cross-media connections — a film can be in conversation with a book or an album.

If `media_type` is missing from an entry, it defaults to `"book"` for backward compatibility.

## Repository Structure

```
llmbrary/
├── config.example.json       # Template for config.json (gitignored). Owner name, profile, cluster sizing.
├── catalog.json              # Enriched catalog entries (gitignored, personal data)
├── CONTEXT.md                # Full catalog as markdown (~40K tokens, gitignored)
├── CONTEXT_COMPACT.md        # One-line per entry with clusters (~5K tokens, gitignored)
├── CONTEXT_OVERVIEW.md       # Intellectual profile only (~500 tokens, gitignored)
├── schema.json               # JSON Schema for catalog validation
├── photos/
│   ├── inbox/                # Drop new shelf photos here (books, DVDs, CDs)
│   └── processed/            # Photos move here after processing
├── wiki/                     # Theme-based cluster pages (generated, gitignored)
│   ├── INDEX.md              # Table of contents for all cluster pages
│   └── *.md                  # One page per theme cluster, listing its entries
├── scripts/
│   ├── ingest.py             # Scan inbox for new photos, build processing manifest
│   ├── import_text.py        # Import books from a plain text list
│   ├── import_media.py       # Import films or music from a plain text list
│   ├── merge_catalog.py      # Merge new extractions into catalog with deduplication
│   ├── regenerate.py         # Regenerate all context files + wiki from catalog.json
│   ├── generate_wiki.py      # Theme-based wiki page generator
│   └── lint.py               # Catalog quality review and suggestions
├── claude/                   # Claude-specific skill integration
│   └── SKILL.md              # Skill wrapper with tiered loading strategy
└── README.md
```

Personal data (`config.json`, `catalog.json`, `CONTEXT*.md`, `wiki/`, processed photos) is gitignored by default, so you can fork this repo, build your own catalog, and still pull upstream improvements without leaking your library.

## Catalog Format

Each entry in `catalog.json` contains:

| Field | Type | Description |
|---|---|---|
| `title` | string | Title of the work |
| `media_type` | "book"\|"film"\|"music" | Type of media (defaults to "book") |
| `author` | string\|null | Author or editor (books) |
| `director` | string\|null | Director (films) |
| `artist` | string\|null | Artist or band (music) |
| `year` | integer\|null | Publication/release year |
| `synopsis` | string | Description and intellectual context |
| `themes` | string[] | Key themes and subjects |
| `source_image` | string | Reference photograph filename |
| `confidence` | "high"\|"medium"\|"low" | Identification confidence |
| `needs_review` | boolean | Whether entry needs verification |
| `in_conversation_with` | string[] | Related titles in the collection (max 5, cross-media) |
| `cast` | string[] | Cast members (films, optional) |
| `label` | string\|null | Record label (music, optional) |
| `publisher` | string\|null | Publisher (books, optional) |
| `format` | string\|null | Physical/digital format |

The `in_conversation_with` field maps relationships between works — not citations, but thematic, methodological, or historical resonance. These relationships allow traversal of intellectual lineages across the collection and across media types.

The full schema is defined in `schema.json`.

## Wiki Layer

The `wiki/` directory contains a theme-based cluster page per qualifying theme in your catalog. Each page lists the catalog entries that share that theme, with their synopses and `in_conversation_with` cross-references.

Clusters are derived directly from the `themes` arrays on your catalog entries — not from hardcoded keyword lists — so the wiki reflects the actual shape of *your* collection without needing code edits. A theme becomes a cluster once it has at least `cluster_min_size` entries (configurable in `config.json`, default 2). Each entry is assigned to its most specific qualifying theme, so narrower clusters aren't swallowed by broader ones.

Pages are regenerated from `catalog.json` alongside the context tiers. They're deliberately honest rather than essayistic: the generator organizes what's in the catalog, it doesn't invent prose. If you want longer-form synthesis for a particular theme, maintain that content outside the pipeline — the generated pages overwrite on each run.

See `wiki/INDEX.md` for the generated table of contents.

## Catalog Quality

Run `scripts/lint.py` to review the catalog for issues: isolated entries with no relationships, broken cross-references, potential duplicates (fuzzy title matching), missing fields, and theme clusters that might warrant new wiki pages.

```bash
python3 scripts/lint.py
```

## Context Tiers

The catalog is rendered at three levels of detail, designed for different token budgets and use cases.

| Tier | File | Size | Tokens | Contains |
|---|---|---|---|---|
| Overview | `CONTEXT_OVERVIEW.md` | ~2-3 KB | ~500 | Intellectual profile, top clusters, cross-cutting threads |
| Compact | `CONTEXT_COMPACT.md` | ~5-20 KB | ~5K | One-line per entry (title/creator/year) organized by cluster |
| Full | `CONTEXT.md` | ~20-250 KB | ~5-40K | Complete synopses, themes, and relationship annotations |

Sizes scale with catalog size. Non-book entries are tagged with `[film]` or `[music]` in the context files for easy identification. Within each cluster, entries are organized by media type (books first, then films, then music).

**Choosing a tier:**

- **Small context window** (8K-32K tokens): Use Overview. It gives the model the vocabulary to recognize thematic overlaps without consuming significant budget.
- **Medium context window** (32K-128K tokens): Use Compact. Every entry is listed with enough structure to identify relevance.
- **Large context window** (128K+ tokens): Can use Full, or load the Overview as baseline and pull specific sections from Full as needed.
- **Structured/programmatic access**: Use `catalog.json` directly for filtering, graph traversal, and tool-building.

The Claude skill wrapper in `claude/SKILL.md` implements a selective loading strategy: always load Overview, escalate to Compact or Full sections based on task requirements, and use catalog.json for structured queries.

## Using with LLMs

### Direct context injection (any LLM)

Pick the appropriate tier for your context budget and paste it into the system prompt or upload as a file. The Overview (~500 tokens) is small enough to always include as baseline context; the Compact version fits comfortably in any modern context window; the Full version is best for models with 128K+ token windows.

### Structured queries

Load `catalog.json` for programmatic access — filtering by theme, media type, creator, year, or traversing the `in_conversation_with` relationship graph. Useful for building tools on top of the catalog or for selective context loading.

### Claude skill integration

The `claude/SKILL.md` file is a skill wrapper for Claude Code and Cowork that implements smart tiered loading. It instructs Claude on when to use each tier, how to walk the relationship graph, and how to surface relevant works during projects.

To use it, add the `claude/` directory to your Claude Code or Cowork skills path.

## Configuration

Copy `config.example.json` to `config.json` and edit the fields to personalize your library:

```bash
cp config.example.json config.json
# edit config.json to set owner_name, collection_name, and profile text
```

`config.json` is gitignored, so your personal profile text stays local even when you push code changes upstream. If no `config.json` exists the pipeline falls back to `config.example.json`, and then to built-in defaults — so the scripts run out of the box on a fresh clone.

Key fields:

| Field | Description |
|---|---|
| `owner_name` | Your name, used internally and in headers |
| `collection_name` | How the collection is titled in generated files ("Your Name's Collection") |
| `intellectual_profile` | Paragraph describing the collection — the main body of `CONTEXT_OVERVIEW.md` |
| `profile_closer` | Optional second paragraph for the overview |
| `cross_cutting_threads` | Closing sentence about what threads run across the collection |
| `cluster_min_size` | Minimum entries a theme needs to become its own cluster (default 2) |
| `max_overview_clusters` | How many clusters to list in `CONTEXT_OVERVIEW.md` (default 15) |

## Extraction Methodology

A suggested pipeline for building the catalog:

1. **Photography** — Photographs of shelves capturing spine text at readable resolution (book spines, DVD/Blu-ray cases, CD jewel cases, vinyl sleeves)
2. **Vision extraction** — LLM vision models identify titles and creators from spine images. When the physical format is identifiable (DVD case vs. book spine vs. CD jewel case), entries get tagged with the appropriate `media_type`.
3. **Enrichment** — Each identified title gets a year, synopsis, themes, and confidence scoring
4. **Relationship mapping** — `in_conversation_with` links are generated by analyzing thematic overlap across the collection (cross-media connections supported)
5. **Context generation** — `scripts/regenerate.py` renders the structured catalog into the three markdown context tiers and the `wiki/` cluster pages

Entries with `confidence: "medium"` or `needs_review: true` may contain inaccuracies and benefit from manual review.

## Workflow

Adding new items follows a three-stage pipeline: ingest photos, extract and merge titles, then regenerate the context file.

### 1. Drop photos

Place new shelf photographs in `photos/inbox/`. Any `.jpg`, `.jpeg`, `.png`, or `.heic` files will be picked up. Photos can contain book spines, DVD/Blu-ray cases, CD jewel cases, or vinyl sleeves.

### 2. Run ingestion

```bash
# Preview what's new
python3 scripts/ingest.py --dry-run

# Log new images and produce inbox_manifest.json
python3 scripts/ingest.py

# Hint that these photos are DVD shelves (helps downstream extraction)
python3 scripts/ingest.py --media-hint film

# After extraction, move processed images out of inbox
python3 scripts/ingest.py --move
```

The script writes `processing_log.json` so images are never processed twice. The `--media-hint` flag records what kind of physical media the photos contain, which helps the vision extraction step tag entries correctly.

### Text import — books

If you have a list of books as plain text, you can skip the photo pipeline entirely:

```bash
# Preview what will be parsed
python3 scripts/import_text.py booklist.txt --dry-run

# Import — writes new_extractions.json
python3 scripts/import_text.py booklist.txt

# Force a specific format instead of auto-detecting
python3 scripts/import_text.py booklist.txt --format dash

# Adjust dedup sensitivity
python3 scripts/import_text.py booklist.txt --threshold 0.80
```

The script auto-detects line format from the following:

| Format | Example |
|---|---|
| Dash | `Title - Author` or `Title — Author` |
| By | `Title by Author` |
| Comma | `Title, Author` |
| Parenthetical | `Title (Author)` |
| Colon | `Author: Title` |
| Tab-separated | `Title\tAuthor` |
| CSV | `"Title","Author","Year"` |
| Title only | `Title` |

### Text import — films and music

Use `import_media.py` for films and music:

```bash
# Import films
python3 scripts/import_media.py --type film films.txt
python3 scripts/import_media.py --type film films.txt --dry-run
python3 scripts/import_media.py --type film films.txt --format dash

# Import music
python3 scripts/import_media.py --type music albums.txt
python3 scripts/import_media.py --type music albums.txt --format by
```

Film formats:

| Format | Example |
|---|---|
| Dash | `Title (Year) - Director` or `Title - Director` |
| Colon | `Director: Title (Year)` |
| Title-year | `Title (Year)` or just `Title` |

Music formats:

| Format | Example |
|---|---|
| Dash | `Artist - Album (Year)` or `Artist - Album` |
| By | `Album by Artist` |
| CSV | `"Artist","Album","Year"` |
| Title only | `Album` or `Title` |

Deduplication is scoped by media_type — a book titled "Drive" won't conflict with a film titled "Drive". Output goes to `new_extractions.json` with the appropriate `media_type` set.

### Browser-based import

You can also import items directly in the browser using the **Text Import** tab in `review.html`. Select the media type (Book/Film/Music), paste a list, preview the parsed results, and add them to the catalog in one step.

### 3. Extract titles

Use your preferred vision extraction method (LLM vision, manual, etc.) to produce a `new_extractions.json` file — an array of objects following `schema.json`. At minimum each entry needs a `title`; include `media_type` to indicate the type. Missing enrichment fields will be flagged for review.

### 4. Merge into catalog

```bash
# Preview the merge
python3 scripts/merge_catalog.py new_extractions.json --dry-run

# Merge for real
python3 scripts/merge_catalog.py new_extractions.json
```

The merge script deduplicates by fuzzy title matching within the same media_type (configurable threshold via `--threshold`) and flags entries that need enrichment with `needs_review: true`.

### 5. Regenerate context files and wiki

```bash
# Regenerate everything (context tiers + wiki pages)
python3 scripts/regenerate.py

# Regenerate wiki pages only
python3 scripts/regenerate.py --wiki

# Regenerate context tiers only
python3 scripts/regenerate.py --context
```

This rebuilds all three context tiers (`CONTEXT.md`, `CONTEXT_COMPACT.md`, `CONTEXT_OVERVIEW.md`) and the `wiki/` directory from the current state of `catalog.json`, preserving thematic groupings and organizing entries by media type within each group. It prints file sizes for verification.

## Contributing

To add items manually, append entries to `catalog.json` following the schema in `schema.json`. Then regenerate the context file:

```bash
python3 scripts/regenerate.py
```

When adding entries:

- Set `media_type` to `"book"`, `"film"`, or `"music"`
- Use the appropriate creator field (`author`, `director`, or `artist`)
- Set `confidence` to `"high"` for manually verified entries
- Include `in_conversation_with` references to existing titles where thematic connections exist (max 5, cross-media allowed)
- Write synopses that capture intellectual context, not just plot summary
- Choose themes that reflect how the work functions in a broader intellectual landscape

## License

The catalog data (synopses, themes, relationships) is original work. Titles and creator names are factual information. Source photographs are not included in the distributed catalog.
