# Preparar una versión

1. Actualiza la versión en `pyproject.toml` y en `src/tradupython/__init__.py`.
2. Ejecuta `python -m unittest discover -s tests -v`.
3. Construye los paquetes: `python -m pip install build` y `python -m build`.
4. Comprueba los archivos: `python -m pip install twine` y `python -m twine check dist/*`.
5. Crea y publica una etiqueta Git para la versión, por ejemplo `v0.2.1`.
6. Cuando la cuenta del proyecto esté configurada en PyPI, publica con `python -m twine upload dist/*`.

No guardes contraseñas ni tokens de PyPI en este repositorio. Para automatizar publicaciones, configura un publicador de confianza (Trusted Publisher) entre PyPI y GitHub Actions antes de habilitar un flujo de publicación.
