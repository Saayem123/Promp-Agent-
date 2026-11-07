"""Load and update the two nuance files.

WhatsApp lives in nuances/whatsapp.yaml. Voice lives in nuances/voicebot.yaml.
Hand-written rules stay as they are. Ingest and transcript review only append
under `added`, so a later compile picks them up without rewriting the craft.
"""

from __future__ import annotations

from pathlib import Path

import yaml

CHANNELS = {
    "whatsapp": "whatsapp.yaml",
    "voice": "voicebot.yaml",
    "voicebot": "voicebot.yaml",
}


class Dumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.SafeDumper, data: str):
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


Dumper.add_representer(str, _represent_str)


def find_root(start: Path | None = None) -> Path:
    here = (start or Path.cwd()).resolve()
    for candidate in [here, *here.parents]:
        nuances = candidate / "nuances"
        if (nuances / "whatsapp.yaml").is_file() and (nuances / "voicebot.yaml").is_file():
            return candidate
    raise SystemExit("Could not find nuances/whatsapp.yaml and nuances/voicebot.yaml.")


def channel_path(root: Path, channel: str) -> Path:
    filename = CHANNELS.get(channel)
    if filename is None:
        known = ", ".join(sorted({"whatsapp", "voice"}))
        raise SystemExit(f"Unknown channel {channel!r}. Use one of: {known}.")
    return root / "nuances" / filename


def load(path: Path) -> dict:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path} is not a nuance file.")
    data.setdefault("rules", [])
    data.setdefault("added", []) or []
    if data["added"] is None:
        data["added"] = []
    data.setdefault("sections", [])
    data.setdefault("examples", [])
    seen: set[str] = set()
    for rule in iter_rules(data):
        rule_id = rule.get("id")
        if not rule_id or not isinstance(rule_id, str):
            raise SystemExit(f"{path} has a rule with no id.")
        if rule_id in seen:
            raise SystemExit(f"Duplicate nuance id {rule_id} in {path}.")
        seen.add(rule_id)
    return data


def iter_rules(data: dict) -> list[dict]:
    return [*(data.get("rules") or []), *(data.get("added") or [])]


def rules_by_section(data: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for rule in data.get("rules") or []:
        grouped.setdefault(rule.get("section") or "added", []).append(rule)
    return grouped


def append_rules(path: Path, new_rules: list[dict]) -> int:
    """Append rules under `added`. Returns how many were written."""
    if not new_rules:
        return 0
    path = Path(path)
    data = load(path)
    existing = {rule["id"] for rule in iter_rules(data)}
    fresh = [rule for rule in new_rules if rule["id"] not in existing]
    if not fresh:
        return 0
    snippet = yaml.dump(fresh, Dumper=Dumper, sort_keys=False, allow_unicode=True, width=88)
    indented = "".join(
        ("  " + line if line.strip() else line) for line in snippet.splitlines(True)
    )
    text = path.read_text(encoding="utf-8")
    stripped = text.rstrip()
    if stripped.endswith("added: []"):
        stripped = stripped[: -len("added: []")].rstrip() + "\nadded:\n" + indented
    elif "\nadded:" in text or stripped.endswith("added:"):
        if stripped.endswith("added:"):
            stripped = stripped + "\n" + indented
        else:
            stripped = stripped + "\n" + indented
    else:
        stripped = stripped + "\n\nadded:\n" + indented
    if not stripped.endswith("\n"):
        stripped += "\n"
    path.write_text(stripped, encoding="utf-8")
    return len(fresh)
