# TraduPython

TraduPython explica en español construcciones comunes de Python para que puedas leerlas con más facilidad. No traduce palabras clave ni ejecuta el programa: analiza su sintaxis y genera una explicación aproximada.

## Instalar desde esta carpeta

```bash
python -m pip install .
```

## Usar desde la terminal

```bash
tradupython mi_programa.py
```

## Usar desde Python

```python
from tradupython import explain

codigo = """
edad = 18
if edad >= 18:
    print('Puede entrar')
"""

print(explain(codigo))
```

Para estudiar solo las variables:

```python
print(explain(codigo, topic="variables"))
```

O desde la terminal:

```bash
tradupython mi_programa.py --tema variables
```

Para estudiar operadores y expresiones:

```python
print(explain(codigo, topic="expresiones"))
```

```bash
tradupython mi_programa.py --tema expresiones
```

Los temas disponibles son `variables`, `expresiones`, `decisiones`, `funciones`, `colecciones`, `clases` y `errores`. La opción `--lineas` numera las líneas de la explicación generada.

Por ejemplo, para revisar condiciones y ciclos sin los demás temas:

```bash
tradupython mi_programa.py --tema decisiones
```

El informe de variables explica que no es necesario declararlas antes de asignarles un valor, cuenta asignaciones y lecturas visibles en el archivo, y señala nombres que no se leen o se reasignan. Recomienda nombres descriptivos y explica que las anotaciones de tipo son opcionales. Estas cuentas son aproximadas: no determinan si el código se ejecutará ni si una variable es necesaria en todos los caminos.

La explicación general conserva los nombres de variables, funciones, módulos y cadenas para no cambiar su significado. Incluye asignaciones, condiciones, ciclos, funciones, clases, llamadas e importaciones; las construcciones aún no reconocidas se muestran como instrucciones Python.

El tema de expresiones describe operaciones aritméticas, comparaciones, lógica booleana, acceso a elementos, atributos y llamadas comunes. No ejecuta las expresiones para calcular resultados: explica el tipo de operación y aclara cuándo el resultado depende de los valores o tipos reales.

## Plan de trabajo

El proyecto avanzará por temas pequeños. Cada etapa añadirá explicaciones en español, ejemplos de entrada y salida, y documentación de sus límites. La meta es que una persona pueda entender qué hace un programa Python sin que la herramienta altere ni ejecute ese programa.

1. **Variables y valores — inicial.** Explica asignaciones y lecturas visibles. El recuento es aproximado y no distingue por completo los ámbitos ni los caminos de ejecución.
2. **Operadores y expresiones — disponible.** Explicar cálculos, comparaciones, lógica booleana, pertenencia, índices y llamadas, con ejemplos de cómo se combinan para producir valores.
3. **Decisiones y ciclos — inicial.** Explica condiciones, ciclos, `break` y `continue` en los bloques reconocidos.
4. **Funciones — inicial.** Resume parámetros, valores predeterminados, retorno, anotaciones y docstrings.
5. **Colecciones — inicial.** Describe listas, tuplas, conjuntos, diccionarios y accesos por índice o clave.
6. **Clases y objetos — inicial.** Resume clases, bases, métodos y asignaciones directas en el cuerpo de clase.
7. **Errores e importaciones — inicial.** Describe bloques `try`/`except`/`else`/`finally`, `raise` e importaciones.
8. **Experiencia de uso — inicial.** La CLI acepta temas y una opción para anteponer números a las líneas de la explicación.
9. **Calidad y publicación — inicial.** Hay pruebas automatizadas e integración continua para Python 3.10–3.12. La cobertura y la precisión deben crecer con más ejemplos reales.

**Criterio para cada etapa:** que la salida sea comprensible, conserve los nombres y literales originales, no ejecute el código y reconozca explícitamente las construcciones que todavía no explica. Las advertencias sobre variables serán orientativas, porque un análisis estático sencillo no puede asegurar todos los efectos de una ejecución.

**Orden de trabajo:** las primeras versiones de todos los temas y el flujo de pruebas están implementados. Los siguientes avances deben mejorar precisión y cobertura con ejemplos reales. Cada avance se guardará en un commit pequeño en GitHub.

## Desarrollo

Desde esta carpeta puedes probar sin instalar:

```bash
python -m pip install -e .
python -m tradupython.cli mi_programa.py
```

Ejecuta las pruebas con:

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Licencia

MIT
