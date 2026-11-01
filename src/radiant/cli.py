"""Command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters.scripted import ScriptedAdapter
from .dataset import load_jsonl
from .runner import run_evaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="radiant", description="Evaluate evidence-sensitive LLM tutoring.")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a JSONL scenario dataset.")
    validate.add_argument("dataset", type=Path)

    evaluate = sub.add_parser("evaluate", help="Run an evaluation.")
    evaluate.add_argument("dataset", type=Path)
    evaluate.add_argument("--adapter", choices=["scripted", "openai-compatible"], default="scripted",
                          help="scripted is only a pipeline smoke test; openai-compatible calls a configured API")
    evaluate.add_argument("--output", type=Path, default=Path("results/demo"))

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "validate":
        scenarios = load_jsonl(args.dataset)
        print(json.dumps({"valid": True, "scenario_count": len(scenarios)}, indent=2))
        return
    if args.command == "evaluate":
        if args.adapter == "scripted":
            adapter = ScriptedAdapter()
        else:
            from .adapters.openai_compatible import OpenAICompatibleAdapter
            adapter = OpenAICompatibleAdapter()
        report = run_evaluation(args.dataset, adapter, args.output)
        print(json.dumps({"output": str(args.output), "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
