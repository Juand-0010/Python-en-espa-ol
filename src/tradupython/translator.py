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
        keywords = ", ".join(f"{item.arg}={_expression(item.value)}" for item in node.keywords)
        all_args = ", ".join(part for part in (args, keywords) if part)
        return f"la llamada a «{ast.unparse(node.func)}»" + (f" con {all_args}" if all_args else "")
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
    if isinstance(node, ast.IfExp):
        return f"{_expression(node.body)} si {_expression(node.test)}; de lo contrario {_expression(node.orelse)}"
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


def _describe_expression(node: ast.AST) -> str:
    """Explica qué operación realiza una expresión y qué resultado produce."""
    if isinstance(node, ast.BinOp):
        actions = {
            ast.Add: "suma o concatena", ast.Sub: "resta", ast.Mult: "multiplica o repite",
            ast.Div: "divide y produce un número decimal", ast.FloorDiv: "divide y redondea hacia abajo",
            ast.Mod: "obtiene el residuo de la división", ast.Pow: "eleva a una potencia",
            ast.BitAnd: "combina los bits con AND", ast.BitOr: "combina los bits con OR",
            ast.BitXor: "combina los bits con XOR", ast.LShift: "desplaza los bits a la izquierda",
            ast.RShift: "desplaza los bits a la derecha",
        }
        action = actions.get(type(node.op), "opera")
        return f"{action} {_expression(node.left)} y {_expression(node.right)}; el resultado depende de los valores y sus tipos"
    if isinstance(node, ast.Compare):
        return f"compara {_expression(node.left)} con {_expression(node.comparators[0])}; produce True o False"
    if isinstance(node, ast.BoolOp):
        operation = "AND (y)" if isinstance(node.op, ast.And) else "OR (o)"
        operands = " y ".join(_expression(value) for value in node.values)
        return f"combina {operands} con {operation}; Python evalúa de izquierda a derecha y puede detenerse al conocer el resultado"
    if isinstance(node, ast.UnaryOp):
        actions = {ast.Not: "invierte el valor lógico de", ast.USub: "cambia el signo de", ast.UAdd: "conserva el signo de", ast.Invert: "invierte los bits de"}
        return f"{actions.get(type(node.op), 'opera sobre')} {_expression(node.operand)}"
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "len" and node.args:
            return f"llama a len para contar los elementos de {_expression(node.args[0])}; devuelve un entero"
        if isinstance(node.func, ast.Name) and node.func.id == "type" and node.args:
            return f"llama a type para consultar el tipo de {_expression(node.args[0])}"
        return f"llama a «{ast.unparse(node.func)}»; el resultado depende de esa función"
    if isinstance(node, ast.Subscript):
        return f"accede al elemento indicado por {_expression(node.slice)} dentro de {_expression(node.value)}"
    if isinstance(node, ast.Attribute):
        return f"accede al atributo «{node.attr}» de {_expression(node.value)}"
    if isinstance(node, ast.IfExp):
        return f"elige {_expression(node.body)} si {_expression(node.test)} es verdadero; si no, elige {_expression(node.orelse)}"
    return f"obtiene {_expression(node)}"


def _expression_report(tree: ast.Module) -> list[str]:
    lines = [
        "Operadores y expresiones en Python:",
        "- Una expresión combina valores, variables y operaciones para producir un resultado.",
        "- El tipo de los operandos importa: + suma números, pero concatena cadenas; operaciones incompatibles pueden producir un error.",
        "- Las comparaciones producen True o False. and y or pueden dejar de evaluar antes de revisar todos sus operandos.",
    ]
    expressions = [node for node in ast.walk(tree) if isinstance(node, (ast.BinOp, ast.Compare, ast.BoolOp, ast.UnaryOp, ast.Call, ast.Subscript, ast.IfExp))]
    seen: set[str] = set()
    for node in sorted(expressions, key=lambda item: (item.lineno, item.col_offset)):
        code = ast.unparse(node)
        if code in seen:
            continue
        seen.add(code)
        lines.append(f"- «{code}»: {_describe_expression(node)}.")
    if not seen:
        lines.append("No encontré operadores ni expresiones de este tipo en el código.")
    return lines


def _arguments(args: ast.arguments) -> str:
    entries: list[str] = []
    positional = [*args.posonlyargs, *args.args]
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for arg, default in zip(positional, defaults):
        item = arg.arg
        if arg.annotation:
            item += f" (tipo sugerido: {ast.unparse(arg.annotation)})"
        if default:
            item += f"; valor predeterminado: {_expression(default)}"
        entries.append(item)
    if args.vararg:
        entries.append(f"*{args.vararg.arg} recibe argumentos adicionales")
    entries.extend(f"{item.arg}={ast.unparse(item.value)}" for item in args.kwonlyargs if item.arg)
    if args.kwarg:
        entries.append(f"**{args.kwarg.arg} recibe argumentos con nombre adicionales")
    return ", ".join(entries) or "ninguno"


def _function_report(tree: ast.Module) -> list[str]:
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    lines = ["Funciones en Python:", "- Se definen con def y su cuerpo se ejecuta cuando se las llama.", "- Los parámetros reciben argumentos; return devuelve un resultado. Sin return explícito, la función devuelve None."]
    if not functions:
        lines.append("No encontré definiciones de funciones.")
        return lines
    for node in sorted(functions, key=lambda item: (item.lineno, item.col_offset)):
        kind = "función asíncrona" if isinstance(node, ast.AsyncFunctionDef) else "función"
        returns = [item for item in ast.walk(node) if isinstance(item, ast.Return)]
        result = "contiene una instrucción return" if returns else "no contiene return explícito y devuelve None al terminar"
        doc = ast.get_docstring(node)
        detail = f"- «{node.name}» es una {kind} con parámetros: {_arguments(node.args)}; {result}."
        if node.returns:
            detail += f" Anotación de retorno: {ast.unparse(node.returns)}; es una indicación, no una conversión automática."
        if doc:
            detail += f" Docstring: {doc.strip()}"
        lines.append(detail)
    return lines


def _collection_report(tree: ast.Module) -> list[str]:
    kinds: dict[type[ast.AST], str] = {ast.List: "lista", ast.Tuple: "tupla", ast.Set: "conjunto", ast.Dict: "diccionario"}
    found: dict[type[ast.AST], list[ast.AST]] = {kind: [] for kind in kinds}
    for node in ast.walk(tree):
        for kind in kinds:
            if isinstance(node, kind):
                found[kind].append(node)
    lines = [
        "Colecciones en Python:",
        "- Las listas guardan elementos en orden y se pueden modificar; las tuplas guardan elementos en orden y no se modifican después de crearse.",
        "- Los conjuntos guardan elementos únicos; los diccionarios relacionan claves con valores.",
        "- Los corchetes acceden a posiciones o claves; algunos métodos, como append, modifican una lista.",
    ]
    any_found = False
    for kind, nodes in found.items():
        if nodes:
            any_found = True
            lines.append(f"- Hay {len(nodes)} expresión(es) de tipo {kinds[kind]}.")
    accesses = [node for node in ast.walk(tree) if isinstance(node, ast.Subscript)]
    for node in sorted(accesses, key=lambda item: (item.lineno, item.col_offset)):
        lines.append(f"- «{ast.unparse(node)}»: {_describe_expression(node)}.")
    if not any_found and not accesses:
        lines.append("No encontré colecciones ni accesos por índice o clave.")
    return lines


def _class_report(tree: ast.Module) -> list[str]:
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    lines = [
        "Clases y objetos en Python:",
        "- Una clase define una estructura; sus instancias son objetos. __init__ configura una instancia al crearla y self se refiere a esa instancia en los métodos.",
        "- La herencia permite que una clase derive de otra. El análisis describe las bases escritas, pero no ejecuta la jerarquía.",
    ]
    if not classes:
        lines.append("No encontré definiciones de clases.")
        return lines
    for node in sorted(classes, key=lambda item: (item.lineno, item.col_offset)):
        bases = ", ".join(ast.unparse(base) for base in node.bases) or "ninguna"
        methods = [item.name for item in node.body if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))]
        fields = [ast.unparse(item.targets[0]) for item in node.body if isinstance(item, ast.Assign)]
        detail = f"- «{node.name}»: bases {bases}."
        if methods:
            detail += f" Métodos: {', '.join(methods)}."
        if fields:
            detail += f" Asignaciones de clase: {', '.join(fields)}."
        lines.append(detail)
    return lines


def _exception_import_report(tree: ast.Module) -> list[str]:
    handlers = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]
    raises = [node for node in ast.walk(tree) if isinstance(node, ast.Raise)]
    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    lines = ["Errores e importaciones:", "- try contiene código que puede fallar; except maneja los errores indicados, else se ejecuta si no hubo error y finally se ejecuta al salir del bloque.", "- raise lanza una excepción. Importar un módulo permite usar nombres que ese módulo ofrece; importar también puede ejecutar código de inicialización del módulo."]
    if not handlers and not raises and not imports:
        lines.append("No encontré bloques de manejo de errores, excepciones ni importaciones.")
    for node in handlers:
        names = ", ".join(ast.unparse(handler.type) if handler.type else "cualquier excepción" for handler in node.handlers) or "ningún tipo declarado"
        lines.append(f"- try en la línea {node.lineno} maneja: {names}.")
    for node in raises:
        lines.append(f"- raise en la línea {node.lineno}: {ast.unparse(node)}.")
    for node in imports:
        lines.append(f"- Importación en la línea {node.lineno}: {ast.unparse(node)}.")
    return lines


def _statements(nodes: list[ast.stmt], level: int = 0) -> list[str]:
    lines: list[str] = []
    pad = _indent(level)
    for node in nodes:
        lines.append(f"{pad}Línea {node.lineno} del código:")
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
                if len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                    lines.append(f"{pad}Si no, comprueba otra condición:")
                    lines.extend(_statements(node.orelse, level))
                else:
                    lines.append(f"{pad}Si no:")
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
            if node.orelse:
                lines.append(f"{pad}Si el ciclo termina sin break:")
                lines.extend(_statements(node.orelse, level + 1))
        elif isinstance(node, ast.Try):
            lines.append(f"{pad}Intenta ejecutar este bloque:")
            lines.extend(_statements(node.body, level + 1))
            for handler in node.handlers:
                exception = ast.unparse(handler.type) if handler.type else "cualquier excepción"
                lines.append(f"{pad}Si ocurre {exception}:")
                lines.extend(_statements(handler.body, level + 1))
            if node.orelse:
                lines.append(f"{pad}Si no ocurre ninguna excepción:")
                lines.extend(_statements(node.orelse, level + 1))
            if node.finalbody:
                lines.append(f"{pad}Al salir del bloque, ejecuta siempre:")
                lines.extend(_statements(node.finalbody, level + 1))
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
            if node.exc is None:
                lines.append(f"{pad}Vuelve a lanzar la excepción que se está manejando.")
            else:
                lines.append(f"{pad}Lanza la excepción {_expression(node.exc)}.")
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            lines.append(f"{pad}Importa «{ast.unparse(node)}».")
        else:
            lines.append(f"{pad}Instrucción Python: «{ast.unparse(node)}».")
    return lines


def explain(source: str, *, topic: str | None = None) -> str:
    """Devuelve una explicación en español, opcionalmente centrada en un tema."""
    topics = (None, "variables", "expresiones", "decisiones", "funciones", "colecciones", "clases", "errores")
    if topic not in topics:
        raise ValueError(f"Tema no disponible. Elige uno de: {', '.join(item for item in topics if item)}.")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        where = f" en la línea {exc.lineno}" if exc.lineno else ""
        raise TranslationError(f"No se pudo analizar el código{where}: {exc.msg}") from exc
    if topic == "variables":
        return "\n".join(_variable_report(tree))
    if topic == "expresiones":
        return "\n".join(_expression_report(tree))
    reports = {
        "decisiones": lambda: ["Decisiones y ciclos:", "- if elige un bloque según una condición; elif comprueba otra condición si las anteriores fueron falsas; else cubre los demás casos.", "- for recorre elementos; while repite mientras su condición sea verdadera. break sale del ciclo y continue salta a la siguiente vuelta.", *_statements(tree.body)],
        "funciones": lambda: _function_report(tree),
        "colecciones": lambda: _collection_report(tree),
        "clases": lambda: _class_report(tree),
        "errores": lambda: _exception_import_report(tree),
    }
    if topic:
        return "\n".join(reports[topic]())
    return "\n".join([*_variable_report(tree), "", *_expression_report(tree), "", *_function_report(tree), "", *_collection_report(tree), "", *_class_report(tree), "", *_exception_import_report(tree), "", "Explicación del código:", *_statements(tree.body)]) or "El programa está vacío."


def explain_file(path: str | Path) -> str:
    """Lee y explica un archivo Python en UTF-8."""
    return explain(Path(path).read_text(encoding="utf-8"))
