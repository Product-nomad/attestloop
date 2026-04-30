"""CLI entrypoint. The actual orchestration lives in
`attestloop.orchestration`; this module is the argparse + .env shell
plus the top-level `run()` function that builds the initial state and
invokes the compiled graph."""
import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console

from attestloop.fetch import EmptyPublicationError
from attestloop.orchestration import PipelineState, build_pipeline_graph
from attestloop.registry import get_framework, get_regulation
from attestloop.runs import create_run_dir

_console = Console()


def run(url: str, regulation_id: str, framework_id: str) -> Path:
    """Execute the pipeline against a single URL and return the path to
    the rendered report.md. Raises EmptyPublicationError if the fetch
    step produced nothing usable; other LLM/IO errors propagate from
    the underlying agents."""
    run_id, started_at, run_dir = create_run_dir()
    initial_state: PipelineState = {
        "url": url,
        "regulation_id": regulation_id,
        "framework_id": framework_id,
        "run_dir": run_dir,
        "run_id": run_id,
        "started_at": started_at,
        "regulation": get_regulation(regulation_id),
        "framework": get_framework(framework_id),
    }

    graph = build_pipeline_graph()
    final_state = graph.invoke(initial_state)
    return final_state["report_path"]


def main(argv: list[str] | None = None) -> int:
    # Auto-load .env from CWD or any parent before constructing any Anthropic
    # client. No-op if the file is absent.
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "error: ANTHROPIC_API_KEY is not set.\n"
            "Copy .env.example to .env and paste your key, e.g.:\n"
            "    cp .env.example .env\n"
            "    # then edit .env and set ANTHROPIC_API_KEY=sk-ant-...\n"
            "Or export ANTHROPIC_API_KEY in your shell before running.",
            file=sys.stderr,
        )
        return 2

    parser = argparse.ArgumentParser(
        prog="attestloop",
        description="Run the Attestloop attestation pipeline against a single URL.",
    )
    parser.add_argument("url", help="URL of the regulator publication to assess.")
    parser.add_argument(
        "--regulation",
        default="eu_ai_act",
        help="Regulation registry id (default: eu_ai_act).",
    )
    parser.add_argument(
        "--framework",
        default="nist_ai_rmf",
        help="Framework registry id (default: nist_ai_rmf).",
    )
    args = parser.parse_args(argv)

    try:
        with _console.status("Running pipeline..."):
            report_path = run(args.url, args.regulation, args.framework)
    except EmptyPublicationError as e:
        print(
            "error: Fetched page returned no usable content. The page may be "
            "JavaScript-rendered or behind a redirect. Try the document's "
            "canonical PDF URL or the publishing body's hosted version.\n\n"
            f"{e}",
            file=sys.stderr,
        )
        return 3

    print(report_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
