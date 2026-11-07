"""Load a use-case brief and resolve the slots it should remember."""

from __future__ import annotations

import copy
from pathlib import Path

import yaml

from prompt_agent.domains import domain_slots

REQUIRED = ("id", "channel", "agent_name", "company", "role", "mission", "domain")


def load_brief(path: Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a brief.")
    missing = [key for key in REQUIRED if not data.get(key)]
    if missing:
        raise SystemExit(f"{path} is missing: {', '.join(missing)}.")
    channel = data["channel"]
    if channel not in ("whatsapp", "voice"):
        raise SystemExit("brief.channel must be whatsapp or voice.")
    data.setdefault("knowledge", {})
    data.setdefault("language", {})
    data.setdefault("identity", {})
    data.setdefault("tools", [])
    data.setdefault("locations", [])
    data.setdefault("notes", "")
    return data


def resolve_slots(brief: dict) -> list[dict]:
    merged: dict[str, dict] = {}
    # Domain slots apply when the brief asks for them, and by default when
    # the brief does not bring a list of its own.
    use_domain = brief.get("slots_from_domain")
    if use_domain is None:
        use_domain = not brief.get("slots")
    if use_domain:
        for slot in domain_slots(brief["domain"]):
            merged[slot["id"]] = slot
    for slot in brief.get("slots") or []:
        if "id" not in slot or "label" not in slot:
            raise SystemExit("Every slot needs an id and a label.")
        merged[slot["id"]] = slot
    slots = [copy.deepcopy(slot) for slot in merged.values()]
    extra_places = brief.get("locations") or []
    if extra_places:
        for slot in slots:
            if slot["id"] != "location":
                continue
            names = "|".join(extra_places)
            slot.setdefault("user_regex", [])
            slot["user_regex"] = [
                *slot["user_regex"],
                rf"(?i)\b(?:{names})\b",
            ]
    return slots
