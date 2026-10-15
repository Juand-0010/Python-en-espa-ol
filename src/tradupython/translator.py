"""Convierte construcciones comunes de Python en explicaciones en español."""

from __future__ import annotations

import ast
import io
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path


class TranslationError(ValueError):
    """Error al analizar el código Python de entrada."""


_SPANISH_WORDS = {
    "si": "if",
    "sino": "else",
    "sino_si": "elif",
    "para": "for",
    "en": "in",
    "mientras": "while",
    "funcion": "def",
    "definir": "def",
    "retornar": "return",
    "romper": "break",
    "continuar": "continue",
    "pasar": "pass",
    "clase": "class",
    "intentar": "try",
    "excepto": "except",
    "finalmente": "finally",
    "lanzar": "raise",
    "importar": "import",
    "desde": "from",
    "como": "as",
    "con": "with",
    "y": "and",
    "o": "or",
    "no": "not",
    "es": "is",
    "verdadero": "True",
    "falso": "False",
    "nulo": "None",
    "imprimir": "print",
    "longitud": "len",
    "rango": "range",
    "entrada": "input",
    "enumerar": "enumerate",
    "tipo": "type",
    "suma": "sum",
    "minimo": "min",
    "maximo": "max",
    "ordenar": "sorted",
    "reverso": "reversed",
    "todos": "all",
    "cualquiera": "any",
    "entero": "int",
    "decimal": "float",
    "cadena": "str",
    "booleano": "bool",
    "abrir": "open",
    "redondear": "round",
    "eliminar": "del",
    "afirmar": "assert",
    "asincrona": "async",
    "esperar": "await",
    "ceder": "yield",
}

_SPANISH_OPERATORS = {
    ("no", "es", "igual", "a"): "!=",
    ("no", "es"): "!=",
    ("es", "distinto", "de"): "!=",
    ("distinto", "de"): "!=",
    ("es", "igual", "a"): "==",
    ("igual", "a"): "==",
    ("es", "mayor", "o", "igual", "que"): ">=",
    ("mayor", "o", "igual", "que"): ">=",
    ("es", "menor", "o", "igual", "que"): "<=",
    ("menor", "o", "igual", "que"): "<=",
    ("es", "mayor", "que"): ">",
    ("mayor", "que"): ">",
    ("es", "menor", "que"): "<",
    ("menor", "que"): "<",
}


def translate(source: str) -> str:
    """Convierte palabras clave y funciones incorporadas españolas a Python.

    Las palabras del vocabulario son reservadas y se convierten también si se
    usan como identificadores. El texto de cadenas y comentarios se conserva.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as exc:
        raise TranslationError(f"No se pudo leer el código: {exc}") from exc

    line_offsets = [0]
    for line in source.splitlines(keepends=True):
        line_offsets.append(line_offsets[-1] + len(line))

    replacements: list[tuple[int, int, str]] = []
    consumed: set[int] = set()
    # Los acentos graves permiten escribir literalmente un nombre reservado:
    # `si` se convierte en el identificador Python si, sin traducirlo a if.
    for index in range(len(tokens) - 2):
        opening, name, closing = tokens[index:index + 3]
        if opening.type == tokenize.OP and opening.string == "`" and name.type == tokenize.NAME and closing.type == tokenize.OP and closing.string == "`":
            start = line_offsets[opening.start[0] - 1] + opening.start[1]
            end = line_offsets[closing.end[0] - 1] + closing.end[1]
            replacements.append((start, end, name.string))
            consumed.update((index, index + 1, index + 2))
    # Reconoce frases de comparación como un solo operador, respetando cadenas
    # y comentarios, que la tokenización identifica como tipos separados.
    significant_indices = [index for index, token in enumerate(tokens) if index not in consumed and token.type not in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT)]
    patterns = sorted(_SPANISH_OPERATORS.items(), key=lambda item: len(item[0]), reverse=True)
    position = 0
    while position < len(significant_indices):
        matched = False
        for phrase, operator in patterns:
            indices = significant_indices[position:position + len(phrase)]
            if len(indices) != len(phrase):
                continue
            phrase_tokens = [tokens[index] for index in indices]
            if tuple(token.string for token in phrase_tokens) != phrase:
                continue
            if len({token.start[0] for token in phrase_tokens}) != 1:
                continue
            start = line_offsets[phrase_tokens[0].start[0] - 1] + phrase_tokens[0].start[1]
            end = line_offsets[phrase_tokens[-1].end[0] - 1] + phrase_tokens[-1].end[1]
            replacements.append((start, end, operator))
            consumed.update(indices)
            position += len(phrase)
            matched = True
            break
        if not matched:
            position += 1

    significant: list[tokenize.TokenInfo] = []
    for index, token in enumerate(tokens):
        if index not in consumed and token.type == tokenize.NAME and token.string in _SPANISH_WORDS:
            previous = next((item for item in reversed(significant) if item.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.COMMENT)), None)
            # Atributos como objeto.si conservan su nombre.
            if previous is None or previous.string != ".":
                start = line_offsets[token.start[0] - 1] + token.start[1]
                end = line_offsets[token.end[0] - 1] + token.end[1]
                replacements.append((start, end, _SPANISH_WORDS[token.string]))
        if token.type not in (tokenize.ENCODING, tokenize.ENDMARKER):
            significant.append(token)

    translated = source
    for start, end, replacement in sorted(replacements, key=lambda item: item[0], reverse=True):
        translated = translated[:start] + replacement + translated[end:]
    try:
        ast.parse(translated)
    except SyntaxError as exc:
        where = f" en la línea {exc.lineno}" if exc.lineno else ""
        raise TranslationError(f"El código traducido no es Python válido{where}: {exc.msg}") from exc
    return translated


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


@dataclass
class _VariableScope:
    label: str
    kind: str
    parent: _VariableScope | None = None
    stores: Counter[str] = field(default_factory=Counter)
    loads: Counter[str] = field(default_factory=Counter)
    reads: Counter[str] = field(default_factory=Counter)
    first_values: dict[str, ast.AST] = field(default_factory=dict)
    annotated: set[str] = field(default_factory=set)
    globals: set[str] = field(default_factory=set)
    nonlocals: set[str] = field(default_factory=set)


class _VariableScopeCollector(ast.NodeVisitor):
    """Collects assignments and reads without folding nested scopes together."""

    def __init__(self) -> None:
        self.root = _VariableScope("módulo", "module")
        self.current = self.root
        self.scopes = [self.root]

    def _store(self, name: str, value: ast.AST | None = None) -> None:
        self.current.stores[name] += 1
        if value is not None:
            self.current.first_values.setdefault(name, value)

    def _target(self, target: ast.AST, value: ast.AST | None = None, *, annotated: bool = False) -> None:
        if isinstance(target, ast.Name):
            self._store(target.id, value)
            if annotated:
                self.current.annotated.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                self._target(item, value, annotated=annotated)
        elif isinstance(target, ast.Starred):
            self._target(target.value, value, annotated=annotated)
        else:
            self.visit(target)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.current.loads[node.id] += 1
        elif isinstance(node.ctx, ast.Store):
            self._store(node.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        for target in node.targets:
            self._target(target, node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value:
            self.visit(node.value)
        self._target(node.target, node.value, annotated=True)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.current.loads[node.target.id] += 1
        else:
            self.visit(node.target)
        self.visit(node.value)
        self._target(node.target)

    def visit_For(self, node: ast.For | ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._target(node.target, node.iter)
        for statement in node.body + node.orelse:
            self.visit(statement)

    visit_AsyncFor = visit_For

    def visit_FunctionDef(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._store(node.name)
        for decorator in node.decorator_list:
            self.visit(decorator)
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default:
                self.visit(default)
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            if argument.annotation:
                self.visit(argument.annotation)
        if node.args.vararg and node.args.vararg.annotation:
            self.visit(node.args.vararg.annotation)
        if node.args.kwarg and node.args.kwarg.annotation:
            self.visit(node.args.kwarg.annotation)
        if node.returns:
            self.visit(node.returns)
        kind = "función asíncrona" if isinstance(node, ast.AsyncFunctionDef) else "función"
        scope = _VariableScope(f"{kind} «{node.name}»", "function", self.current)
        self.scopes.append(scope)
        previous = self.current
        self.current = scope
        arguments = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
        arguments.extend(arg for arg in (node.args.vararg, node.args.kwarg) if arg)
        for argument in arguments:
            self._store(argument.arg)
        for statement in node.body:
            self.visit(statement)
        self.current = previous

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if default:
                self.visit(default)
        scope = _VariableScope("función lambda", "function", self.current)
        self.scopes.append(scope)
        previous = self.current
        self.current = scope
        for argument in [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]:
            self._store(argument.arg)
        for argument in (node.args.vararg, node.args.kwarg):
            if argument:
                self._store(argument.arg)
        self.visit(node.body)
        self.current = previous

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._store(node.name)
        for expression in [*node.decorator_list, *node.bases, *(keyword.value for keyword in node.keywords)]:
            self.visit(expression)
        scope = _VariableScope(f"clase «{node.name}»", "class", self.current)
        self.scopes.append(scope)
        previous = self.current
        self.current = scope
        for statement in node.body:
            self.visit(statement)
        self.current = previous

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._store(alias.asname or alias.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name != "*":
                self._store(alias.asname or alias.name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type:
            self.visit(node.type)
        if node.name:
            self._store(node.name)
        for statement in node.body:
            self.visit(statement)

    def visit_Global(self, node: ast.Global) -> None:
        self.current.globals.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.current.nonlocals.update(node.names)


def _resolve_variable_scope(scope: _VariableScope, name: str, root: _VariableScope) -> _VariableScope | None:
    if name in scope.globals:
        return root if root.stores[name] else None
    if name in scope.nonlocals:
        parent = scope.parent
        while parent:
            if parent.kind == "function" and parent.stores[name]:
                return parent
            parent = parent.parent
        return None
    if scope.stores[name]:
        return scope
    parent = scope.parent
    if scope.kind == "function":
        while parent and parent.kind == "class":
            parent = parent.parent
    while parent:
        if parent.stores[name]:
            return parent
        parent = parent.parent
    return None


def _variable_report(tree: ast.Module) -> list[str]:
    """Reports variable use per scope and resolves simple closure/global reads."""
    collector = _VariableScopeCollector()
    collector.visit(tree)
    for scope in collector.scopes:
        for name, count in scope.loads.items():
            resolved = _resolve_variable_scope(scope, name, collector.root)
            if resolved:
                resolved.reads[name] += count

    lines = [
        "Variables en Python:",
        "- No hace falta declarar una variable antes de asignarle un valor.",
        "- Conviene elegir nombres descriptivos y asignarles un valor antes de leerlas.",
        "- Las anotaciones de tipo son opcionales; sirven para documentar y para algunas herramientas.",
    ]
    scopes_with_assignments = [scope for scope in collector.scopes if scope.stores or scope.loads]
    if not scopes_with_assignments:
        lines.append("Este código no asigna variables con nombres simples.")
        return lines
    for scope in scopes_with_assignments:
        lines.append(f"Variables en el ámbito de {scope.label}:")
        if not scope.stores:
            lines.append("- Este ámbito no asigna variables propias; sus lecturas pueden corresponder a nombres exteriores o incorporados.")
        for name in sorted(scope.stores):
            assignments = scope.stores[name]
            use_count = scope.reads[name]
            value = scope.first_values.get(name)
            detail = f"- «{name}» se asigna {assignments} vez/veces"
            if value is not None:
                detail += f", empezando con {_expression(value)}"
            detail += f"; se lee {use_count} vez/veces"
            if use_count == 0:
                detail += ". No encontré una lectura que pueda asociar a esta variable"
            elif assignments > 1:
                detail += ". Se reasigna; comprueba que cada cambio sea intencional"
            else:
                detail += ". Encontré una lectura en este ámbito o en uno interno"
            if name in scope.annotated:
                detail += ". Tiene una anotación de tipo, que Python no exige para crearla"
            lines.append(f"{detail}.")
    unresolved = [(scope.label, name, count) for scope in collector.scopes for name, count in scope.loads.items() if _resolve_variable_scope(scope, name, collector.root) is None]
    if unresolved:
        lines.append("Algunas lecturas se refieren a nombres globales, importados o incorporados que no se asignan en este archivo.")
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
