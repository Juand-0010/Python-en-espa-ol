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

El resultado describe las instrucciones; los nombres de variables, funciones, módulos y cadenas se conservan para no cambiar su significado. La cobertura inicial incluye asignaciones, condiciones, ciclos, funciones, clases, llamadas e importaciones. Las construcciones aún no reconocidas se muestran como instrucciones Python.

## Desarrollo

Desde esta carpeta puedes probar sin instalar:

```bash
python -m pip install -e .
python -m tradupython.cli mi_programa.py
```

## Licencia

MIT
