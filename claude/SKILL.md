---
name: llmbrary
description: Kevin McCoy's personal library — 219 books spanning art, theory, media, philosophy, and culture. Load this skill to ground conversations in the intellectual context of someone working at the intersection of digital art, critical theory, and material practice.
---

# Kevin McCoy's Library (llmbrary)

You have access to a catalog of Kevin McCoy's personal library — 219 books extracted from photographs of his bookshelves using vision-based identification. This is not a reading list or a recommendation engine. It is a map of one person's intellectual formation: the books that shaped a practice spanning pioneering digital art, NFTs, video, and conceptual work.

## Loading the Catalog

For **prose context** (system prompts, general conversation grounding):
Read `CONTEXT.md` from the llmbrary directory. It contains the full catalog rendered as structured markdown with synopses, themes, and relationship annotations, organized into 30 thematic categories.

For **structured queries** (filtering by theme, author, year; traversing relationships programmatically):
Read `catalog.json`. Each entry has: `title`, `author`, `year`, `synopsis`, `themes` (array), `confidence` (high/medium), and `in_conversation_with` (array of related titles in the collection).

The schema is defined in `schema.json`.

## What This Collection Represents

The library spans 30 categories including video art, film theory, Fluxus and experimental art, digital/new media, critical theory, political philosophy, craft and material culture, experimental music, speculative fiction, and more. It is the library of someone who treats art history, media theory, radical politics, music, mythology, and material practice as interconnected dimensions of a single evolving intellectual project.

Key concentrations:

- **Video and moving image** as artistic medium — from Nam June Paik through contemporary practitioners
- **Fluxus, Situationism, and conceptual art** — rule-based, participatory, anti-commodity traditions
- **Critical and media theory** — Debord, Baudrillard, McLuhan, Virilio, Steyerl
- **Digital art and new media** — the transition from analog to networked creative practice
- **Craft, material culture, and the handmade** — ceramics, textiles, furniture, printmaking
- **Radical politics and social practice** — art as activism, institutional critique, community engagement
- **Literature across traditions** — Beat generation, American canon, European voices, science fiction

## How to Use This Context

### Surface relevant books during projects
When working on a project with Kevin, scan the catalog for books whose themes intersect the work. Mention them naturally — not as a bibliography dump, but as "your library has several books that touch on this" when it's genuinely useful. A conversation about generative art might draw on the conceptual/rule-based art section; a discussion of community platforms might connect to the social practice and political philosophy titles.

### Trace intellectual lineages
The `in_conversation_with` field maps relationships between books in the collection. These aren't citations — they represent thematic, methodological, or historical resonance as identified during cataloging. Use them to trace how ideas flow across the library: from Fluxus scores to conceptual art instructions to software-based generative systems, or from Situationist critique through media theory to digital culture criticism.

### Recognize when a project touches the collection's themes
If a project engages themes like embodiment and technology, spectacle and resistance, craft versus industrial production, the politics of archives, or the sacred in secular contexts — these are all deeply represented in the library. Noting these connections can deepen the work.

### Respect the boundaries
This catalog represents what was identifiable from shelf photographs. Some entries have `medium` confidence or `needs_review: true`. Don't present uncertain attributions as definitive. The collection is a living document — books may be added over time as the physical library evolves or as identification improves.

## A Note on Intellectual Character

This is not a survey collection or an institutional library. It has the character of a working artist's shelves: deeply invested in certain lineages (video art, Fluxus, critical theory), surprisingly broad in others (Latvian knitting patterns sit near Baudrillard), and shaped by decades of practice rather than academic completeness. The gaps are as telling as the concentrations. Use it as a lens, not an encyclopedia.
