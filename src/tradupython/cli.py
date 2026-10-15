"""Interfaz de línea de comandos de TraduPython."""

import argparse
import subprocess
import sys
from pathlib import Path

from .translator import TranslationError, explain, translate


def main() -> int:
    parser = argparse.ArgumentParser(description="Traduce código español a Python o explica código Python.")
    parser.add_argument("archivo", help="archivo .py que quieres entender")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tema", choices=("variables", "expresiones", "decisiones", "funciones", "colecciones", "clases", "errores"), help="explica solo el tema indicado")
    mode.add_argument("--traducir", action="store_true", help="convierte el vocabulario español a código Python")
    mode.add_argument("--ejecutar", action="store_true", help="traduce y ejecuta el programa; úsalo solo con código de confianza")
    parser.add_argument("--lineas", action="store_true", help="numera las líneas de la explicación generada")
    args = parser.parse_args()
    try:
        source = Path(args.archivo).read_text(encoding="utf-8")
        if args.traducir or args.ejecutar:
            if args.lineas:
                parser.error("--lineas solo se usa al explicar código")
            translated = translate(source)
            if args.ejecutar:
                completed = subprocess.run([sys.executable, "-c", translated], cwd=Path(args.archivo).resolve().parent, check=False)
                return completed.returncode
            print(translated)
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
