from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="md-man")
    parser.add_argument("root_path", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
