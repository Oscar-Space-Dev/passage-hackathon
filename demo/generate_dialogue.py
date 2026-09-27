"""Generate a two-voice Gradium dialogue for the hackathon video."""
from pathlib import Path
import io
import json
import os
import time
import wave

from passage.voice import Speech, speak
from passage import integrations


ROOT = Path(__file__).resolve().parent
VOICES = {'scientifique': 'l2nzlZ4fcaobSwPk', 'marguerite': 'FXxJ9mANRq6BCTX5'}


def main():
    suffix = os.environ.get('PASSAGE_DIALOGUE_SUFFIX', '')
    lines = json.loads((ROOT / f'dialogue{suffix}.json').read_text(encoding='utf-8'))
    clips = ROOT / f'dialogue_clips{suffix}'
    clips.mkdir(exist_ok=True)
    frames = []
    fmt = None
    timing = []
    elapsed = 0.0
    for index, line in enumerate(lines):
        integrations.SESSION_SECRETS['GRADIUM_VOICE_ID'] = VOICES[line['speaker']]
        clip_path = clips / f'{index:02d}-{line["speaker"]}.wav'
        if os.environ.get('PASSAGE_REUSE_DIALOGUE_CLIPS') == '1' and clip_path.exists():
            body = clip_path.read_bytes()
        else:
            for attempt in range(2):
                try:
                    body = speak(Speech(text=line['text'])).body
                    break
                except Exception:
                    if attempt:
                        raise
                    time.sleep(1)
            clip_path.write_bytes(body)
        with wave.open(io.BytesIO(body), 'rb') as clip:
            current = (clip.getnchannels(), clip.getsampwidth(), clip.getframerate())
            if fmt is None:
                fmt = current
            elif current != fmt:
                raise RuntimeError('Gradium returned incompatible audio formats.')
            raw = clip.readframes(clip.getnframes())
            duration = len(raw) / (current[0] * current[1] * current[2])
        timing.append({'scene': index, 'speaker': line['speaker'], 'start': round(elapsed, 3), 'duration': round(duration, 3)})
        frames.append(raw)
        elapsed += duration
        if index < len(lines) - 1:
            pause = .22
            frames.append(b'\0' * int(fmt[2] * pause) * fmt[0] * fmt[1])
            timing[-1]['duration'] += pause
            elapsed += pause
    with wave.open(str(ROOT / f'voix-off{suffix}.wav'), 'wb') as out:
        out.setnchannels(fmt[0])
        out.setsampwidth(fmt[1])
        out.setframerate(fmt[2])
        out.writeframes(b''.join(frames))
    (ROOT / f'dialogue_timing{suffix}.json').write_text(json.dumps(timing, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Dialogue Gradium: {elapsed:.1f} s')


if __name__ == '__main__':
    main()
