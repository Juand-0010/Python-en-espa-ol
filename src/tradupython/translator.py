"""Convierte construcciones comunes de Python en explicaciones en español."""

from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path


class TranslationError(ValueError):
    """Error al analizar el código Python de entrada."""


def _expression(node: ast.AST) -> str:
    """Describe una expresión sin intentar traducir nombres o cadenas."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f"la cadena {node.value!r}"
        if node.value is None:
            return "el valor None (ausencia de valor)"
        if node.value is True:
            return "el valor verdadero (True)"
        if node.value is False:
            return "el valor falso (False)"
        return f"el valor {node.value!r}"
    if isinstance(node, ast.Name):
        return f"la variable «{node.id}»"
    if isinstance(node, ast.BinOp):
        operators = {
            ast.Add: "más", ast.Sub: "menos", ast.Mult: "por",
            ast.Div: "dividido entre", ast.FloorDiv: "dividido entre (redondeando hacia abajo)",
            ast.Mod: "módulo", ast.Pow: "elevado a",
        }
        op = operators.get(type(node.op), ast.unparse(node.op))
        return f"({_expression(node.left)} {op} {_expression(node.right)})"
    if isinstance(node, ast.Compare):
        operators = {
            ast.Eq: "es igual a", ast.NotEq: "es distinto de", ast.Lt: "es menor que",
            ast.LtE: "es menor o igual que", ast.Gt: "es mayor que", ast.GtE: "es mayor o igual que",
            ast.In: "está dentro de", ast.NotIn: "no está dentro de", ast.Is: "es", ast.IsNot: "no es",
        }
        bits = [_expression(node.left)]
        for op, comparator in zip(node.ops, node.comparators):
            bits.extend((operators.get(type(op), "se compara con"), _expression(comparator)))
        return " ".join(bits)
    if isinstance(node, ast.Call):
        args = ", ".join(_expression(arg) for arg in node.args)
        return f"la llamada a «{ast.unparse(node.func)}»" + (f" con {args}" if args else "")
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        label = {ast.List: "lista", ast.Tuple: "tupla", ast.Set: "conjunto"}[type(node)]
        return f"una {label} con {len(node.elts)} elemento(s)"
    if isinstance(node, ast.Dict):
        return f"un diccionario con {len(node.keys)} elemento(s)"
    if isinstance(node, ast.Subscript):
        return f"el elemento indicado por {_expression(node.slice)} dentro de {_expression(node.value)}"
    if isinstance(node, ast.Attribute):
        return f"el atributo «{node.attr}» de {_expression(node.value)}"
    if isinstance(node, ast.UnaryOp):
        op = "no" if isinstance(node.op, ast.Not) else "menos" if isinstance(node.op, ast.USub) else "más"
        return f"{op} {_expression(node.operand)}"
    if isinstance(node, ast.BoolOp):
        joiner = " y " if isinstance(node.op, ast.And) else " o "
        return joiner.join(_expression(value) for value in node.values)
    return f"la expresión «{ast.unparse(node)}»"


def _indent(level: int) -> str:
    return "  " * level


def _target_names(target: ast.AST) -> list[str]:
    """Obtiene los nombres asignados, incluso en desempaquetado."""
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        return [name for item in target.elts for name in _target_names(item)]
    return []


def _variable_report(tree: ast.Module) -> list[str]:
    """Resume dónde aparecen los nombres y cómo se asignan en el módulo."""
    stores: Counter[str] = Counter()
    loads: Counter[str] = Counter()
    first_values: dict[str, ast.AST] = {}
    annotated: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if isinstance(node.ctx, ast.Store):
                stores[node.id] += 1
            elif isinstance(node.ctx, ast.Load):
                loads[node.id] += 1
        elif isinstance(node, ast.AnnAssign):
            annotated.update(_target_names(node.target))

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                for name in _target_names(target):
                    first_values.setdefault(name, node.value)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)) and node.value is not None:
            for name in _target_names(node.target):
                first_values.setdefault(name, node.value)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            for name in _target_names(node.target):
                first_values.setdefault(name, node.iter)

    lines = [
        "Variables en Python:",
        "- No hace falta declarar una variable antes de usarla: se crea al asignarle un valor.",
        "- Conviene elegir nombres descriptivos y asignar un valor antes de leer la variable.",
        "- Añadir un tipo (por ejemplo, edad: int = 18) es opcional; ayuda a documentar la intención y a algunas herramientas.",
    ]
    names = sorted(stores)
    if not names:
        lines.append("Este código no asigna variables con nombres simples.")
        return lines

    lines.append("Variables encontradas:")
    for name in names:
        use_count = loads[name]
        assignments = stores[name]
        value = first_values.get(name)
        detail = f"«{name}» se asigna {assignments} vez/veces"
        if value is not None:
            detail += f", empezando con {_expression(value)}"
        detail += f"; se lee {use_count} vez/veces"
        if use_count == 0:
            detail += ". No aparece leída en este código; revisa si la asignación hace falta"
        elif assignments > 1:
            detail += ". Se reasigna; comprueba que cada cambio sea intencional"
        else:
            detail += ". Su uso está respaldado por una lectura posterior"
        if name in annotated:
            detail += ". Tiene una anotación de tipo, que Python no exige para crearla"
        lines.append(f"- {detail}.")
    return lines


def _statements(nodes: list[ast.stmt], level: int = 0) -> list[str]:
    lines: list[str] = []
    pad = _indent(level)
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            params = ", ".join(arg.arg for arg in node.args.args) or "ninguno"
            kind = "función asíncrona" if isinstance(node, ast.AsyncFunctionDef) else "función"
            lines.append(f"{pad}Define la {kind} «{node.name}» con parámetros: {params}.")
            lines.extend(_statements(node.body, level + 1))
        elif isinstance(node, ast.ClassDef):
            lines.append(f"{pad}Define la clase «{node.name}».")
            lines.extend(_statements(node.body, level + 1))
        elif isinstance(node, ast.Assign):
            targets = ", ".join(ast.unparse(target) for target in node.targets)
            lines.append(f"{pad}Guarda {_expression(node.value)} en «{targets}».")
        elif isinstance(node, ast.AnnAssign):
            value = f" con {_expression(node.value)}" if node.value else ""
            lines.append(f"{pad}Declara «{ast.unparse(node.target)}» como «{ast.unparse(node.annotation)}»{value}.")
        elif isinstance(node, ast.AugAssign):
            lines.append(f"{pad}Actualiza «{ast.unparse(node.target)}» aplicándole {ast.unparse(node.op)} y {_expression(node.value)}.")
        elif isinstance(node, ast.If):
            lines.append(f"{pad}Si {_expression(node.test)}:")
            lines.extend(_statements(node.body, level + 1) or [f"{_indent(level + 1)}No hace nada."])
            if node.orelse:
                label = "Si no:" if len(node.orelse) != 1 or not isinstance(node.orelse[0], ast.If) else "Si no, si:"
                lines.append(f"{pad}{label}")
                lines.extend(_statements(node.orelse, level + 1))
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            lines.append(f"{pad}Para cada elemento de {_expression(node.iter)}, lo guarda en «{ast.unparse(node.target)}» y:")
            lines.extend(_statements(node.body, level + 1) or [f"{_indent(level + 1)}No hace nada."])
            if node.orelse:
                lines.append(f"{pad}Al terminar el ciclo sin interrupciones:")
                lines.extend(_statements(node.orelse, level + 1))
        elif isinstance(node, ast.While):
            lines.append(f"{pad}Mientras {_expression(node.test)}:")
            lines.extend(_statements(node.body, level + 1) or [f"{_indent(level + 1)}No hace nada."])
        elif isinstance(node, ast.Return):
            lines.append(f"{pad}Devuelve {_expression(node.value)}." if node.value else f"{pad}Termina la función sin devolver un valor.")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            lines.append(f"{pad}Ejecuta {_expression(node.value)}.")
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            lines.append(f"{pad}Texto de documentación: {node.value.value.strip()}")
        elif isinstance(node, ast.Pass):
            lines.append(f"{pad}No hace nada en este punto.")
        elif isinstance(node, ast.Break):
            lines.append(f"{pad}Sale del ciclo actual.")
        elif isinstance(node, ast.Continue):
            lines.append(f"{pad}Salta a la siguiente vuelta del ciclo.")
        elif isinstance(node, ast.Raise):
            lines.append(f"{pad}Lanza el error {_expression(node.exc)}.")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.append(f"{pad}Importa «{ast.unparse(node)}».")
        else:
            lines.append(f"{pad}Instrucción Python: «{ast.unparse(node)}».")
    return lines


def explain(source: str, *, topic: str | None = None) -> str:
    """Devuelve una explicación en español; ``topic='variables'`` resume variables."""
    if topic not in (None, "variables"):
        raise ValueError("Tema no disponible. Por ahora puedes usar 'variables'.")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        where = f" en la línea {exc.lineno}" if exc.lineno else ""
        raise TranslationError(f"No se pudo analizar el código{where}: {exc.msg}") from exc
    if topic == "variables":
        return "\n".join(_variable_report(tree))
    return "\n".join([*_variable_report(tree), "", "Explicación del código:", *_statements(tree.body)]) or "El programa está vacío."


def explain_file(path: str | Path) -> str:
    """Lee y explica un archivo Python en UTF-8."""
    return explain(Path(path).read_text(encoding="utf-8"))
