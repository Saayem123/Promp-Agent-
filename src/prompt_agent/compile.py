"""Turn a brief plus the channel nuance file into a system prompt."""

from __future__ import annotations

import re

from prompt_agent.flow import build_flow, render_flow
from prompt_agent.library import iter_rules, rules_by_section

PLACEHOLDER = re.compile(r"\{\{\s*([a-z_]+)\s*\}\}")


def _values(brief: dict) -> dict[str, str]:
    channel = brief["channel"]
    companion = brief.get("companion_channel") or "message"
    return {
        "agent_name": brief["agent_name"],
        "company": brief["company"],
        "role": brief["role"],
        "mission": brief["mission"].strip(),
        "domain": brief["domain"],
        "companion_channel": companion,
        "channel_name": "WhatsApp" if channel == "whatsapp" else "the phone",
    }


def fill(text: str, brief: dict) -> str:
    values = _values(brief)

    def replace(match: re.Match) -> str:
        key = match.group(1)
        if key not in values:
            raise SystemExit(f"Unknown placeholder {{{{{key}}}}} in a nuance.")
        return values[key]

    return PLACEHOLDER.sub(replace, text or "")


def _bullet_block(title: str, items: list) -> str:
    if not items:
        return ""
    lines = [title]
    for item in items:
        lines.append(f"- {item}")
    return "\n".join(lines)


def render_scope(brief: dict) -> str:
    knowledge = brief.get("knowledge") or {}
    parts = [
        "## What you answer and what you defer",
        (
            "Anything specific comes from the live knowledge source. You never invent it and "
            "you never quote it from memory. General questions you answer fully, with real "
            "substance. Hiding behind let me check on a general question is a failure. "
            "The lists below are the line."
        ),
    ]
    verify = _bullet_block(
        "Comes live, every time.",
        list(knowledge.get("verify") or []),
    )
    general = _bullet_block(
        "Answer these yourself.",
        list(knowledge.get("answer_generally") or []),
    )
    defer = _bullet_block(
        "Defer these and confirm later. Never guess.",
        list(knowledge.get("defer") or []),
    )
    for block in (verify, general, defer):
        if block:
            parts.append(block)
    notes = (brief.get("notes") or "").strip()
    if notes:
        parts.append(
            "Background, not a source of figures. Anything in here about a price, a date, "
            "a size or availability still has to come from the live source before you say it."
        )
        parts.append(notes)
    return "\n\n".join(parts)


def render_identity(brief: dict) -> str:
    identity = brief.get("identity") or {}
    company_answer = identity.get("company_answer") or (
        f"I'm with {brief['company']}. I look after their enquiries."
    )
    bot_answer = identity.get("bot_answer") or (
        f"You're talking to {brief['company']}'s assistant. I can answer most things myself, "
        "and I pull the team in when it needs a person."
    )
    return "\n\n".join(
        [
            "If they ask which company you are from, answer warmly and briefly, then carry on.",
            company_answer,
            "If they ask whether they are talking to a bot, tell them the truth without making it awkward, then carry straight on.",
            bot_answer,
        ]
    )


def _example_allowed(example: dict, brief: dict) -> bool:
    domain = (example.get("domain") or "any").lower()
    if domain in ("any", "all", "*"):
        return True
    return domain in brief["domain"].lower() or brief["domain"].lower() in domain


def render_examples(data: dict, brief: dict) -> str:
    examples = [item for item in (data.get("examples") or []) if _example_allowed(item, brief)]
    if not examples:
        return ""
    lines = [
        "## How it sounds",
        (
            "The register and the shape only. Never reuse the wording. "
            "Square brackets are notes to you, not words you send. "
            "Every place name and every figure still comes from the live source."
        ),
    ]
    for example in examples:
        kind = example.get("kind") or "good"
        lines.append(f"{'Right' if kind == 'good' else 'Wrong'}.")
        lines.append(f"They said: {fill(example['user'], brief)}")
        lines.append(f"You: {fill(example['assistant'], brief)}")
        if example.get("why"):
            lines.append(fill(example["why"], brief))
    return "\n\n".join(lines)


def render_added(data: dict, brief: dict) -> str:
    added = data.get("added") or []
    if not added:
        return ""
    lines = [
        "## Learned from later instructions and real conversations",
        (
            "These were saved after the base craft. They apply by default. "
            "A hard one never bends. A default one bends only when the person in front of you needs something different."
        ),
    ]
    for rule in added:
        lines.append(fill(rule.get("instruction") or "", brief))
    return "\n\n".join(lines)


def compile_prompt(brief: dict, library: dict) -> str:
    arabic = bool(brief.get("language", {}).get("arabic_particles"))
    grouped = rules_by_section(library)
    parts: list[str] = []
    meta = library.get("meta") or {}
    opener = fill(meta.get("opener") or "", brief)
    if opener:
        parts.append(opener)
    for section in library.get("sections") or []:
        if section.get("id") == "arabic" and not arabic:
            continue
        rules = grouped.get(section["id"]) or []
        intro = fill(section.get("intro") or "", brief)
        body = [fill(rule.get("instruction") or "", brief) for rule in rules]
        chunks = [f"## {section['title']}"]
        if intro:
            chunks.append(intro)
        chunks.extend(body)
        if section["id"] == "identity":
            chunks.append(render_identity(brief))
        chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
        if len(chunks) == 1:
            continue
        parts.append("\n\n".join(chunks))
    parts.append(render_scope(brief))
    parts.append(render_flow(build_flow(brief)))
    examples = render_examples(library, brief)
    if examples:
        parts.append(examples)
    added = render_added(library, brief)
    if added:
        parts.append(added)
    # Rules whose section was not listed still matter.
    known_sections = {section["id"] for section in library.get("sections") or []}
    orphans = [
        rule
        for rule in iter_rules(library)
        if rule.get("section") not in known_sections and rule.get("section") != "added"
    ]
    if orphans:
        extra = ["## Also in force"]
        extra.extend(fill(rule.get("instruction") or "", brief) for rule in orphans)
        parts.append("\n\n".join(extra))
    text = "\n\n".join(part.strip() for part in parts if part and part.strip())
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    leftover = PLACEHOLDER.search(text)
    if leftover:
        raise SystemExit(f"Unfilled placeholder {leftover.group(0)} in compiled prompt.")
    return text
