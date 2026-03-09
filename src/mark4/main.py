from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Callable, Protocol

from mark4.app import MarkdownBrowserApp
from mark4.translator import clear_translation_cache


class RunnableApp(Protocol):
    def run(self) -> object: ...


def parse_args(argv: list[str] | None = None) -> Namespace:
    parser = ArgumentParser(prog="mark4")
    parser.add_argument(
        "--no-translate",
        action="store_true",
        help="Disable external translation requests",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable persistent translation cache",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear persistent translation cache and exit",
    )
    parser.add_argument("root_path", type=Path)
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    app_factory: Callable[..., RunnableApp] = MarkdownBrowserApp,
) -> int:
    args = parse_args(argv)
    if args.clear_cache:
        clear_translation_cache()
        return 0

    app = app_factory(
        str(args.root_path),
        translation_enabled=not args.no_translate,
        persistent_cache_enabled=not args.no_cache,
    )
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
