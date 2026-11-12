---
name: draft-voicebot-prompt
description: >-
  Draft client voicebot (or phone) system prompts for Promp-Agent-: one final
  .md or .txt file, embedded knowledgebase, no tables, ## / # / - structure,
  and a [Critical] persona opening line. Use when the user asks for a voicebot
  prompt, Fixit prompt, call script, or property advisor persona.
---

# Draft voicebot prompt

Use this skill whenever you create or revise a **phone / voicebot** system prompt in this repository (not the compiled Modon outputs from `prompt-agent compile`, unless the user asks to change that pipeline).

## Deliverable — one file only

- Ship **exactly one** final prompt file per client or project.
- Path: `prompts/<client>-<project>-voice.md` (preferred) or `prompts/<client>-<project>-voice.txt` if the platform requires plain text only.
- **Do not** split knowledge into a separate `*-knowledge.md` and `*-voice.md` for the client deliverable. Merge the full knowledge base into the same file under a dedicated section (for example `## Project knowledgebase`).
- Optional `examples/<id>.brief.yaml` may point to that single file via `knowledge.prompt_file` only — no parallel static KB path for end users.

## Formatting (mandatory)

- **No markdown tables.** Never use `|` table syntax. Facts belong in explanatory bullet pointers.
- **Headings:** `##` for main sections (persona, call flow, knowledgebase, hard rules, etc.).
- **Subheadings:** `#` for subsections inside a `##` block (for example unit types, amenities groups).
- **Pointers:** `-` for every list item; write full explanatory lines, not telegraphic labels.
- No `===` banner lines in the final file unless the user explicitly wants Fixit-style separators.
- Prefer readable prose inside bullets where the reference sample used paragraphs.

## First line (mandatory)

The **first sentence of the file** must be a single `[Critical]` block (spacing as below is fine):

`[Critical] You are {AgentName}. You are {persona nationality/identity} and you speak English in a {accent description}. {Optional: default language, switch rules, and that every project fact comes from the knowledge in this prompt — never invented, never announced as a lookup.}`

Examples:

- Indian advisor: `[Critical] You are Aman. You are Indian, native Punjabi, and you speak English in a natural Indian accent. You speak English by default, and you switch to any language the caller uses. Every project-specific fact you state comes from the knowledge in this prompt — you never invent one, and you never say you are fetching it.`
- British advisor: `[Critical] You are Alex. You are British and you speak in a British accent. ...`

Tailor nationality, accent, and language rules to the brief. The `[Critical]` line is always line one — no title or front matter above it.

## Content shape (follow the reference sample)

Mirror the depth of a senior call prompt (persona, voice, opening line, first turn, number source, disinterest, objective, knowledgebase, language, turn length, human behaviour, hard rules, close). Inherit craft from `nuances/voicebot.yaml` unless the brief overrides.

Include:

- Hardcoded opening line (platform-fired; agent does not repeat it)
- Knowledge section with all brochure-verified facts in `-` bullets (sizes, RERA, location, amenities, defer list)
- Explicit **defer list** for prices, possession, availability, legal — never guess
- Turn length and banned phrases as in the reference when the client expects them

## Workflow

1. Read the user brief, sample prompt, and any PDFs/brochures.
2. Build a structured internal outline (units, amenities, contacts) — **without tables**.
3. Write **one** `prompts/...-voice.md` file: `[Critical]` first, then `##` sections, `#` subsections, `-` pointers.
4. Update `examples/*-voice.brief.yaml` to reference only that file if a brief exists.
5. Remove or avoid committing extra split deliverables (`*-knowledge.md`, duplicate `*-fixit.txt`) unless the user explicitly wants both; default is **one** final file.

## Quality checks before finishing

- First line is `[Critical]` with persona and accent.
- Zero tables in the deliverable.
- Exactly one client-facing prompt file.
- Knowledge and behaviour live in the same document.
- Headings use `##` and `#` as specified; lists use `-` only.
