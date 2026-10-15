# TraduPython

TraduPython convierte un vocabulario básico de instrucciones en español a código Python y también explica código Python en español. La traducción no ejecuta el programa.

Versión actual del proyecto: **0.3.0 (alfa)**. La publicación en PyPI aún no se ha realizado.

## Instalar desde esta carpeta

```bash
python -m pip install .
```

## Usar desde la terminal

```bash
tradupython mi_programa.py
```

Para convertir un archivo escrito con palabras clave en español:

```bash
tradupython mi_programa.py --traducir
```

La salida es código Python; puedes guardarla desde la terminal con `tradupython mi_programa.py --traducir > programa.py`.

Si el programa es tuyo y confías en él, puedes traducirlo y ejecutarlo con `tradupython mi_programa.py --ejecutar`. Este modo ejecuta el código con los mismos permisos del usuario; no lo uses con archivos desconocidos.

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

Para traducir código escrito en español desde Python:

```python
from tradupython import translate

codigo_espanol = """\
edad = 20
si edad >= 18:
    imprimir("Puede entrar")
sino:
    imprimir("Todavía no")
"""

codigo_python = translate(codigo_espanol)
print(codigo_python)
```

El vocabulario cubre las palabras clave habituales de control, funciones, clases, excepciones, importaciones, operadores lógicos, declaraciones `global`/`nonlocal`, funciones asíncronas y patrones `match`/`case`. También ofrece nombres españoles para numerosos built-ins y tipos (`imprimir`, `longitud`, `rango`, `entrada`, `lista`, `diccionario`, `instancia_de`, entre otros) y comparaciones escritas como `mayor que`, `mayor o igual que`, `igual a` y `distinto de`. Las palabras ambiguas como `de`, `caso`, `global` y `lambda` se reconocen en posiciones concretas; el acento grave sigue permitiendo usar literalmente un nombre reservado.

### Alcance de la traducción

TraduPython traduce código escrito con su vocabulario español a Python; no es todavía una traducción completa de toda la sintaxis ni de todas las bibliotecas del ecosistema. La sintaxis nueva de Python debe añadirse y probarse por versión. Las expresiones de tipo, anotaciones, patrones avanzados, identificadores españoles con tilde, cadenas de formato con expresiones y algunas formas de importación requieren cobertura adicional. Los built-ins no incluidos pueden escribirse con su nombre original. Las palabras traducidas se consideran reservadas, salvo las reglas contextuales descritas arriba; rodea un nombre reservado con acentos graves para conservarlo como identificador.

Las palabras del vocabulario se traducen cuando aparecen como identificadores. Para usar una de ellas literalmente como nombre, enciérrala entre acentos graves: `` `si` = 3 `` se convierte en `si = 3`. El texto en cadenas, comentarios y atributos después de un punto se conserva.

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

El informe de variables explica que no es necesario declararlas antes de asignarles un valor, separa el módulo de las funciones y clases, y asocia lecturas sencillas de funciones internas con variables de ámbitos exteriores. También señala nombres que no se leen o se reasignan. Es una aproximación estática: no determina si una variable es necesaria en todos los caminos ni cubre todos los casos de ámbitos dinámicos.

La explicación general conserva los nombres de variables, funciones, módulos y cadenas para no cambiar su significado. Incluye asignaciones, condiciones, ciclos, funciones, clases, llamadas e importaciones; las construcciones aún no reconocidas se muestran como instrucciones Python.

El tema de expresiones describe operaciones aritméticas, comparaciones, lógica booleana, acceso a elementos, atributos y llamadas comunes. No ejecuta las expresiones para calcular resultados: explica el tipo de operación y aclara cuándo el resultado depende de los valores o tipos reales.

## Plan de trabajo

El proyecto avanza por temas pequeños. Cada etapa añade ejemplos de entrada y salida y documenta sus límites. La herramienta puede convertir vocabulario español a sintaxis Python, pero nunca ejecuta el código por su cuenta.

1. **Variables y valores — inicial.** Explica asignaciones y lecturas visibles. El recuento es aproximado y no distingue por completo los ámbitos ni los caminos de ejecución.
2. **Operadores y expresiones — disponible.** Explicar cálculos, comparaciones, lógica booleana, pertenencia, índices y llamadas, con ejemplos de cómo se combinan para producir valores.
3. **Decisiones y ciclos — inicial.** Explica condiciones, ciclos, `break` y `continue` en los bloques reconocidos.
4. **Funciones — inicial.** Resume parámetros, valores predeterminados, retorno, anotaciones y docstrings.
5. **Colecciones — inicial.** Describe listas, tuplas, conjuntos, diccionarios y accesos por índice o clave.
6. **Clases y objetos — inicial.** Resume clases, bases, métodos y asignaciones directas en el cuerpo de clase.
7. **Errores e importaciones — inicial.** Describe bloques `try`/`except`/`else`/`finally`, `raise` e importaciones.
8. **Experiencia de uso — inicial.** La CLI acepta temas, numera la explicación y convierte archivos con `--traducir`.
9. **Calidad y publicación — inicial.** Hay pruebas automatizadas e integración continua para Python 3.10–3.13, incluida una comprobación del comportamiento de un programa traducido. La cobertura y la precisión deben crecer con más ejemplos reales.

**Criterio para cada etapa:** que la salida sea comprensible, conserve los nombres y literales originales, no ejecute el código y reconozca explícitamente las construcciones que todavía no explica. Las advertencias sobre variables serán orientativas, porque un análisis estático sencillo no puede asegurar todos los efectos de una ejecución.

**Orden de trabajo:** la base del traductor, los temas de explicación y la CLI están implementados. La etapa de cobertura del lenguaje sigue abierta: cada versión de Python soportada debe tener una lista de palabras clave, operadores, built-ins y formas gramaticales, con ejemplos que se traduzcan, compilen y mantengan su comportamiento. Cada avance se guardará en commits pequeños en GitHub.

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

Consulta [RELEASING.md](RELEASING.md) para construir y preparar una publicación.
