"""Entry point: ``python -m acb_large_print`` or double-click the .exe."""

from __future__ import annotations

import sys


def main() -> None:
    from acb_large_print.cli import main as cli_main

    sys.exit(cli_main())


if __name__ == "__main__":
    main()
