---
name: mosima-reels
description: Produz Reels jurídicos do escritório Moraes Silva & Massimino (Mosima) no padrão "action mode" — da capa ao cartão final. Use sempre que o usuário enviar um vídeo gravado (advogado falando para a câmera) e pedir para editar, montar, legendar ou transformar em Reels/TikTok/Shorts no padrão do escritório, ou quando mencionar "action mode", "padrão Mosima de vídeo", "tela dividida", "Reels do escritório", "capa do Reels" ou "próximo vídeo nesse padrão". Cobre transcrição, checagem jurídica da fala, cortes de regravações, limpeza de áudio, duração até 75 s, tela cheia + tela dividida com painel animado, legenda curta o tempo todo, capa com foto sorrindo e nome, cartão final com @mosimaadv.
---

# Reels Mosima — padrão "action mode"

Este skill transforma uma gravação do advogado falando para a câmera num Reels vertical
(1080×1920, 30 fps, até ~75 s) com a identidade Mosima. O motor é `scripts/reels.py`, que lê um
**roteiro JSON**. O exemplo completo e validado está em `exemplos/tema-1285/roteiro.json`.

## O padrão (o que o vídeo final tem)

| Momento | Formato |
|---|---|
| **Capa** (imagem separada) | Foto do advogado **sorrindo** (quadro do próprio vídeo), degradê verde embaixo, selo do tema, chamada em 2 linhas (branco + cobre), subtítulo, **nome e OAB só aqui**. Sem logotipo sobre o rosto. |
| **Gancho** (0–~10 s) | Rosto em **tela cheia**, título grande sobre o peito (ex.: "COBRANDO OU / SENDO COBRADO?"). |
| **Explicação** | **Tela dividida**: painel animado em cima (fundo verde-escuro com brilho), advogado num **cartão arredondado** embaixo. O painel se monta no ritmo da fala (chips, contadores, ícones com ✔/✖, listas, gráficos que se desenham, colunas "antes → depois"). |
| **Viradas** ("mas atenção", "exceções") | Volta à tela cheia com título grande. |
| **Legenda** | **O tempo todo**, 1–3 palavras, Lato Black branco com contorno — no peito (tela cheia) ou na parte de baixo do cartão (tela dividida). |
| **CTA** | Tela cheia + título "SIGA / @mosimaadv". |
| **Final** | Cartão com o logotipo completo, @mosimaadv e frase curta (1,6 s). |
| **Áudio** | Regravações cortadas, pausas enxugadas (≤0,3 s), limpeza (ruído, sibilância, EQ, compressão), aceleração ≤8%, −14 LUFS, pico ≤ −1,5 dBTP. |

Não usar: faixa de nome durante o vídeo, número do tema fixo na tela, rodapé permanente com artigo de lei.

Identidade: verde `#2E5156`, verde-escuro `#1F383C`/`#132629`, cobre `#C57A55`, areia `#F4EFEA`; fonte **Lato** (Black títulos, Bold destaques, Regular apoio) — já incluída em `assets/fontes`; logotipos em `assets/`.

## Fluxo de trabalho (siga nesta ordem)

### 1. Receber o material
- Peça o **arquivo original** (não o do WhatsApp, que comprime para ~576×1024). Se vier link do Google Drive,
  ele precisa estar em "Qualquer pessoa com o link" para o Scriptivox transcrever; o download do arquivo grande
  pelo Drive costuma falhar no servidor — nesse caso use o arquivo anexado ao chat.
- Confira com `ffprobe`: duração, resolução, rotação, volume (`volumedetect`).

### 2. Transcrever com tempo por palavra
- Scriptivox: `transcribe_url` (link do Drive público, Instagram, etc.) ou upload pelo site/caixa.
- Exporte **CSV com 1 palavra por linha**: `export_transcript(formats=["csv"], max_words=1, max_duration=2, include_speakers="false")`.
- **Sem cota no Scriptivox** (3/dia no plano grátis): use `scripts/transcrever.py` (Whisper `medium`, local, ~2 min por minuto de áudio). O Whisper às vezes "cola" a pausa no início de uma palavra: confira os limites das tomadas com `silencedetect` e garanta que a primeira/última palavra de cada corte esteja **inteira dentro** do intervalo (senão some da legenda).
- Salve como `palavras.csv` (colunas `index,start,end,text`, tempos em segundos — converta `00:01:02.345` → `62.345`).
  Pode manter só as palavras dos trechos aproveitados.

### 3. Checagem jurídica da fala (antes de editar)
Separe e informe ao usuário: **fatos confirmados** (tese/súmula/artigo conferidos na fonte oficial — STJ, STF,
planalto.gov.br), **imprecisões técnicas na fala** (ex.: "não pode ficar bloqueado" × "é impenhorável"),
**opiniões**, e o que precisa de ressalva na descrição do post. Confira número de tema/súmula (ex.: "Súmula 1285"
não existe; era Tema Repetitivo 1285). Não invente tese. Verifique o Provimento 205/2021 da OAB:
sem captação, sem promessa de resultado, CTA informativo ("siga o perfil").

### 4. Decidir os cortes
- Elimine regravações ("vamos fazer de novo", "apaga essa parte", "é para ficar esse último"), frases truncadas,
  erros de concordância/termo (cortando o trecho, sem inventar fala) e repetições.
- Se passar de ~75 s, corte o trecho menos essencial (geralmente uma conclusão que repete algo já dito) em vez
  de acelerar mais de 8%.
- `cortes` = lista de intervalos **mantidos** em segundos do original. O motor ainda enxuga pausas internas.

### 5. Escrever o roteiro JSON
Copie `exemplos/tema-1285/roteiro.json` e ajuste. Todos os tempos (`t`, `fim`, `de`, `ate`, `t2`) são
**segundos do vídeo original**, tirados do CSV (o motor converte para a linha do tempo editada).
Ancore cada elemento na palavra em que ele deve aparecer.

Campos do projeto: `nome`, `video`, `palavras_csv`, `saida`, `handle`, `frase_final`, `cortes`,
`duracao_alvo` (74), `pausa_max` (0.30), `vel_max` (1.08), `cauda` (1.6), `correcoes` (palavra→palavra, ex. `"StJ":"STJ"`),
`correcoes_indice` (índice do CSV→texto), `reusar_base` (true para não reprocessar o áudio/vídeo base),
`layout` opcional (`cartao`, `recorte` — ajuste o `recorte` se o rosto estiver em outra altura —, `legenda_cheio`, `legenda_split`).

**Variações de forma** (para não repetir o mesmo visual e para testes A/B em tráfego pago):
- `layout.estilo`: `"split"` (painel em cima, padrão) ou `"invertido"` (rosto em cima no cartão, painel embaixo, y≈1030–1450; legenda em y≈920).
- `layout.tema`: `"escuro"` (padrão) ou `"claro"` (painel areia; textos brancos viram verde-escuro automaticamente).
- `layout.transicao`: `"cortina"` (painel entra deslizando da direita) — padrão é o cartão encolher.
- `layout.zoom_cheio`: `{"escala": 1.6, "centro": [540, 600]}` para gravações de corpo inteiro (enquadra rosto e tronco).
- `"punch": true` num bloco de tela cheia: zoom de 12% alternado a cada frase (punch-in). `punch_forca` ajusta.
- `"barra_progresso": true`: barra cobre no topo, indicando quanto falta (retenção).
- `"destaques": [...]`: palavras da legenda em cobre (números, sintomas, "não", direito).
- Elementos extras: `carimbo` (`texto`, ex. "MITO", girado, cobre) e `check` (`texto`, `t_ok` — caixa que ganha ✔).
- Primeiro quadro: use `"anim": "nenhum"` no título do gancho para ele já aparecer no quadro 0 (anúncios).

**Legenda com ritmo (padrão recomendado):** `"legenda_estilo": "karaoke"`: grupos de até 4 palavras que entram
com um "pop"; a palavra que está sendo falada fica em cobre e cresce no instante em que é dita; palavras em
`destaques` ficam em cobre o grupo todo. Alternativas: `"frase"` (discreta, por frase) e o padrão curto (1–3 palavras).
Cortes em preto e branco (`pb`) devem durar **~3 s** com a frase visível o tempo todo; menos que isso não dá para ler.
Evite selos numerados ("01/02/03") — o escritório achou desnecessários.

**Estilo editorial** (mais sóbrio; aprovado pelo escritório como "modelo A"): rosto em tela cheia o tempo todo,
sem tela dividida. Use `"legenda_estilo": "frase"` (legenda discreta por frase, 2 linhas), `"marca_dagua": true`
(@ pequeno no canto superior direito) e os elementos:
- `titulo_serifa` (`l1`, `l2`): abertura elegante com Playfair (2ª linha em itálico cobre), y≈1110 (sobre o tronco).
- `numero` (`texto` "01"…): selo de capítulo — disponível, mas não usar por padrão.
- `pb` (`t`, `fim`): ~3 s em preto e branco com o topo escurecido, para abrir capítulo (com `manchete` entre aspas no mesmo intervalo).
- `manchete` (`texto`, `tam`, `cor`): frase curta em Oswald condensada, cobre, y≈1110; entre aspas no corte P&B.
Títulos e manchetes ficam **acima da cabeça** (y≈310), longe da legenda (y≈1290): use `layout.descer` (ex.: 270) para descer a imagem e abrir espaço no topo (preenchido com o fundo desfocado) e `layout.escurecer_topo: true` para dar contraste; `layout.marca_y` (130) sobe o @. Sem filtro preto e branco no modelo A (o escritório preferiu a imagem sempre colorida). Para destacar uma frase no painel, use `faixa` (`texto`, `tam`: caixa cobre sólida com texto branco, pode pulsar). Exemplo: `projetos/auxilio-acidente/roteiro-A.json`.

**Técnicas de atração para tráfego pago** (aplicar quando o vídeo for impulsionado):
gancho escrito no quadro 0 em forma de pergunta de identificação; troca visual a cada 2–4 s (punch-in, painel,
carimbo); checklist de sintomas/situações que o público reconhece; quebra de mito ("muita gente acredita… MITO");
legenda sempre com palavras-chave em cobre (assistido sem som); 40–60 s; CTA informativo (seguir o perfil).
Produza **duas variações (A/B)** com mesmos cortes e formas diferentes, e capas com chamadas diferentes.
OAB: impulsionamento de conteúdo informativo é admitido; evite promessa de resultado, "ganhe", valores,
urgência artificial e chamada direta para contratação; revise o texto do anúncio no gerenciador de anúncios também.

`capa`: `instante` (segundo do original com o advogado **sorrindo** — procure em pausas e no fim das tomadas),
`selo`, `linha1`, `linha2`, `subtitulo`, `nome`, `registro`, opcionais `zoom` (1.25) e `deslocamento_y` (60).

`blocos`: `{"de", "ate" (ou "fim"), "modo": "cheio"|"split", "elementos": [...]}` em sequência contínua.
Painel da tela dividida ocupa y≈150–820; títulos de tela cheia ficam em y≈1120.

Tipos de elemento (campos comuns: `t`, `fim`, `x`=540, `y`, `anim`, `dur`, `loop` ("pulso"/"flutuar"/"balanco"), `amp`):

| tipo | campos | uso |
|---|---|---|
| `titulo` | `l1`, `l2`, `cor` | título de tela cheia (2 linhas, 2ª em cobre) |
| `chip` | `texto`, `cor` | etiqueta do painel ("• EXCEÇÃO 1"), y=180 |
| `texto` | `texto`, `estilo` (titulo, destaque, corpo, nota, grande, alerta), `tam`, `cor` | textos do painel |
| `contador` | `ate`, `de`, `rotulo`, `sufixo`, `t2`, `y` | número que conta (ex.: "ATÉ 40") |
| `icone` | `nome`, `escala` | moeda, escudo, cofrinho, cedulas, grafico_estavel, grafico_risco, grafico_volatil, grafico_subida, calendario, cadeado, martelo, balanca, documento, casa, alerta, seta |
| `selo` | `ok` (true=✔ verde, false=✖ cobre), `r` | marca de permitido/proibido |
| `tile` | `rotulo`, `icone` | cartão 300×260 com ícone (3 por linha: x=200/540/880) |
| `linha` | `texto`, `valor`, `positivo` | linha de extrato/lista (+/−) |
| `coluna` | `titulo`, `texto`, `cor` | caixa "MÊS 1 / MÊS 2", "ANTES / DEPOIS" |
| `moedas` | `n`, `passo`, `r` | moedas caindo e flutuando |

Animações (`anim`): pop, subir, esq, dir, fade, cair, revelar (gráficos se desenham).

### 6. Conferir antes de renderizar tudo
```
python3 scripts/reels.py roteiro.json --capa
python3 scripts/reels.py roteiro.json --quadros 2,17,30,47,60
```
Monte uma folha de contato dos PNGs e **olhe**: sobreposição de textos, rosto coberto, legenda legível,
capa com rosto e título dentro da área 4:5 (retângulo vermelho em `capa-grade.png`).

### 7. Renderizar e verificar
```
python3 scripts/reels.py roteiro.json
```
Gera `saida/<nome>.mp4`, `saida/capa.png`, `saida/legendas.srt`. Verifique duração (`ffprobe`) e
loudness (`ebur128`: I≈−14 LUFS). Extraia ~15 quadros e confira a sincronia visual.
Diga ao usuário o que foi verificado por quadros e o que só ele pode conferir ouvindo (cortes, voz).

### 8. Entregar
- Envie capa + vídeo; salve no repositório; liste cortes feitos, pontos jurídicos e pendências.
- Sugira a descrição do post com a ressalva técnica necessária e crédito a fontes de terceiros.
- Lembre: capa vai em "Editar capa → Adicionar da galeria" no Instagram.

## Requisitos
Python 3 com Pillow, ffmpeg com libx264 (filtros afftdn, deesser, loudnorm, alimiter). Memória: o motor
usa `select/aselect` num único fluxo para não estourar RAM. ~30–60 s de render para 75 s de vídeo.
