# Modon WhatsApp property assistant

This file is the instruction source for `nuances/whatsapp.yaml`.

**Deployed system prompt:** [`../prompts/modon-khalid-whatsapp.md`](../prompts/modon-khalid-whatsapp.md)  
**Authoritative prose (full brief you supplied):** [`modon-whatsapp-authored-prompt.md`](modon-whatsapp-authored-prompt.md)

The repo keeps three layers in sync:

1. `modon-whatsapp-authored-prompt.md` — your full prompt text (Modon Real Estate / Khalid).
2. `nuances/whatsapp.yaml` — craft rules the prompt agent merges into every WhatsApp brief.
3. `prompts/modon-khalid-whatsapp.md` — compiled prompt for `examples/modon-property.brief.yaml`.

To rebuild after edits to the YAML:

```bash
pip install -e .
prompt-agent build examples/modon-property.brief.yaml -o prompts
```

**Synced 2026-11-08** with your latest brief, including:

- Hard rule: introduce yourself once; no exclamation marks anywhere.
- First message after the WhatsApp template (four parts, no project on message one).
- After message one: no Hi, no re-intro, no name again, no “Modon’s assistant” opener unless they ask if you are a bot.
- When not to use the project shape (definitions, locations, how-it-works).
- If they ask the same thing twice.
- Expanded Arabic placement, density, mafi mushkil / zain, and misuse examples.
