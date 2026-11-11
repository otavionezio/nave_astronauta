"""
Checagem de SENSIBILIDADE dos testes de sombra (não é um teste do projeto).
Degrada de propósito o viés do shadow mapping e confirma que os testes certos FALHAM.
Uso:  FORCE_HEADLESS_SHIM=1 python tests/mutation_shadow_bias.py
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, ".."))
for p in (ROOT, HERE, os.path.join(HERE, "headless")):
    sys.path.insert(0, p)
import bootstrap  # noqa: E402,F401
import lighting  # noqa: E402
import test_render_headless as T  # noqa: E402

CASOS = [
    ("viés 0,03 (~2,7 m de profundidade): peter-panning", dict(bias=0.03, slopeBias=0.0), "test_sombra_encosta_na_base_sem_flutuar"),
    ("viés 0,01 (valor do livro, ~0,9 m aqui)", dict(bias=0.01, slopeBias=0.0), "test_sombra_encosta_na_base_sem_flutuar"),
    ("viés 0,02 (~1,8 m)", dict(bias=0.02, slopeBias=0.0), "test_sombra_encosta_na_base_sem_flutuar"),
    ("viés mínimo 0,0001 e inclinação 0,0025", dict(bias=0.0001, slopeBias=0.0025), "test_sem_acne_em_piso_livre"),
    ("viés mínimo 0,0004 e SEM inclinação", dict(bias=0.0004, slopeBias=0.0), "test_sem_acne_em_piso_livre"),
    ("viés mínimo 0,0002 e inclinação 0,0012 (metade)", dict(bias=0.0002, slopeBias=0.0012), "test_sem_acne_em_piso_livre"),
    ("sem nenhum viés: acne", dict(bias=0.0, slopeBias=0.0), "test_sem_acne_em_piso_livre"),
]
nome, mut, teste = CASOS[int(sys.argv[1])]
lighting.SHADOW.update(mut)
res = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w")).run(unittest.TestSuite([T.TestSombras(teste)]))
print("viés=%.4f inclinação=%.4f | %-52s | %s" % (mut["bias"], mut["slopeBias"], nome + " [" + teste.replace("test_", "") + "]",
      "teste FALHOU (defeito detectado)" if res.failures else "teste PASSOU (nada detectado)"))
for _, tb in res.failures:
    print("   motivo:", tb.strip().splitlines()[-1])
