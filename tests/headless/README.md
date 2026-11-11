# Validação headless (ferramenta de teste — NÃO faz parte do trabalho)

Este diretório contém uma camada mínima que imita o subconjunto de **PyOpenGL** e
**Pygame** usado pelo framework, apoiada em `ctypes` + Mesa (EGL, rasterizador por
software). Serve apenas para executar os testes em máquinas SEM janela/GPU/pip
(CI, servidor Linux). Ela só é usada quando `pygame`/`OpenGL` reais não estão
instalados (ver `tests/headless_env.py`).

* NÃO substitui rodar `python main.py` com Pygame e PyOpenGL reais.
* Linux + Mesa apenas. Pode ser apagada sem afetar o projeto.
