#!/usr/bin/env python3
"""Motor de Reels no padrão Mosima ("action mode").

Lê um roteiro JSON (ver SKILL.md e exemplos/) e gera:
  - capa.png (+ capa-grade.png para conferir o recorte 4:5 do perfil)
  - <nome>.mp4 (1080x1920, 30 fps, -14 LUFS) com tela cheia / tela dividida, painéis animados,
    legenda curta o tempo todo e cartão final com o @.
  - legendas.srt

Uso:
  python3 reels.py roteiro.json                # tudo (capa + vídeo)
  python3 reels.py roteiro.json --capa         # só a capa
  python3 reels.py roteiro.json --quadros 2,17,44   # só quadros de conferência (PNG), sem vídeo
Todos os tempos do roteiro são em SEGUNDOS DO VÍDEO ORIGINAL; o motor converte para o tempo editado.
"""
import csv, json, math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(AQUI, "..", "assets")
W, H, FPS, SS = 1080, 1920, 30, 2

# ---------------- identidade visual ----------------
VERDE, VERDE_ESC, COBRE, CINZA, BRANCO, AREIA = "#2E5156", "#1F383C", "#C57A55", "#464646", "#FFFFFF", "#F4EFEA"
CLARO, VERDE_OK, ESCURO, POS, NEG = "#DCE6E7", "#3E8E6E", "#132629", "#7FC8A4", "#E9A07C"
CORES = {"verde": VERDE, "verde_escuro": VERDE_ESC, "cobre": COBRE, "cinza": CINZA, "branco": BRANCO, "areia": AREIA,
         "claro": CLARO, "positivo": POS, "negativo": NEG}
def cor(c): return CORES.get(c, c) if c else BRANCO
TEMA = {"claro": False}
def pc(c):
    """Cor de painel: no tema claro, branco vira verde-escuro e 'claro' vira cinza."""
    c = cor(c)
    if TEMA["claro"]:
        if c == BRANCO: return VERDE_ESC
        if c == CLARO: return CINZA
    return c
def borda(a_fill=22, a_out=60):
    return ((0, 0, 0, a_fill // 2), (31, 56, 60, a_out)) if TEMA["claro"] else ((255, 255, 255, a_fill), (255, 255, 255, a_out))
_FONTES = {}
def F(peso, tam):
    k = (peso, tam)
    if k not in _FONTES:
        arq = f"{peso}.ttf" if peso in ("Oswald", "Playfair", "PlayfairItalic") else f"Lato-{peso}.ttf"
        _FONTES[k] = ImageFont.truetype(os.path.join(ASSETS, "fontes", arq), tam)
    return _FONTES[k]
LOGO = Image.open(os.path.join(ASSETS, "logo-completo.png")).convert("RGBA")

# ---------------- utilidades de animação ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_cubic(p): return 1 - (1 - p) ** 3
def out_back(p, k=1.70158): p -= 1; return 1 + (k + 1) * p ** 3 + k * p ** 2

def sprite(w, h, desenho):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); desenho(ImageDraw.Draw(im), SS)
    return im.resize((w, h), Image.LANCZOS)

def texto(txt, peso, tam, c=BRANCO, esp=1.12, painel=True):
    c = pc(c) if painel else cor(c)
    linhas = txt.split("\n"); f2 = F(peso, tam * SS)
    larg = max(int(f2.getlength(l)) for l in linhas) // SS + 24; alt = int(tam * esp * len(linhas)) + 24
    def d(dr, s):
        y = 12 * s
        for l in linhas: dr.text((larg * s // 2, y), l, font=f2, fill=c, anchor="mt"); y += int(tam * esp * s)
    return sprite(larg, alt, d)

class El:
    def __init__(self, spr, x, y, t0, anim="pop", dur=0.45, loop=None, amp=0, de=None, fim=None):
        self.spr, self.x, self.y, self.t0, self.anim, self.dur, self.loop, self.amp, self.de, self.fim = spr, x, y, t0, anim, dur, loop, amp, de, fim
    def estado(self, t):
        if t < self.t0 or (self.fim is not None and t > self.fim): return None
        p = clamp((t - self.t0) / self.dur); sc, dx, dy, rot, al, rev = 1.0, 0, 0, 0, 1.0, 1.0; a = self.anim
        if a == "pop": sc = max(0.01, out_back(p))
        elif a == "subir": dy = (1 - out_cubic(p)) * 140; al = p
        elif a == "esq": dx = -(1 - out_cubic(p)) * 900
        elif a == "dir": dx = (1 - out_cubic(p)) * 900
        elif a == "fade": al = p
        elif a == "cair": dy = -(1 - p ** 2) * (self.de or 300)
        elif a == "revelar": rev = out_cubic(p)
        if p >= 1 and self.loop:
            u = t - self.t0 - self.dur
            if self.loop == "pulso": sc *= 1 + self.amp * math.sin(u * 6)
            elif self.loop == "balanco": rot += self.amp * math.sin(u * 2.4)
            elif self.loop == "flutuar": dy += self.amp * math.sin(u * 2.2)
        return sc, dx, dy, rot, al, rev

def compor(base, els, t):
    for e in els:
        st = e.estado(t)
        if not st: continue
        sc, dx, dy, rot, al, rev = st; im = e.spr
        if rev < 1:
            w = max(1, int(im.width * rev)); m = Image.new("RGBA", im.size, (0, 0, 0, 0)); m.paste(im.crop((0, 0, w, im.height)), (0, 0)); im = m
        if abs(sc - 1) > 0.005: im = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.BILINEAR)
        if abs(rot) > 0.1: im = im.rotate(rot, Image.BICUBIC, expand=True)
        if al < 0.999: a = im.getchannel("A").point(lambda v: int(v * clamp(al))); im = im.copy(); im.putalpha(a)
        base.alpha_composite(im, (int(e.x + dx - im.width / 2), int(e.y + dy - im.height / 2)))

# ---------------- biblioteca de ícones (desenho vetorial) ----------------
def ic_moeda(r=40):
    def d(dr, s):
        dr.ellipse([2*s, 2*s, (2*r-2)*s, (2*r-2)*s], fill=COBRE); dr.ellipse([10*s, 10*s, (2*r-10)*s, (2*r-10)*s], outline="#E9B396", width=4*s)
        dr.text((r*s, r*s), "R$", font=F("Black", int(r*0.7)*s), fill=BRANCO, anchor="mm")
    return sprite(2*r, 2*r, d)
def ic_escudo(r=52):
    def d(dr, s):
        w = 2*r
        dr.polygon([(r*s, 4*s), ((w-6)*s, 40*s), ((w-6)*s, int(r*1.05)*s), (r*s, int(r*2.2)*s), (6*s, int(r*1.05)*s), (6*s, 40*s)], fill=VERDE_OK)
        dr.line([(int(r*.55)*s, int(r*1.05)*s), (int(r*.88)*s, int(r*1.4)*s), (int(r*1.45)*s, int(r*.7)*s)], fill=BRANCO, width=int(r*.16)*s, joint="curve")
    return sprite(2*r, int(r*2.25), d)
def ic_cofrinho():
    def d(dr, s):
        dr.ellipse([20*s, 40*s, 220*s, 190*s], fill=COBRE); dr.polygon([(70*s, 60*s), (95*s, 10*s), (115*s, 55*s)], fill=COBRE)
        dr.rounded_rectangle([200*s, 95*s, 240*s, 135*s], 10*s, fill="#D9906B")
        dr.rectangle([60*s, 170*s, 90*s, 215*s], fill=COBRE); dr.rectangle([150*s, 170*s, 180*s, 215*s], fill=COBRE)
        dr.rounded_rectangle([100*s, 55*s, 150*s, 65*s], 4*s, fill=VERDE_ESC); dr.ellipse([165*s, 85*s, 180*s, 100*s], fill=VERDE_ESC)
    return sprite(250, 220, d)
def ic_cedulas():
    def d(dr, s):
        for i, c in enumerate(["#9CC3AE", "#B5D3C2", "#CFE3D6"]):
            o = i*18; dr.rounded_rectangle([(10+o)*s, (60-o)*s, (230+o)*s, (180-o)*s], 12*s, fill=c, outline=VERDE, width=4*s)
        dr.ellipse([110*s, 75*s, 170*s, 135*s], outline=VERDE, width=5*s); dr.text((140*s, 105*s), "R$", font=F("Black", 26*s), fill=VERDE, anchor="mm")
    return sprite(270, 200, d)
def ic_grafico_estavel():
    def d(dr, s):
        for i, h in enumerate([70, 100, 125, 150]): dr.rounded_rectangle([(20+i*55)*s, (190-h)*s, (60+i*55)*s, 190*s], 8*s, fill="#6FA8A0")
        dr.line([(20*s, 195*s), (245*s, 195*s)], fill=CLARO, width=5*s)
    return sprite(260, 210, d)
def ic_grafico_risco():
    def d(dr, s):
        pts = [(25, 150), (65, 60), (100, 170), (140, 40), (175, 185), (215, 70), (250, 195), (275, 205)]
        dr.line([(x*s, y*s) for x, y in pts], fill=COBRE, width=12*s, joint="curve")
    return sprite(300, 220, d)
def ic_grafico_volatil():
    def d(dr, s):
        for y in (60, 140, 220): dr.line([(10*s, y*s), (690*s, y*s)], fill=(255, 255, 255, 30), width=2*s)
        pts = [(10, 200), (80, 120), (140, 210), (210, 50), (280, 230), (350, 90), (420, 250), (490, 70), (560, 240), (630, 150), (690, 270)]
        dr.line([(x*s, y*s) for x, y in pts], fill=COBRE, width=12*s, joint="curve"); dr.ellipse([680*s, 260*s, 700*s, 280*s], fill=COBRE)
    return sprite(700, 290, d)
def ic_grafico_subida():
    def d(dr, s):
        for y in (60, 140, 220): dr.line([(10*s, y*s), (690*s, y*s)], fill=(255, 255, 255, 30), width=2*s)
        pts = [(10, 260), (120, 240), (230, 210), (340, 170), (450, 130), (560, 80), (690, 30)]
        dr.line([(x*s, y*s) for x, y in pts], fill=POS, width=12*s, joint="curve"); dr.ellipse([680*s, 20*s, 700*s, 40*s], fill=POS)
    return sprite(700, 290, d)
def ic_calendario():
    def d(dr, s):
        dr.rounded_rectangle([10*s, 30*s, 270*s, 230*s], 18*s, fill=AREIA)
        dr.rounded_rectangle([10*s, 30*s, 270*s, 85*s], 18*s, fill=COBRE); dr.rectangle([10*s, 65*s, 270*s, 85*s], fill=COBRE)
        for i in range(3):
            for j in range(5): dr.rounded_rectangle([(30+j*48)*s, (105+i*40)*s, (62+j*48)*s, (130+i*40)*s], 5*s, fill="#C9C2BB")
        for x in (60, 220): dr.rounded_rectangle([(x-8)*s, 10*s, (x+8)*s, 50*s], 6*s, fill=CINZA)
    return sprite(280, 240, d)
def ic_cadeado():
    def d(dr, s):
        dr.arc([50*s, 10*s, 190*s, 170*s], 180, 360, fill=COBRE, width=26*s)
        dr.rectangle([50*s, 88*s, 76*s, 120*s], fill=COBRE); dr.rectangle([164*s, 88*s, 190*s, 120*s], fill=COBRE)
        dr.rounded_rectangle([20*s, 110*s, 220*s, 280*s], 28*s, fill=COBRE)
        dr.ellipse([100*s, 160*s, 140*s, 200*s], fill=VERDE_ESC); dr.rectangle([112*s, 190*s, 128*s, 240*s], fill=VERDE_ESC)
    return sprite(240, 290, d)
def ic_martelo():
    def d(dr, s):
        dr.rounded_rectangle([150*s, 60*s, 175*s, 330*s], 10*s, fill="#8A5A3C"); dr.rounded_rectangle([60*s, 10*s, 265*s, 95*s], 20*s, fill=COBRE)
    return sprite(330, 340, d)
def ic_balanca():
    def d(dr, s):
        dr.rounded_rectangle([245*s, 40*s, 275*s, 300*s], 10*s, fill=AREIA); dr.rounded_rectangle([160*s, 290*s, 360*s, 325*s], 14*s, fill=AREIA)
        dr.rounded_rectangle([20*s, 50*s, 500*s, 66*s], 8*s, fill=COBRE)
        for x in (60, 460):
            dr.line([(x*s, 58*s), ((x-55)*s, 190*s)], fill=COBRE, width=5*s); dr.line([(x*s, 58*s), ((x+55)*s, 190*s)], fill=COBRE, width=5*s)
            dr.chord([((x-75)*s, 140*s), ((x+75)*s, 240*s)], 0, 180, fill=COBRE)
    return sprite(520, 330, d)
def ic_documento():
    def d(dr, s):
        dr.rounded_rectangle([10*s, 10*s, 290*s, 370*s], 20*s, fill=AREIA)
        dr.rectangle([40*s, 60*s, 260*s, 66*s], fill=COBRE)
        for i in range(7): dr.rounded_rectangle([40*s, (95+i*38)*s, (250-(i % 3)*40)*s, (110+i*38)*s], 6*s, fill="#B9C3C4")
    return sprite(300, 380, d)
def ic_casa():
    def d(dr, s):
        dr.polygon([(150*s, 10*s), (290*s, 130*s), (10*s, 130*s)], fill=COBRE); dr.rectangle([45*s, 125*s, 255*s, 270*s], fill=AREIA)
        dr.rectangle([125*s, 180*s, 175*s, 270*s], fill=VERDE)
    return sprite(300, 280, d)
def ic_alerta():
    def d(dr, s):
        dr.polygon([(170*s, 10*s), (330*s, 290*s), (10*s, 290*s)], fill=COBRE)
        dr.rounded_rectangle([155*s, 95*s, 185*s, 205*s], 12*s, fill=VERDE_ESC); dr.ellipse([152*s, 225*s, 188*s, 261*s], fill=VERDE_ESC)
    return sprite(340, 300, d)
def ic_seta():
    def d(dr, s):
        dr.line([(10*s, 40*s), (120*s, 40*s)], fill=COBRE, width=10*s); dr.polygon([(120*s, 18*s), (150*s, 40*s), (120*s, 62*s)], fill=COBRE)
    return sprite(160, 80, d)
ICONES = {"moeda": ic_moeda, "escudo": ic_escudo, "cofrinho": ic_cofrinho, "cedulas": ic_cedulas, "grafico_estavel": ic_grafico_estavel,
          "grafico_risco": ic_grafico_risco, "grafico_volatil": ic_grafico_volatil, "grafico_subida": ic_grafico_subida,
          "calendario": ic_calendario, "cadeado": ic_cadeado, "martelo": ic_martelo, "balanca": ic_balanca, "documento": ic_documento,
          "casa": ic_casa, "alerta": ic_alerta, "seta": ic_seta}

# ---------------- componentes do painel ----------------
def chip(txt, c=COBRE):
    f = F("Black", 30); w = int(f.getlength(txt)) + 70
    def d(dr, s):
        fi, ou = borda()
        dr.rounded_rectangle([0, 0, (w-1)*s, 54*s], 27*s, fill=fi, outline=ou, width=2*s)
        dr.ellipse([22*s, 21*s, 34*s, 33*s], fill=cor(c)); dr.text((46*s, 27*s), txt, font=F("Black", 30*s), fill=pc(BRANCO), anchor="lm")
    return sprite(w, 56, d)
def selo(ok=True, r=34):
    def d(dr, s):
        dr.ellipse([2*s, 2*s, (2*r-2)*s, (2*r-2)*s], fill=VERDE_OK if ok else COBRE, outline=BRANCO, width=4*s); c = r*s; k = r/40
        if ok: dr.line([(c-int(18*k)*s, c+int(2*k)*s), (c-int(5*k)*s, c+int(16*k)*s), (c+int(20*k)*s, c-int(14*k)*s)], fill=BRANCO, width=int(9*k)*s, joint="curve")
        else:
            q = int(15*k)*s; dr.line([(c-q, c-q), (c+q, c+q)], fill=BRANCO, width=int(9*k)*s); dr.line([(c-q, c+q), (c+q, c-q)], fill=BRANCO, width=int(9*k)*s)
    return sprite(2*r, 2*r, d)
def tile(rotulo, icone):
    def d(dr, s):
        fi, ou = borda(18, 50)
        dr.rounded_rectangle([0, 0, 299*s, 259*s], 28*s, fill=fi, outline=ou, width=2*s)
        dr.text((150*s, 222*s), rotulo, font=F("Bold", 32*s), fill=pc(BRANCO), anchor="mm")
    im = sprite(300, 260, d); ic = ICONES[icone]().copy(); ic.thumbnail((190, 150), Image.LANCZOS)
    im.alpha_composite(ic, ((300 - ic.width)//2, 30 + (150 - ic.height)//2)); return im
def linha(txt, valor, positivo=True):
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 519*s, 69*s], 16*s, fill=borda(16)[0])
        dr.text((24*s, 35*s), txt, font=F("Regular", 32*s), fill=pc(CLARO), anchor="lm")
        dr.text((496*s, 35*s), valor, font=F("Black", 34*s), fill=POS if positivo else NEG, anchor="rm")
    return sprite(520, 70, d)
def coluna(titulo, txt, c):
    def d(dr, s):
        fi, ou = borda(18, 50)
        dr.rounded_rectangle([0, 0, 379*s, 99*s], 20*s, fill=fi, outline=ou, width=2*s)
        dr.text((190*s, 34*s), titulo, font=F("Black", 34*s), fill=pc(BRANCO), anchor="mm"); dr.text((190*s, 72*s), txt, font=F("Regular", 28*s), fill=cor(c), anchor="mm")
    return sprite(380, 100, d)
def titulo_cheio(l1, l2, c2=COBRE):
    t1s, t2s = 64, 96
    while F("Black", t2s).getlength(l2) > 920: t2s -= 4
    while F("Black", t1s).getlength(l1) > 920: t1s -= 4
    t1 = texto(l1, "Black", t1s, painel=False); t2 = texto(l2, "Black", t2s, c2, painel=False)
    w, h = max(t1.width, t2.width) + 80, t1.height + t2.height + 40
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); im.alpha_composite(t1, ((w-t1.width)//2, 20)); im.alpha_composite(t2, ((w-t2.width)//2, 20+t1.height-10))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v*.85)))
    o = Image.new("RGBA", im.size, (0, 0, 0, 0)); o.alpha_composite(sh); o.alpha_composite(im); return o
def carimbo(txt, c=COBRE):
    f = F("Black", 64); w = int(f.getlength(txt)) + 80
    def d(dr, s):
        dr.rounded_rectangle([4*s, 4*s, (w-4)*s, 112*s], 18*s, outline=cor(c), width=8*s)
        dr.text((w*s//2, 58*s), txt, font=F("Black", 64*s), fill=cor(c), anchor="mm")
    return sprite(w, 116, d).rotate(-9, Image.BICUBIC, expand=True)
def check_linha(txt, marcado):
    def d(dr, s):
        fi, ou = borda(16, 60)
        dr.rounded_rectangle([0, 0, 959*s, 87*s], 20*s, fill=fi)
        dr.rounded_rectangle([22*s, 19*s, 72*s, 69*s], 12*s, outline=pc(BRANCO), width=5*s, fill=VERDE_OK if marcado else None)
        if marcado: dr.line([(31*s, 44*s), (43*s, 58*s), (63*s, 31*s)], fill=BRANCO, width=8*s, joint="curve")
        dr.text((96*s, 44*s), txt, font=F("Bold", 42*s), fill=pc(BRANCO), anchor="lm")
    return sprite(960, 88, d)

def com_sombra(im, raio=12, forca=0.8):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(raio)).point(lambda v: int(v * forca)))
    o = Image.new("RGBA", (im.width, im.height), (0, 0, 0, 0)); o.alpha_composite(sh); o.alpha_composite(im); return o
def numero(txt):
    def d(dr, s):
        dr.rounded_rectangle([4*s, 4*s, 92*s, 104*s], 14*s, fill=BRANCO, outline=(0, 0, 0, 255), width=3*s)
        dr.text((48*s, 55*s), txt, font=F("Oswald", 64*s), fill="#111111", anchor="mm")
    return com_sombra(sprite(96, 108, d), 8, 0.6)
def manchete(txt, c=COBRE, tam=58):
    linhas = txt.split("\n")
    while max(F("Oswald", tam).getlength(l) for l in linhas) > 880: tam -= 2
    return com_sombra(texto(txt, "Oswald", tam, c, esp=1.08, painel=False), 10, 0.9)
def titulo_serifa(l1, l2, c1="#F1E4D6", c2=COBRE):
    t1, t2 = 62, 70
    while F("Playfair", t1).getlength(l1) > 820: t1 -= 2
    while F("PlayfairItalic", t2).getlength(l2) > 820: t2 -= 2
    a = texto(l1, "Playfair", t1, c1, painel=False); b = texto(l2, "PlayfairItalic", t2, c2, painel=False)
    w = max(a.width, b.width); im = Image.new("RGBA", (w, a.height + b.height - 14), (0, 0, 0, 0))
    im.alpha_composite(a, ((w - a.width) // 2, 0)); im.alpha_composite(b, ((w - b.width) // 2, a.height - 14))
    return com_sombra(im, 14, 0.9)

ESTILOS = {"titulo": ("Black", 58, BRANCO), "destaque": ("Black", 54, COBRE), "corpo": ("Bold", 42, BRANCO),
           "nota": ("Regular", 40, CLARO), "grande": ("Black", 72, BRANCO), "alerta": ("Bold", 42, NEG)}

# ---------------- projeto ----------------
class Projeto:
    def __init__(self, caminho):
        self.base_dir = os.path.dirname(os.path.abspath(caminho))
        self.r = json.load(open(caminho, encoding="utf-8"))
        r = self.r; rel = lambda p: p if os.path.isabs(p) else os.path.join(self.base_dir, p)
        self.video, self.csv, self.saida = rel(r["video"]), rel(r["palavras_csv"]), rel(r.get("saida", "saida"))
        os.makedirs(self.saida, exist_ok=True)
        self.cortes = [tuple(c) for c in r["cortes"]]
        folga, pmax, self.cauda = r.get("folga", 0.12), r.get("pausa_max", 0.30), r.get("cauda", 1.6)
        self.linhas = list(csv.DictReader(open(self.csv, encoding="utf-8")))
        pal = [(float(l["start"]), float(l["end"])) for l in self.linhas if self.dentro(float(l["start"]), float(l["end"]))]
        tr = []
        for s, e in pal:
            if tr and s - tr[-1][1] + folga <= pmax: tr[-1][1] = e + folga
            else: tr.append([s - folga, e + folga])
        def corte(x): return next(c for c in self.cortes if c[0] - folga <= x <= c[1] + folga)
        self.trechos = [(max(a, corte(a + folga)[0]), min(b, corte(b - folga)[1])) for a, b in tr]
        bruta = sum(e - s for s, e in self.trechos)
        self.vel = clamp(bruta / (r.get("duracao_alvo", 74) - self.cauda), 1.0, r.get("vel_max", 1.08))
        self.dur_fala = bruta / self.vel; self.dur = self.dur_fala + self.cauda
        corr = r.get("correcoes", {}); por_indice = r.get("correcoes_indice", {})
        self.pw = []
        for l in self.linhas:
            s, e = float(l["start"]), float(l["end"])
            if not self.dentro(s, e): continue
            txt = por_indice.get(l["index"], corr.get(l["text"], l["text"]))
            self.pw.append((self.T(s), self.T(e), txt))
        self.leg = self.grupos()
        self.frases = [self.pw[0][0]] + [self.pw[i + 1][0] for i in range(len(self.pw) - 1) if self.pw[i][2][-1] in ".?!,"]
        self.destaques = {w.lower() for w in r.get("destaques", [])}

    def dentro(self, s, e): return any(a <= s and e <= b for a, b in self.cortes)
    def T(self, t):
        acc = 0.0
        for s, e in self.trechos:
            if t < s: return acc / self.vel
            if t <= e: return (acc + t - s) / self.vel
            acc += e - s
        return acc / self.vel

    def grupos(self):
        if self.r.get("legenda_estilo") == "frase": return self.grupos_frase()
        return self.grupos_curtos()

    def grupos_frase(self):
        out, at = [], []
        for p in self.pw:
            at.append(p); txt = " ".join(x[2] for x in at)
            if p[2][-1] in ".?!" or (p[2][-1] in ",:" and len(txt) >= 18) or len(txt) >= 34 or len(at) >= 7:
                out.append(at); at = []
        if at: out.append(at)
        res = []
        for i, g in enumerate(out):
            fim = g[-1][1] + 0.35
            if i + 1 < len(out): fim = min(fim, out[i + 1][0][0])
            res.append((g[0][0], fim, " ".join(x[2] for x in g).rstrip(".,:!")))
        return res

    def grupos_curtos(self):
        fracas = {"de", "para", "a", "o", "os", "as", "em", "um", "uma", "como", "se", "no", "na", "do", "da", "dos", "das", "ou", "que",
                  "e", "não", "ser", "pode", "foi", "ele", "ela", "nosso", "sua", "seu", "essa", "esse", "com", "mais", "vai", "à", "ao", "é"}
        out, at = [], []
        for p in self.pw:
            at.append(p); txt = " ".join(x[2] for x in at)
            if p[2][-1] in ".,?:!" or (len(at) >= 2 and p[2].lower() not in fracas) or len(at) >= 3 or len(txt) >= 16:
                out.append(at); at = []
        if at: out.append(at)
        res = []
        for i, g in enumerate(out):
            fim = g[-1][1] + 0.3
            if i + 1 < len(out): fim = min(fim, out[i + 1][0][0])
            res.append((g[0][0], fim, " ".join(x[2] for x in g).rstrip(".,:!")))
        return res

    # ---------- áudio e vídeo base ----------
    def gerar_base(self):
        out = os.path.join(self.saida, "base.mkv")
        if self.r.get("reusar_base") and os.path.exists(out):
            return out
        sel = "+".join(f"between(t,{s:.3f},{e:.3f})" for s, e in self.trechos)
        limpeza = ("pan=mono|c0=0.5*c0+0.5*c1,highpass=f=85,lowpass=f=15000,afftdn=nr=12:nf=-42:tn=1,deesser=i=0.4,"
                   "equalizer=f=250:t=q:w=1.2:g=-2,equalizer=f=3500:t=q:w=1.5:g=2,"
                   f"acompressor=threshold=-24dB:ratio=3:attack=6:release=90:makeup=2,atempo={self.vel:.4f},apad=pad_dur={self.cauda}")
        fa = f"[0:a]aselect='{sel}',asetpts=N/SR/TB,{limpeza}"
        fv = (f"[0:v]select='{sel}',setpts=N/({FPS}*TB),setpts=PTS/{self.vel:.4f},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
              f"crop={W}:{H},fps={FPS},tpad=stop_mode=clone:stop_duration={self.cauda}[vo]")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", self.video, "-vn", "-filter_complex", fa + ",loudnorm=I=-14:print_format=json[ao]",
                            "-map", "[ao]", "-f", "null", "-"], capture_output=True, text=True)
        if r.returncode: sys.exit(r.stderr[-2000:])
        m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1]); ganho = -14.0 - float(m["input_i"])
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", self.video, "-filter_complex",
                        fv + ";" + fa + f",volume={ganho:.2f}dB,alimiter=limit=0.84:attack=3:release=50:level=false[ao]",
                        "-map", "[vo]", "-map", "[ao]", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-c:a", "pcm_s16le",
                        "-t", f"{self.dur:.3f}", out], check=True)
        return out

    # ---------- elementos ----------
    def elemento(self, e, blocos_y0=0):
        tp = e["tipo"]; t = self.T(e["t"]); fim = self.T(e["fim"]) if "fim" in e else None
        x, y = e.get("x", 540), e.get("y", 400)
        anim = e.get("anim"); dur = e.get("dur", 0.45); loop = e.get("loop"); amp = e.get("amp", 0)
        if tp == "chip": spr = chip(e["texto"], e.get("cor", COBRE)); anim = anim or "fade"; dur = e.get("dur", 0.3)
        elif tp == "texto":
            peso, tam, c = ESTILOS[e.get("estilo", "corpo")]
            spr = texto(e["texto"], e.get("peso", peso), e.get("tam", tam), e.get("cor", c)); anim = anim or "subir"
        elif tp == "titulo": spr = titulo_cheio(e["l1"], e["l2"], cor(e.get("cor", COBRE))); anim = anim or "pop"; y = e.get("y", 1120)
        elif tp == "icone":
            spr = ICONES[e["nome"]](); esc = e.get("escala", 1.0)
            if esc != 1.0: spr = spr.resize((int(spr.width * esc), int(spr.height * esc)), Image.LANCZOS)
            anim = anim or ("revelar" if e["nome"].startswith("grafico_") and e["nome"] != "grafico_estavel" else "pop")
            if anim == "revelar": dur = e.get("dur", 1.4)
        elif tp == "selo": spr = selo(e.get("ok", True), e.get("r", 34)); anim = anim or "pop"; dur = e.get("dur", 0.35)
        elif tp == "tile": spr = tile(e["rotulo"], e["icone"]); anim = anim or "pop"; dur = e.get("dur", 0.4)
        elif tp == "linha": spr = linha(e["texto"], e["valor"], e.get("positivo", True)); anim = anim or "dir"; dur = e.get("dur", 0.35)
        elif tp == "coluna": spr = coluna(e["titulo"], e["texto"], e.get("cor", "positivo")); anim = anim or "pop"; dur = e.get("dur", 0.4)
        elif tp == "carimbo":
            spr = carimbo(e["texto"], e.get("cor", COBRE)); anim = anim or "pop"; dur = e.get("dur", 0.3)
        elif tp == "check":
            t_ok = self.T(e.get("t_ok", e["t"] + 0.5))
            return [El(check_linha(e["texto"], False), x, y, t, anim or "dir", dur, fim=t_ok),
                    El(check_linha(e["texto"], True), x, y, t_ok, "nenhum", 0.01, fim=fim)]
        elif tp == "numero": spr = numero(e["texto"]); x = e.get("x", 110); y = e.get("y", 300); anim = anim or "pop"; dur = e.get("dur", 0.3)
        elif tp == "manchete": spr = manchete(e["texto"], cor(e.get("cor", COBRE)), e.get("tam", 58)); y = e.get("y", 330); anim = anim or "fade"; dur = e.get("dur", 0.25)
        elif tp == "titulo_serifa": spr = titulo_serifa(e["l1"], e["l2"]); y = e.get("y", 330); anim = anim or "fade"; dur = e.get("dur", 0.4)
        elif tp == "pb": return [("pb", t, fim if fim is not None else t + 1.5)]
        elif tp == "moedas":
            return [El(ic_moeda(e.get("r", 40)), x + i * e.get("passo", 60), y, t + i * 0.15, "cair", 0.4, loop="flutuar", amp=5, de=120, fim=fim)
                    for i in range(e.get("n", 3))]
        elif tp == "contador":
            return [("contador", t, self.T(e["t2"]), e.get("de", 0), e["ate"], e.get("rotulo", ""), e.get("y", 205), e.get("sufixo", ""))]
        else: raise ValueError(f"tipo desconhecido: {tp}")
        return [El(spr, x, y, t, anim, dur, loop, amp, fim=fim)]

    def blocos(self):
        B = []
        for b in self.r["blocos"]:
            els = []
            for e in b.get("elementos", []): els += self.elemento(e)
            fim_b = self.T(b["ate"]) if b.get("ate") != "fim" else self.dur_fala - 0.1
            B.append((self.T(b["de"]), fim_b, b["modo"], els, b))
        return B

# ---------------- render ----------------
CACHE = {}
def desenhar_contador(base, t, c):
    _, t0, t1, de, ate, rot, y, suf = c
    if t < t0: return
    n = int(round(de + (ate - de) * out_cubic(clamp((t - t0) / max(0.01, t1 - t0)))))
    k = ("n", n, rot, suf)
    if k not in CACHE: CACHE[k] = (texto(rot, "Bold", 46, COBRE) if rot else None, texto(f"{n}{suf}", "Black", 190))
    a, b = CACHE[k]
    if a: base.alpha_composite(a, (540 - a.width // 2, y))
    base.alpha_composite(b, (540 - b.width // 2, y + (65 if a else 0)))

def legenda_frase(base, leg, t, y):
    txt = next((l[2] for l in leg if l[0] <= t < l[1]), "")
    if not txt: return
    k = ("F", txt)
    if k not in CACHE:
        palavras, linhas, at = txt.split(" "), [], ""
        for p_ in palavras:
            if at and F("Bold", 46).getlength(at + " " + p_) > 760: linhas.append(at); at = p_
            else: at = (at + " " + p_).strip()
        linhas.append(at)
        CACHE[k] = com_sombra(texto("\n".join(linhas), "Bold", 46, BRANCO, esp=1.18, painel=False), 8, 0.95)
    im = CACHE[k]; base.alpha_composite(im, (540 - im.width // 2, int(y - im.height / 2)))

def legenda(base, leg, t, y, destaques=frozenset()):
    txt = next((l[2] for l in leg if l[0] <= t < l[1]), "")
    if not txt: return
    if txt not in CACHE:
        f = F("Black", 140); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1))); bb = d0.textbbox((0, 0), txt, font=f, stroke_width=10)
        w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        x = 20 - bb[0]; esp = f.getlength(" ")
        for pal in txt.split(" "):
            limpo = pal.strip(".,:;!?").lower()
            d.text((x, h // 2), pal, font=f, fill=COBRE if limpo in destaques else BRANCO, anchor="lm", stroke_width=10, stroke_fill=(10, 20, 22, 230))
            x += f.getlength(pal) + esp
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(12)).point(lambda v: int(v * .6)))
        o = Image.new("RGBA", im.size, (0, 0, 0, 0)); o.alpha_composite(sh); o.alpha_composite(im); CACHE[txt] = o.resize((w // 2, h // 2), Image.LANCZOS)
    im = CACHE[txt]; base.alpha_composite(im, (540 - im.width // 2, int(y - im.height / 2)))

def painel_fundo(claro=False, centro_y=450):
    im = Image.new("RGBA", (W, H), AREIA if claro else ESCURO); g = Image.new("RGBA", (W, H), (255, 255, 255, 0) if claro else (46, 81, 86, 0))
    ImageDraw.Draw(g).ellipse([140, centro_y - 410, 940, centro_y + 410], fill=(255, 255, 255, 255) if claro else (46, 81, 86, 255))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(160))); return im

def cartao_final(handle, frase):
    im = painel_fundo(); lg = LOGO.copy(); lg.thumbnail((700, 400), Image.LANCZOS)
    box = Image.new("RGBA", (lg.width + 80, lg.height + 60), (255, 255, 255, 255)); m = Image.new("L", box.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, box.width - 1, box.height - 1], 36, fill=255); box.putalpha(m); box.alpha_composite(lg, (40, 30))
    return im, [El(box, 540, 760, 0, "pop", 0.5), El(texto(handle, "Black", 80, COBRE, painel=False), 540, 1060, 0.3, "subir", 0.4),
                El(texto(frase, "Regular", 38, CLARO, painel=False), 540, 1150, 0.5, "fade", 0.4)]

def mascara(w, h, r):
    m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, h * 2 - 1], int(r * 2), fill=255)
    return m.resize((w, h), Image.LANCZOS)
def lerp(a, b, k): return tuple(x + (y - x) * k for x, y in zip(a, b))

def config_layout(P):
    """Lê o layout do roteiro. estilo: 'split' (painel em cima) ou 'invertido' (rosto em cima, painel embaixo)."""
    lay = dict(P.r.get("layout", {}))
    inv = lay.get("estilo") == "invertido"
    lay.setdefault("cartao", (60, 150, 1020, 1000) if inv else (40, 860, 1040, 1860))
    lay.setdefault("recorte", (60, 60, 1020, 910) if inv else (40, 120, 1040, 1120))
    lay.setdefault("legenda_cheio", 1330)
    lay.setdefault("legenda_split", 920 if inv else 1560)
    lay.setdefault("painel_centro", 1230 if inv else 450)
    return lay

def aplicar_zoom(rosto, esc, cx, cy):
    if esc <= 1.001: return rosto
    w, h = W / esc, H / esc
    x0 = clamp(cx - w / 2, 0, W - w); y0 = clamp(cy - h / 2, 0, H - h)
    return rosto.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)

def quadro(P, B, fundo, fim_im, fim_els, rosto, t):
    lay = P.lay; CARD, CROP = tuple(lay["cartao"]), tuple(lay["recorte"])
    RAIO, TR, t_fim = 44, 0.35, P.dur_fala - 0.1
    # enquadramento base (para gravações de corpo inteiro) + punch-in nas frases dos blocos com "punch"
    z = lay.get("zoom_cheio", {}); esc = z.get("escala", 1.0); cx, cy = z.get("centro", (540, 960))
    bloco_atual = next((b for b in B if b[0] <= t < b[1]), None)
    if bloco_atual and bloco_atual[4].get("punch"):
        idx = max([i for i, f in enumerate(P.frases) if f <= t] or [0]); ini = P.frases[idx]
        alvo = 1 + bloco_atual[4].get("punch_forca", 0.12) * (idx % 2)
        ant = 1 + bloco_atual[4].get("punch_forca", 0.12) * ((idx - 1) % 2)
        esc *= ant + (alvo - ant) * out_cubic(clamp((t - ini) / 0.14))
    rosto = aplicar_zoom(rosto, esc, cx, cy)
    pb = [(e[1], e[2]) for b in B for e in b[3] if isinstance(e, tuple) and e[0] == "pb"]
    if any(a <= t <= b for a, b in pb):
        g = rosto.convert("L").point(lambda v: int(v * 0.82)).convert("RGBA")
        sombra = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sombra)
        for yy in range(0, 700, 4): ds.rectangle([0, yy, W, yy + 4], fill=(0, 0, 0, int(200 * (1 - yy / 700))))
        g.alpha_composite(sombra); rosto = g
    if t >= t_fim:
        q = fim_im.copy(); compor(q, fim_els, t - t_fim); k = out_cubic(clamp((t - t_fim) / 0.3))
        if k < 1: r2 = rosto.copy(); r2.putalpha(int(255 * (1 - k))); q.alpha_composite(r2)
        return q
    k = 0.0
    for a, b, modo, _, _o in B:
        if modo != "split": continue
        antes = any(x[1] == a and x[2] == "split" for x in B); depois = any(x[0] == b and x[2] == "split" for x in B)
        if a <= t <= b: k = max(k, 1 if antes else min(1, (t - a) / TR))
        elif b < t < b + TR and not depois: k = max(k, 1 - (t - b) / TR)
    k = out_cubic(clamp(k)); cortina = lay.get("transicao") == "cortina"
    dx = int((1 - k) * W) if cortina else 0
    if k <= 0.001: q = rosto.copy()
    else:
        if cortina:
            q = rosto.copy(); q.alpha_composite(fundo.crop((0, 0, W - dx, H)), (dx, 0)) if dx < W else None
        else: q = fundo.copy()
        card = [int(v) for v in lerp((0, 0, W, H), CARD, k)]; crop = [int(v) for v in lerp((0, 0, W, H), CROP, k)]
        cw, ch = card[2] - card[0], card[3] - card[1]; face = rosto.crop(crop).resize((cw, ch), Image.BILINEAR); face.putalpha(mascara(cw, ch, RAIO * k))
        sh = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, cw + 40, ch + 40], RAIO, fill=(0, 0, 0, int(120 * k)))
        q.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)), (card[0] - 40, card[1] - 40)); q.alpha_composite(face, (card[0], card[1]))
    for a, b, modo, els, _o in B:
        if not (a - 0.01 <= t <= b + 0.25): continue
        cam = Image.new("RGBA", (W, H), (0, 0, 0, 0)); compor(cam, [e for e in els if isinstance(e, El)], t)
        for e in els:
            if isinstance(e, tuple) and e[0] == "contador": desenhar_contador(cam, t, e)
        if t > b: cam.putalpha(cam.getchannel("A").point(lambda v, f=1 - (t - b) / 0.25: int(v * f)))
        elif modo == "split" and k < 1 and not cortina: cam.putalpha(cam.getchannel("A").point(lambda v, f=k: int(v * f)))
        if modo == "split" and cortina and dx: q.alpha_composite(cam.crop((0, 0, W - dx, H)), (dx, 0))
        else: q.alpha_composite(cam)
    y_leg = lay["legenda_cheio"] * (1 - k) + lay["legenda_split"] * k
    if P.r.get("legenda_estilo") == "frase": legenda_frase(q, P.leg, t, y_leg)
    else: legenda(q, P.leg, t, y_leg, P.destaques)
    if P.r.get("marca_dagua"):
        k_ = ("MD", P.r.get("handle"))
        if k_ not in CACHE: CACHE[k_] = com_sombra(texto(P.r.get("handle", "@mosimaadv"), "Bold", 26, BRANCO, painel=False), 6, 0.8)
        md = CACHE[k_]; q.alpha_composite(md, (W - md.width - 30, 200))
    if P.r.get("barra_progresso"):
        d = ImageDraw.Draw(q); d.rectangle([0, 0, W, 12], fill=(0, 0, 0, 90)); d.rectangle([0, 0, int(W * clamp(t / t_fim)), 12], fill=COBRE)
    return q

def render(P, so_quadros=None):
    P.lay = config_layout(P); TEMA["claro"] = P.lay.get("tema") == "claro"
    base = P.gerar_base(); B = P.blocos(); fundo = painel_fundo(TEMA["claro"], P.lay["painel_centro"])
    fim_im, fim_els = cartao_final(P.r.get("handle", "@mosimaadv"), P.r.get("frase_final", "Decisões do STJ explicadas de forma simples"))
    nome = P.r.get("nome", "reels")
    if so_quadros:
        for t in so_quadros:
            fr = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", base, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgba", "-"], capture_output=True).stdout
            quadro(P, B, fundo, fim_im, fim_els, Image.frombytes("RGBA", (W, H), fr), t).convert("RGB").save(os.path.join(P.saida, f"quadro-{t}.png"))
        return
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", base, "-f", "rawvideo", "-pix_fmt", "rgba", "-"], stdout=subprocess.PIPE)
    saida = os.path.join(P.saida, f"{nome}.mp4")
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", base, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", saida], stdin=subprocess.PIPE)
    tam, n = W * H * 4, 0
    while True:
        buf = dec.stdout.read(tam)
        if len(buf) < tam: break
        t = n / FPS; n += 1
        enc.stdin.write(quadro(P, B, fundo, fim_im, fim_els, Image.frombytes("RGBA", (W, H), buf), t).tobytes())
        if n % 300 == 0: print(f"  {t:5.1f}s", flush=True)
    enc.stdin.close(); enc.wait(); dec.wait()
    ts = lambda t: f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(t * 1000 % 1000):03d}"
    with open(os.path.join(P.saida, "legendas.srt"), "w", encoding="utf-8") as fh:
        for i, (a, b, x) in enumerate(P.leg, 1): fh.write(f"{i}\n{ts(a)} --> {ts(b)}\n{x}\n\n")
    print(f"ok: {saida} · {P.dur:.1f}s · velocidade {P.vel:.3f}")

# ---------------- capa ----------------
def capa(P):
    c = P.r["capa"]; out = os.path.join(P.saida, "capa.png"); tmp = out + ".q.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(c["instante"]), "-i", P.video, "-frames:v", "1",
                    "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},unsharp=5:5:0.6", tmp], check=True)
    foto = Image.open(tmp).convert("RGBA"); os.remove(tmp)
    z = c.get("zoom", 1.25); fw, fh = int(W * z), int(H * z); dy = c.get("deslocamento_y", 60)
    im = foto.resize((fw, fh), Image.LANCZOS).crop(((fw - W) // 2, dy, (fw - W) // 2 + W, dy + H))
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(grad)
    for y in range(820, H):
        a = min(245, int(245 * ((y - 820) / 420) ** 1.3)) if y < 1240 else 245; g.line([(0, y), (W, y)], fill=(31, 56, 60, a))
    im.alpha_composite(grad); d = ImageDraw.Draw(im)
    if c.get("selo"):
        f = F("Black", 40); w = int(f.getlength(c["selo"])) + 60
        d.rounded_rectangle([540 - w // 2, 1010, 540 + w // 2, 1080], 16, fill=COBRE); d.text((540, 1045), c["selo"], font=f, fill=BRANCO, anchor="mm")
    y = 1110
    for linha_, cr in [(c["linha1"], BRANCO), (c["linha2"], COBRE)]:
        tam = 96
        while F("Black", tam).getlength(linha_) > 980: tam -= 4
        d.text((540, y), linha_, font=F("Black", tam), fill=cr, anchor="mt"); y += int(tam * 1.1)
    if c.get("subtitulo"): d.text((540, y + 4), c["subtitulo"], font=F("Regular", 40), fill=BRANCO, anchor="mt"); y += 56
    d.rectangle([440, y + 22, 640, y + 28], fill=COBRE)
    d.text((540, y + 60), c["nome"], font=F("Bold", 46), fill=BRANCO, anchor="mt")
    d.text((540, y + 118), c["registro"], font=F("Regular", 30), fill="#E9D3C6", anchor="mt")
    d.rectangle([0, H - 40, W, H], fill=COBRE)
    im.convert("RGB").save(out, quality=95)
    chk = im.convert("RGB"); dc = ImageDraw.Draw(chk); top = (H - 1350) // 2
    dc.rectangle([0, top, W - 1, top + 1350], outline="#FF3B30", width=6); chk.resize((540, 960)).save(out.replace(".png", "-grade.png"))
    print("ok:", out)

if __name__ == "__main__":
    P = Projeto(sys.argv[1])
    if "--capa" in sys.argv: capa(P)
    elif "--quadros" in sys.argv: render(P, [float(x) for x in sys.argv[sys.argv.index("--quadros") + 1].split(",")])
    else: capa(P); render(P)
