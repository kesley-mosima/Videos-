"""Capa do Reels Tema 1285: foto sorrindo + nome do advogado (identidade Mosima).

Uso: python3 capa_tema1285.py <video_original.mp4> <instante_segundos> <saida.png>
"""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from render_tema1285 import F, VERDE, VERDE_ESC, COBRE, BRANCO, SIMB

W, H = 1080, 1920

def main():
    video, t, out = sys.argv[1], sys.argv[2], sys.argv[3]
    tmp = out + ".quadro.png"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", t, "-i", video, "-frames:v", "1",
                    "-vf", f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6", tmp], check=True)
    foto = Image.open(tmp).convert("RGBA"); os.remove(tmp)
    # aproxima no rosto (o terço superior do quadro) para valorizar o sorriso
    z = 1.25; fw, fh = int(W * z), int(H * z)
    foto = foto.resize((fw, fh), Image.LANCZOS).crop(((fw - W) // 2, 60, (fw - W) // 2 + W, 60 + H))
    im = foto.copy()
    # degradê verde na metade de baixo para o texto
    grad = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(grad)
    r, gg, b = int(VERDE_ESC[1:3], 16), int(VERDE_ESC[3:5], 16), int(VERDE_ESC[5:7], 16)
    for y in range(820, H):
        a = min(245, int(245 * ((y - 820) / 420) ** 1.3)) if y < 1240 else 245
        g.line([(0, y), (W, y)], fill=(r, gg, b, a))
    im.alpha_composite(grad)
    d = ImageDraw.Draw(im)
    # selo do tema (área central visível na grade 4:5 do perfil)
    d.rounded_rectangle([340, 1010, 740, 1080], 16, fill=COBRE)
    d.text((540, 1045), "TEMA 1285 · STJ", font=F("Black", 40), fill=BRANCO, anchor="mm")
    y = 1110
    for linha in ["SEU DINHEIRO PODE", "SER PENHORADO?"]:
        d.text((540, y), linha, font=F("Black", 92), fill=BRANCO, anchor="mt"); y += 104
    d.rectangle([440, y + 22, 640, y + 28], fill=COBRE)
    d.text((540, y + 60), "Kesley de Moraes Silva", font=F("Bold", 46), fill=BRANCO, anchor="mt")
    d.text((540, y + 118), "OAB/SC nº 30.490  ·  Moraes Silva & Massimino Advogados", font=F("Regular", 30), fill="#E9D3C6", anchor="mt")
    # símbolo no topo
    im.alpha_composite(SIMB.resize((110, 108), Image.LANCZOS), (485, 110))
    d.rectangle([482, 107, 597, 220], outline=COBRE, width=3)
    d.rectangle([0, H - 40, W, H], fill=COBRE)
    im.convert("RGB").save(out, quality=95)
    # versão de conferência com a área que aparece na grade do perfil (4:5 central)
    chk = im.convert("RGB").copy(); dc = ImageDraw.Draw(chk); top = (H - 1350) // 2
    dc.rectangle([0, top, W - 1, top + 1350], outline="#FF3B30", width=6)
    chk.resize((540, 960)).save(out.replace(".png", "-grade.png"))
    print("ok", out)

if __name__ == "__main__":
    main()
