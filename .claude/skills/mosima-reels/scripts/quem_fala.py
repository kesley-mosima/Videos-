"""Separa as falas de quem aparece no vídeo das falas de um narrador/ponto fora de quadro.

Mede o movimento da boca (diferença entre quadros numa caixa sobre a boca) em cada frase do CSV de palavras.
Quem aparece falando: índice alto (≈10–15). Narrador/ponto: índice baixo (≈3), próximo ou abaixo do silêncio.

Uso: python3 quem_fala.py video palavras.csv X Y L A
  X Y L A = caixa da boca em pixels do quadro 1080x1920 (já girado). Ex.: 450 375 180 110
Dica: extraia um quadro (ffmpeg -ss 10 -i video -frames:v 1 -vf scale=1080:1920 q.png) e localize a boca.
"""
import csv, subprocess, sys
import numpy as np

video, arq, x, y, l, a = sys.argv[1], sys.argv[2], *map(int, sys.argv[3:7])
raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", video, "-vf",
                      f"scale=1080:1920,fps=10,crop={l}:{a}:{x}:{y},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, check=True).stdout
q = np.frombuffer(raw, dtype=np.uint8).reshape(-1, a, l).astype(np.float32)
mov = np.abs(np.diff(q, axis=0)).mean(axis=(1, 2))

frases, atual = [], []
for r in csv.DictReader(open(arq, encoding="utf-8")):
    atual.append((float(r["start"]), float(r["end"]), r["text"]))
    if r["text"].rstrip()[-1:] in ".?!":
        frases.append(atual); atual = []
if atual: frases.append(atual)

print(f"{'início':>7} {'fim':>7} {'boca':>6}  quem   frase")
for f in frases:
    s, e = f[0][0], f[-1][1]
    v = mov[int(s * 10):max(int(s * 10) + 1, int(e * 10))].mean()
    quem = "PESSOA" if v >= 9 else ("narr." if v < 5.5 else "dúvida")
    txt = " ".join(w[2] for w in f)
    print(f"{s:7.2f} {e:7.2f} {v:6.2f}  {quem:6s} {txt[:90]}")
