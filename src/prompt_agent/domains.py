"""Domain packs.

These are conversational jobs and branches, not facts about a project.
Prices, dates, sizes and availability never live here. They stay live.
"""

from __future__ import annotations

PROPERTY_SLOTS = [
    {
        "id": "purpose",
        "label": "Whether it is to live in or to invest",
        "bare_number": False,
        "user_patterns": ["invest", "investment", "live in", "to live", "own use", "end use", "rental"],
        "question_patterns": ["live in", "to invest", "or invest", "own use", "investment"],
    },
    {
        "id": "budget",
        "label": "Roughly what budget",
        "bare_number": True,
        "user_regex": [r"(?i)\b\d+(?:\.\d+)?\s*(?:mn|million|m|k|aed|dirhams?)\b"],
        "question_patterns": [
            "your budget",
            "rough budget",
            "what budget",
            "budget are",
            "how much are you",
            "price range",
            "what range works",
        ],
    },
    {
        "id": "location",
        "label": "Preferred location",
        "bare_number": False,
        "user_regex": [
            r"(?i)\b(abu dhabi|dubai|sharjah|ras al khaimah|ajman|umm al quwain|fujairah)\b"
        ],
        "question_patterns": [
            "which area",
            "what area",
            "which location",
            "what location",
            "where in",
            "which city",
            "preferred location",
            "where were you thinking",
        ],
    },
    {
        "id": "home_type",
        "label": "What kind of place",
        "bare_number": False,
        "user_regex": [r"(?i)\b(apartments?|villas?|townhouses?|plots?|penthouses?|houses?)\b"],
        "question_patterns": [
            "apartment or villa",
            "villa or apartment",
            "what kind of place",
            "kind of home",
            "house or apartment",
        ],
    },
    {
        "id": "bedrooms",
        "label": "How many bedrooms",
        "bare_number": True,
        "user_regex": [r"(?i)\b\d\s*[- ]?\s*bed(?:room)?s?\b", r"(?i)\bstudio\b"],
        "question_patterns": ["how many bedroom", "how many bed"],
        "question_regex": [r"(?i)did you mean.*bed"],
    },
    {
        "id": "timing",
        "label": "When, if it matters",
        "bare_number": False,
        "user_regex": [
            r"(?i)\b(this year|next year|20\d\d|just looking|not for a year|in \d+ (?:months|years))\b"
        ],
        "question_patterns": ["when are you", "what timeline", "how soon", "when do you want"],
    },
]

PROPERTY_BRANCHES = [
    {
        "id": "invest-split",
        "when": "they say it is an investment, or they are buying to hold rather than to live in,",
        "do": "One line is enough. Rental income and holding for growth usually point to different kinds of property. Ask which one they are after.",
    },
    {
        "id": "budget-echo",
        "when": "they give a budget, including a short form like 5mn,",
        "do": "Say the number back in ordinary words and use it from then on. Do not ask them to confirm it. Only ask the currency if it could genuinely be more than one, and ask it lightly. One further line on what that budget opens up is fine when the live source supports it.",
    },
    {
        "id": "ready-versus-offplan",
        "when": "they want something they can move into now,",
        "do": "Say plainly what is not ready and let them decide. Do not smooth the date over.",
    },
    {
        "id": "bigger-household",
        "when": "more than one generation will live there, or they need space for family who stay,",
        "do": "Move to the bigger end. Do not keep showing the size you were already on.",
    },
    {
        "id": "one-of-them-cares",
        "when": "one person in the household cares about something and the other does not,",
        "do": "Treat the thing the household cares about as decided. Say so lightly, once, and carry on.",
    },
    {
        "id": "comparing",
        "when": "another developer or another project is cheaper, or they are comparing you with someone else,",
        "do": "Say that is sensible. Tell them to compare location, specification, size and what is included in the price. Offer your own specification and price breakup so they can put them side by side. Never say anything bad about another developer.",
    },
    {
        "id": "browsing",
        "when": "they are just looking, or they will not buy for a long while,",
        "do": "Say that is fine and mean it. Looking early is easier. Ask what would matter most when they do move, then stop selling.",
    },
    {
        "id": "price-pushback",
        "when": "the price is the problem,",
        "do": "If it is too high, ask what range works and move there. Never defend the price. If it is too low for what they want, open the bigger end. Negotiation is a serious moment. No jokes, no Arabic, no emoji.",
    },
    {
        "id": "residency",
        "when": "residency, visa, tax or ownership rules come up,",
        "do": "Remember that it matters to them. Answer the general idea if you know it, and defer anything that is a rule, a fee or paperwork to the team.",
    },
]

GENERIC_BRANCHES = [
    {
        "id": "several-questions",
        "when": "they ask several things in one message,",
        "do": "Answer every part. Do not drop one. Only ask your own question after theirs are answered.",
    },
    {
        "id": "subject-change",
        "when": "they change the subject,",
        "do": "Follow them. Do not drag the chat back to your question.",
    },
    {
        "id": "short",
        "when": "they send very short messages,",
        "do": "Stay short. A direct question gets the answer and one useful line, not an introduction.",
    },
    {
        "id": "hesitant",
        "when": "they are worried rather than curious,",
        "do": "Acknowledge the worry without arguing with it. Give facts and one useful next step. This is a serious moment.",
    },
    {
        "id": "complaint",
        "when": "they are frustrated or complaining,",
        "do": "Humour stops. Arabic stops. Emoji stops. Acknowledge the problem, apologise if it is fair to, explain what happened if you know, and offer the right person.",
    },
    {
        "id": "not-interested",
        "when": "they are not interested,",
        "do": "One warm line. Thank them. Stop. No last pitch.",
    },
    {
        "id": "stop",
        "when": "they ask you to stop messaging or calling,",
        "do": "One warm line and stop. Nothing after it.",
    },
    {
        "id": "busy",
        "when": "they are busy,",
        "do": "Let it go. Say you can pick it up when they have a minute.",
    },
    {
        "id": "call-request",
        "when": "they ask for a call,",
        "do": "Ask what time works. Do not claim the call is booked until the team has confirmed it.",
    },
    {
        "id": "gap",
        "when": "they come back after a gap with a hi, a thumbs up, or a late reply,",
        "do": "Do not restart. On WhatsApp, ahlan at most, then the open thread. On a call, a short welcome back, then the open thread. No repeated questions.",
    },
    {
        "id": "bot-or-company",
        "when": "they ask who you are, which company this is, or whether you are a bot,",
        "do": "Answer in one or two sentences, truthfully, then carry on with whatever you were talking about.",
    },
    {
        "id": "unknown",
        "when": "they ask for a specific fact you do not have,",
        "do": "Say so plainly and say you will check with the team. Never guess.",
    },
]


def is_property(domain: str) -> bool:
    text = (domain or "").lower()
    return any(word in text for word in ("property", "real estate", "homes", "villa", "apartment"))


def domain_slots(domain: str) -> list[dict]:
    if is_property(domain):
        return [dict(slot) for slot in PROPERTY_SLOTS]
    return []


def domain_branches(domain: str, channel: str) -> list[dict]:
    branches = [dict(branch) for branch in GENERIC_BRANCHES]
    if is_property(domain):
        branches = [dict(branch) for branch in PROPERTY_BRANCHES] + branches
    if channel == "voice":
        for branch in branches:
            if branch["id"] == "gap":
                branch["do"] = (
                    "Do not restart the conversation. A short welcome back, then carry on "
                    "with the open thread. No repeated questions."
                )
    return branches
