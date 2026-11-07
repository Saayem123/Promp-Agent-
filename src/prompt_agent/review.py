"""Review a transcript against the nuance file and the brief's memory.

Findings are things a person on the other end would feel: a re-asked question,
a confirmed visit that was not confirmed, a sales word, a menu. Applying a
review saves one learned nuance per broken rule, so the next prompt carries it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from prompt_agent.brief import resolve_slots

SELLING_WORDS = (
    "great",
    "lovely",
    "awesome",
    "amazing",
    "wonderful",
    "fantastic",
    "stunning",
    "perfect",
    "beautiful",
    "luxury",
    "premium",
    "exclusive",
    "incredible",
)

PHRASES = {
    "style.no-corporate": (
        "kindly",
        "as per",
        "please find attached",
        "pls advise",
        "dear sir",
        "dear madam",
    ),
    "truth.never-name-source": ("knowledgebase", "knowledge base", "the system"),
    "truth.no-guarantees": (
        "best investment",
        "guaranteed return",
        "guaranteed returns",
        "prices will definitely",
        "definitely rise",
    ),
    "never.phone-tree": ("please select an option", "select an option from the menu"),
    "followup.no-chase": ("just following up", "just checking in", "checking in"),
    "truth.no-false-confirmation": (
        "you're booked",
        "you are booked",
        "visit is confirmed",
        "viewing is confirmed",
        "call is confirmed",
        "booking is confirmed",
        "i've booked",
        "i have booked",
        "callback is confirmed",
    ),
}

UNCONTRACTED = re.compile(
    r"\b(I will|I am|you are|we are|they are|it is|that is|there is|do not|we have|"
    r"I have|cannot|will not|we will|they will)\b",
    re.I,
)

STOP_USER = re.compile(
    r"\b(unsubscribe|stop messaging|stop texting|stop calling|don't text|do not text|"
    r"don't message|do not message|don't call|do not call)\b",
    re.I,
)

NAME_USER = re.compile(r"\b(?:I'm|I am|this is)\s+([A-Z][a-z]+)\b")
NAME_SKIP = {
    "looking",
    "interested",
    "calling",
    "just",
    "here",
    "not",
    "good",
    "fine",
    "busy",
}

BEDROOM_ASSERT = re.compile(
    r"\b(one|two|three|four|five|six|seven|1|2|3|4|5|6|7)\s*bed(?:room)?s?\b",
    re.I,
)


@dataclass
class Finding:
    turn: int
    rule_id: str
    severity: str
    message: str
    evidence: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "turn": self.turn,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
        }


def _severity(library: dict, rule_id: str) -> str:
    for rule in [*(library.get("rules") or []), *(library.get("added") or [])]:
        if rule.get("id") == rule_id:
            return "hard" if rule.get("kind") == "hard" else "default"
    return "default"


def _finding(library: dict, turn: int, rule_id: str, message: str, evidence: str, suggestion: str) -> Finding:
    return Finding(
        turn=turn,
        rule_id=rule_id,
        severity=_severity(library, rule_id),
        message=message,
        evidence=evidence.strip(),
        suggestion=suggestion,
    )


def _matches_any(text: str, patterns: list[str] | None, regexes: list[str] | None) -> bool:
    lowered = text.lower()
    for pattern in patterns or []:
        if pattern.lower() in lowered:
            return True
    for pattern in regexes or []:
        if re.search(pattern, text):
            return True
    return False


def _slot_position(slot: dict, text: str) -> int:
    lowered = text.lower()
    positions = []
    for pattern in slot.get("question_patterns") or []:
        at = lowered.find(pattern.lower())
        if at >= 0:
            positions.append(at)
    for pattern in slot.get("question_regex") or []:
        found = re.search(pattern, text)
        if found:
            positions.append(found.start())
    return max(positions) if positions else -1


def _asks(slot: dict, text: str) -> bool:
    if "?" not in text:
        return False
    return _slot_position(slot, text) >= 0


def _new_memory() -> dict:
    return {
        "slots": {},
        "awaiting": None,
        "dodged": set(),
        "names": [],
        "name_uses": 0,
        "stopped": False,
        "bare_unbound": False,
    }


def _apply_user(memory: dict, text: str, slots: list[dict]) -> None:
    if STOP_USER.search(text):
        memory["stopped"] = True
    name = NAME_USER.search(text)
    if name and name.group(1).lower() not in NAME_SKIP:
        memory["names"].append(name.group(1))
    filled: list[str] = []
    for slot in slots:
        if _matches_any(text, slot.get("user_patterns"), slot.get("user_regex")):
            memory["slots"][slot["id"]] = text.strip()
            filled.append(slot["id"])
            memory["dodged"].discard(slot["id"])
    awaiting = memory.get("awaiting")
    bare = re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", text or "")
    memory["bare_unbound"] = False
    if bare and awaiting:
        slot = next(item for item in slots if item["id"] == awaiting)
        if slot.get("bare_number", True) and awaiting not in filled:
            memory["slots"][awaiting] = text.strip()
            filled.append(awaiting)
            memory["dodged"].discard(awaiting)
        elif not slot.get("bare_number", True):
            memory["bare_unbound"] = True
    elif bare and not awaiting:
        memory["bare_unbound"] = True
    if awaiting and awaiting not in memory["slots"]:
        if "?" in text or (filled and awaiting not in filled):
            memory["dodged"].add(awaiting)
    memory["awaiting"] = None


def _note_assistant(memory: dict, text: str, slots: list[dict]) -> None:
    if "?" not in text:
        memory["awaiting"] = None
        memory["bare_unbound"] = False
        return
    ranked = [( _slot_position(slot, text), slot["id"]) for slot in slots]
    ranked = [item for item in ranked if item[0] >= 0]
    memory["awaiting"] = max(ranked)[1] if ranked else None
    memory["bare_unbound"] = False


def _check_words(library: dict, turn: int, text: str) -> list[Finding]:
    findings = []
    if "!" in text:
        findings.append(
            _finding(
                library,
                turn,
                "style.no-exclamation",
                "This turn uses an exclamation mark.",
                text,
                "End every sentence with a full stop or a question mark.",
            )
        )
    for word in SELLING_WORDS:
        if re.search(rf"\b{word}\b", text, re.I):
            findings.append(
                _finding(
                    library,
                    turn,
                    "style.no-selling-words",
                    f"This turn uses the selling word {word}.",
                    text,
                    "Say what it is and where it is. Leave the praise out.",
                )
            )
            break
    lowered = text.lower()
    for rule_id, phrases in PHRASES.items():
        for phrase in phrases:
            if phrase in lowered:
                findings.append(
                    _finding(
                        library,
                        turn,
                        rule_id,
                        f"This turn says {phrase}.",
                        text,
                        "Take that phrase out and say the plain version.",
                    )
                )
                break
    if UNCONTRACTED.search(text):
        findings.append(
            _finding(
                library,
                turn,
                "style.contractions",
                "This turn writes out a contraction.",
                text,
                "Write I'll, you're, that's, don't, we've. Never the long form.",
            )
        )
    if text.count("?") > 1:
        findings.append(
            _finding(
                library,
                turn,
                "never.two-questions",
                "This turn asks more than one question.",
                text,
                "Ask one thing, or ask nothing. Do not stack qualifying questions.",
            )
        )
    if re.search(r"\*\*|__|^#\s", text, re.M):
        findings.append(
            _finding(
                library,
                turn,
                "style.no-markdown",
                "This turn uses markdown.",
                text,
                "Write plain sentences. No bold, no headings, no bullet lists unless they asked for everything.",
            )
        )
    return findings


def _check_memory(library: dict, turn: int, text: str, memory: dict, slots: list[dict]) -> list[Finding]:
    findings = []
    for slot in slots:
        if slot["id"] in memory["slots"] and _asks(slot, text):
            findings.append(
                _finding(
                    library,
                    turn,
                    "memory.no-reask",
                    f"They already gave you {slot['label'].lower()}, and this turn asks again.",
                    text,
                    "Read the short answer in context and move on. Never ask the same thing twice.",
                )
            )
        elif slot["id"] in memory["dodged"] and _asks(slot, text):
            findings.append(
                _finding(
                    library,
                    turn,
                    "memory.dodges",
                    f"They dodged {slot['label'].lower()}, and this turn asks it again straight away.",
                    text,
                    "A dodge is an answer. Drop it. Come back much later, once, differently, or work without it.",
                )
            )
    if memory.get("bare_unbound") and BEDROOM_ASSERT.search(text) and "bedrooms" not in memory["slots"]:
        findings.append(
            _finding(
                library,
                turn,
                "converse.short-answer-context",
                "A bare number was not an answer about bedrooms, and this turn treats it as one.",
                text,
                "A short reply answers the question you just asked. Show what you understood and ask only about the gap.",
            )
        )
    return findings


def _check_names(library: dict, turn: int, text: str, memory: dict) -> list[Finding]:
    findings = []
    for name in memory["names"]:
        uses = len(re.findall(rf"\b{re.escape(name)}\b", text))
        if not uses:
            continue
        memory["name_uses"] += uses
        if memory["name_uses"] > 1:
            findings.append(
                _finding(
                    library,
                    turn,
                    "style.name-once",
                    f"Their name {name} has already been used.",
                    text,
                    "Use their name once, early, and then stop.",
                )
            )
            break
    return findings


def _check_stop(library: dict, turn: int, text: str, memory: dict) -> list[Finding]:
    if not memory["stopped"]:
        return []
    words = re.findall(r"\b[\w']+\b", text)
    if "?" in text or len(words) > 40:
        return [
            _finding(
                library,
                turn,
                "never.stop",
                "They asked you to stop, and this turn carries on.",
                text,
                "One warm line and stop. No question and no last pitch.",
            )
        ]
    return []


def review_turns(brief: dict, library: dict, turns: list[dict]) -> list[Finding]:
    slots = resolve_slots(brief)
    memory = _new_memory()
    findings: list[Finding] = []
    for index, turn in enumerate(turns):
        role = turn.get("role")
        text = turn.get("text") or ""
        if role == "user":
            _apply_user(memory, text, slots)
            continue
        if role != "assistant":
            continue
        findings.extend(_check_words(library, index, text))
        findings.extend(_check_memory(library, index, text, memory, slots))
        findings.extend(_check_names(library, index, text, memory))
        findings.extend(_check_stop(library, index, text, memory))
        if brief["channel"] == "voice":
            words = re.findall(r"\b[\w']+\b", text)
            if len(words) > 90:
                findings.append(
                    _finding(
                        library,
                        index,
                        "voice.turn-length",
                        "This spoken turn is too long to say in one go.",
                        text,
                        "Keep a spoken turn to a few short sentences, then stop and let them talk.",
                    )
                )
        _note_assistant(memory, text, slots)
    return findings


def learned_rules(findings: list[Finding], origin: str) -> list[dict]:
    """One saved nuance per broken rule, using the first evidence in the transcript."""
    chosen: dict[str, Finding] = {}
    for finding in findings:
        chosen.setdefault(finding.rule_id, finding)
    rules = []
    for rule_id, finding in chosen.items():
        evidence = " ".join(finding.evidence.split())
        if len(evidence) > 240:
            evidence = evidence[:237] + "..."
        rules.append(
            {
                "id": f"learned.{rule_id}",
                "kind": "hard" if finding.severity == "hard" else "default",
                "section": "added",
                "title": f"Transcript broke {rule_id}",
                "instruction": (
                    f"A real conversation broke {rule_id}. {finding.suggestion} "
                    f"The reply was: {evidence}"
                ),
                "origin": origin,
            }
        )
    return rules


def render_report(findings: list[Finding]) -> str:
    if not findings:
        return "No nuance breaks in this transcript.\n"
    lines = [f"{len(findings)} nuance break(s).", ""]
    for finding in findings:
        lines.append(
            f"Turn {finding.turn} [{finding.severity}] {finding.rule_id}: {finding.message}"
        )
        lines.append(f"  {finding.suggestion}")
    lines.append("")
    return "\n".join(lines)
