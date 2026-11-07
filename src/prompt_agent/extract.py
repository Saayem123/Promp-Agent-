"""Pull reusable nuances out of a free-form instruction and save them.

This is how a new brief gets remembered. The next compile, for any use case
on that channel, inherits whatever was saved.
"""

from __future__ import annotations

import re
from pathlib import Path

from prompt_agent.library import append_rules, iter_rules, load

HARD_HEADING = re.compile(r"hard rule", re.I)
SKIP_HEADING = re.compile(r"how it sounds|for example|wrong", re.I)
BULLET = re.compile(r"^(?:[-*]|\d+[.)])\s+(.*\S)\s*$")
IMPERATIVE = re.compile(
    r"^(?:never|always|do not|don't|you never|you always|you do not)\b",
    re.I,
)
STOPWORDS = {
    "you",
    "the",
    "a",
    "an",
    "to",
    "and",
    "of",
    "in",
    "on",
    "for",
    "it",
    "is",
    "are",
    "be",
    "this",
    "that",
    "with",
    "or",
    "if",
    "they",
    "them",
    "their",
    "your",
    "from",
    "as",
    "at",
    "by",
    "we",
    "i",
}


def _tokens(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9']+", text.lower()) if token not in STOPWORDS}


def _similar(left: str, right: str) -> bool:
    a = _tokens(left)
    b = _tokens(right)
    if not a or not b:
        return False
    overlap = len(a & b) / len(a | b)
    if overlap >= 0.62:
        return True
    smaller, larger = (a, b) if len(a) <= len(b) else (b, a)
    return len(smaller) >= 4 and smaller <= larger


def _slug(text: str) -> str:
    words = [token for token in re.findall(r"[a-z0-9]+", text.lower()) if token not in STOPWORDS]
    words = words[:8] or ["note"]
    return "ingested." + "-".join(words)


def _locked(text: str) -> str | None:
    lowered = text.lower()
    whatsapp = any(word in lowered for word in ("whatsapp", "emoji", "markdown", "brochure", "pdf"))
    voice = any(
        word in lowered
        for word in ("barge-in", "barge in", "aloud", "caller", "phone menu", "on the line")
    )
    if whatsapp and not voice:
        return "whatsapp"
    if voice and not whatsapp:
        return "voice"
    return None


def _mirror_text(text: str, target: str) -> str:
    if target == "voice":
        return "On a live call, the same standard holds. " + text
    return "On WhatsApp, the same standard holds. " + text


def extract_rules(text: str, origin: str) -> list[dict]:
    kind = "default"
    skip = False
    found: list[dict] = []
    seen_slugs: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if HARD_HEADING.search(line):
                kind = "hard"
                skip = False
            elif line.startswith("## ") or line.startswith("# "):
                kind = "default"
                skip = bool(SKIP_HEADING.search(line))
            continue
        if skip:
            continue
        match = BULLET.match(line)
        candidate = match.group(1).strip() if match else line
        if not match and not IMPERATIVE.match(candidate):
            continue
        if candidate.startswith("```") or len(_tokens(candidate)) < 5:
            continue
        rule_id = _slug(candidate)
        if rule_id in seen_slugs:
            continue
        seen_slugs.add(rule_id)
        found.append(
            {
                "id": rule_id,
                "kind": "hard" if kind == "hard" or candidate.lower().startswith("never") else "default",
                "section": "added",
                "title": " ".join(candidate.split()[:12]),
                "instruction": candidate.rstrip("."),
                "origin": origin,
            }
        )
    return found


def _is_new(rule: dict, existing: list[dict]) -> bool:
    blob = rule["instruction"]
    for current in existing:
        current_blob = " ".join(
            [
                current.get("title") or "",
                current.get("instruction") or "",
            ]
        )
        if rule["id"] == current.get("id") or _similar(blob, current_blob):
            return False
    return True


def ingest_text(path: Path, text: str, *, mirror: bool = False) -> list[dict]:
    """Save new nuances into one channel file. Mirror copies unlocked rules across."""
    library = load(path)
    origin = "instructions"
    extracted = extract_rules(text, origin)
    fresh = [rule for rule in extracted if _is_new(rule, iter_rules(library))]
    append_rules(path, fresh)
    return fresh


def ingest_file(path: Path, instruction_file: Path, *, mirror_to: Path | None = None) -> dict:
    text = instruction_file.read_text(encoding="utf-8")
    saved = ingest_text(path, text)
    mirrored: list[dict] = []
    if mirror_to is not None:
        target = "voice" if mirror_to.name.startswith("voice") else "whatsapp"
        library = load(mirror_to)
        existing = iter_rules(library)
        for rule in saved:
            if _locked(rule["instruction"]) not in (None, target):
                continue
            copy = dict(rule)
            copy["id"] = rule["id"] + ".mirrored"
            copy["instruction"] = _mirror_text(rule["instruction"], target)
            copy["origin"] = f"mirrored from {path.name}"
            if _is_new(copy, existing):
                mirrored.append(copy)
        append_rules(mirror_to, mirrored)
    return {"saved": saved, "mirrored": mirrored}
