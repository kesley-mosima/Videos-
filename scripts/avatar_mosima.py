"""Avatar ilustrado (vetorial, desenhado em PIL) do apresentador, baseado na foto de referência.

Traços: cabelo preto penteado para trás com entradas, óculos de armação metálica fina hexagonal,
barba curta com fios grisalhos, terno azul, camisa branca, gravata marinho com poá.
A boca é animada pelo volume da narração real (sem síntese de voz, sem deepfake).
"""
import math, random
from PIL import Image, ImageDraw

SS = 2
PELE, PELE_SOMBRA, PELE_LUZ = "#B9805C", "#9A6446", "#C99573"
CABELO, CABELO_BRILHO = "#1A1512", "#3B332E"
BARBA, GRISALHO = "#2A211C", "#8E8780"
LABIO, BOCA_INT, DENTE = "#8A4B40", "#3A1B1B", "#F3EEE8"
OCULOS = "#3A3A3C"
TERNO, TERNO_SOMBRA, TERNO_LUZ = "#5676A3", "#435F88", "#6A8AB6"
CAMISA, CAMISA_SOMBRA = "#FBFBFB", "#DADDE2"
GRAVATA, POA1, POA2 = "#1F2B4D", "#8FB4E2", "#E9D9C6"

HW, HH = 600, 720          # tela da cabeça
BW, BH = 1080, 900         # tela do corpo


def _sprite(w, h, desenho):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    desenho(ImageDraw.Draw(im), SS)
    return im.resize((w, h), Image.LANCZOS)


def _p(pts, s):
    return [(x * s, y * s) for x, y in pts]


def _curva(p0, p1, p2, n=24):
    """Bézier quadrática -> lista de pontos."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


# ---------------- corpo ----------------
def corpo():
    def d(dr, s):
        # pescoço
        dr.rounded_rectangle([455 * s, 0, 625 * s, 200 * s], 40 * s, fill=PELE_SOMBRA)
        # paletó (ombros largos, descendo até a borda)
        ombro = [(80, 900), (95, 360), (150, 250), (330, 175), (470, 150), (610, 150), (750, 175), (930, 250), (985, 360), (1000, 900)]
        dr.polygon(_p(ombro, s), fill=TERNO)
        dr.polygon(_p([(80, 900), (95, 360), (150, 250), (250, 205), (230, 900)], s), fill=TERNO_SOMBRA)
        dr.polygon(_p([(1000, 900), (985, 360), (930, 250), (830, 205), (850, 900)], s), fill=TERNO_SOMBRA)
        # camisa (V)
        dr.polygon(_p([(450, 150), (630, 150), (690, 300), (540, 640), (390, 300)], s), fill=CAMISA)
        # colarinho
        dr.polygon(_p([(455, 120), (540, 205), (470, 290), (400, 215)], s), fill=CAMISA_SOMBRA)
        dr.polygon(_p([(625, 120), (540, 205), (610, 290), (680, 215)], s), fill=CAMISA_SOMBRA)
        dr.polygon(_p([(462, 128), (540, 205), (474, 275), (412, 210)], s), fill=CAMISA)
        dr.polygon(_p([(618, 128), (540, 205), (606, 275), (668, 210)], s), fill=CAMISA)
        # gravata: nó e corpo
        dr.polygon(_p([(505, 200), (575, 200), (565, 265), (515, 265)], s), fill=GRAVATA)
        gr = [(515, 262), (565, 262), (610, 760), (540, 860), (470, 760)]
        dr.polygon(_p(gr, s), fill=GRAVATA)
        rnd = random.Random(7)
        for yy in range(290, 840, 34):
            for xx in range(470, 615, 34):
                x = xx + (17 if (yy // 34) % 2 else 0)
                larg = 50 + (yy - 262) * 0.09
                if abs(x - 540) < larg - 8:
                    c = POA1 if rnd.random() < 0.75 else POA2
                    dr.ellipse([(x - 4) * s, (yy - 4) * s, (x + 4) * s, (yy + 4) * s], fill=c)
        # lapelas
        dr.polygon(_p([(450, 150), (330, 178), (300, 330), (385, 420), (330, 470), (470, 760), (540, 650), (390, 300)], s), fill=TERNO_LUZ)
        dr.polygon(_p([(630, 150), (750, 178), (780, 330), (695, 420), (750, 470), (610, 760), (540, 650), (690, 300)], s), fill=TERNO_LUZ)
        dr.line(_p([(385, 420), (330, 470)], s), fill=TERNO_SOMBRA, width=4 * s)
        dr.line(_p([(695, 420), (750, 470)], s), fill=TERNO_SOMBRA, width=4 * s)
        # bolso e casa de botão
        dr.line(_p([(760, 640), (880, 625)], s), fill=TERNO_SOMBRA, width=6 * s)
        dr.line(_p([(355, 520), (395, 510)], s), fill=TERNO_SOMBRA, width=5 * s)
    return _sprite(BW, BH, d)


# ---------------- cabeça ----------------
def cabeca_base():
    def d(dr, s):
        # orelhas
        for x0 in (118, 438):
            dr.ellipse([x0 * s, 330 * s, (x0 + 44) * s, 450 * s], fill=PELE_SOMBRA)
            dr.ellipse([(x0 + 10) * s, 350 * s, (x0 + 32) * s, 430 * s], fill=PELE)
        # rosto
        dr.ellipse([140 * s, 130 * s, 460 * s, 640 * s], fill=PELE)
        # cabelo (calota) + entradas em "M"
        dr.chord([136 * s, 112 * s, 464 * s, 450 * s], 180, 360, fill=CABELO)
        dr.rectangle([136 * s, 270 * s, 162 * s, 360 * s], fill=CABELO)          # costeletas
        dr.rectangle([438 * s, 270 * s, 464 * s, 360 * s], fill=CABELO)
        testa = (_curva((178, 330), (176, 240), (232, 208)) + _curva((232, 208), (265, 236), (300, 228))
                 + _curva((300, 228), (335, 236), (368, 208)) + _curva((368, 208), (424, 240), (422, 330)))
        dr.polygon(_p(testa, s), fill=PELE)
        # mechas penteadas para trás (brilho de gel)
        for x in (220, 260, 300, 340, 380):
            pts = _curva((x, 200 + abs(300 - x) * 0.15), (x + (x - 300) * 0.15, 165), (x + (x - 300) * 0.3, 132 + abs(300 - x) * 0.3))
            dr.line(_p(pts, s), fill=CABELO_BRILHO, width=4 * s)
        # barba: maxilar inteiro + costeletas
        barba = (_curva((150, 360), (150, 470), (190, 545)) + _curva((190, 545), (240, 650), (300, 655))
                 + _curva((300, 655), (360, 650), (410, 545)) + _curva((410, 545), (450, 470), (450, 360)))
        barba += list(reversed(_curva((150, 360), (180, 470), (240, 492)) + _curva((240, 492), (300, 478), (360, 492))
                               + _curva((360, 492), (420, 470), (450, 360))))
        dr.polygon(_p(barba, s), fill=BARBA)
        dr.rectangle([150 * s, 300 * s, 168 * s, 380 * s], fill=BARBA)
        dr.rectangle([432 * s, 300 * s, 450 * s, 380 * s], fill=BARBA)
        # bigode
        big = _curva((236, 496), (300, 466), (364, 496)) + list(reversed(_curva((242, 506), (300, 488), (358, 506))))
        dr.polygon(_p(big, s), fill=BARBA)
        # fios grisalhos espalhados na barba
        rnd = random.Random(3)
        for _ in range(120):
            x, y = rnd.uniform(160, 440), rnd.uniform(470, 650)
            dentro = all(dr._image.getpixel((int(px * s), int(py * s)))[:3] == (0x2A, 0x21, 0x1C) for px, py in ((x, y), (x, y + 7)))
            if dentro and not (255 < x < 345 and 500 < y < 545):
                dr.line([(x * s, y * s), ((x + rnd.uniform(-3, 3)) * s, (y + 6) * s)], fill=GRISALHO, width=2 * s)
        # região da boca (pele entre bigode e cavanhaque)
        # sobrancelhas grossas
        dr.polygon(_p(_curva((192, 322), (232, 296), (278, 312)) + list(reversed(_curva((194, 334), (234, 312), (278, 324)))), s), fill=CABELO)
        dr.polygon(_p(_curva((322, 312), (368, 296), (408, 322)) + list(reversed(_curva((322, 324), (366, 312), (406, 334)))), s), fill=CABELO)
        # nariz
        dr.line(_p(_curva((292, 372), (284, 420), (280, 448)), s), fill=PELE_SOMBRA, width=5 * s)
        dr.polygon(_p(_curva((268, 448), (300, 472), (332, 448)) + [(320, 440), (300, 452), (280, 440)], s), fill=PELE_SOMBRA)
        dr.ellipse([272 * s, 444 * s, 286 * s, 454 * s], fill="#6E4430"); dr.ellipse([314 * s, 444 * s, 328 * s, 454 * s], fill="#6E4430")
    return _sprite(HW, HH, d)


def olhos(aberto=True):
    def d(dr, s):
        def hexa(cx):
            h = [(cx - 58, 335), (cx - 30, 318), (cx + 34, 320), (cx + 50, 345), (cx + 44, 405), (cx - 46, 408), (cx - 62, 372)]
            return [(2 * cx - x, y) for x, y in h] if cx > 300 else h
        for cx in (238, 362):
            dr.polygon(_p(hexa(cx), s), fill="#C79A7C")
        for cx in (238, 362):
            if aberto:
                dr.ellipse([(cx - 26) * s, 352 * s, (cx + 26) * s, 382 * s], fill="#F6F1EC")
                dr.ellipse([(cx - 13) * s, 353 * s, (cx + 13) * s, 380 * s], fill="#3B2418")
                dr.ellipse([(cx - 6) * s, 360 * s, (cx + 6) * s, 372 * s], fill="#0D0705")
                dr.ellipse([(cx + 2) * s, 358 * s, (cx + 7) * s, 363 * s], fill="#FFFFFF")
                dr.arc([(cx - 27) * s, 350 * s, (cx + 27) * s, 384 * s], 190, 350, fill="#2A1C16", width=4 * s)
            else:
                dr.arc([(cx - 26) * s, 352 * s, (cx + 26) * s, 380 * s], 15, 165, fill="#2A1C16", width=5 * s)
        # óculos hexagonais (armação fina)
        for cx in (238, 362):
            h = hexa(cx); dr.line(_p(h + [h[0]], s), fill=OCULOS, width=5 * s, joint="curve")
        dr.line(_p(_curva((284, 336), (300, 328), (316, 336)), s), fill=OCULOS, width=5 * s)
        dr.line(_p([(176, 340), (148, 352)], s), fill=OCULOS, width=5 * s)
        dr.line(_p([(424, 340), (452, 352)], s), fill=OCULOS, width=5 * s)
    return _sprite(HW, HH, d)


def boca(nivel):
    """nivel 0 = fechada (sorriso leve) ... 4 = bem aberta."""
    def d(dr, s):
        cx, cy = 300, 520
        if nivel == 0:
            dr.line(_p(_curva((268, 516), (300, 532), (332, 516)), s), fill=LABIO, width=7 * s)
            return
        a = [0, 9, 16, 24, 32][nivel]; l = [0, 28, 31, 33, 34][nivel]
        dr.ellipse([(cx - l) * s, (cy - a * 0.45) * s, (cx + l) * s, (cy + a) * s], fill=LABIO)
        dr.ellipse([(cx - l + 6) * s, (cy - a * 0.45 + 5) * s, (cx + l - 6) * s, (cy + a - 5) * s], fill=BOCA_INT)
        dr.rectangle([(cx - l + 10) * s, (cy - a * 0.45 + 5) * s, (cx + l - 10) * s, (cy - a * 0.45 + 5 + min(9, a * 0.4)) * s], fill=DENTE)
        if nivel >= 3:
            dr.ellipse([(cx - 14) * s, (cy + a - 16) * s, (cx + 14) * s, (cy + a - 6) * s], fill="#A8524F")
    return _sprite(HW, HH, d)


class Avatar:
    def __init__(self):
        self.corpo = corpo()
        self.cab = cabeca_base()
        self.olhos = {True: olhos(True), False: olhos(False)}
        self.bocas = [boca(n) for n in range(5)]
        self._cache = {}

    def cabeca(self, nivel, aberto):
        k = (nivel, aberto)
        if k not in self._cache:
            im = self.cab.copy(); im.alpha_composite(self.olhos[aberto]); im.alpha_composite(self.bocas[nivel]); self._cache[k] = im
        return self._cache[k]

    def desenhar(self, base, x, y, nivel=0, aberto=True, rot=0.0, dy=0.0, escala=1.0):
        """(x, y) = centro do topo do corpo (base do pescoço) no quadro."""
        c = self.corpo if escala == 1 else self.corpo.resize((int(BW * escala), int(BH * escala)), Image.BILINEAR)
        base.alpha_composite(c, (int(x - c.width / 2), int(y)))
        h = self.cabeca(nivel, aberto)
        if escala != 1: h = h.resize((int(HW * escala), int(HH * escala)), Image.BILINEAR)
        if abs(rot) > 0.05: h = h.rotate(rot, Image.BICUBIC, center=(h.width / 2, h.height * 0.85))
        base.alpha_composite(h, (int(x - h.width / 2), int(y - 540 * escala + dy)))


if __name__ == "__main__":
    import sys
    av = Avatar()
    im = Image.new("RGBA", (1080, 1920), "#2E5156")
    av.desenhar(im, 540, 1120, nivel=int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    im.convert("RGB").save(sys.argv[1] if len(sys.argv) > 1 else "avatar.png")
