from __future__ import annotations

import argparse
from pathlib import Path

from automation_pcaps.config import ensure_dirs, load_config
from automation_pcaps.health import assert_startup_checks
from automation_pcaps.pipeline import Pipeline
from automation_pcaps.state import StateStore
from automation_pcaps.web_server import AutomationServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local PCAP automation runner with web UI")
    parser.add_argument("--config", required=True, help="Path to config JSON")
    parser.add_argument("--no-start", action="store_true", help="Serve the UI with the worker stopped")
    parser.add_argument("--skip-checks", action="store_true", help="Do not check repo paths or tshark at startup")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(Path(args.config))
    ensure_dirs(cfg)
    if not args.skip_checks:
        assert_startup_checks(cfg)

    store = StateStore(cfg.state_db_path)
    pipeline = Pipeline(cfg, store)
    if not args.no_start:
        pipeline.start()

    server = AutomationServer(cfg, store, pipeline)
    print(f"PCAP automation UI: http://{cfg.host}:{cfg.port}")
    print(f"Workspace: {cfg.workspace_dir}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        pipeline.shutdown()
        server.server_close()
    return 0

