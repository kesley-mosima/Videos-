"""Gera quadros de prévia (1080x1920) com a identidade visual Mosima."""
from PIL import Image, ImageDraw, ImageFont
import os
B = os.path.join(os.path.dirname(__file__), "..", "identidade-visual")
VERDE, COBRE, CINZA, BRANCO = "#2E5156", "#C57A55", "#464646", "#FFFFFF"
VERDE_ESC = "#1F383C"
F = lambda w, s: ImageFont.truetype(f"{B}/fontes/Lato-{w}.ttf", s)
W, H = 1080, 1920
logo_sym = Image.open(f"{B}/logo-simbolo.png").convert("RGBA")

def base(fundo=VERDE):
    im = Image.new("RGB", (W, H), fundo); d = ImageDraw.Draw(im)
    # faixa cobre superior (assinatura do timbrado)
    d.rectangle([80, 150, 420, 158], fill=COBRE); d.rectangle([660, 150, 1000, 158], fill=COBRE)
    s = logo_sym.resize((150, 148)); im.paste(s, (465, 80))
    if fundo != "#F4EFEA": d.rectangle([462, 77, 617, 230], outline=COBRE, width=3)
    # rodapé fixo
    # área segura do Reels: nada essencial abaixo de ~1480 px nem colado à direita
    d.text((W//2, 1440), "STJ · Tema Repetitivo 1285 · art. 833, IV e X, CPC", font=F("Regular", 30), fill="#BFD0D2" if fundo!="#F4EFEA" else CINZA, anchor="mm")
    d.rectangle([0, H-40, W, H], fill=COBRE)
    return im, d

def centro(d, linhas, y, fonte, cor=BRANCO, esp=1.15):
    for l in linhas:
        d.text((W//2, y), l, font=fonte, fill=cor, anchor="mm"); y += int(fonte.size*esp)
    return y

def legenda(d, texto):
    f = F("Bold", 50); bb = d.textbbox((W//2, 1330), texto, font=f, anchor="mm")
    d.rounded_rectangle([bb[0]-30, bb[1]-18, bb[2]+30, bb[3]+18], 18, fill="#000000AA" if False else "#0E1C1E")
    d.text((W//2, 1330), texto, font=f, fill=BRANCO, anchor="mm")

def check(d, x, y, ok=True, r=46):
    d.ellipse([x-r, y-r, x+r, y+r], fill=COBRE if not ok else "#3E8E6E")
    if ok: d.line([(x-22, y+2), (x-6, y+20), (x+24, y-18)], fill=BRANCO, width=12)
    else:
        d.line([(x-18, y-18), (x+18, y+18)], fill=BRANCO, width=12); d.line([(x-18, y+18), (x+18, y-18)], fill=BRANCO, width=12)

out = f"{B}/previas"
# Cena 1 — gancho
im, d = base(); y = centro(d, ["SEU DINHEIRO", "PODE SER", "PENHORADO?"], 620, F("Black", 118))
d.rectangle([390, y+10, 690, y+18], fill=COBRE); centro(d, ["Tema 1285 — STJ"], y+90, F("Bold", 62), COBRE)
legenda(d, "O STJ acabou de definir quando…"); im.save(f"{out}/cena01-gancho.png")
# Cena 3 — regra
im, d = base(); centro(d, ["ATÉ"], 520, F("Bold", 70), COBRE)
centro(d, ["40", "SALÁRIOS", "MÍNIMOS"], 680, F("Black", 140)); centro(d, ["protegidos da penhora"], 1150, F("Regular", 58), "#DCE6E7")
legenda(d, "não podem ser tomados para pagar a dívida"); im.save(f"{out}/cena03-regra.png")
# Cena 4/5 — protegido (fundo claro, contraste com exceções)
im, d = base("#F4EFEA"); d.rectangle([0,0,W,0], fill=VERDE)
centro(d, ["O QUE ESTÁ", "PROTEGIDO"], 400, F("Black", 96), VERDE)
itens = [("POUPANÇA", "mesmo usada como conta corrente"), ("DINHEIRO VIVO", "reserva de emergência"), ("CONTA / INVESTIMENTO", "reserva de emergência")]
y = 640
for t, s in itens:
    check(d, 170, y+30, True); d.text((250, y), t, font=F("Black", 62), fill=VERDE); d.text((250, y+78), s, font=F("Regular", 40), fill=CINZA); y += 200
legenda(d, "mesmo usada como conta corrente"); im.save(f"{out}/cena04-protegido.png")
# Cena 7/8 — exceções
im, d = base(VERDE_ESC); centro(d, ["MAS ATENÇÃO:", "NÃO ESTÁ PROTEGIDO"], 450, F("Black", 84), COBRE)
y = 700
for t, s in [("ALTO RISCO", "investir para tentar ganhar mais"), ("SOBRAS DE MESES", "salário que ficou parado na conta")]:
    check(d, 170, y+30, False); d.text((250, y), t, font=F("Black", 64), fill=BRANCO); d.text((250, y+80), s, font=F("Regular", 40), fill="#BFD0D2"); y += 260
legenda(d, "pode ser penhorado"); im.save(f"{out}/cena08-excecoes.png")
# Cena 10 — encerramento
im = Image.new("RGB", (W, H), BRANCO); d = ImageDraw.Draw(im)
lg = Image.open(f"{B}/logo-completo.png").convert("RGBA"); lg = lg.resize((800, int(800*lg.height/lg.width)))
im.paste(lg, ((W-800)//2, 620)); centro(d, ["GUARDE SEUS EXTRATOS"], 380, F("Black", 70), VERDE)
d.rectangle([340, 440, 740, 446], fill=COBRE)
centro(d, ["Siga para mais decisões do STJ", "explicadas de forma simples"], 1180, F("Regular", 48), CINZA)
centro(d, ["@[perfil do escritório]"], 1360, F("Bold", 56), COBRE)
d.rectangle([0, H-60, W, H], fill=VERDE); im.save(f"{out}/cena10-encerramento.png")
# Folha de contato
fs = sorted(x for x in os.listdir(out) if x.startswith("cena"))
sheet = Image.new("RGB", (len(fs)*560+40, 1040), "#DDDDDD")
for i, f in enumerate(fs):
    t = Image.open(f"{out}/{f}").resize((540, 960)); sheet.paste(t, (20+i*560, 40))
sheet.save(f"{out}/_visao-geral.png"); print("ok", fs)
