# Prompt Agent

Builds a WhatsApp or phone prompt that already knows how to talk like a person.

Two files hold the craft. Every new prompt on that channel inherits them.

- `nuances/whatsapp.yaml` is how a WhatsApp chat should behave.
- `nuances/voicebot.yaml` is the same judgement, rebuilt for a live call.

Hard rules never bend. They cover truth, confirmation, guarantees, and not pretending to be a human. Everything else is the normal way of talking, and it bends when the person in front of you needs something different.

The first set was taken from the Modon property assistant brief in `examples/modon-whatsapp-instructions.md`. Prices, dates and availability are not stored. Those stay in the live source the assistant is told to use.

## Write a prompt

A brief is who the assistant is, what they are deciding, and which facts they may not guess. The domain pack adds the conversation around that. For property, that includes live-in versus investment, a budget said back in plain words, and one project at a time.

```bash
pip install -e .
prompt-agent build examples/modon-property.brief.yaml -o prompts
prompt-agent build examples/modon-voice.brief.yaml -o prompts
```

`prompt-agent compile` writes only the prompt. `prompt-agent flow` writes only the end-to-end flow. The flow is a guide. The person outranks it. A hard rule outranks the person.

`examples/clinic-front-desk.brief.yaml` is a non-property brief on the same WhatsApp file, so the craft carries over without the property slots.

## Save a new instruction

When a new instruction arrives, save the nuances that are not already covered. The next prompt on that channel picks them up.

```bash
prompt-agent ingest path/to/instructions.md --channel whatsapp --mirror
```

`--mirror` copies rules that are not tied to one channel onto the other file, with a line saying whether they apply on a call or on WhatsApp. A rule about emoji stays on WhatsApp. A rule about barge-in stays on voice.

## Update from a transcript

A transcript is JSONL. Each line has `role` (`user` or `assistant`) and `text`.

```bash
prompt-agent review \
  --brief examples/modon-property.brief.yaml \
  --transcript examples/transcripts/reask.jsonl \
  --apply \
  --recompile prompts/modon-khalid-whatsapp.md
```

The review catches a question asked again, a bare number read against the wrong question, an exclamation mark, a selling word, a visit said to be confirmed, a guarantee, a written-out contraction, a chase message, and a pitch after they asked you to stop. `--apply` appends one learned nuance per broken rule under `added` in the channel file. The compiled prompt then includes them.

Learned lines accumulate. They are how a later conversation changes the next prompt.
