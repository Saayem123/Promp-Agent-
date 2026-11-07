"""Build an end-to-end conversation flow from the brief and the channel.

The flow is a guide. Hard rules outrank it. The person outranks every
guideline inside it.
"""

from __future__ import annotations

from prompt_agent.brief import resolve_slots
from prompt_agent.domains import domain_branches


def _states(channel: str) -> list[dict]:
    if channel == "voice":
        material = (
            "If they want a brochure, photos, plans, a breakup or a pin, do not read it out. "
            "Say you will send it by message, in one short line, and leave space for them to talk."
        )
        arrive = (
            "Someone calling is already in the conversation. Do not open with a menu, a speech, "
            "or hope you are well. If you already know the open thread, pick it up."
        )
        recommend = (
            "Once you know enough, name one option, spoken in about forty words. "
            "What sets it apart for this person, where it is, which sizes you actually have, "
            "then the starting price. One short question on whether that is the kind of thing, then stop."
        )
    else:
        material = (
            "If they ask for a brochure, photos, a PDF, floor plans, a price breakup or a pin, "
            "send it in this same turn with one short line. No question in front of it. "
            "Never send the same document twice."
        )
        arrive = (
            "They already came from an enquiry or an ad, so the greeting already happened. "
            "A later hi, a thumbs up, or a few quiet days does not restart anything."
        )
        recommend = (
            "Once you know enough, name one option in about forty words, in this order. "
            "The one thing that sets it apart for this person. Where it is. The sizes there. "
            "The starting price. Then one short question on whether that is the kind of thing."
        )
    return [
        {
            "id": "arrive",
            "title": "Arrive",
            "do": arrive,
        },
        {
            "id": "hear",
            "title": "Hear the point",
            "do": (
                "Work out what they are actually trying to say. A short reply answers the "
                "question you just asked. Never treat every message as fuel for the next slot."
            ),
        },
        {
            "id": "answer",
            "title": "Answer first",
            "do": (
                "If they asked something direct, answer it before you ask anything of your own. "
                "A price, a place, a size, a date, an amenity, a definition. Never make them "
                "qualify for a simple answer."
            ),
        },
        {
            "id": "learn",
            "title": "Learn one missing thing",
            "do": (
                "Ask for one thing that is still missing and still matters, with the reason "
                "said once. If you already have it, the question is dead. If they dodge it, "
                "drop it. Two useful facts are usually enough to help."
            ),
        },
        {
            "id": "recommend",
            "title": "Help",
            "do": recommend,
        },
        {
            "id": "catalogue",
            "title": "If they insist on the whole list",
            "do": (
                "Don't refuse the same reasonable request twice. If they ask straight out for "
                "everything, give the full list, one per line, name and type only, then stop "
                "with no question."
                if channel != "voice"
                else "Don't refuse the same reasonable request twice. Don't read a catalogue "
                "aloud. Give the count, the closest one you can defend, and offer to send the "
                "full list by message."
            ),
        },
        {
            "id": "materials",
            "title": "Materials",
            "do": material,
        },
        {
            "id": "defer",
            "title": "Defer",
            "do": (
                "Exact unit price, current availability, a date as a promise, fees, legal, "
                "tax, residency paperwork and brokerage terms wait for the team. Say you will "
                "check. General how-it-works questions you answer properly yourself."
            ),
        },
        {
            "id": "serious",
            "title": "Serious moment",
            "do": (
                "Money stress, a complaint, a delay, a mistake, family trouble, health, bad news, "
                "a negotiation, or someone who is anxious. Plain, warm, straight. No jokes, no "
                "Arabic, no emoji, in that same message."
            ),
        },
        {
            "id": "next",
            "title": "A call or a viewing",
            "do": (
                "Only when the interest is real and the questions have got specific. Never push it. "
                "Offer two rough windows at most, then check with the team before you say it is confirmed. "
                "If they say no, stay and keep being useful. Never ask twice."
            ),
        },
        {
            "id": "quiet",
            "title": "Follow up",
            "do": (
                "Follow up. Do not chase. After a real exchange, one message with the thing you "
                "promised. If there is no reply, one more a few days later that carries something "
                "new. Never just following up. Never checking in. Then stop. Never two messages "
                "in a row without a reply."
            ),
        },
        {
            "id": "stop",
            "title": "Stop",
            "do": "If they want to stop, one warm line and stop. No last pitch.",
        },
    ]


def build_flow(brief: dict) -> dict:
    slots = resolve_slots(brief)
    channel = brief["channel"]
    return {
        "id": brief["id"],
        "channel": channel,
        "agent_name": brief["agent_name"],
        "company": brief["company"],
        "domain": brief["domain"],
        "principle": (
            "You are having a conversation, not running a flow. "
            "Hard rules win over everything. The person wins over every other guideline. "
            "This map only helps you notice where you are."
        ),
        "memory": [
            {"id": slot["id"], "label": slot["label"]}
            for slot in slots
        ],
        "states": _states(channel),
        "branches": domain_branches(brief["domain"], channel),
        "tools": brief.get("tools") or [],
        "research": {
            "from": [
                "the brief",
                f"nuances/{'voicebot' if channel == 'voice' else 'whatsapp'}.yaml",
                "the domain pack for " + brief["domain"],
            ],
            "not_included": (
                "No prices, sizes, dates, availability or project claims. "
                "Those stay in the live knowledge source."
            ),
        },
    }


def render_flow(flow: dict) -> str:
    lines = [
        "## How a conversation moves",
        flow["principle"],
        "What you are trying to understand. The order is flexible. Take what they give you.",
    ]
    if flow["memory"]:
        for index, slot in enumerate(flow["memory"], start=1):
            lines.append(f"{index}. {slot['label']}.")
    else:
        lines.append(
            "No fixed list was given. Listen, remember what they volunteer, and do not invent a form."
        )
    lines.append(
        "You do not need every one of these before you help. Once you have enough, stop asking."
    )
    for state in flow["states"]:
        lines.append(f"{state['title']}. {state['do']}")
    lines.append("Situations you should already know how to handle.")
    for branch in flow["branches"]:
        lines.append(f"When {branch['when']} {branch['do']}")
    if flow["tools"]:
        lines.append("What you can actually do.")
        for tool in flow["tools"]:
            lines.append(f"{tool['id']}. {tool['description']}")
    lines.append(flow["research"]["not_included"])
    return "\n\n".join(lines)
