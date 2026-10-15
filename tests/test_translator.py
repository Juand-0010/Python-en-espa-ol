import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from tradupython import TranslationError, __version__, explain, translate


class ExplainTests(unittest.TestCase):
    def test_version_matches_release_metadata(self):
        self.assertEqual(__version__, "0.2.1")

    def test_variable_report_separates_function_scopes(self):
        source = '''
valor = 1
def mostrar():
    print(valor)
def duplicar(valor):
    valor += 1
    return valor
'''
        report = explain(source, topic="variables")
        self.assertIn("ámbito de módulo", report)
        self.assertIn("ámbito de función «mostrar»", report)
        self.assertIn("ámbito de función «duplicar»", report)
        self.assertIn("«valor» se asigna 1 vez/veces, empezando con el valor 1; se lee 1 vez/veces", report)
        self.assertIn("«valor» se asigna 2 vez/veces; se lee 2 vez/veces", report)

    def test_variable_report_counts_closure_reads_in_outer_scope(self):
        report = explain("def exterior():\n    dato = 4\n    def interior():\n        return dato\n    return interior()", topic="variables")
        self.assertIn("«dato» se asigna 1 vez/veces, empezando con el valor 4; se lee 1 vez/veces", report)

    def test_reports_all_supported_topics(self):
        source = '''
items = [1, 2]
def twice(value=2) -> int:
    """Returns twice a value."""
    return value * 2
class Child(Base):
    pass
try:
    if items:
        for item in items:
            print(twice(item))
except ValueError:
    raise
'''
        expected = {
            "variables": "Variables en Python",
            "expresiones": "Operadores y expresiones",
            "decisiones": "Decisiones y ciclos",
            "funciones": "Funciones en Python",
            "colecciones": "Colecciones en Python",
            "clases": "Clases y objetos en Python",
            "errores": "Errores e importaciones",
        }
        for topic, heading in expected.items():
            with self.subTest(topic=topic):
                self.assertIn(heading, explain(source, topic=topic))

    def test_explains_else_if_as_elif(self):
        result = explain("if x:\n    pass\nelif y:\n    pass\nelse:\n    pass", topic="decisiones")
        self.assertIn("Si la variable «x»", result)
        self.assertIn("Si la variable «y»", result)
        self.assertIn("Si no:", result)

    def test_invalid_syntax_has_readable_error(self):
        with self.assertRaises(TranslationError):
            explain("if:")

    def test_unknown_topic_is_rejected(self):
        with self.assertRaises(ValueError):
            explain("x = 1", topic="magia")

    def test_translates_spanish_program_and_keeps_strings_comments(self):
        source = '''# imprimir se conserva en comentario
edad = 20
si edad >= 18:
    imprimir("si edad >= 18")
sino_si edad == 17:
    imprimir("menor")
sino:
    imprimir("otro")
'''
        result = translate(source)
        self.assertIn("if edad >= 18:", result)
        self.assertIn("elif edad == 17:", result)
        self.assertIn("else:", result)
        self.assertIn('print("si edad >= 18")', result)
        self.assertIn("# imprimir se conserva en comentario", result)
        compile(result, "<tradupython>", "exec")

    def test_translates_loops_and_boolean_operators(self):
        result = translate("para numero en rango(3):\n    si numero > 0 y no falso:\n        imprimir(numero)\n")
        self.assertIn("for numero in range(3):", result)
        self.assertIn("if numero > 0 and not False:", result)

    def test_rejects_invalid_translated_syntax(self):
        with self.assertRaises(TranslationError):
            translate("si verdadero imprimir('hola')")

    def test_translates_written_comparison_operators(self):
        source = '''
si edad es mayor o igual que 18:
    imprimir("adulto")
si nombre es distinto de "" y nombre no es "anónimo":
    imprimir(nombre)
'''
        result = translate(source)
        self.assertIn("if edad >= 18:", result)
        self.assertIn('if nombre != "" and nombre != "anónimo":', result)

    def test_escaped_reserved_word_can_be_an_identifier(self):
        result = translate("`si` = 4\nimprimir(`si`)\n")
        self.assertIn("si = 4", result)
        self.assertIn("print(si)", result)

    def test_translates_more_common_builtins(self):
        result = translate("total = suma([1, 2])\nmayor = maximo([1, 2])\n")
        self.assertIn("sum([1, 2])", result)
        self.assertIn("max([1, 2])", result)

    def test_translated_program_keeps_expected_behavior(self):
        source = '''
funcion suma_hasta(limite):
    total = 0
    para numero en rango(limite):
        total = total + numero
    retornar total
imprimir(suma_hasta(5))
'''
        translated = translate(source)
        output = StringIO()
        with redirect_stdout(output):
            exec(compile(translated, "<tradupython-test>", "exec"), {
                "__builtins__": {"print": print, "range": range},
            })
        self.assertEqual(output.getvalue(), "10\n")

    def test_cli_executes_only_when_requested(self):
        with tempfile.TemporaryDirectory() as folder:
            source_path = Path(folder) / "programa_espanol.py"
            source_path.write_text("imprimir(3 * 2)\n", encoding="utf-8")
            environment = os.environ.copy()
            source_root = str(Path(__file__).resolve().parents[1] / "src")
            environment["PYTHONPATH"] = source_root + os.pathsep + environment.get("PYTHONPATH", "")
            result = subprocess.run(
                [sys.executable, "-m", "tradupython.cli", str(source_path), "--ejecutar"],
                capture_output=True,
                text=True,
                env=environment,
                check=False,
            )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "6\n")


if __name__ == "__main__":
    unittest.main()
