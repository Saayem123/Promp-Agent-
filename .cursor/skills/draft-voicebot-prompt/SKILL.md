---
name: draft-voicebot-prompt
description: >-
  Draft client voicebot (or phone) system prompts for Promp-Agent-: one final
  .md or .txt file, embedded knowledgebase, no tables, ## / # / - structure,
  [Critical] persona line, platform opening out-of-prompt, and staged USP flow.
  Use when the user asks for a voicebot prompt, Fixit prompt, call script, or
  property advisor persona.
---

# Draft voicebot prompt

Use this skill whenever you create or revise a **phone / voicebot** system prompt in this repository (not the compiled Modon outputs from `prompt-agent compile`, unless the user asks to change that pipeline).

## Deliverable — one file per channel (outbound and inbound)

- When the client uses **both** dialer and helpline, ship **two** final files with the **same knowledgebase body** and **different call-type sections**:
  - `prompts/<client>-<project>-voice-outbound.md`
  - `prompts/<client>-<project>-voice-inbound.md`
- If only one channel exists, ship one file using the matching suffix (`-outbound` or `-inbound`).
- **Do not** split knowledge into a separate `*-knowledge.md`; merge the full knowledge base inside each file under `## … knowledgebase` (duplicate is fine so each Fixit bot is self-contained).
- Optional `examples/*-voice-outbound.brief.yaml` and `*-voice-inbound.brief.yaml` each point to their `knowledge.prompt_file`.

### Outbound vs inbound

- **Outbound:** platform opening includes reach-out / enquiry framing (for example `{lead_name} ji, I am reaching out because you showed interest in properties around Chandigarh. Still exploring options?`). Stage 1 after they engage. Keep `## Where did you get my number` when relevant.
- **Inbound:** customer dialed in — **no** "reaching out", **no** "you showed interest", **no** "I wanted to inform you about Opus One" on platform or agent turns. Platform opening: greet plus **how may I help**. Stage 1 starts when **they** name Opus One, pricing, site visit, or Chandigarh property — then USPs plus "know more?". Replace number-source section with `## What this inbound call is`. Ban outbound callback language in `[Critical]` and in call progression.

## Formatting (mandatory)

- **No markdown tables.** Never use `|` table syntax. Facts belong in explanatory bullet pointers.
- **Headings:** `##` for main sections (persona, call flow, knowledgebase, hard rules, etc.).
- **Subheadings:** `#` for subsections inside a `##` block (for example unit types, amenities groups).
- **Pointers:** `-` for every list item; write full explanatory lines, not telegraphic labels.
- No `===` banner lines in the final file unless the user explicitly wants Fixit-style separators.
- Prefer readable prose inside bullets where the reference sample used paragraphs.

## First line of the file (mandatory) — not the first spoken sentence

The **first line of the prompt document** must be a single `[Critical]` block:

`[Critical] You are {AgentName}. You are {persona nationality/identity} and you speak English in a {accent description}. {Optional: default language, switch rules, and that every project fact comes from the knowledge in this prompt — never invented, never announced as a lookup.}`

Examples:

- Indian advisor: `[Critical] You are Aman. You are Indian, native Punjabi, and you speak English in a natural Indian accent. ...`
- British advisor: `[Critical] You are Alex. You are British and you speak in a British accent. ...`

Tailor nationality, accent, and language rules to the brief. The `[Critical]` line is always line one of the **prompt file** — no title or front matter above it.

## Opening sentence — spoken OUT OF the prompt, not FROM the prompt

- The **first sentence the caller hears** is **not** generated from this prompt. The telephony / Fixit platform plays it from a **separate hardcoded script** (opening line config, TTS preset, or dialer field).
- Document that opening in a section such as `## Opening line (platform — out of prompt)`. State clearly: **you do not generate, repeat, or paraphrase this line** on your first turn; your dialogue begins on the **second** beat, after the lead responds.
- **Outbound** default (adapt region per brief):
  - `{lead_name} ji, I am reaching out to you because you have shown interest in properties around {city/region}. Are you still exploring some options?`
- **Inbound** default:
  - `Namaste, welcome to {company}, {agent} here. How may I help you today?` — no reach-out, no enquiry assumption.
- Include Punjabi/Hindi variants in the same section if needed — still **out of prompt**, platform-fired only.
- Never confuse the `[Critical]` document line with the spoken opening. One is **instructions** (in the prompt file); the other is **audio** (outside the prompt file).

## Call progression (mandatory staging)

After the platform opening, the **first turn you generate** must follow this ladder. Do not skip stages or dump the knowledgebase early.

- **Stage 0 (platform, out of prompt):** Outbound — interest check and still exploring; inbound — greet and how may I help only.
- **Stage 1:** Outbound — after they engage; inbound — after they name the project or need — in both cases give **two or three short USPs** (hyper-luxury township, location one-liner, one certification or scale fact). **No amenity laundry list.** Inbound must never frame as "reason I'm calling you". End with **one** follow-up: whether they would like to know more (vary wording every call).
- **Stage 2 (if they say yes or ask):** Answer their thread in **tight turns** — sizes, location landmarks, payment defer to RM, amenities **only as asked**.
- **Stage 3 (when genuine interest):** Objective ask — site visit at Eco City / official quote pack on WhatsApp with layouts.
- **Stage 4:** Low-level detail — unit house names, carpet and super areas, technical specs, consultant pedigree, master plan zones, comparisons to other Tricity pockets.

Rules:

- USPs are **two or three sentences total** in stage 1, still respecting client turn-length limits if specified (for example thirty to forty words — then USPs may span two turns only if the user allows; default is one turn with two USPs plus interest question).
- "Interested to know more?" (or equivalent) is **mandatory** before stage 2 detail.
- Qualification (budget, end-use) comes **after** stage 1 interest — never in the first generated turn.

## Knowledgebase (mandatory — extensive)

- The `## … knowledgebase` section must be **long and brochure-complete**, not a short summary.
- Include at minimum when the source material allows:
  - Project identity, positioning copy, certifications, RERA, approvals, disclaimer
  - Location narrative, micro-market, highways, **full landmark list** from map/brochure
  - Developer and conglomerate story
  - Design consultants with **named principals** and notable credits (one line each)
  - Master plan zone list
  - Amenities grouped (arrival, landscape, club, sports, convenience, safety) — every brochure line as a bullet
  - All unit types with carpet, covered, super; house names; variant notes
  - Technical specifications by room/finish category
  - Contacts, site and corporate office
  - **USP bank** — five to eight ready one-liners the agent may rotate in stage 1
  - **Defer list** — price, possession, payment plan, availability, legal, all-in cost
- Pull facts from brochures and layout sheets; if layout PDFs are image-only, use brochure unit pages for areas.

## Content shape (follow the reference sample)

Mirror the depth of a senior call prompt (persona, voice, **opening out-of-prompt**, **staged call progression**, number source, disinterest, objective, knowledgebase, language, turn length, human behaviour, hard rules, close). Inherit craft from `nuances/voicebot.yaml` unless the brief overrides.

## Workflow

1. Read the user brief, sample prompt, and any PDFs/brochures.
2. Build a structured internal outline (units, amenities, contacts) — **without tables**.
3. Write `prompts/...-voice-outbound.md` and/or `...-voice-inbound.md`: `[Critical]` first (state call type), then `##` sections, `#` subsections, `-` pointers.
4. Document platform opening under `## Opening line — outbound` or `## Opening line — inbound` (both **out of prompt**).
5. Update matching `examples/*-brief.yaml` files.
6. Do not ship a generic `*-voice.md` without inbound/outbound suffix when both channels exist.

## Quality checks before finishing

- First **file** line is `[Critical]` with persona and accent.
- Opening line documented as **out of prompt**; agent told not to generate it.
- Staged call flow: objective opening → USPs → interested to know more → detail → close ask.
- Knowledgebase is **extensive** (USP bank + full amenities + units + specs + defer list).
- Zero tables in the deliverable.
- One file per channel (outbound and/or inbound); each self-contained.
- Headings use `##` and `#` as specified; lists use `-` only.
