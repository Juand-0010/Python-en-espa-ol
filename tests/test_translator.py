import unittest

from tradupython import TranslationError, explain


class ExplainTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
