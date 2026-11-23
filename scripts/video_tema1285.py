"""Reels Tema 1285 com o vídeo do advogado + ilustrações animadas (identidade Mosima).

Uso: python3 video_tema1285.py <video_original.mp4> <pasta_saida>
"""
import csv, json, math, os, subprocess, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motion_tema1285 as M
from motion_tema1285 import El, texto, compor, fundo, clamp, out_cubic, out_back
from render_tema1285 import F, VERDE, VERDE_ESC, COBRE, CINZA, BRANCO, AREIA, LOGO

W, H, FPS = 1080, 1920, 30
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PROJ = f"{RAIZ}/projetos/tema-1285-video"
CLARO, VERDE_OK = "#DCE6E7", "#3E8E6E"

# ---------- 1. Cortes e enxugamento ----------
# Mantém: tudo até "essa sobra pode sim ser penhorada" + a última versão do CTA.
# Remove: "Haverá ainda muitas discussões... saudar dívidas de um devedor" (repete o "conceito aberto"),
# as duas primeiras versões do CTA e "É para ficar esse último a versão. Ok."
CORTES = [(1.15, 82.75), (112.15, 117.45)]
FOLGA, PAUSA_MAX, DUR_ALVO = 0.12, 0.30, 74.0
TAIL = 1.6   # segundos finais com o cartão da marca

linhas = list(csv.DictReader(open(f"{PROJ}/palavras.csv", encoding="utf-8")))
def dentro(s, e): return any(a <= s and e <= b for a, b in CORTES)
pal = [(float(r["start"]), float(r["end"])) for r in linhas if dentro(float(r["start"]), float(r["end"]))]
TRECHOS = []
for s, e in pal:
    if TRECHOS and s - TRECHOS[-1][1] + FOLGA <= PAUSA_MAX: TRECHOS[-1][1] = e + FOLGA
    else: TRECHOS.append([s - FOLGA, e + FOLGA])
def corte(x): return next(c for c in CORTES if c[0] - FOLGA <= x <= c[1] + FOLGA)
TRECHOS = [(max(a, corte(a + FOLGA)[0]), min(b, corte(b - FOLGA)[1])) for a, b in TRECHOS]
BRUTA = sum(e - s for s, e in TRECHOS)
VEL = max(1.0, BRUTA / (DUR_ALVO - TAIL))
DUR_FALA = BRUTA / VEL
DUR = DUR_FALA + TAIL

def T(t):
    acc = 0.0
    for s, e in TRECHOS:
        if t < s: return acc / VEL
        if t <= e: return (acc + t - s) / VEL
        acc += e - s
    return acc / VEL

# ---------- 2. Legendas ----------
CORR = {"dinheiros": "dinheiros"}
pw = [(T(float(r["start"])), T(float(r["end"])), CORR.get(r["text"], r["text"])) for r in linhas if dentro(float(r["start"]), float(r["end"]))]
FRACAS = {"de", "para", "a", "o", "os", "em", "um", "uma", "como", "se", "no", "na", "do", "dos", "ou", "que", "e", "não",
          "ser", "pode", "alto", "foi", "ele", "nosso", "sua", "essa", "esse", "com", "as", "mais", "vai", "à", "desse", "tipo", "é"}
grupos, at = [], []
for p in pw:
    at.append(p); txt = " ".join(x[2] for x in at)
    if p[2][-1] in ".,?:" or ((len(at) >= 4 or len(txt) >= 22) and p[2].lower() not in FRACAS) or len(txt) >= 30:
        grupos.append(at); at = []
if at: grupos.append(at)
LEG = []
for i, g in enumerate(grupos):
    fim = g[-1][1] + 0.4
    if i + 1 < len(grupos): fim = min(fim, grupos[i + 1][0][0])
    LEG.append((g[0][0], fim, " ".join(x[2] for x in g).rstrip(".,:")))

# ---------- 3. Áudio + vídeo base (cortes, limpeza, velocidade) ----------
def gerar_base(video, saida):
    """Corta (select/aselect num único fluxo, pouca memória), limpa o áudio, acelera e normaliza."""
    sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in TRECHOS)
    limpeza = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,lowpass=f=15000,afftdn=nr=12:nf=-42:tn=1,deesser=i=0.4,"
               "equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=2,"
               f"acompressor=threshold=-24dB:ratio=3:attack=6:release=90:makeup=2,atempo={VEL:.4f},apad=pad_dur={TAIL}")
    fa = f"[0:a]aselect='{sel}',asetpts=N/SR/TB,{limpeza}"
    fv = f"[0:v]select='{sel}',setpts=N/(30*TB),setpts=PTS/{VEL:.4f},scale={W}:{H}:flags=lanczos,fps={FPS},tpad=stop_mode=clone:stop_duration={TAIL}[vo]"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-filter_complex", fa + ",loudnorm=I=-14:print_format=json[ao]",
                        "-map", "[ao]", "-f", "null", "-"], capture_output=True, text=True)
    if r.returncode: sys.exit(r.stderr[-2000:])
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ganho = -14.0 - float(m["input_i"])
    out = f"{saida}/base.mkv"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", video, "-filter_complex",
                    fv + ";" + fa + f",volume={ganho:.2f}dB,alimiter=limit=0.84:attack=3:release=50:level=false[ao]",
                    "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-c:a", "pcm_s16le",
                    "-t", f"{DUR:.3f}", out], check=True)
    return out

# ---------- 4. Elementos gráficos ----------
def caixa(txt, fonte, cor_txt, cor_fundo, pad=(36, 22), raio=20, icone=None):
    f = F(*fonte); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    linhas = txt.split("\n"); bbs = [d0.textbbox((0, 0), l, font=f) for l in linhas]
    lh = int(fonte[1] * 1.18); tw = max(b[2] - b[0] for b in bbs); ic = 70 if icone else 0
    w, h = tw + 2 * pad[0] + ic, lh * len(linhas) + 2 * pad[1]
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im); f2 = F(fonte[0], fonte[1] * 2)
    d.rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], raio * 2, fill=cor_fundo)
    if icone:
        cx, cy, r = (pad[0] + 26) * 2, h, 26 * 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=VERDE_OK if icone == "ok" else COBRE)
        if icone == "ok": d.line([(cx - 24, cy + 2), (cx - 6, cy + 20), (cx + 26, cy - 16)], fill=BRANCO, width=12, joint="curve")
        elif icone == "x":
            d.line([(cx - 18, cy - 18), (cx + 18, cy + 18)], fill=BRANCO, width=12); d.line([(cx - 18, cy + 18), (cx + 18, cy - 18)], fill=BRANCO, width=12)
        else: d.text((cx, cy), "!", font=F("Black", 60), fill=BRANCO, anchor="mm")
    y = pad[1] * 2
    for l in linhas:
        d.text(((pad[0] + ic) * 2, y), l, font=f2, fill=cor_txt); y += lh * 2
    return im.resize((w, h), Image.LANCZOS)

def faixa_nome():
    w, h = 900, 150
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 14 * 2, h * 2], fill=COBRE)
    d.rectangle([14 * 2, 0, w * 2, 92 * 2], fill=VERDE)
    d.rectangle([14 * 2, 92 * 2, w * 2, h * 2], fill=(31, 56, 60, 235))
    d.text((40 * 2, 46 * 2), "Kesley de Moraes Silva", font=F("Black", 52 * 2), fill=BRANCO, anchor="lm")
    d.text((40 * 2, 121 * 2), "OAB/SC nº 30.490  ·  Moraes Silva & Massimino Advogados", font=F("Regular", 30 * 2), fill="#E9D3C6", anchor="lm")
    return im.resize((w, h), Image.LANCZOS)

# ---------- 5. Linha do tempo ----------
def montar():
    moeda, sel_ok, sel_x = M.spr_moeda(), M.spr_selo(True), M.spr_selo(False)
    # Sobreposições sobre o rosto (tempo editado)
    sobre = [
        El(faixa_nome(), 75 + 450, 1150, T(1.3), "esq", 0.5, fim=T(8.4)),
        El(caixa("TEMA 1285 · STJ", ("Black", 46), BRANCO, COBRE), 540, 215, T(1.3), "pop", 0.45, fim=T(13.7)),
        El(caixa("Reserva de emergência\nem qualquer lugar", ("Bold", 44), VERDE, (244, 239, 234, 240), icone="ok"), 540, 1150, T(25.8), "pop", 0.45, fim=T(33.3)),
        El(caixa("2 EXCEÇÕES", ("Black", 54), BRANCO, COBRE, icone="!"), 540, 1150, T(47.8), "pop", 0.45, fim=T(54.5), loop="pulso", amp=0.03),
        El(caixa("Sobra do salário de um\nmês para o outro: PENHORÁVEL", ("Bold", 42), BRANCO, (31, 56, 60, 240), icone="x"), 540, 1150, T(76.0), "pop", 0.45, fim=T(82.6)),
        El(caixa("@mosimaadv", ("Black", 70), BRANCO, COBRE), 540, 1130, T(115.9), "pop", 0.5, loop="pulso", amp=0.03),
    ]
    # Inserções de tela cheia: (início, fim, fundo, elementos)
    ins = []
    t0, t1 = T(15.75), T(25.4)
    ins.append((t0, t1, fundo(VERDE), [
        El(texto("O STJ FIXOU A TESE", ("Bold", 56), COBRE), 540, 330, t0, "fade", 0.3),
        ("contador", T(15.85), T(16.9)),
        El(texto("SALÁRIOS MÍNIMOS", ("Black", 84), BRANCO), 540, 730, T(16.5), "subir", 0.4),
        El(texto("IMPENHORÁVEIS", ("Black", 70), COBRE), 540, 830, T(18.4), "pop", 0.45),
        El(M.spr_escudo(110), 540, 1050, T(21.5), "pop", 0.5, loop="pulso", amp=0.025),
        El(texto("se funcionarem como reserva", ("Regular", 46), CLARO), 540, 1230, T(23.3), "fade", 0.4),
    ]))
    t0, t1 = T(33.45), T(42.75)
    ins.append((t0, t1, fundo(AREIA), [
        El(texto("O QUE ESTÁ PROTEGIDO", ("Black", 72), VERDE), 540, 330, t0, "subir", 0.45),
        El(M.spr_cedulas().resize((210, 156), Image.LANCZOS), 220, 600, t0 + 0.1, "pop", 0.45),
        El(sel_ok, 310, 670, t0 + 0.35, "pop", 0.35),
        El(texto("RESERVA DE\nEMERGÊNCIA", ("Black", 54), VERDE), 650, 570, t0 + 0.2, "dir", 0.45),
        El(texto("conta, investimento ou dinheiro vivo", ("Regular", 34), CINZA), 650, 680, t0 + 0.3, "fade", 0.4),
        El(M.spr_cofrinho().resize((195, 172), Image.LANCZOS), 220, 880, T(34.9), "pop", 0.45),
        El(sel_ok, 310, 950, T(35.2), "pop", 0.35),
        El(texto("POUPANÇA", ("Black", 54), VERDE), 650, 860, T(35.0), "dir", 0.45),
        El(texto("mesmo com movimentação", ("Regular", 34), CINZA), 650, 930, T(38.2), "fade", 0.4),
        El(texto("mesmo com movimentação", ("Bold", 34), COBRE), 650, 930, T(41.0), "fade", 0.3),
    ]))
    t0, t1 = T(54.7), T(65.4)
    ins.append((t0, t1, fundo(VERDE_ESC), [
        El(texto("EXCEÇÃO 1", ("Black", 64), COBRE), 540, 330, t0, "subir", 0.45),
        El(M.spr_grafico_risco(), 540, 640, t0 + 0.2, "revelar", 1.4),
        El(sel_x, 690, 740, T(60.2), "pop", 0.35),
        El(texto("INVESTIMENTO DE\nALTO RISCO", ("Black", 70), BRANCO), 540, 910, T(58.8), "subir", 0.45),
        El(texto("conceito aberto: será\ndetalhado pelos tribunais", ("Regular", 46), CLARO), 540, 1150, T(62.2), "fade", 0.4),
    ]))
    t0, t1 = T(67.5), T(74.6)
    ins.append((t0, t1, fundo(VERDE_ESC), [
        El(texto("EXCEÇÃO 2", ("Black", 64), COBRE), 540, 330, t0, "subir", 0.45),
        El(M.spr_calendario(), 540, 640, t0 + 0.2, "pop", 0.45),
        *[El(moeda.resize((64, 64), Image.LANCZOS), 470 + i * 70, 760, T(71.0) + i * 0.15, "fade", 0.3, loop="flutuar", amp=6) for i in range(3)],
        El(sel_x, 690, 740, T(71.3), "pop", 0.35),
        El(texto("SOBRAS DE\nVALORES PROTEGIDOS", ("Black", 64), BRANCO), 540, 960, T(69.2), "subir", 0.45),
        El(texto("ex.: salário que ficou parado na conta", ("Regular", 40), CLARO), 540, 1150, T(72.4), "fade", 0.4),
    ]))
    # cartão final (cauda)
    t0 = DUR_FALA - 0.1
    lg = LOGO.resize((760, int(760 * LOGO.height / LOGO.width)), Image.LANCZOS)
    ins.append((t0, DUR + 1, fundo(BRANCO), [
        El(lg, 540, 760, t0, "pop", 0.5),
        El(texto("@mosimaadv", ("Black", 72), COBRE), 540, 1080, t0 + 0.3, "subir", 0.4),
        El(texto("mosima.com.br", ("Regular", 38), CINZA), 540, 1160, t0 + 0.5, "fade", 0.4),
    ]))
    return sobre, ins

CACHE = {}
def contador(base, t, t0, t1):
    if t < t0: return
    n = int(round(40 * out_cubic(clamp((t - t0) / (t1 - t0)))))
    if n not in CACHE: CACHE[n] = (texto("ATÉ", ("Bold", 64), COBRE), texto(str(n), ("Black", 230), BRANCO))
    a, b = CACHE[n]; base.alpha_composite(a, (540 - a.width // 2, 365)); base.alpha_composite(b, (540 - b.width // 2, 455))

def legenda(base, t):
    leg = next((l[2] for l in LEG if l[0] <= t < l[1]), "")
    if not leg or t > DUR_FALA: return
    if ("L", leg) not in CACHE: CACHE[("L", leg)] = caixa(leg, ("Bold", 52), BRANCO, (14, 28, 30, 235), pad=(28, 16), raio=16)
    im = CACHE[("L", leg)]; base.alpha_composite(im, (540 - im.width // 2, 1330 - im.height // 2))

def tela_ins(ins, t):
    bg = ins[2].copy(); compor(bg, [e for e in ins[3] if isinstance(e, El)], t)
    for e in ins[3]:
        if isinstance(e, tuple): contador(bg, t, e[1], e[2])
    return bg

def main():
    video, saida = sys.argv[1], sys.argv[2]; os.makedirs(saida, exist_ok=True)
    print(f"trechos {len(TRECHOS)} · bruta {BRUTA:.1f}s · velocidade {VEL:.3f} · final {DUR:.1f}s", flush=True)
    base = gerar_base(video, saida)
    sobre, ins = montar()
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", base, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{saida}/tema-1285-video.mp4"], stdin=subprocess.PIPE)
    tam, n, TR = W * H * 4, 0, 0.28
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam: break
        t = n / FPS; n += 1
        q = Image.frombytes("RGBA", (W, H), buf)
        compor(q, sobre, t)
        for it in ins:
            a, b = it[0], it[1]
            if a - 0.001 <= t <= b + TR:
                tela = tela_ins(it, t)
                if t < a + TR: off = int((1 - out_cubic((t - a) / TR)) * H)          # entra de baixo
                elif t > b: off = int(out_cubic((t - b) / TR) * H)                    # sai para baixo
                else: off = 0
                q.paste(tela.crop((0, 0, W, H - off)), (0, off)) if off < H else None
        legenda(q, t)
        enc.stdin.write(q.tobytes())
        if n % 300 == 0: print(f"  {t:5.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("ok", f"{saida}/tema-1285-video.mp4")

if __name__ == "__main__":
    main()
