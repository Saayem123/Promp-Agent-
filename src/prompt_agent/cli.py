"""Command line for the prompt agent."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from prompt_agent.brief import load_brief
from prompt_agent.compile import compile_prompt
from prompt_agent.extract import ingest_file
from prompt_agent.flow import build_flow
from prompt_agent.library import append_rules, channel_path, find_root, iter_rules, load
from prompt_agent.review import learned_rules, render_report, review_turns


def _load_turns(path: Path) -> list[dict]:
    turns = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        if "role" not in item or "text" not in item:
            raise SystemExit(f"{path} has a line without role and text.")
        turns.append({"role": item["role"], "text": item["text"]})
    return turns


def _cmd_nuances(args: argparse.Namespace) -> int:
    root = find_root()
    channel = args.channel
    channels = ["whatsapp", "voice"] if channel == "all" else [channel]
    for name in channels:
        path = channel_path(root, name)
        data = load(path)
        rules = iter_rules(data)
        hard = sum(1 for rule in rules if rule.get("kind") == "hard")
        print(f"{path.relative_to(root)}: {len(rules)} nuances, {hard} hard, {len(data.get('added') or [])} learned")
    return 0


def _cmd_compile(args: argparse.Namespace) -> int:
    root = find_root()
    brief = load_brief(Path(args.brief))
    library = load(channel_path(root, brief["channel"]))
    prompt = compile_prompt(brief, library)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(prompt, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(prompt, end="")
    return 0


def _cmd_flow(args: argparse.Namespace) -> int:
    brief = load_brief(Path(args.brief))
    flow = build_flow(brief)
    text = yaml.safe_dump(flow, sort_keys=False, allow_unicode=True, width=88)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        print(f"Wrote {out}")
    else:
        print(text, end="")
    return 0


def _cmd_build(args: argparse.Namespace) -> int:
    root = find_root()
    brief = load_brief(Path(args.brief))
    library = load(channel_path(root, brief["channel"]))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    prompt_path = out / f"{brief['id']}.md"
    flow_path = out / f"{brief['id']}.flow.yaml"
    prompt_path.write_text(compile_prompt(brief, library), encoding="utf-8")
    flow_path.write_text(
        yaml.safe_dump(build_flow(brief), sort_keys=False, allow_unicode=True, width=88),
        encoding="utf-8",
    )
    print(f"Wrote {prompt_path}")
    print(f"Wrote {flow_path}")
    return 0


def _cmd_ingest(args: argparse.Namespace) -> int:
    root = find_root()
    target = channel_path(root, args.channel)
    mirror = channel_path(root, "voice" if args.channel == "whatsapp" else "whatsapp") if args.mirror else None
    result = ingest_file(target, Path(args.instructions), mirror_to=mirror)
    print(f"Saved {len(result['saved'])} new nuances to {target.relative_to(root)}")
    for rule in result["saved"]:
        print(f"  {rule['id']}")
    if mirror is not None:
        print(f"Mirrored {len(result['mirrored'])} to {mirror.relative_to(root)}")
    if not result["saved"]:
        print("Nothing new. Those nuances were already covered.")
    return 0


def _cmd_review(args: argparse.Namespace) -> int:
    root = find_root()
    brief = load_brief(Path(args.brief))
    path = channel_path(root, brief["channel"])
    library = load(path)
    turns = _load_turns(Path(args.transcript))
    findings = review_turns(brief, library, turns)
    print(render_report(findings), end="")
    if args.apply and findings:
        rules = learned_rules(findings, origin=str(Path(args.transcript)))
        written = append_rules(path, rules)
        print(f"Saved {written} learned nuances to {path.relative_to(root)}")
        if args.recompile:
            library = load(path)
            out = Path(args.recompile)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(compile_prompt(brief, library), encoding="utf-8")
            print(f"Rewrote {out}")
    return 1 if args.strict and findings else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="prompt-agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    nuances = sub.add_parser("nuances", help="Show how many nuances are saved on each channel.")
    nuances.add_argument("--channel", choices=["whatsapp", "voice", "all"], default="all")
    nuances.set_defaults(func=_cmd_nuances)

    compile_ = sub.add_parser("compile", help="Compile a brief into a system prompt.")
    compile_.add_argument("brief")
    compile_.add_argument("-o", "--out")
    compile_.set_defaults(func=_cmd_compile)

    flow = sub.add_parser("flow", help="Research the brief into an end-to-end conversation flow.")
    flow.add_argument("brief")
    flow.add_argument("-o", "--out")
    flow.set_defaults(func=_cmd_flow)

    build = sub.add_parser("build", help="Write both the prompt and the flow for a brief.")
    build.add_argument("brief")
    build.add_argument("-o", "--out", required=True)
    build.set_defaults(func=_cmd_build)

    ingest = sub.add_parser("ingest", help="Save new nuances from an instruction file.")
    ingest.add_argument("instructions")
    ingest.add_argument("--channel", choices=["whatsapp", "voice"], required=True)
    ingest.add_argument(
        "--mirror",
        action="store_true",
        help="Also save channel-neutral rules onto the other channel.",
    )
    ingest.set_defaults(func=_cmd_ingest)

    review = sub.add_parser("review", help="Check a transcript and optionally update the nuance file.")
    review.add_argument("--brief", required=True)
    review.add_argument("--transcript", required=True)
    review.add_argument("--apply", action="store_true")
    review.add_argument("--recompile")
    review.add_argument("--strict", action="store_true")
    review.set_defaults(func=_cmd_review)

    args = parser.parse_args(argv)
    return args.func(args)
