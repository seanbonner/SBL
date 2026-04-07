---
name: llmbrary
description: A personal media catalog (books, films, music) with synopses, themes, and cross-references. Load this skill to ground conversations in the intellectual context of the catalog's owner — the works that shaped how they think and work.
---

# llmbrary

You have access to a personal catalog of books, films, and music. This is not a reading list or a recommendation engine. It is a map of one person's intellectual formation: the works that shaped their practice and thinking.

The catalog's owner and the shape of the collection are described in `CONTEXT_OVERVIEW.md` (always load this first). Use it to ground your work in what the person has actually read, watched, and listened to, rather than generic knowledge.

## Context Tiers — Smart Loading Strategy

The library is rendered at three levels of detail. **Always start with the overview**, then escalate as needed.

### Tier 1: CONTEXT_OVERVIEW.md (~500 tokens) — ALWAYS LOAD

Read this file on every skill invocation. It contains a short intellectual profile of the collection's owner and a list of the major theme clusters. This costs almost nothing and gives you the vocabulary to recognize when a project intersects the library.

### Tier 2: CONTEXT_COMPACT.md (~5K tokens) — Load for thematic work

Load this when working on a project with clear thematic overlap with the library. It lists every entry by title, creator, and year, organized into theme clusters. Non-book entries are tagged with `[film]` or `[music]`. Use it to:
- Identify specific titles relevant to a project
- See what's in a thematic cluster at a glance
- Find works by author/director/artist or approximate title
- Get a sense of the depth of coverage in a given area

### Tier 3: CONTEXT.md (~5–40K tokens depending on catalog size) — Load selectively

The full rendering with complete synopses, themes, and `in_conversation_with` relationship annotations. **Do not load this entire file unless the context window is large enough and the task genuinely benefits from full synopses.** Instead, load it selectively:
- Read just the section(s) relevant to the current project (search for a cluster header)
- Pull full entries for a specific set of titles identified from the compact tier
- Use when you need the synopsis text to characterize a work's intellectual contribution

### Tier 4: catalog.json (structured data) — For programmatic queries

Use `catalog.json` directly when you need to:
- Filter by theme, creator, year, or confidence level programmatically
- Traverse the `in_conversation_with` relationship graph
- Answer structured queries like "what works do I have about X" or "which works connect to Y"
- Build lists, counts, or cross-references

### Tier 5: wiki/ pages — Theme cluster pages

The `wiki/` directory contains one page per theme cluster in the catalog. Each page lists the entries that share that theme, with their synopses and cross-references. **Use wiki pages when you need to see all works in a particular theme at once.** Start with `wiki/INDEX.md` for the table of contents.

Wiki pages are especially valuable for:
- Grounding a project in the collection's relevant thematic context
- Seeing every work tagged with a given theme at a glance
- Identifying cross-references between works in the same cluster

## Decision Framework

| Situation | What to load |
|---|---|
| Skill just invoked, no specific task yet | Overview only |
| Project with thematic overlap | Overview + relevant wiki/ page(s) |
| Need to discuss specific works in depth | Overview + relevant section of Full |
| "What works do I have about X?" | catalog.json (programmatic filter) |
| Tracing connections from a seed work | catalog.json (graph traversal via `in_conversation_with`) |
| Understanding the landscape of a theme cluster | wiki/ pages (start with INDEX.md) |
| System prompt / context injection for another LLM | Overview or Compact depending on budget |

## The Relationship Graph

The `in_conversation_with` field in catalog.json maps thematic resonance between works — not citations, but intellectual adjacency. Use it to walk connections outward from a seed set:

1. Start with 1–3 works relevant to the current context
2. Follow their `in_conversation_with` links to find adjacent titles
3. Check those titles' connections for a second hop if needed
4. The resulting cluster often reveals unexpected intellectual threads

This is especially useful when the user mentions a work or topic — you can fan out from that seed to surface related titles they might not have thought to connect.

## How to Use This Context

### Surface relevant works during projects
When working on a project, scan for works whose themes intersect the task. Mention them naturally — not as a bibliography dump, but as "your library has several works that touch on this" when it's genuinely useful.

### Trace connections
Use the relationship graph to trace how ideas flow across the library. A work can be in conversation with another regardless of media type (a film with a book, an album with a film).

### Recognize when a project touches the collection's themes
The collection's `CONTEXT_OVERVIEW.md` lists the owner's major theme clusters. If a project engages one of those themes, the collection probably has something to say about it.

### Respect the boundaries
Some entries have `confidence: "medium"` or `needs_review: true`. Don't present uncertain attributions as definitive. The collection is a living document.
