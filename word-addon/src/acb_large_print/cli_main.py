"""CLI-only entry point: never launches the GUI."""

from __future__ import annotations

import sys


def main() -> None:
    from .cli import main as cli_main
    sys.exit(cli_main(force_cli=True))


if __name__ == "__main__":
    main()
