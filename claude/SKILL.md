---
name: llmbrary
description: Kevin McCoy's personal collection — 348 books and 19 music recordings (367 works total) spanning art, theory, media, philosophy, and culture. Load this skill to ground conversations in the intellectual context of someone working at the intersection of digital art, critical theory, and material practice.
---

# Kevin McCoy's Library (llmbrary)

You have access to a catalog of Kevin McCoy's personal collection — 348 books and 19 music recordings (367 works total) extracted from photographs and text imports. This is not a reading list or a recommendation engine. It is a map of one person's intellectual formation: the books, albums, and recordings that shaped a practice spanning pioneering digital art, NFTs, video, and conceptual work.

## Context Tiers — Smart Loading Strategy

The library is rendered at three levels of detail. **Always start with the overview**, then escalate as needed.

### Tier 1: CONTEXT_OVERVIEW.md (~500 tokens) — ALWAYS LOAD

Read this file on every skill invocation. It contains the intellectual fingerprint of the collection: what traditions it draws on, where the center of gravity lies, and which thematic clusters exist. This costs almost nothing and gives you the vocabulary to recognize when a project intersects the library.

### Tier 2: CONTEXT_COMPACT.md (~5K tokens) — Load for thematic work

Load this when working on a project with clear thematic overlap with the library. It lists every entry by title, creator, year, organized into 30 thematic groupings. Non-book entries are tagged with [film] or [music]. Use it to:
- Identify specific titles relevant to a project
- See what's in a thematic cluster at a glance
- Find books by author or approximate title
- Get a sense of the depth of coverage in a given area

### Tier 3: CONTEXT.md (~40K tokens) — Load selectively

The full rendering with complete synopses, themes, and `in_conversation_with` relationship annotations. **Do not load this entire file unless the context window is large enough and the task genuinely benefits from full synopses.** Instead, load it selectively:
- Read just the section(s) relevant to the current project (search for the grouping header)
- Pull full entries for a specific set of books identified from the compact tier
- Use when you need the synopsis text to characterize a book's intellectual contribution

### Tier 4: catalog.json (structured data) — For programmatic queries

Use `catalog.json` directly when you need to:
- Filter by theme, author, year, or confidence level programmatically
- Traverse the `in_conversation_with` relationship graph
- Answer structured queries like "what books do I have about X" or "which books connect to Y"
- Build lists, counts, or cross-references

### Tier 5: wiki/ pages — Synthesized thematic context

The `wiki/` directory contains ~25 essay-length pages that synthesize across multiple books to map intellectual threads. Each page traces a theme, movement, or conceptual lineage through the collection. **Use wiki pages when you need the intellectual landscape of a topic rather than individual entries.** Start with `wiki/INDEX.md` to find relevant pages.

Examples of wiki pages:
- `wiki/video-art-and-media-theory.md` — traces video art from Paik through Viola to database cinema
- `wiki/situationism-spectacle-and-everyday-life.md` — Debord through Fisher to contemporary spectacle critique
- `wiki/digital-art-and-blockchain-culture.md` — net art through creative coding to NFTs and crypto art
- `wiki/vernacular-cultural-forms.md` — shape-note singing, Haida literature, craft traditions

Wiki pages are especially valuable for:
- Grounding a project in the collection's relevant intellectual context
- Understanding how different parts of the collection relate to each other
- Identifying unexpected connections between holdings
- Providing thematic context to another LLM or collaborator

## Decision Framework

| Situation | What to load |
|---|---|
| Skill just invoked, no specific task yet | Overview only |
| Project with thematic overlap (e.g. "working on a video piece") | Overview + relevant wiki page(s) |
| Need to discuss specific books in depth | Overview + relevant section of Full |
| "What books do I have about X?" | catalog.json (programmatic filter) |
| Tracing connections from a seed book | catalog.json (graph traversal via `in_conversation_with`) |
| Understanding the intellectual landscape of a topic | wiki/ pages (start with INDEX.md) |
| System prompt / context injection for another LLM | Overview or Compact depending on budget |

## The Relationship Graph

The `in_conversation_with` field in catalog.json maps thematic resonance between books — not citations, but intellectual adjacency. Use it to walk connections outward from a seed set:

1. Start with 1-3 books relevant to the current context
2. Follow their `in_conversation_with` links to find adjacent titles
3. Check those titles' connections for a second hop if needed
4. The resulting cluster often reveals unexpected intellectual threads

This is especially useful when Kevin mentions a book or topic — you can fan out from that seed to surface related titles he might not have thought to connect.

## How to Use This Context

### Surface relevant books during projects
When working on a project with Kevin, scan for books whose themes intersect the work. Mention them naturally — not as a bibliography dump, but as "your library has several books that touch on this" when it's genuinely useful.

### Trace intellectual lineages
Use the relationship graph to trace how ideas flow across the library: from Fluxus scores to conceptual art instructions to software-based generative systems, or from Situationist critique through media theory to digital culture criticism.

### Recognize when a project touches the collection's themes
If a project engages themes like embodiment and technology, spectacle and resistance, craft versus industrial production, the politics of archives, or the sacred in secular contexts — these are all deeply represented in the library. Noting these connections can deepen the work.

### Respect the boundaries
Some entries have `confidence: "medium"` or `needs_review: true`. Don't present uncertain attributions as definitive. The collection is a living document.
