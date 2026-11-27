"""Transcrição local com tempo por palavra (Whisper). Uso: python3 transcrever.py audio16k.wav palavras.csv [medium]
Pré-requisitos: pip install openai-whisper; host openaipublic.azureedge.net liberado (download do modelo, 1x).
Extraia o áudio antes: ffmpeg -i video.mov -vn -ac 1 -ar 16000 audio16k.wav"""
import sys, csv, whisper, time
audio, saida, modelo = sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "medium"
t0 = time.time(); m = whisper.load_model(modelo)
r = m.transcribe(audio, language="pt", word_timestamps=True, condition_on_previous_text=False, fp16=False)
rows, i = [("index", "start", "end", "text")], 0
for seg in r["segments"]:
    for w in seg.get("words", []):
        i += 1; rows.append((i, f"{w['start']:.3f}", f"{w['end']:.3f}", w["word"].strip()))
csv.writer(open(saida, "w", encoding="utf-8", newline="")).writerows(rows)
for seg in r["segments"]: print(f"[{seg['start']:6.2f}-{seg['end']:6.2f}] {seg['text'].strip()}")
print(f"palavras: {i} · {time.time()-t0:.0f}s")
