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

## Desarrollo

Desde esta carpeta puedes probar sin instalar:

```bash
python -m pip install -e .
python -m tradupython.cli mi_programa.py
```

## Licencia

MIT
