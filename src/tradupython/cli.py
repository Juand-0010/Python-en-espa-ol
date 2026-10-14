"""Interfaz de línea de comandos de TraduPython."""

import argparse
import sys
from pathlib import Path

from .translator import TranslationError, explain, translate


def main() -> int:
    parser = argparse.ArgumentParser(description="Explica código Python en español.")
    parser.add_argument("archivo", help="archivo .py que quieres entender")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tema", choices=("variables", "expresiones", "decisiones", "funciones", "colecciones", "clases", "errores"), help="explica solo el tema indicado")
    mode.add_argument("--traducir", action="store_true", help="convierte el vocabulario español a código Python")
    parser.add_argument("--lineas", action="store_true", help="numera las líneas de la explicación generada")
    args = parser.parse_args()
    try:
        source = Path(args.archivo).read_text(encoding="utf-8")
        if args.traducir:
            if args.lineas:
                parser.error("--lineas solo se usa al explicar código")
            print(translate(source))
            return 0
        result = explain(source, topic=args.tema)
        if args.lineas:
            result = "\n".join(f"{index:>3}: {line}" for index, line in enumerate(result.splitlines(), start=1))
        print(result)
    except (OSError, UnicodeError, TranslationError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
