import copy
from pathlib import Path

import yaml

from prompt_agent.brief import load_brief, resolve_slots
from prompt_agent.compile import compile_prompt
from prompt_agent.extract import extract_rules, ingest_file
from prompt_agent.flow import build_flow
from prompt_agent.library import append_rules, find_root, iter_rules, load
from prompt_agent.review import learned_rules, review_turns

ROOT = find_root(Path(__file__).resolve().parents[1])
EXAMPLES = ROOT / "examples"


def _brief(name: str) -> dict:
    return load_brief(EXAMPLES / name)


def _library(channel: str) -> dict:
    filename = "voicebot.yaml" if channel == "voice" else "whatsapp.yaml"
    return load(ROOT / "nuances" / filename)


def test_both_nuance_files_cover_the_hard_rules():
    for channel in ("whatsapp", "voice"):
        text = (ROOT / "nuances" / ("voicebot.yaml" if channel == "voice" else "whatsapp.yaml")).read_text(
            encoding="utf-8"
        )
        for phrase in (
            "never invent",
            "knowledgebase",
            "check with the team",
            "guaranteed returns",
            "exclamation",
            "pretend to be a human",
        ):
            assert phrase in text.lower(), phrase


def test_modon_whatsapp_prompt_is_usable():
    brief = _brief("modon-property.brief.yaml")
    prompt = compile_prompt(brief, _library("whatsapp"))
    lowered = prompt.lower()
    assert "you are khalid" in lowered
    assert "modon" in lowered
    assert "i'll" in lowered
    assert "one project" in lowered or "one option" in lowered
    assert "live in or to invest" in lowered
    assert "roughly what budget" in lowered
    assert "how many bedrooms" in lowered
    assert "wallah" in lowered
    assert "introduce yourself exactly once" in lowered
    assert "do not name a project in your first message" in lowered
    assert "when not to use the project shape" in lowered
    assert "modon real estate" in lowered
    assert "here's everything" not in lowered or "full list" in lowered
    assert "!" not in prompt
    assert "{{" not in prompt


def test_modon_voice_prompt_is_spoken():
    brief = _brief("modon-voice.brief.yaml")
    prompt = compile_prompt(brief, _library("voice"))
    lowered = prompt.lower()
    assert "talk over" in lowered
    assert "don't read" in lowered or "do not read" in lowered
    assert "whatsapp" in lowered
    assert "press one" in lowered or "phone menu" in lowered
    assert "five million" in lowered
    assert "!" not in prompt
    assert "{{" not in prompt


def test_clinic_inherits_whatsapp_craft_not_arabic_or_property_slots():
    brief = _brief("clinic-front-desk.brief.yaml")
    prompt = compile_prompt(brief, _library("whatsapp"))
    lowered = prompt.lower()
    assert "you are noor" in lowered
    assert "harbour clinic" in lowered
    assert "exclamation" in lowered
    assert "wallah" not in lowered
    assert "whether it is to live in or to invest" not in lowered
    assert "what they want to sort out" in lowered
    assert "a diagnosis" in lowered
    assert "!" not in prompt


def test_property_flow_has_memory_and_no_prices():
    flow = build_flow(_brief("modon-property.brief.yaml"))
    ids = [slot["id"] for slot in flow["memory"]]
    assert ids[:3] == ["purpose", "budget", "location"]
    assert any(branch["id"] == "invest-split" for branch in flow["branches"])
    dumped = yaml.safe_dump(flow)
    assert "4.2" not in dumped
    assert "aed" not in dumped.lower()


def test_good_transcript_does_not_reask():
    import json

    brief = _brief("modon-property.brief.yaml")
    turns = [json.loads(line) for line in (EXAMPLES / "transcripts" / "good-property.jsonl").read_text().splitlines()]
    findings = review_turns(brief, _library("whatsapp"), turns)
    assert findings == []


def test_bare_four_after_bedrooms_is_not_a_new_question():
    import json

    brief = _brief("modon-property.brief.yaml")
    turns = [json.loads(line) for line in (EXAMPLES / "transcripts" / "reask.jsonl").read_text().splitlines()]
    findings = review_turns(brief, _library("whatsapp"), turns)
    assert any(item.rule_id == "memory.no-reask" for item in findings)


def test_bare_four_after_apartment_or_villa_is_not_bedrooms():
    brief = _brief("modon-property.brief.yaml")
    turns = [
        {"role": "assistant", "text": "Okay, around 5 million. Apartment or villa?"},
        {"role": "user", "text": "4"},
        {"role": "assistant", "text": "Four bedrooms, got it."},
    ]
    findings = review_turns(brief, _library("whatsapp"), turns)
    assert any(item.rule_id == "converse.short-answer-context" for item in findings)
    assert not any(item.rule_id == "memory.no-reask" for item in findings)


def test_three_facts_are_remembered():
    brief = _brief("modon-property.brief.yaml")
    turns = [
        {"role": "user", "text": "apartment, 4 bed, abu dhabi"},
        {"role": "assistant", "text": "How many bedrooms were you thinking?"},
    ]
    findings = review_turns(brief, _library("whatsapp"), turns)
    assert any(item.rule_id == "memory.no-reask" for item in findings)


def test_style_breaks_and_stop():
    import json

    brief = _brief("modon-property.brief.yaml")
    turns = [
        json.loads(line) for line in (EXAMPLES / "transcripts" / "style-breaks.jsonl").read_text().splitlines()
    ]
    findings = review_turns(brief, _library("whatsapp"), turns)
    rules = {item.rule_id for item in findings}
    assert "style.no-exclamation" in rules
    assert "style.no-selling-words" in rules
    assert "truth.no-false-confirmation" in rules
    assert "truth.no-guarantees" in rules
    assert "style.contractions" in rules
    assert "followup.no-chase" in rules
    assert "never.stop" in rules


def test_apply_saves_a_learned_nuance_once(tmp_path: Path):
    source = ROOT / "nuances" / "whatsapp.yaml"
    copy_path = tmp_path / "whatsapp.yaml"
    # The loader only needs this file, but find_root is not used here.
    copy_path.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    # append_rules loads a single file. Give it a valid nuance file.
    import json

    brief = _brief("modon-property.brief.yaml")
    turns = [
        json.loads(line) for line in (EXAMPLES / "transcripts" / "reask.jsonl").read_text().splitlines()
    ]
    findings = review_turns(brief, load(copy_path), turns)
    rules = learned_rules(findings, origin="reask.jsonl")
    assert append_rules(copy_path, rules) == len(rules)
    assert append_rules(copy_path, rules) == 0
    again = load(copy_path)
    assert any(rule["id"].startswith("learned.") for rule in iter_rules(again))
    prompt = compile_prompt(brief, again)
    assert "A real conversation broke" in prompt


def test_ingest_saves_a_new_nuance_and_skips_a_known_one(tmp_path: Path):
    nuances = tmp_path / "nuances"
    nuances.mkdir()
    for name in ("whatsapp.yaml", "voicebot.yaml"):
        (nuances / name).write_text((ROOT / "nuances" / name).read_text(encoding="utf-8"), encoding="utf-8")
    instructions = tmp_path / "new.md"
    instructions.write_text(
        "\n".join(
            [
                "# Extra instructions",
                "Never promise a discount before the team has agreed the number.",
                "You never use an exclamation mark.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    # ingest_file uses the path it is given, not find_root.
    result = ingest_file(nuances / "whatsapp.yaml", instructions, mirror_to=nuances / "voicebot.yaml")
    saved_ids = [rule["id"] for rule in result["saved"]]
    assert any("discount" in rule_id for rule_id in saved_ids)
    assert not any("exclamation" in rule_id for rule_id in saved_ids)
    assert result["mirrored"]
    voice = load(nuances / "voicebot.yaml")
    assert any("discount" in rule["id"] for rule in voice.get("added") or [])


def test_extract_marks_a_hard_section():
    text = "# Notes\n## The hard rules\n1. Never invent a price to keep the chat moving forward.\n"
    rules = extract_rules(text, origin="test")
    assert rules[0]["kind"] == "hard"


def test_reintro_transcript():
    import json

    brief = _brief("modon-property.brief.yaml")
    turns = [json.loads(line) for line in (EXAMPLES / "transcripts" / "reintro.jsonl").read_text().splitlines()]
    findings = review_turns(brief, _library("whatsapp"), turns)
    rules = {item.rule_id for item in findings}
    assert "after_first.no-greeting" in rules
    assert "after_first.no-reintro" in rules


def test_domain_slot_patterns_are_not_mutated():
    from prompt_agent.domains import PROPERTY_SLOTS

    before = copy.deepcopy(PROPERTY_SLOTS)
    brief = _brief("modon-property.brief.yaml")
    brief["locations"] = ["saadiyat"]
    resolve_slots(brief)
    assert PROPERTY_SLOTS == before
