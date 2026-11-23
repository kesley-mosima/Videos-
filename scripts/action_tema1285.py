"""Reels Tema 1285 no formato da referência ("action mode"): tela dividida com painel animado
em cima e o advogado num cartão arredondado embaixo; tela cheia nos ganchos; legenda curta só
quando não há explicação na tela. Identidade Mosima.

Uso: python3 action_tema1285.py <video_original.mp4> <pasta_saida>
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import motion_tema1285 as M
import video_tema1285 as V
from motion_tema1285 import El, texto, compor, clamp, out_cubic, out_back
from render_tema1285 import F, VERDE, VERDE_ESC, COBRE, CINZA, BRANCO, AREIA, LOGO, SIMB

W, H, FPS = 1080, 1920, 30
T = V.T
CLARO, VERDE_OK, ESCURO = "#DCE6E7", "#3E8E6E", "#132629"
CARD = (40, 860, 1040, 1860)          # cartão do advogado na tela dividida
CROP = (40, 120, 1040, 1120)          # região do quadro original mostrada no cartão
RAIO = 44

# ---------------- peças gráficas ----------------
def painel_fundo():
    im = Image.new("RGBA", (W, H), ESCURO)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    g.ellipse([140, 40, 940, 860], fill=(46, 81, 86, 255))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(160)))
    return im

def chip(txt, cor=COBRE):
    f = F("Black", 30); w = int(f.getlength(txt)) + 70
    def d(dr, s):
        dr.rounded_rectangle([0, 0, (w - 1) * s, 54 * s], 27 * s, fill=(255, 255, 255, 22), outline=(255, 255, 255, 60), width=2 * s)
        dr.ellipse([22 * s, 21 * s, 34 * s, 33 * s], fill=cor)
        dr.text((46 * s, 27 * s), txt, font=F("Black", 30 * s), fill=BRANCO, anchor="lm")
    return M.sprite(w, 56, d)

def tile(rotulo, icone):
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 299 * s, 259 * s], 28 * s, fill=(255, 255, 255, 18), outline=(255, 255, 255, 50), width=2 * s)
        dr.text((150 * s, 222 * s), rotulo, font=F("Bold", 32 * s), fill=BRANCO, anchor="mm")
    im = M.sprite(300, 260, d)
    ic = icone.copy(); ic.thumbnail((190, 150), Image.LANCZOS)
    im.alpha_composite(ic, ((300 - ic.width) // 2, 30 + (150 - ic.height) // 2))
    return im

def selo(ok=True, r=34): return M.spr_selo(ok, r)

def linha_mov(txt, valor, pos=True):
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 519 * s, 69 * s], 16 * s, fill=(255, 255, 255, 16))
        dr.text((24 * s, 35 * s), txt, font=F("Regular", 32 * s), fill=CLARO, anchor="lm")
        dr.text((496 * s, 35 * s), valor, font=F("Black", 34 * s), fill="#7FC8A4" if pos else "#E9A07C", anchor="rm")
    return M.sprite(520, 70, d)

def grafico_volatil():
    def d(dr, s):
        for y in (60, 140, 220): dr.line([(10 * s, y * s), (690 * s, y * s)], fill=(255, 255, 255, 30), width=2 * s)
        pts = [(10, 200), (80, 120), (140, 210), (210, 50), (280, 230), (350, 90), (420, 250), (490, 70), (560, 240), (630, 150), (690, 270)]
        dr.line([(x * s, y * s) for x, y in pts], fill=COBRE, width=12 * s, joint="curve")
        dr.ellipse([680 * s, 260 * s, 700 * s, 280 * s], fill=COBRE)
    return M.sprite(700, 290, d)

def coluna_mes(titulo, txt, cor):
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 379 * s, 99 * s], 20 * s, fill=(255, 255, 255, 18), outline=(255, 255, 255, 50), width=2 * s)
        dr.text((190 * s, 34 * s), titulo, font=F("Black", 34 * s), fill=BRANCO, anchor="mm")
        dr.text((190 * s, 72 * s), txt, font=F("Regular", 28 * s), fill=cor, anchor="mm")
    return M.sprite(380, 100, d)

def seta():
    def d(dr, s):
        dr.line([(10 * s, 40 * s), (120 * s, 40 * s)], fill=COBRE, width=10 * s)
        dr.polygon([(120 * s, 18 * s), (150 * s, 40 * s), (120 * s, 62 * s)], fill=COBRE)
    return M.sprite(160, 80, d)

def titulo_cheio(l1, l2, cor2=COBRE):
    """Título de tela cheia com brilho (como na referência), legível sobre o vídeo."""
    t1 = texto(l1, ("Black", 64), BRANCO); t2 = texto(l2, ("Black", 96), cor2)
    w, h = max(t1.width, t2.width) + 80, t1.height + t2.height + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    im.alpha_composite(t1, ((w - t1.width) // 2, 20)); im.alpha_composite(t2, ((w - t2.width) // 2, 20 + t1.height - 10))
    sombra = Image.new("RGBA", im.size, (0, 0, 0, 0)); sombra.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.85)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.alpha_composite(sombra); out.alpha_composite(im)
    return out

# ---------------- roteiro visual ----------------
def montar():
    moeda = M.spr_moeda(40)
    # blocos: (início, fim, modo, elementos)  — modo "cheio" (rosto em tela cheia) ou "split"
    B = []
    # 1 · gancho em tela cheia
    B.append((T(1.15), T(14.25), "cheio", [
        El(titulo_cheio("COBRANDO OU", "SENDO COBRADO?"), 540, 1120, T(1.2), "pop", 0.5, fim=T(8.3)),
        El(titulo_cheio("O QUE PODE SER", "PENHORADO", BRANCO), 540, 1120, T(8.4), "pop", 0.45),
    ]))
    # 2 · tese: 40 salários mínimos
    B.append((T(14.25), T(25.5), "split", [
        El(chip("TESE FIXADA · STJ"), 540, 180, T(14.3), "fade", 0.3),
        ("contador", T(15.85), T(16.9)),
        El(texto("SALÁRIOS MÍNIMOS", ("Black", 58), BRANCO), 540, 545, T(16.5), "subir", 0.4),
        El(M.spr_escudo(52), 270, 690, T(18.4), "pop", 0.45),
        El(texto("IMPENHORÁVEIS", ("Black", 56), COBRE), 600, 680, T(18.5), "dir", 0.45),
        El(texto("se funcionarem como reserva", ("Regular", 40), CLARO), 540, 790, T(22.9), "fade", 0.4),
    ]))
    # 3 · em qualquer lugar
    icones = [("Conta", M.spr_grafico_estavel()), ("Investimento", M.spr_grafico_risco()), ("Dinheiro vivo", M.spr_cedulas())]
    els = [El(chip("SEJA ONDE ESTIVER"), 540, 180, T(25.6), "fade", 0.3)]
    for i, (nome, ic) in enumerate(icones):
        x = 200 + i * 340; t = T(26.0) + i * 0.3
        els += [El(tile(nome, ic), x, 420, t, "pop", 0.4), El(selo(True), x + 115, 300, T(28.3) + i * 0.15, "pop", 0.3)]
    els.append(El(texto("RESERVA DE EMERGÊNCIA", ("Black", 54), COBRE), 540, 640, T(28.2), "subir", 0.4))
    els.append(El(texto("= não paga a dívida", ("Regular", 42), CLARO), 540, 730, T(30.0), "fade", 0.4))
    B.append((T(25.5), T(33.3), "split", els))
    # 4 · poupança
    B.append((T(33.3), T(43.6), "split", [
        El(chip("POUPANÇA"), 540, 180, T(33.4), "fade", 0.3),
        El(M.spr_cofrinho().resize((240, 211), Image.LANCZOS), 190, 470, T(35.0), "pop", 0.45),
        El(linha_mov("Depósito", "+ R$"), 700, 330, T(38.3), "dir", 0.35),
        El(linha_mov("Pagamento", "− R$", False), 700, 415, T(38.8), "dir", 0.35),
        El(linha_mov("Pix recebido", "+ R$"), 700, 500, T(39.4), "dir", 0.35),
        El(linha_mov("Boleto", "− R$", False), 700, 585, T(40.0), "dir", 0.35),
        El(selo(True, 40), 300, 560, T(41.4), "pop", 0.35),
        El(texto("protegida mesmo com movimentação", ("Bold", 40), BRANCO), 540, 730, T(41.3), "fade", 0.4),
    ]))
    # 5 · virada: duas exceções (tela cheia)
    B.append((T(43.6), T(54.5), "cheio", [
        El(titulo_cheio("MAS ATENÇÃO:", "2 EXCEÇÕES"), 540, 1120, T(47.8), "pop", 0.5),
    ]))
    # 6 · exceção 1 — alto risco
    B.append((T(54.5), T(67.3), "split", [
        El(chip("EXCEÇÃO 1"), 540, 180, T(54.6), "fade", 0.3),
        El(grafico_volatil(), 540, 410, T(55.3), "revelar", 1.6),
        El(texto("INVESTIMENTO DE ALTO RISCO", ("Black", 50), BRANCO), 540, 620, T(58.8), "subir", 0.4),
        El(selo(False, 36), 170, 720, T(60.4), "pop", 0.35),
        El(texto("pode ser penhorado", ("Bold", 42), "#E9A07C"), 470, 720, T(60.5), "dir", 0.4),
        El(chip("CONCEITO ABERTO", CLARO), 540, 805, T(62.3), "pop", 0.4),
    ]))
    # 7 · exceção 2 — sobras
    B.append((T(67.3), T(82.8), "split", [
        El(chip("EXCEÇÃO 2"), 540, 180, T(67.4), "fade", 0.3),
        El(texto("SOBRAS DE VALORES PROTEGIDOS", ("Black", 46), BRANCO), 540, 285, T(70.8), "subir", 0.4),
        El(coluna_mes("MÊS 1", "salário: protegido", "#7FC8A4"), 250, 430, T(76.3), "pop", 0.4),
        El(seta(), 540, 430, T(77.6), "esq", 0.35),
        El(coluna_mes("MÊS 2", "o que sobrou", "#E9A07C"), 830, 430, T(78.0), "pop", 0.4),
        *[El(moeda, 770 + i * 60, 560, T(78.5) + i * 0.15, "cair", 0.4, de=120, loop="flutuar", amp=5) for i in range(3)],
        El(selo(False, 40), 540, 680, T(81.0), "pop", 0.35),
        El(texto("PODE SER PENHORADA", ("Black", 50), COBRE), 540, 780, T(81.1), "subir", 0.4),
    ]))
    # 8 · CTA em tela cheia
    B.append((T(112.0), V.DUR_FALA - 0.1, "cheio", [
        El(titulo_cheio("SIGA", "@mosimaadv"), 540, 1120, T(115.8), "pop", 0.5),
    ]))
    return B

def cartao_final():
    im = painel_fundo(); d = ImageDraw.Draw(im)
    lg = LOGO.copy(); lg.thumbnail((700, 400), Image.LANCZOS)
    box = Image.new("RGBA", (lg.width + 80, lg.height + 60), (255, 255, 255, 255)); m = Image.new("L", box.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 36, fill=255); box.putalpha(m); box.alpha_composite(lg, (40, 30))
    return im, [El(box, 540, 760, 0, "pop", 0.5), El(texto("@mosimaadv", ("Black", 80), COBRE), 540, 1060, 0.3, "subir", 0.4),
                El(texto("Decisões do STJ explicadas de forma simples", ("Regular", 38), CLARO), 540, 1150, 0.5, "fade", 0.4)]

# ---------------- legenda curta (só em tela cheia sem título) ----------------
FRACAS = V.FRACAS
def grupos_curtos():
    out, at = [], []
    for p in V.pw:
        at.append(p); txt = " ".join(x[2] for x in at)
        if p[2][-1] in ".,?:" or (len(at) >= 2 and p[2].lower() not in FRACAS) or len(at) >= 3 or len(txt) >= 16:
            out.append(at); at = []
    if at: out.append(at)
    res = []
    for i, g in enumerate(out):
        fim = g[-1][1] + 0.3
        if i + 1 < len(out): fim = min(fim, out[i + 1][0][0])
        res.append((g[0][0], fim, " ".join(x[2] for x in g).rstrip(".,:")))
    return res
LEG = grupos_curtos()
CACHE = {}
def legenda(base, t):
    leg = next((l[2] for l in LEG if l[0] <= t < l[1]), "")
    if not leg: return
    if leg not in CACHE:
        f = F("Black", 70 * 2); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); bb = d0.textbbox((0, 0), leg, font=f, stroke_width=10)
        w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.text((w // 2, h // 2), leg, font=f, fill=BRANCO, anchor="mm", stroke_width=10, stroke_fill=(10, 20, 22, 230))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * 0.6)))
        o = Image.new("RGBA", im.size, (0, 0, 0, 0)); o.alpha_composite(sh); o.alpha_composite(im)
        CACHE[leg] = o.resize((w // 2, h // 2), Image.LANCZOS)
    im = CACHE[leg]; base.alpha_composite(im, (540 - im.width // 2, 1300 - im.height // 2))

def contador(base, t, t0, t1):
    if t < t0: return
    n = int(round(40 * out_cubic(clamp((t - t0) / (t1 - t0)))))
    k = ("n", n)
    if k not in CACHE: CACHE[k] = (texto("ATÉ", ("Bold", 46), COBRE), texto(str(n), ("Black", 190), BRANCO))
    a, b = CACHE[k]; base.alpha_composite(a, (540 - a.width // 2, 205)); base.alpha_composite(b, (540 - b.width // 2, 270))

# ---------------- composição ----------------
def lerp(a, b, k): return tuple(x + (y - x) * k for x, y in zip(a, b))

def mascara(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], int(r * 2), fill=255)
    return m.resize((w, h), Image.LANCZOS)

def main():
    video, saida = sys.argv[1], sys.argv[2]; os.makedirs(saida, exist_ok=True)
    base = f"{saida}/base.mkv"
    if not os.path.exists(base): base = V.gerar_base(video, saida)
    blocos = montar(); fundo = painel_fundo(); fim_im, fim_els = cartao_final()
    t_fim = V.DUR_FALA - 0.1
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", base, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", f"{saida}/tema-1285-action.mp4"], stdin=subprocess.PIPE)
    TR, tam, n = 0.35, W * H * 4, 0
    def split_k(t):
        """0 = rosto em tela cheia, 1 = tela dividida (com transição suave)."""
        k = 0.0
        for a, b, modo, _ in blocos:
            if modo != "split": continue
            if a <= t <= b: k = max(k, min(1, (t - a) / TR) if not any(x[1] == a and x[2] == "split" for x in blocos) else 1)
            elif b < t < b + TR and not any(x[0] == b and x[2] == "split" for x in blocos): k = max(k, 1 - (t - b) / TR)
        return out_cubic(clamp(k))
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam: break
        t = n / FPS; n += 1
        rosto = Image.frombytes("RGBA", (W, H), buf)
        if t >= t_fim:
            q = fim_im.copy(); compor(q, fim_els, t - t_fim)
            k = out_cubic(clamp((t - t_fim) / 0.3))
            if k < 1: rosto.putalpha(int(255 * (1 - k))); q.alpha_composite(rosto)
            enc.stdin.write(q.tobytes()); continue
        k = split_k(t)
        if k <= 0.001:
            q = rosto
        else:
            q = fundo.copy()
            card = [int(v) for v in lerp((0, 0, W, H), CARD, k)]; crop = [int(v) for v in lerp((0, 0, W, H), CROP, k)]
            cw, ch = card[2] - card[0], card[3] - card[1]
            face = rosto.crop(crop).resize((cw, ch), Image.BILINEAR)
            face.putalpha(mascara(cw, ch, RAIO * k))
            sombra = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0)); ImageDraw.Draw(sombra).rounded_rectangle([40, 50, cw + 40, ch + 40], RAIO, fill=(0, 0, 0, int(120 * k)))
            q.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(18)), (card[0] - 40, card[1] - 40))
            q.alpha_composite(face, (card[0], card[1]))
        # elementos do bloco ativo (com saída em fade de 0,25 s)
        explicando = False
        for a, b, modo, els in blocos:
            if not (a - 0.01 <= t <= b + 0.25): continue
            camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            compor(camada, [e for e in els if isinstance(e, El)], t)
            for e in els:
                if isinstance(e, tuple): contador(camada, t, e[1], e[2])
            if t > b: camada.putalpha(camada.getchannel("A").point(lambda v, f=1 - (t - b) / 0.25: int(v * f)))
            elif modo == "split" and k < 1: camada.putalpha(camada.getchannel("A").point(lambda v, f=k: int(v * f)))
            q.alpha_composite(camada)
            if modo == "split" or any(e.estado(t) for e in els if isinstance(e, El)): explicando = True
        if not explicando: legenda(q, t)
        enc.stdin.write(q.tobytes())
        if n % 300 == 0: print(f"  {t:5.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    print("ok", f"{saida}/tema-1285-action.mp4")

if __name__ == "__main__":
    main()
