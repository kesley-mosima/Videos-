"""Reels Tema 1285 com avatar ilustrado do apresentador intercalado às ilustrações animadas.

- Voz: a narração real (mesmos cortes de render_tema1285.py). Não há síntese nem clonagem de voz.
- Avatar: avatar_mosima.py; boca guiada pelo volume da narração e pelos tempos de cada palavra.
- Ilustrações: cenas de motion_tema1285.py.
- Encerramento: foto real do apresentador em círculo + marca.

Uso: python3 avatar_tema1285.py <audio_original.m4a> <foto_apresentador.jpg> <pasta_saida> [--de S] [--ate S]
"""
import math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import motion_tema1285 as M
from avatar_mosima import Avatar

R, T, W, H, FPS = M.R, M.T, M.W, M.H, M.FPS
CAUDA = 1.5                                # segundos de imagem final após a última palavra
DUR = R.DUR + CAUDA

# janelas do apresentador (tempo editado) · selo · título
APRESENTADOR = [
    (0.0,   T(5.10),  "NOVA DECISÃO DO STJ", "SEU DINHEIRO\nPODE SER PENHORADO?"),
    (T(25.30), T(27.15), "TEMA 1285",        "O QUE O STJ\nDECIDIU"),
    (T(53.85), T(59.29), "MAS ATENÇÃO",      "A PROTEÇÃO NÃO VALE\nEM DOIS CASOS"),
    (T(100.8), T(103.4), "AINDA EM DEBATE",  "VAI TER MUITA\nDISCUSSÃO"),
    (T(111.3), T(114.3), "CONTA BLOQUEADA?", "O QUE FAZER\nAGORA"),
    (T(129.10), T(131.55), "GOSTOU?",        "DECISÕES DO STJ\nDE FORMA SIMPLES"),
]
T_FINAL = T(131.55)                        # card de encerramento com a foto real
FADE = 0.16


# ---------------- boca: envelope de volume + palavras ----------------
def niveis_boca(wav):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", wav, "-f", "s16le", "-ac", "1", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    n = int(DUR * FPS) + 2; jan = 48000 // FPS
    db = np.full(n, -90.0)
    for i in range(n):
        seg = a[i * jan:(i + 1) * jan]
        if len(seg): db[i] = 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
    ref = np.percentile(db[db > -60], 95)
    alvo = np.clip((db - (ref - 30)) / 26, 0, 1)
    fala = np.zeros(n, bool)
    for s, e, _ in R.palavras:
        fala[max(0, int((s - 0.04) * FPS)):int((e + 0.06) * FPS) + 1] = True
    alvo[~fala] = 0
    out, v = np.zeros(n), 0.0
    for i in range(n):                     # ataque rápido, soltura mais lenta
        v += (alvo[i] - v) * (0.75 if alvo[i] > v else 0.45); out[i] = v
    return np.clip(np.round(out * 4.4), 0, 4).astype(int), out


def piscando(t):
    k = int(t / 3.4); base = k * 3.4 + 1.3 + ((k * 7919) % 10) / 10
    return base <= t < base + 0.11


# ---------------- apresentador ----------------
def fundo_apresentador():
    im = M.fundo(M.VERDE).copy()
    ImageDraw.Draw(im).rectangle([0, 1410, W, 1470], fill=M.VERDE)          # sem rodapé de texto atrás do avatar
    an = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(an)
    for r, a in ((390, 70), (320, 95), (250, 120)):
        d.ellipse([540 - r, 1010 - r, 540 + r, 1010 + r], outline=(197, 122, 85, a), width=3)
    im.alpha_composite(an)
    return im

def selo(txt):
    f = M.F("Black", 40); w = int(f.getlength(txt)) + 70
    im = Image.new("RGBA", (w, 76), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, 75], 38, fill=M.COBRE); d.text((w // 2, 38), txt, font=f, fill=M.BRANCO, anchor="mm")
    return im

def preparar_janelas():
    out = []
    for a, b, s, tit in APRESENTADOR:
        out.append((a, b, selo(s), M.texto(tit, ("Black", 64), M.BRANCO)))
    return out

def quadro_apresentador(av, fundo, jan, t, nivel, lvl):
    a, b, sl, tit = jan
    q = fundo.copy(); u = t - a
    p = M.out_cubic(M.clamp(u / 0.35))
    sl_y = 285 + int((1 - p) * -60)
    q.alpha_composite(sl, (540 - sl.width // 2, sl_y))
    if u > 0.12:
        pt = M.clamp((u - 0.12) / 0.35); ti = tit.copy(); ti.putalpha(ti.getchannel("A").point(lambda v: int(v * pt)))
        q.alpha_composite(ti, (540 - ti.width // 2, 395 + int((1 - M.out_cubic(pt)) * 40)))
    rot = 1.6 * math.sin(t * 1.15) + 1.2 * lvl * math.sin(t * 5.3)
    dy = -6 * lvl + 3 * math.sin(t * 1.7) + (1 - p) * 300
    av.desenhar(q, 540, 1230 + (1 - p) * 300, nivel=nivel, aberto=not piscando(t), rot=rot, dy=dy - (1 - p) * 300)
    ImageDraw.Draw(q).rectangle([0, H - 40, W, H], fill=M.COBRE)
    return q


# ---------------- encerramento com a foto real ----------------
def card_final(foto):
    q = M.fundo(M.BRANCO).copy(); d = ImageDraw.Draw(q)
    fo = Image.open(foto).convert("RGB")
    lado = int(fo.width * 0.74); cx, cy = int(fo.width * 0.72), int(fo.height * 0.44)
    x0 = min(max(0, cx - lado // 2), fo.width - lado); y0 = cy - lado // 2
    rosto = fo.crop((x0, y0, x0 + lado, y0 + lado)).resize((500, 500), Image.LANCZOS)
    m = Image.new("L", (500 * 2, 500 * 2), 0); ImageDraw.Draw(m).ellipse([0, 0, 999, 999], fill=255); m = m.resize((500, 500), Image.LANCZOS)
    d.ellipse([540 - 262, 520 - 262, 540 + 262, 520 + 262], fill=M.COBRE)
    q.paste(rosto, (290, 270), m)
    lg = R.LOGO.resize((620, int(620 * R.LOGO.height / R.LOGO.width)), Image.LANCZOS)
    q.alpha_composite(lg, (540 - lg.width // 2, 830))
    els = [M.texto("Siga nosso perfil", ("Black", 60), M.VERDE), M.texto("mosima.com.br", ("Bold", 50), M.COBRE)]
    q.alpha_composite(els[0], (540 - els[0].width // 2, 830 + lg.height + 40))
    q.alpha_composite(els[1], (540 - els[1].width // 2, 830 + lg.height + 130))
    return q


# ---------------- cenas de ilustração (mesma lógica de motion_tema1285) ----------------
def quadro_cena(cenas, t):
    i = max(k for k, c in enumerate(cenas) if c[0] <= t + 1e-6) if t >= cenas[0][0] else 0
    t0, bg, els = cenas[i]
    def render(bg, els):
        q = bg.copy(); M.compor(q, [e for e in els if isinstance(e, M.El)], t)
        for e in els:
            if isinstance(e, tuple) and e[0] == "contador": M.contador(q, t, e[1], e[2])
        return q
    q = render(bg, els)
    if i > 0 and t - t0 < 0.25:
        ant = render(cenas[i - 1][1], cenas[i - 1][2]); off = int(-M.out_cubic((t - t0) / 0.25) * H)
        q = q.copy(); q.paste(ant.crop((0, -off, W, H)), (0, 0))
    return q


def main():
    audio, foto, saida = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(saida, exist_ok=True)
    de = float(sys.argv[sys.argv.index("--de") + 1]) if "--de" in sys.argv else 0.0
    ate = float(sys.argv[sys.argv.index("--ate") + 1]) if "--ate" in sys.argv else DUR
    wav = f"{saida}/narracao-editada.wav"
    if not os.path.exists(wav):
        filtros, rot = [], []
        for k, (s, e) in enumerate(R.CORTES):
            filtros.append(f"[0:a]atrim={s}:{e},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={e - s - 0.04:.3f}:d=0.04[a{k}]"); rot.append(f"[a{k}]")
        filtros.append("".join(rot) + f"concat=n={len(R.CORTES)}:v=0:a=1,highpass=f=80,loudnorm=I=-14:TP=-1.5:LRA=11,apad=pad_dur={CAUDA}[out]")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", audio, "-filter_complex", ";".join(filtros), "-map", "[out]",
                        "-ar", "48000", "-ac", "1", wav], check=True)
    niv, env = niveis_boca(wav)
    av, fundo_ap, janelas, cenas, final = Avatar(), fundo_apresentador(), preparar_janelas(), M.montar_cenas(), card_final(foto)
    completo = de == 0 and ate >= DUR
    nome = f"{saida}/tema-1285-avatar{'' if completo else '-amostra'}.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-ss", str(de), "-t", str(ate - de), "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", nome], stdin=subprocess.PIPE)

    def base(t, n):
        if t >= T_FINAL: return final
        jan = next((j for j in janelas if j[0] <= t < j[1]), None)
        if jan: return quadro_apresentador(av, fundo_ap, jan, t, int(niv[n]), float(env[n]))
        return quadro_cena(cenas, t)

    for n in range(int(de * FPS), int(ate * FPS)):
        t = n / FPS
        q = base(t, n)
        # fusões curtas na entrada/saída do apresentador e do card final
        for j in janelas:
            if j[1] <= t < j[1] + FADE and t < T_FINAL:
                q0 = quadro_apresentador(av, fundo_ap, j, t, int(niv[n]), float(env[n]))
                q = Image.blend(q0, q, M.out_cubic((t - j[1]) / FADE))
        if T_FINAL <= t < T_FINAL + FADE * 2:
            j = janelas[-1]; q0 = quadro_apresentador(av, fundo_ap, j, t, 0, 0.0)
            q = Image.blend(q0, q, (t - T_FINAL) / (FADE * 2))
        if t < T_FINAL: M.legenda(q, t, None)
        ff.stdin.write(q.convert("RGB").tobytes())
        if n % 300 == 0: print(f"  {t:5.1f}s", flush=True)
    ff.stdin.close(); ff.wait()
    print("ok:", nome)


if __name__ == "__main__":
    main()
