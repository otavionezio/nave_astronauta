"""Coloca a raiz do projeto e a pasta framework/ no sys.path, para que os imports no estilo
do livro (`from core.base import Base`, `from geometry.boxGeometry import ...`) funcionem."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(ROOT, "framework"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
