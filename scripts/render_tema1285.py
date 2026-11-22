"""Renderiza o Reels do Tema 1285 (identidade Mosima) a partir da narração e dos tempos por palavra.

Uso: python3 render_tema1285.py <audio_original.m4a> <pasta_saida> [--amostra INICIO FIM]
"""
import csv, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IV = f"{RAIZ}/identidade-visual"
PROJ = f"{RAIZ}/projetos/tema-1285"
VERDE, VERDE_ESC, COBRE, CINZA, BRANCO, AREIA = "#2E5156", "#1F383C", "#C57A55", "#464646", "#FFFFFF", "#F4EFEA"
W, H = 1080, 1920
F = lambda w, s: ImageFont.truetype(f"{IV}/fontes/Lato-{w}.ttf", s)
SIMB = Image.open(f"{IV}/logo-simbolo.png").convert("RGBA").resize((150, 148))
LOGO = Image.open(f"{IV}/logo-completo.png").convert("RGBA")

# ---------- 1. Cortes (tempos do áudio original, em segundos) ----------
# Remove: "A pergunta é, esse dinheiro pode ser devolvido?", as três regravações e o "se" solto.
CORTES = [(2.45, 14.40), (25.30, 59.29), (77.40, 120.45), (129.10, 133.30)]

def novo_t(t):
    acc = 0.0
    for s, e in CORTES:
        if s <= t <= e: return acc + (t - s)
        acc += e - s
    return None
DUR = sum(e - s for s, e in CORTES)

# ---------- 2. Palavras e legendas ----------
CORRECOES = {"StJ": "STJ", "C.": "Se", "2.": "Dois:", "Há": "as"}
palavras = []
for r in csv.DictReader(open(f"{PROJ}/narracao-palavras.csv", encoding="utf-8")):
    s, e = float(r["start"]), float(r["end"])
    ns, ne = novo_t(s), novo_t(e)
    if ns is None or ne is None: continue
    txt = CORRECOES.get(r["text"], r["text"])
    if r["index"] == "140": txt = "o"  # "Se, o dinheiro estiver..."
    palavras.append((ns, ne, txt))

grupos, atual = [], []
for p in palavras:
    atual.append(p)
    txt = " ".join(x[2] for x in atual)
    fraca = p[2].lower() in {"de", "para", "a", "o", "os", "em", "um", "uma", "como", "se", "no", "na", "do", "dos", "ou", "que", "e", "não", "ser", "pode", "alto", "foi", "ele", "nosso", "sua"}
    if p[2][-1] in ".,?:" or ((len(atual) >= 4 or len(txt) >= 22) and not fraca) or len(txt) >= 30:
        grupos.append(atual); atual = []
if atual: grupos.append(atual)
legendas = []
for i, g in enumerate(grupos):
    ini = g[0][0]
    fim = g[-1][1] + 0.5
    if i + 1 < len(grupos): fim = min(fim, grupos[i + 1][0][0])
    texto = " ".join(x[2] for x in g).rstrip(".,:")
    legendas.append((ini, fim, texto))

# ---------- 3. Cenas (tempo original de início, nome, parâmetros) ----------
CENAS_ORIG = [
    (2.45, "gancho", {}), (9.70, "bloqueio", {}), (25.30, "regra", {}),
    (34.80, "protegido", {"n": 1}), (43.70, "protegido", {"n": 2}), (45.25, "protegido", {"n": 3}),
    (49.40, "protegido", {"n": 3, "reserva": True}),
    (53.85, "atencao", {}), (77.40, "excecoes", {"n": 1}), (84.00, "excecoes", {"n": 2}),
    (100.80, "debate", {}), (111.30, "extratos", {}), (129.10, "fim", {}),
]
CENAS = [(novo_t(t) if novo_t(t) is not None else 0, n, p) for t, n, p in CENAS_ORIG]

# ---------- 4. Desenho ----------
def base(d_im, fundo):
    d = ImageDraw.Draw(d_im)
    d.rectangle([80, 150, 420, 158], fill=COBRE); d.rectangle([660, 150, 1000, 158], fill=COBRE)
    d_im.paste(SIMB, (465, 80))
    if fundo != AREIA: d.rectangle([462, 77, 617, 230], outline=COBRE, width=3)
    d.text((W // 2, 1440), "STJ · Tema Repetitivo 1285 · art. 833, IV e X, CPC", font=F("Regular", 30),
           fill=CINZA if fundo == AREIA else "#BFD0D2", anchor="mm")
    d.rectangle([0, H - 40, W, H], fill=COBRE)
    return d

def centro(d, linhas, y, fonte, cor=BRANCO, esp=1.15):
    for l in linhas:
        d.text((W // 2, y), l, font=fonte, fill=cor, anchor="mm"); y += int(fonte.size * esp)
    return y

def marca(d, x, y, ok, r=46):
    d.ellipse([x - r, y - r, x + r, y + r], fill="#3E8E6E" if ok else COBRE)
    if ok: d.line([(x - 22, y + 2), (x - 6, y + 20), (x + 24, y - 18)], fill=BRANCO, width=12)
    else:
        d.line([(x - 18, y - 18), (x + 18, y + 18)], fill=BRANCO, width=12)
        d.line([(x - 18, y + 18), (x + 18, y - 18)], fill=BRANCO, width=12)

def cena(nome, p):
    fundo = {"protegido": AREIA, "atencao": VERDE_ESC, "excecoes": VERDE_ESC, "fim": BRANCO}.get(nome, VERDE)
    im = Image.new("RGB", (W, H), fundo)
    if nome == "fim":
        d = ImageDraw.Draw(im)
        lg = LOGO.resize((820, int(820 * LOGO.height / LOGO.width))); im.paste(lg, ((W - 820) // 2, 520))
        centro(d, ["Decisões do STJ", "explicadas de forma simples"], 1000, F("Regular", 50), CINZA)
        centro(d, ["mosima.com.br"], 1150, F("Bold", 54), COBRE)
        d.rectangle([0, H - 60, W, H], fill=VERDE)
        return im
    d = base(im, fundo)
    if nome == "gancho":
        y = centro(d, ["SEU DINHEIRO", "PODE SER", "PENHORADO?"], 560, F("Black", 118))
        d.rectangle([390, y + 10, 690, y + 18], fill=COBRE); centro(d, ["Tema 1285 — STJ"], y + 90, F("Bold", 62), COBRE)
    elif nome == "bloqueio":
        centro(d, ["CONTA", "BLOQUEADA"], 560, F("Black", 130))
        # cadeado simples
        x, y = W // 2, 960
        d.rounded_rectangle([x - 110, y - 10, x + 110, y + 160], 24, fill=COBRE)
        d.arc([x - 75, y - 130, x + 75, y + 40], 180, 360, fill=COBRE, width=26)
        d.ellipse([x - 18, y + 50, x + 18, y + 86], fill=VERDE); d.rectangle([x - 7, y + 80, x + 7, y + 120], fill=VERDE)
    elif nome == "regra":
        centro(d, ["ATÉ"], 520, F("Bold", 70), COBRE)
        centro(d, ["40", "SALÁRIOS", "MÍNIMOS"], 680, F("Black", 140))
        centro(d, ["protegidos da penhora"], 1150, F("Regular", 58), "#DCE6E7")
    elif nome == "protegido":
        centro(d, ["O QUE ESTÁ", "PROTEGIDO"], 400, F("Black", 96), VERDE)
        itens = [("POUPANÇA", "mesmo usada como conta corrente"), ("DINHEIRO VIVO", "se for reserva de emergência"),
                 ("CONTA / INVESTIMENTO", "se for reserva de emergência")]
        y = 640
        for i, (t, s) in enumerate(itens[:p["n"]]):
            marca(d, 170, y + 30, True); d.text((250, y), t, font=F("Black", 62), fill=VERDE)
            dest = p.get("reserva") and i > 0
            d.text((250, y + 78), s, font=F("Bold" if dest else "Regular", 40), fill=COBRE if dest else CINZA); y += 200
    elif nome == "atencao":
        centro(d, ["MAS", "ATENÇÃO"], 600, F("Black", 150), COBRE)
        centro(d, ["a proteção não vale", "em dois casos"], 1000, F("Regular", 58), "#DCE6E7")
    elif nome == "excecoes":
        centro(d, ["NÃO ESTÁ", "PROTEGIDO"], 400, F("Black", 96), COBRE)
        y = 700
        for t, s in [("ALTO RISCO", "investir para tentar ganhar mais"), ("SOBRAS DE MESES", "salário que ficou parado na conta")][:p["n"]]:
            marca(d, 170, y + 30, False); d.text((250, y), t, font=F("Black", 64), fill=BRANCO)
            d.text((250, y + 80), s, font=F("Regular", 40), fill="#BFD0D2"); y += 260
    elif nome == "debate":
        centro(d, ["“ALTO RISCO”"], 620, F("Black", 110), BRANCO)
        centro(d, ["= ?"], 800, F("Black", 160), COBRE)
        centro(d, ["será definido", "caso a caso"], 1020, F("Regular", 58), "#DCE6E7")
    elif nome == "extratos":
        centro(d, ["GUARDE", "SEUS", "EXTRATOS"], 560, F("Black", 130))
        centro(d, ["de onde veio o dinheiro", "e para que ele serve"], 1060, F("Regular", 54), "#DCE6E7")
    return im

def com_legenda(im, texto):
    if not texto: return im
    im = im.copy(); d = ImageDraw.Draw(im); f = F("Bold", 54)
    bb = d.textbbox((W // 2, 1330), texto, font=f, anchor="mm")
    d.rounded_rectangle([bb[0] - 30, bb[1] - 20, bb[2] + 30, bb[3] + 20], 18, fill="#0E1C1E")
    d.text((W // 2, 1330), texto, font=f, fill=BRANCO, anchor="mm")
    return im

# ---------- 5. Montagem ----------
def main():
    audio, saida = sys.argv[1], sys.argv[2]
    amostra = None
    if "--amostra" in sys.argv:
        i = sys.argv.index("--amostra"); amostra = (float(sys.argv[i + 1]), float(sys.argv[i + 2]))
    quadros = f"{saida}/quadros"; os.makedirs(quadros, exist_ok=True)

    # áudio: cortes com micro-fades, normalização para redes sociais
    filtros, rotulos = [], []
    for k, (s, e) in enumerate(CORTES):
        filtros.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.04:.3f}:d=0.04[a{k}]")
        rotulos.append(f"[a{k}]")
    filtros.append("".join(rotulos) + f"concat=n={len(CORTES)}:v=0:a=1,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    wav = f"{saida}/narracao-editada.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-filter_complex", ";".join(filtros),
                    "-map", "[out]", "-ar", "48000", "-ac", "1", wav], check=True)

    # linha do tempo: pontos de mudança de cena ou legenda
    pontos = sorted({0.0, DUR} | {c[0] for c in CENAS} | {l[0] for l in legendas} | {l[1] for l in legendas})
    pontos = [p for p in pontos if 0 <= p <= DUR]
    lista, cache = [], {}
    for a, b in zip(pontos, pontos[1:]):
        if b - a < 0.01: continue
        meio = (a + b) / 2
        c = [x for x in CENAS if x[0] <= meio][-1]
        leg = next((l[2] for l in legendas if l[0] <= meio < l[1]), "")
        chave = (c[1], tuple(sorted(c[2].items())), leg)
        if chave not in cache:
            fn = f"{quadros}/q{len(cache):04d}.png"; com_legenda(cena(c[1], c[2]), leg).save(fn); cache[chave] = fn
        lista.append((cache[chave], a, b))
    if amostra:
        lista = [(f, max(a, amostra[0]) - amostra[0], min(b, amostra[1]) - amostra[0]) for f, a, b in lista if b > amostra[0] and a < amostra[1]]
    with open(f"{saida}/concat.txt", "w") as fh:
        for f, a, b in lista: fh.write(f"file '{f}'\nduration {b - a:.3f}\n")
        fh.write(f"file '{lista[-1][0]}'\n")
    nome = "amostra.mp4" if amostra else "tema-1285-reels.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{saida}/concat.txt"]
    if amostra: cmd += ["-ss", str(amostra[0]), "-t", str(amostra[1] - amostra[0])]
    cmd += ["-i", wav, "-vf", "fps=30,format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{saida}/{nome}"]
    subprocess.run(cmd, check=True)
    with open(f"{saida}/legendas.srt", "w", encoding="utf-8") as fh:
        ts = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(t * 1000 % 1000):03d}"
        for i, (a, b, t) in enumerate(legendas, 1): fh.write(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n\n")
    print(f"ok: {nome} · duração total {DUR:.1f}s · {len(cache)} quadros únicos · {len(legendas)} legendas")

if __name__ == "__main__":
    main()
