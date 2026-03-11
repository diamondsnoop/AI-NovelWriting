from __future__ import annotations

import argparse
import json

from novelos.foundation.config import load_config
from novelos.foundation.logging import configure_logging
from novelos.foundation.project_locator import resolve_project_root
from novelos.workflow.init_flow import run_init
from novelos.workflow.learn_flow import run_learn
from novelos.workflow.plan_flow import run_plan
from novelos.workflow.query_flow import run_query
from novelos.workflow.resume_flow import run_resume
from novelos.workflow.write_flow import run_write


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="novel")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("title")
    init_parser.add_argument("--root", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--project", required=True)
    plan_parser.add_argument("--chapter", type=int, required=True)

    write_parser = subparsers.add_parser("write")
    write_parser.add_argument("--project", required=True)
    write_parser.add_argument("--chapter", type=int, required=True)
    write_parser.add_argument("--on-conflict", choices=["overwrite", "abort"])

    resume_parser = subparsers.add_parser("resume")
    resume_parser.add_argument("--project", required=True)

    learn_parser = subparsers.add_parser("learn")
    learn_parser.add_argument("--project", required=True)
    learn_parser.add_argument("--type", required=True)
    learn_parser.add_argument("--content", required=True)
    learn_parser.add_argument("--source-ref", action="append", default=[])

    query_parser = subparsers.add_parser("query")
    query_parser.add_argument("--project", required=True)
    query_parser.add_argument(
        "--type",
        required=True,
        choices=[
            "project",
            "progress",
            "tasks",
            "snapshots",
            "decisions",
            "entities",
            "relationships",
            "foreshadowing",
            "summaries",
            "project_memory",
            "status_report",
            "dashboard",
        ],
    )
    return parser


def main() -> None:
    configure_logging()
    config = load_config()
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        result = run_init(resolve_project_root(args.root), args.title)
    elif args.command == "plan":
        result = run_plan(
            project_root=resolve_project_root(args.project),
            chapter_no=args.chapter,
            provider=config.llm_provider,
            model_name=config.model_name,
            base_url=config.base_url,
            api_mode=config.api_mode,
            timeout_seconds=config.plan_timeout_seconds,
            max_retries=config.max_retries,
        )
    elif args.command == "write":
        result = run_write(
            project_root=resolve_project_root(args.project),
            chapter_no=args.chapter,
            provider=config.llm_provider,
            model_name=config.model_name,
            base_url=config.base_url,
            api_mode=config.api_mode,
            write_timeout_seconds=config.write_timeout_seconds,
            write_max_retries=config.write_max_retries,
            review_timeout_seconds=config.review_timeout_seconds,
            summary_timeout_seconds=config.summary_timeout_seconds,
            extraction_timeout_seconds=config.extraction_timeout_seconds,
            character_profile_timeout_seconds=config.character_profile_timeout_seconds,
            write_target_chars=config.write_target_chars,
            max_retries=config.max_retries,
            on_conflict=args.on_conflict,
        )
    elif args.command == "resume":
        result = run_resume(resolve_project_root(args.project))
    elif args.command == "learn":
        result = run_learn(
            project_root=resolve_project_root(args.project),
            memory_type=args.type,
            content=args.content,
            source_refs=args.source_ref,
        )
    elif args.command == "query":
        result = run_query(resolve_project_root(args.project), args.type)
    else:
        raise ValueError(f"Unsupported command: {args.command}")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
