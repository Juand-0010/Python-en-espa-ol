"""Interfaz de línea de comandos de TraduPython."""

import argparse
import sys

from .translator import TranslationError, explain_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Explica código Python en español.")
    parser.add_argument("archivo", help="archivo .py que quieres entender")
    parser.add_argument("--tema", choices=("variables", "expresiones"), help="explica solo el tema indicado")
    args = parser.parse_args()
    try:
        if args.tema:
            from pathlib import Path

            from .translator import explain

            print(explain(Path(args.archivo).read_text(encoding="utf-8"), topic=args.tema))
        else:
            print(explain_file(args.archivo))
    except (OSError, UnicodeError, TranslationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
