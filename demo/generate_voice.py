"""Generate the hackathon narration with the configured Gradium installation key."""
from pathlib import Path
import io
import time
import wave

from passage.voice import Speech, speak


def main():
    root = Path(__file__).resolve().parent
    paragraphs = [part.strip() for part in (root / 'voix-off.txt').read_text(encoding='utf-8').split('\n\n') if part.strip()]
    target = root / 'voix-off.wav'
    sample_rate = None
    frames = []
    for index, paragraph in enumerate(paragraphs, 1):
        for attempt in range(2):
            try:
                response = speak(Speech(text=paragraph))
                break
            except Exception:
                if attempt:
                    raise
                time.sleep(1)
        with wave.open(io.BytesIO(response.body), 'rb') as piece:
            current = (piece.getnchannels(), piece.getsampwidth(), piece.getframerate())
            if sample_rate is None:
                sample_rate = current
            elif current != sample_rate:
                raise RuntimeError('Formats audio Gradium incompatibles entre les paragraphes.')
            frames.append(piece.readframes(piece.getnframes()))
            if index < len(paragraphs):
                frames.append(b'\0' * int(piece.getframerate() * .3) * piece.getnchannels() * piece.getsampwidth())
    with wave.open(str(target), 'wb') as audio:
        audio.setnchannels(sample_rate[0])
        audio.setsampwidth(sample_rate[1])
        audio.setframerate(sample_rate[2])
        audio.writeframes(b''.join(frames))
    with wave.open(str(target), 'rb') as audio:
        duration = audio.getnframes() / audio.getframerate()
    print(f'{target.name}: {duration:.1f} s')


if __name__ == '__main__':
    main()
