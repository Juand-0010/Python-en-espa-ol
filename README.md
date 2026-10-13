# TraduPython

TraduPython explica en español construcciones comunes de Python para que puedas leerlas con más facilidad. No traduce palabras clave ni ejecuta el programa: analiza su sintaxis y genera una explicación aproximada. El primer tema guiado es el uso de variables.

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

El informe de variables explica que no es necesario declararlas antes de asignarles un valor, cuenta asignaciones y lecturas visibles en el archivo, y señala nombres que no se leen o se reasignan. Recomienda nombres descriptivos y explica que las anotaciones de tipo son opcionales. Estas cuentas son aproximadas: no determinan si el código se ejecutará ni si una variable es necesaria en todos los caminos.

La explicación general conserva los nombres de variables, funciones, módulos y cadenas para no cambiar su significado. Incluye asignaciones, condiciones, ciclos, funciones, clases, llamadas e importaciones; las construcciones aún no reconocidas se muestran como instrucciones Python.

## Plan de trabajo

El proyecto avanzará por temas pequeños. Cada etapa añadirá explicaciones en español, ejemplos de entrada y salida, y documentación de sus límites. La meta es que una persona pueda entender qué hace un programa Python sin que la herramienta altere ni ejecute ese programa.

1. **Variables y valores — en curso.** Explicar asignación, lectura, reasignación, nombres sin uso visible, valores comunes y anotaciones de tipo. Mejorar el análisis para distinguir ámbitos de funciones y clases y evitar conclusiones que dependan de rutas de ejecución.
2. **Operadores y expresiones.** Explicar cálculos, comparaciones, lógica booleana, pertenencia, índices y llamadas, con ejemplos de cómo se combinan para producir valores.
3. **Decisiones y ciclos.** Explicar `if`/`elif`/`else`, `for`, `while`, `break` y `continue`, detallando condiciones y bloques de forma consistente.
4. **Funciones.** Explicar parámetros, argumentos, valores predeterminados, retorno, ámbito local y global, y docstrings.
5. **Colecciones.** Explicar listas, tuplas, conjuntos y diccionarios, sus operaciones habituales y acceso a elementos.
6. **Clases y objetos.** Explicar clases, atributos, métodos, `self`, inicialización y herencia básica.
7. **Errores e importaciones.** Explicar `try`/`except`/`finally`, excepciones, módulos e importaciones.
8. **Experiencia de uso.** Añadir selección de tema desde la terminal, salida por línea con referencias al código fuente y mensajes claros ante sintaxis no compatible.
9. **Calidad y publicación.** Incorporar pruebas automatizadas para cada tema, integración continua y documentación de instalación, ejemplos y versiones.

**Criterio para cada etapa:** que la salida sea comprensible, conserve los nombres y literales originales, no ejecute el código y reconozca explícitamente las construcciones que todavía no explica. Las advertencias sobre variables serán orientativas, porque un análisis estático sencillo no puede asegurar todos los efectos de una ejecución.

**Orden de trabajo:** completar variables; avanzar por expresiones y control de flujo; cubrir funciones y colecciones; luego clases, errores e importaciones; cerrar con mejoras de uso y publicación. Cada avance se guardará en un commit pequeño en GitHub.

## Desarrollo

Desde esta carpeta puedes probar sin instalar:

```bash
python -m pip install -e .
python -m tradupython.cli mi_programa.py
```

## Licencia

MIT
