"""Versão motion graphics do Reels Tema 1285: ilustrações vetoriais animadas na identidade Mosima.

Reaproveita cortes, legendas e tempos de render_tema1285.py.
Uso: python3 motion_tema1285.py <audio_original.m4a> <pasta_saida> [--ate SEGUNDOS] [--de SEGUNDOS]
"""
import math, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import render_tema1285 as R

W, H, FPS, SS = 1080, 1920, 30, 2          # SS = supersampling dos desenhos
VERDE, VERDE_ESC, COBRE, CINZA, BRANCO, AREIA = R.VERDE, R.VERDE_ESC, R.COBRE, R.CINZA, R.BRANCO, R.AREIA
VERDE_OK, CLARO = "#3E8E6E", "#DCE6E7"
F = R.F
T = R.novo_t                                 # tempo original -> tempo editado

# ---------------- utilidades ----------------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def out_cubic(p): return 1 - (1 - p) ** 3
def out_back(p, k=1.70158): p -= 1; return 1 + (k + 1) * p ** 3 + k * p ** 2

def sprite(w, h, desenho):
    """Desenha em 2x e reduz (antisserrilhado)."""
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); desenho(ImageDraw.Draw(im), SS)
    return im.resize((w, h), Image.LANCZOS)

def texto(txt, fonte, cor, linhas_esp=1.12):
    linhas = txt.split("\n"); f2 = F(fonte[0], fonte[1] * SS)
    larg = max(f2.getbbox(l)[2] for l in linhas) // SS + 20; alt = int(fonte[1] * linhas_esp * len(linhas)) + 20
    def d(dr, s):
        y = 10 * s
        for l in linhas:
            dr.text((larg * s // 2, y), l, font=f2, fill=cor, anchor="mt"); y += int(fonte[1] * linhas_esp * s)
    return sprite(larg, alt, d)

# ---------------- ilustrações ----------------
def spr_cofre():
    def d(dr, s):
        dr.rounded_rectangle([10*s, 10*s, 330*s, 330*s], 28*s, fill=VERDE_ESC, outline=COBRE, width=8*s)
        dr.ellipse([105*s, 105*s, 235*s, 235*s], outline=COBRE, width=10*s)
        for a in range(0, 360, 45):
            x, y = 170 + 52*math.cos(math.radians(a)), 170 + 52*math.sin(math.radians(a))
            dr.ellipse([(x-6)*s, (y-6)*s, (x+6)*s, (y+6)*s], fill=COBRE)
        dr.ellipse([150*s, 150*s, 190*s, 190*s], fill=COBRE)
        dr.rounded_rectangle([290*s, 130*s, 312*s, 210*s], 8*s, fill=COBRE)
        dr.rectangle([130*s, 30*s, 210*s, 44*s], fill="#0E1C1E")          # fenda
    return sprite(340, 340, d)

def spr_moeda(r=46):
    def d(dr, s):
        dr.ellipse([2*s, 2*s, (2*r-2)*s, (2*r-2)*s], fill=COBRE)
        dr.ellipse([12*s, 12*s, (2*r-12)*s, (2*r-12)*s], outline="#E9B396", width=4*s)
        dr.text((r*s, r*s), "R$", font=F("Black", int(r*0.7)*s), fill=BRANCO, anchor="mm")
    return sprite(2*r, 2*r, d)

def spr_martelo():
    def d(dr, s):
        dr.rounded_rectangle([150*s, 60*s, 175*s, 330*s], 10*s, fill="#8A5A3C")          # cabo
        dr.rounded_rectangle([60*s, 10*s, 265*s, 95*s], 20*s, fill=COBRE)                # cabeça
        dr.rectangle([95*s, 10*s, 115*s, 95*s], fill="#A8653F"); dr.rectangle([210*s, 10*s, 230*s, 95*s], fill="#A8653F")
    return sprite(330, 340, d)

def spr_cartao():
    def d(dr, s):
        dr.rounded_rectangle([5*s, 5*s, 515*s, 325*s], 34*s, fill=AREIA)
        dr.rectangle([5*s, 70*s, 515*s, 120*s], fill=VERDE_ESC)
        dr.rounded_rectangle([50*s, 160*s, 130*s, 220*s], 10*s, fill=COBRE)
        for i in range(4): dr.rounded_rectangle([(50+i*105)*s, 255*s, (135+i*105)*s, 275*s], 6*s, fill="#9AA9AB")
    return sprite(520, 330, d)

def spr_cadeado_corpo():
    def d(dr, s):
        dr.rounded_rectangle([5*s, 5*s, 235*s, 195*s], 30*s, fill=COBRE)
        dr.ellipse([97*s, 60*s, 143*s, 106*s], fill=VERDE_ESC); dr.rectangle([111*s, 95*s, 129*s, 145*s], fill=VERDE_ESC)
    return sprite(240, 200, d)

def spr_cadeado_alca():
    def d(dr, s): dr.arc([10*s, 10*s, 190*s, 220*s], 180, 360, fill=COBRE, width=30*s); \
        [dr.rectangle([10*s, 112*s, 40*s, 200*s], fill=COBRE), dr.rectangle([160*s, 112*s, 190*s, 200*s], fill=COBRE)]
    return sprite(200, 210, d)

def spr_escudo(r=150, cor=VERDE_OK):
    def d(dr, s):
        w = 2*r
        dr.polygon([(r*s, 4*s), ((w-6)*s, 40*s), ((w-6)*s, int(r*1.05)*s), (r*s, int(r*2.2)*s), (6*s, int(r*1.05)*s), (6*s, 40*s)], fill=cor)
        dr.line([(int(r*0.55)*s, int(r*1.05)*s), (int(r*0.88)*s, int(r*1.4)*s), (int(r*1.45)*s, int(r*0.7)*s)], fill=BRANCO, width=int(r*0.16)*s, joint="curve")
    return sprite(2*r, int(r*2.25), d)

def spr_cofrinho():
    def d(dr, s):
        dr.ellipse([20*s, 40*s, 220*s, 190*s], fill=COBRE)
        dr.polygon([(70*s, 60*s), (95*s, 10*s), (115*s, 55*s)], fill=COBRE)
        dr.rounded_rectangle([200*s, 95*s, 240*s, 135*s], 10*s, fill="#D9906B")
        dr.rectangle([60*s, 170*s, 90*s, 215*s], fill=COBRE); dr.rectangle([150*s, 170*s, 180*s, 215*s], fill=COBRE)
        dr.rounded_rectangle([100*s, 55*s, 150*s, 65*s], 4*s, fill=VERDE_ESC); dr.ellipse([165*s, 85*s, 180*s, 100*s], fill=VERDE_ESC)
    return sprite(250, 220, d)

def spr_cedulas():
    def d(dr, s):
        for i, c in enumerate(["#9CC3AE", "#B5D3C2", "#CFE3D6"]):
            o = i * 18
            dr.rounded_rectangle([(10+o)*s, (60-o)*s, (230+o)*s, (180-o)*s], 12*s, fill=c, outline=VERDE, width=4*s)
        dr.ellipse([(110)*s, (75)*s, (170)*s, (135)*s], outline=VERDE, width=5*s)
        dr.text((140*s, 105*s), "R$", font=F("Black", 26*s), fill=VERDE, anchor="mm")
    return sprite(270, 200, d)

def spr_grafico_estavel():
    def d(dr, s):
        for i, h in enumerate([70, 100, 125, 150]):
            dr.rounded_rectangle([(20+i*55)*s, (190-h)*s, (60+i*55)*s, 190*s], 8*s, fill=VERDE)
        dr.line([(20*s, 195*s), (245*s, 195*s)], fill=CINZA, width=5*s)
    return sprite(260, 210, d)

def spr_selo(ok=True, r=40):
    def d(dr, s):
        dr.ellipse([2*s, 2*s, (2*r-2)*s, (2*r-2)*s], fill=VERDE_OK if ok else COBRE, outline=BRANCO, width=5*s)
        c = r*s
        if ok: dr.line([(c-18*s, c+2*s), (c-5*s, c+16*s), (c+20*s, c-14*s)], fill=BRANCO, width=9*s, joint="curve")
        else:
            dr.line([(c-15*s, c-15*s), (c+15*s, c+15*s)], fill=BRANCO, width=9*s); dr.line([(c-15*s, c+15*s), (c+15*s, c-15*s)], fill=BRANCO, width=9*s)
    return sprite(2*r, 2*r, d)

def spr_alerta():
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 1, 1], 0, fill=None)
        dr.polygon([(170*s, 10*s), (330*s, 290*s), (10*s, 290*s)], fill=COBRE)
        dr.rounded_rectangle([155*s, 95*s, 185*s, 205*s], 12*s, fill=VERDE_ESC); dr.ellipse([152*s, 225*s, 188*s, 261*s], fill=VERDE_ESC)
    return sprite(340, 300, d)

def spr_grafico_risco():
    def d(dr, s):
        dr.rounded_rectangle([0, 0, 300*s, 220*s], 20*s, fill="#2A474B")
        for y in (60, 110, 160): dr.line([(20*s, y*s), (280*s, y*s)], fill="#3B5C60", width=2*s)
        pts = [(25, 150), (65, 60), (100, 170), (140, 40), (175, 185), (215, 70), (250, 195), (275, 205)]
        dr.line([(x*s, y*s) for x, y in pts], fill=COBRE, width=10*s, joint="curve")
        dr.polygon([(275*s, 215*s), (255*s, 185*s), (290*s, 190*s)], fill=COBRE)
    return sprite(300, 220, d)

def spr_calendario():
    def d(dr, s):
        dr.rounded_rectangle([10*s, 30*s, 270*s, 230*s], 18*s, fill=AREIA)
        dr.rounded_rectangle([10*s, 30*s, 270*s, 85*s], 18*s, fill=COBRE); dr.rectangle([10*s, 65*s, 270*s, 85*s], fill=COBRE)
        dr.text((140*s, 58*s), "MÊS PASSADO", font=F("Black", 24*s), fill=BRANCO, anchor="mm")
        for i in range(3):
            for j in range(5): dr.rounded_rectangle([(30+j*48)*s, (105+i*40)*s, (62+j*48)*s, (130+i*40)*s], 5*s, fill="#C9C2BB")
        for x in (60, 220): dr.rounded_rectangle([(x-8)*s, 10*s, (x+8)*s, 50*s], 6*s, fill=CINZA)
    return sprite(280, 240, d)

def spr_balanca_haste():
    def d(dr, s):
        dr.rounded_rectangle([20*s, 30*s, 500*s, 48*s], 9*s, fill=COBRE)
        for x in (60, 460):
            dr.line([(x*s, 40*s), ((x-55)*s, 190*s)], fill=COBRE, width=5*s); dr.line([(x*s, 40*s), ((x+55)*s, 190*s)], fill=COBRE, width=5*s)
            dr.chord([((x-75)*s, 140*s), ((x+75)*s, 240*s)], 0, 180, fill=COBRE)
        dr.ellipse([240*s, 20*s, 280*s, 60*s], fill=AREIA)
    return sprite(520, 250, d)

def spr_balanca_base():
    def d(dr, s):
        dr.rounded_rectangle([110*s, 0, 140*s, 300*s], 10*s, fill=AREIA)
        dr.rounded_rectangle([20*s, 290*s, 230*s, 330*s], 16*s, fill=AREIA)
    return sprite(250, 330, d)

def spr_extrato():
    def d(dr, s):
        dr.rounded_rectangle([10*s, 10*s, 390*s, 500*s], 20*s, fill=AREIA)
        dr.text((200*s, 60*s), "EXTRATO", font=F("Black", 40*s), fill=VERDE, anchor="mm")
        dr.rectangle([40*s, 95*s, 360*s, 100*s], fill=COBRE)
        for i in range(8):
            y = 135 + i*44
            dr.rounded_rectangle([40*s, y*s, (210 - (i % 3)*30)*s, (y+16)*s], 6*s, fill="#B9C3C4")
            dr.rounded_rectangle([280*s, y*s, 360*s, (y+16)*s], 6*s, fill=VERDE_OK if i % 3 else COBRE)
    return sprite(400, 510, d)

def spr_lupa():
    def d(dr, s):
        dr.ellipse([10*s, 10*s, 150*s, 150*s], outline=VERDE_ESC, width=16*s); dr.ellipse([26*s, 26*s, 134*s, 134*s], fill=(255, 255, 255, 70))
        dr.line([(128*s, 128*s), (200*s, 200*s)], fill=VERDE_ESC, width=26*s)
    return sprite(210, 210, d)

# ---------------- elementos e animação ----------------
class El:
    def __init__(self, spr, x, y, t0, anim="pop", dur=0.45, loop=None, amp=0, de=None, rot0=0, fim=None):
        self.spr, self.x, self.y, self.t0, self.anim, self.dur = spr, x, y, t0, anim, dur
        self.loop, self.amp, self.de, self.rot0, self.fim = loop, amp, de, rot0, fim
    def estado(self, t):
        if t < self.t0 or (self.fim is not None and t > self.fim): return None
        p = clamp((t - self.t0) / self.dur); sc, dx, dy, rot, al, rev = 1.0, 0, 0, 0, 1.0, 1.0
        a = self.anim
        if a == "pop": sc = max(0.01, out_back(p))
        elif a == "subir": dy = (1 - out_cubic(p)) * 140; al = p
        elif a == "esq": dx = -(1 - out_cubic(p)) * 900
        elif a == "dir": dx = (1 - out_cubic(p)) * 900
        elif a == "fade": al = p
        elif a == "cair": dy = -(1 - p ** 2) * (self.de or 600); al = 1 if p < 0.92 else 1 - (p - 0.92) / 0.08 * (self.fim is None)
        elif a == "revelar": rev = out_cubic(p)
        elif a == "golpe":   # martelo: gira de rot0 até 0
            rot = self.rot0 * (1 - out_back(p, 2.5))
        if p >= 1 and self.loop:
            u = t - self.t0 - self.dur
            if self.loop == "pulso": sc *= 1 + self.amp * math.sin(u * 6)
            elif self.loop == "balanco": rot += self.amp * math.sin(u * 2.4)
            elif self.loop == "flutuar": dy += self.amp * math.sin(u * 2.2)
            elif self.loop == "varrer": dx += self.amp * math.sin(u * 1.6); dy += self.amp * 0.6 * math.sin(u * 3.1)
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
        if al < 0.999:
            a = im.getchannel("A").point(lambda v: int(v * clamp(al))); im = im.copy(); im.putalpha(a)
        base.alpha_composite(im, (int(e.x + dx - im.width / 2), int(e.y + dy - im.height / 2)))

def fundo(cor, rodape=True):
    im = Image.new("RGBA", (W, H), cor); d = ImageDraw.Draw(im)
    if cor != BRANCO:
        d.rectangle([80, 150, 420, 158], fill=COBRE); d.rectangle([660, 150, 1000, 158], fill=COBRE)
        im.alpha_composite(R.SIMB, (465, 80))
        if cor != AREIA: d.rectangle([462, 77, 617, 230], outline=COBRE, width=3)
        d.text((W // 2, 1440), "STJ · Tema Repetitivo 1285 · art. 833, IV e X, CPC", font=F("Regular", 30),
               fill=CINZA if cor == AREIA else "#BFD0D2", anchor="mm")
        d.rectangle([0, H - 40, W, H], fill=COBRE)
    else:
        d.rectangle([0, H - 60, W, H], fill=VERDE)
    return im

# ---------------- roteiro de cenas ----------------
def montar_cenas():
    moeda, sel_ok, sel_x = spr_moeda(), spr_selo(True), spr_selo(False)
    C = []
    # 1 · gancho
    t = T(2.45)
    C.append((t, fundo(VERDE), [
        El(texto("SEU DINHEIRO\nPODE SER PENHORADO?", ("Black", 76), BRANCO), 540, 400, t, "subir", 0.5),
        El(spr_cofre(), 540, 900, t + 0.3, "pop", 0.5),
        *[El(moeda, 480 + i * 60, 760, T(5.2) + i * 0.25, "cair", 0.5, de=230, fim=T(5.2) + i * 0.25 + 0.55) for i in range(3)],
        El(spr_martelo(), 760, 780, T(7.6), "golpe", 0.6, rot0=-75),
        El(texto("TEMA 1285 · STJ", ("Bold", 56), COBRE), 540, 1180, t + 0.6, "fade", 0.4),
    ]))
    # 2 · conta bloqueada
    t = T(9.70)
    C.append((t, fundo(VERDE), [
        El(texto("CONTA\nBLOQUEADA", ("Black", 110), BRANCO), 540, 430, t, "subir", 0.5),
        El(spr_cartao(), 540, 920, t + 0.1, "esq", 0.6),
        El(spr_cadeado_alca(), 540, 780, T(12.6), "cair", 0.35, de=220),
        El(spr_cadeado_corpo(), 540, 930, T(12.4), "pop", 0.4, loop="pulso", amp=0.02),
    ]))
    # 3 · regra 40 SM (contador + escudo)
    t = T(25.30)
    C.append((t, fundo(VERDE), [
                ("contador", T(27.26), T(28.3)),
        El(texto("SALÁRIOS MÍNIMOS", ("Black", 84), BRANCO), 540, 730, T(28.0), "subir", 0.4),
        El(spr_escudo(130), 540, 1000, T(29.45), "pop", 0.5, loop="pulso", amp=0.025),
        El(texto("não podem ser penhorados", ("Regular", 50), CLARO), 540, 1210, T(30.0), "fade", 0.4),
    ]))
    # 4 · o que está protegido
    t = T(34.80)
    linhas = [(T(35.0), spr_cofrinho(), "POUPANÇA", "mesmo usada como conta corrente"),
              (T(43.7), spr_cedulas(), "DINHEIRO VIVO", "se for reserva de emergência"),
              (T(45.25), spr_grafico_estavel(), "CONTA OU\nINVESTIMENTO", "se for reserva de emergência")]
    els = [El(texto("O QUE ESTÁ PROTEGIDO", ("Black", 72), VERDE), 540, 330, t, "subir", 0.45)]
    for i, (ti, ic, tit, sub) in enumerate(linhas):
        y = 590 + i * 250
        els += [El(ic.resize((int(ic.width * 0.78), int(ic.height * 0.78)), Image.LANCZOS), 220, y, ti, "pop", 0.45),
                El(sel_ok, 310, y + 70, ti + 0.25, "pop", 0.35),
                El(texto(tit, ("Black", 54), VERDE), 650, y - 30, ti + 0.1, "dir", 0.45),
                El(texto(sub, ("Regular", 38), CINZA), 650, y + 50 if i < 2 else y + 70, ti + 0.2, "fade", 0.4)]
        if i:
            els.append(El(texto(sub, ("Bold", 38), COBRE), 650, y + 50 if i < 2 else y + 70, T(49.4), "fade", 0.3))
    C.append((t, fundo(AREIA), els))
    # 5 · mas atenção
    t = T(53.85)
    C.append((t, fundo(VERDE_ESC), [
        El(spr_alerta(), 540, 640, t, "pop", 0.5, loop="pulso", amp=0.04),
        El(texto("MAS ATENÇÃO", ("Black", 100), COBRE), 540, 920, t + 0.2, "subir", 0.4),
        El(texto("a proteção não vale\nem dois casos", ("Regular", 56), CLARO), 540, 1110, T(56.4), "fade", 0.4),
    ]))
    # 6 · exceções
    t = T(77.40)
    C.append((t, fundo(VERDE_ESC), [
        El(texto("NÃO ESTÁ PROTEGIDO", ("Black", 72), COBRE), 540, 330, t, "subir", 0.45),
        El(spr_grafico_risco(), 250, 620, t + 0.2, "revelar", 1.2),
        El(sel_x, 370, 720, T(80.1), "pop", 0.35),
        El(texto("ALTO RISCO", ("Black", 58), BRANCO), 720, 580, t + 0.4, "dir", 0.45),
        El(texto("investir para tentar\nganhar mais", ("Regular", 36), "#BFD0D2"), 720, 670, T(81.3), "fade", 0.4),
        El(spr_calendario(), 250, 990, T(84.0), "pop", 0.45),
        *[El(moeda.resize((60, 60), Image.LANCZOS), 200 + i * 55, 1080, T(86.3) + i * 0.15, "fade", 0.3, loop="flutuar", amp=6) for i in range(3)],
        El(sel_x, 370, 1090, T(88.6), "pop", 0.35),
        El(texto("SOBRAS DE\nMESES ANTERIORES", ("Black", 50), BRANCO), 720, 960, T(84.2), "dir", 0.45),
        El(texto("salário que ficou\nparado na conta", ("Regular", 36), "#BFD0D2"), 720, 1080, T(93.4), "fade", 0.4),
    ]))
    # 7 · debate
    t = T(100.8)
    C.append((t, fundo(VERDE), [
        El(texto("“ALTO RISCO” = ?", ("Black", 90), BRANCO), 540, 380, t, "subir", 0.45),
        El(spr_balanca_base(), 540, 960, t + 0.2, "fade", 0.4),
        El(spr_balanca_haste(), 540, 860, t + 0.2, "pop", 0.5, loop="balanco", amp=9),
        El(texto("será definido caso a caso", ("Regular", 52), CLARO), 540, 1210, T(107.6), "fade", 0.4),
    ]))
    # 8 · guarde extratos
    t = T(111.3)
    C.append((t, fundo(VERDE), [
        El(texto("GUARDE SEUS EXTRATOS", ("Black", 76), BRANCO), 540, 330, T(114.5), "subir", 0.45),
        El(spr_extrato(), 540, 830, t, "subir", 0.6),
        El(spr_lupa(), 640, 760, T(117.1), "pop", 0.4, loop="varrer", amp=70),
        El(texto("de onde veio · para que serve", ("Bold", 44), COBRE), 540, 1180, T(117.3), "fade", 0.4),
    ]))
    # 9 · encerramento
    t = T(129.10)
    lg = R.LOGO.resize((820, int(820 * R.LOGO.height / R.LOGO.width)), Image.LANCZOS)
    C.append((t, fundo(BRANCO), [
        El(lg, 540, 680, t, "pop", 0.6),
        El(texto("Decisões do STJ\nexplicadas de forma simples", ("Regular", 50), CINZA), 540, 1020, t + 0.4, "fade", 0.4),
        El(texto("mosima.com.br", ("Bold", 56), COBRE), 540, 1170, t + 0.7, "subir", 0.4),
    ]))
    return C

# ---------------- render ----------------
CACHE_TXT = {}
def contador(base, t, t0, t1):
    if t < t0: return
    n = int(round(40 * out_cubic(clamp((t - t0) / (t1 - t0)))))
    k = ("num", n)
    if k not in CACHE_TXT:
        CACHE_TXT[k] = (texto("ATÉ", ("Bold", 64), COBRE), texto(str(n), ("Black", 230), BRANCO))
    ate, num = CACHE_TXT[k]
    base.alpha_composite(ate, (540 - ate.width // 2, 330)); base.alpha_composite(num, (540 - num.width // 2, 400))

def legenda(base, t, fundo_cor):
    leg = next((l[2] for l in R.legendas if l[0] <= t < l[1]), "")
    if not leg: return
    if leg not in CACHE_TXT:
        f = F("Bold", 54); d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        bb = d0.textbbox((0, 0), leg, font=f); w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 40
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], 18, fill="#0E1C1E"); d.text((w // 2, h // 2), leg, font=f, fill=BRANCO, anchor="mm")
        CACHE_TXT[leg] = im
    im = CACHE_TXT[leg]; base.alpha_composite(im, (540 - im.width // 2, 1330 - im.height // 2))

def main():
    audio, saida = sys.argv[1], sys.argv[2]; os.makedirs(saida, exist_ok=True)
    de = float(sys.argv[sys.argv.index("--de") + 1]) if "--de" in sys.argv else 0.0
    ate = float(sys.argv[sys.argv.index("--ate") + 1]) if "--ate" in sys.argv else R.DUR
    wav = f"{saida}/narracao-editada.wav"
    if not os.path.exists(wav):
        filtros, rot = [], []
        for k, (s, e) in enumerate(R.CORTES):
            filtros.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.04:.3f}:d=0.04[a{k}]"); rot.append(f"[a{k}]")
        filtros.append("".join(rot) + f"concat=n={len(R.CORTES)}:v=0:a=1,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-filter_complex", ";".join(filtros), "-map", "[out]", "-ar", "48000", "-ac", "1", wav], check=True)
    cenas = montar_cenas()
    nome = f"{saida}/tema-1285-motion{'' if (de == 0 and ate >= R.DUR) else '-amostra'}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-ss", str(de), "-t", str(ate - de), "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", nome], stdin=subprocess.PIPE)
    n0, n1 = int(de * FPS), int(ate * FPS)
    for n in range(n0, n1):
        t = n / FPS
        i = max(k for k, c in enumerate(cenas) if c[0] <= t + 1e-6) if t >= cenas[0][0] else 0
        t0, bg, els = cenas[i]
        quadro = bg.copy()
        compor(quadro, [e for e in els if isinstance(e, El)], t)
        for e in els:
            if isinstance(e, tuple) and e[0] == "contador": contador(quadro, t, e[1], e[2])
        # transição: cena anterior desliza para cima nos primeiros 0,25 s
        if i > 0 and t - t0 < 0.25:
            pt0, pbg, pels = cenas[i - 1]; ant = pbg.copy(); compor(ant, [e for e in pels if isinstance(e, El)], t)
            for e in pels:
                if isinstance(e, tuple): contador(ant, t, e[1], e[2])
            k = out_cubic((t - t0) / 0.25); off = int(-k * H)
            q = Image.new("RGBA", (W, H)); q.alpha_composite(quadro, (0, 0)); q.alpha_composite(ant, (0, 0)) if off == 0 else None
            q = quadro.copy(); q.paste(ant.crop((0, -off, W, H)), (0, 0)); quadro = q
        legenda(quadro, t, None)
        ff.stdin.write(quadro.convert("RGB").tobytes())
        if n % 300 == 0: print(f"  {t:5.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    print("ok:", nome)

if __name__ == "__main__":
    main()
