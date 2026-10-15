# TraduPython

TraduPython convierte un vocabulario básico de instrucciones en español a código Python y también explica código Python en español. La traducción no ejecuta el programa.

Versión actual del proyecto: **0.2.1 (alfa)**. La publicación en PyPI aún no se ha realizado.

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

El vocabulario incluye palabras de control (`si`, `sino`, `sino_si`, `para`, `mientras`), definiciones y errores (`funcion`, `clase`, `retornar`, `intentar`, `excepto`, `finalmente`, `lanzar`), importaciones (`importar`, `desde`, `como`), lógica (`y`, `o`, `no`), valores (`verdadero`, `falso`, `nulo`) y funciones habituales (`imprimir`, `longitud`, `rango`, `entrada`, `suma`, `minimo`, `maximo`, entre otras). También reconoce comparaciones como `mayor que`, `mayor o igual que`, `igual a` y `distinto de`.

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

Consulta [RELEASING.md](RELEASING.md) para construir y preparar una publicación.
