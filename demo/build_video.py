"""Build an illustrated first-cut hackathon video with the real Gradium narration."""
from pathlib import Path
import subprocess
import json
import wave

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / 'video_frames'
OUTPUT = ROOT / 'Passage_demo.mp4'
W, H = 1280, 720
INK = '#132c2a'
GREEN = '#15685f'
PALE = '#e6f3ec'
GRAY = '#526461'
WHITE = '#ffffff'


def font(size, bold=False):
    name = 'segoeuib.ttf' if bold else 'segoeui.ttf'
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / name), size)


def wrapped(draw, text, x, y, width, face, fill=INK, line=1.25):
    words = text.split()
    row = ''
    dy = int(face.size * line)
    for word in words:
        candidate = (row + ' ' + word).strip()
        if row and draw.textbbox((0, 0), candidate, font=face)[2] > width:
            draw.text((x, y), row, font=face, fill=fill)
            y += dy
            row = word
        else:
            row = candidate
    if row:
        draw.text((x, y), row, font=face, fill=fill)
        y += dy
    return y


def pill(draw, text, x, y, active=False):
    face = font(22, True)
    width = draw.textbbox((0, 0), text, font=face)[2] + 42
    draw.rounded_rectangle((x, y, x + width, y + 48), radius=23,
                           fill=GREEN if active else PALE)
    draw.text((x + 21, y + 10), text, font=face, fill=WHITE if active else GREEN)
    return width


def card(draw, title, text, x, y, width, height, number=None):
    draw.rounded_rectangle((x, y, x + width, y + height), radius=20, fill=WHITE,
                           outline='#d8e3dc', width=2)
    if number:
        pill(draw, number, x + 25, y + 25, True)
        title_y = y + 88
    else:
        title_y = y + 28
    text_y = wrapped(draw, title, x + 28, title_y, width - 56, font(31, True), INK, 1.2)
    wrapped(draw, text, x + 28, max(title_y + 66, text_y + 15), width - 56,
            font(24), GRAY, 1.3)


def base(kicker, title, subtitle):
    image = Image.new('RGB', (W, H), '#f5f8f3')
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((36, 28, 1244, 692), radius=30, fill='#f9fbf8',
                           outline='#d8e3dc', width=2)
    draw.text((76, 62), 'PASSAGE', font=font(25, True), fill=GREEN)
    draw.text((76, 119), kicker.upper(), font=font(18, True), fill=GREEN)
    wrapped(draw, title, 76, 155, 1110, font(50, True), INK, 1.15)
    wrapped(draw, subtitle, 76, 244, 1110, font(25), GRAY, 1.25)
    draw.line((76, 654, 1204, 654), fill='#d8e3dc', width=2)
    draw.text((76, 663), 'Présentation illustrée  ·  Sébastien Tricoire  ·  voix Gradium', font=font(17), fill=GRAY)
    return image, draw


def make_scenes():
    FRAMES.mkdir(exist_ok=True)
    scenes = []

    image, draw = base('La question de départ', 'Tester un programme pour une thèse',
                       'Protocole, code, données et preuves dans un même projet.')
    pill(draw, 'Doctorant', 76, 360, True)
    pill(draw, 'Analyse de données', 256, 360)
    pill(draw, 'Contrôle humain', 520, 360)
    wrapped(draw, 'Une équipe d’agents. Une décision scientifique humaine.', 76, 477, 1030,
            font(37, True), INK)
    scenes.append((image, 11))

    image, draw = base('1  Cadrer', 'Du projet aux tâches R1–R3',
                       '32 parcours couvrent le travail du doctorant, du jeune docteur et du directeur.')
    card(draw, 'Projet', 'Question, contraintes et résultat attendu', 76, 350, 340, 235, '01')
    card(draw, 'Expérience', 'Concevoir un protocole et ses contrôles', 448, 350, 340, 235, '02')
    card(draw, 'Logiciel', 'Spécifier le code et les tests de référence', 820, 350, 384, 235, '03')
    scenes.append((image, 14))

    image, draw = base('2  Dialoguer', 'Marguerite propose un plan',
                       'Les actions sont visibles et attendent l’accord de l’utilisateur.')
    card(draw, 'Votre demande', '« Aide-moi à tester mon programme d’analyse. »', 76, 350, 480, 240)
    card(draw, 'Plan de Marguerite', 'Cadrer, créer les tâches et définir les contrôles.',
         589, 350, 615, 240)
    pill(draw, 'Valider et exécuter', 850, 522, True)
    scenes.append((image, 15))

    image, draw = base('3  Documenter', 'Le dossier garde les faits et les limites',
                       'Un brouillon d’agent n’est jamais une validation scientifique automatique.')
    card(draw, 'Questions et hypothèses', 'Les paramètres à établir.',
         76, 350, 345, 265, 'A')
    card(draw, 'Preuves et versions', 'Données, pièces et corrections.',
         454, 350, 345, 265, 'B')
    card(draw, 'Décision humaine', 'Le livrable est relu et approuvé.',
         832, 350, 372, 265, 'C')
    scenes.append((image, 14))

    image, draw = base('4  Dessiner', 'Du schéma au brouillon de méthode',
                       'Excalidraw intégré : étapes, décisions et transitions versionnées.')
    for x, title, note in [(76, 'Question', 'Entrées'), (460, 'Processus', 'Décisions'),
                           (844, 'Méthode', 'Brouillon .mthds')]:
        card(draw, title, note, x, 360, 300, 210)
    draw.line((376, 465, 450, 465), fill=GREEN, width=5)
    draw.line((760, 465, 834, 465), fill=GREEN, width=5)
    scenes.append((image, 14))

    image, draw = base('5  Produire', 'Code et tests restent à vérifier',
                       'Le document Python ou R garde chaque version et les preuves associées.')
    card(draw, 'Spécification', 'Hypothèses, données et sorties.', 76, 350, 345, 245, 'A')
    card(draw, 'Programme', 'Code et cas de référence.', 454, 350, 345, 245, 'B')
    card(draw, 'Relecture', 'Avis lié à la version partagée.', 832, 350, 372, 245, 'C')
    scenes.append((image, 16))

    image, draw = base('6  Interroger', 'Qui agit dans le projet ?',
                       'Le scientifique demande quel cerveau, quels outils et quels accès sont utilisés.')
    card(draw, 'Cerveau', 'Compte ChatGPT personnel via Codex.', 76, 350, 495, 240)
    card(draw, 'Harnais', 'Mission, skill, contexte, mémoire et outils.',
         603, 350, 601, 240)
    scenes.append((image, 15))

    image, draw = base('7  Relier', 'Des partenaires et des limites visibles',
                       'Connexion personnelle, outils accordés et traces d’exécution.')
    pill(draw, 'Gradium · voix', 76, 364, True)
    pill(draw, 'Dust · outils MCP', 350, 364)
    pill(draw, 'Pipelex · méthodes', 683, 364)
    wrapped(draw, 'Jinkō SDK : projet personnel à connecter. Code et tests publics.',
            76, 478, 1050, font(34, True), INK)
    scenes.append((image, 12))

    for index, (frame, duration) in enumerate(scenes):
        pill(ImageDraw.Draw(frame), 'Le scientifique' if index % 2 == 0 else 'Marguerite', 76, 296, True)
        frame.save(FRAMES / f'scene-{index:02d}.png', optimize=True)
    return scenes


def main():
    scenes = make_scenes()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    audio_path = ROOT / 'voix-off.wav'
    with wave.open(str(ROOT / 'voix-off.wav'), 'rb') as audio:
        narration_duration = audio.getnframes() / audio.getframerate()
    if narration_duration >= 118:
        # A small tempo correction keeps Gradium's voice while meeting the 119 s limit.
        tempo = narration_duration / 116.5
        audio_path = FRAMES / 'voix-off-montage.wav'
        subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-i', str(ROOT / 'voix-off.wav'),
                        '-filter:a', f'atempo={tempo:.5f}', str(audio_path)], check=True)
        with wave.open(str(audio_path), 'rb') as audio:
            narration_duration = audio.getnframes() / audio.getframerate()
    if narration_duration >= 118:
        raise RuntimeError('La narration dépasse encore le budget de deux minutes.')
    timing_file = ROOT / 'dialogue_timing.json'
    if timing_file.exists():
        timing = json.loads(timing_file.read_text(encoding='utf-8'))
        if len(timing) == len(scenes):
            scenes = [(frame, timing[i]['duration']) for i, (frame, _) in enumerate(scenes)]
    scale = (narration_duration + 1) / sum(duration for _, duration in scenes)
    scenes = [(frame, duration * scale) for frame, duration in scenes]
    concat = FRAMES / 'scenes.txt'
    lines = []
    for index, (_, duration) in enumerate(scenes):
        lines += [f"file 'scene-{index:02d}.png'", f'duration {duration}']
    lines.append(f"file 'scene-{len(scenes) - 1:02d}.png'")
    concat.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    starts = []
    cursor = 0.0
    for _, duration in scenes:
        starts.append(cursor)
        cursor += duration
    active = []
    for speaker in (0, 1):
        parts = [f'between(t\\,{starts[i]:.3f}\\,{starts[i]+scenes[i][1]:.3f})'
                 for i in range(len(scenes)) if i % 2 == speaker]
        active.append('+'.join(parts))
    filters = ('[0:v][2:v]overlay=x=W-w-44:y=46+7*sin(2*PI*t/2.5):'
               f'eval=frame:enable={active[0]}[v1];'
               '[v1][3:v]overlay=x=W-w-42:y=46+7*sin(2*PI*t/2.5):'
               f'eval=frame:enable={active[1]}[v]')
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(concat), '-i', str(audio_path), '-loop', '1',
                    '-framerate', '30', '-i', str(ROOT / 'scientifique-homme-video.png'),
                    '-loop', '1', '-framerate', '30', '-i', str(ROOT / 'scientifique-video.png'),
                    '-filter_complex', filters, '-map', '[v]', '-map', '1:a', '-c:v', 'libx264',
                    '-r', '30', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                    '-t', '118', '-shortest', '-movflags', '+faststart', str(OUTPUT)], check=True)
    print(OUTPUT)


if __name__ == '__main__':
    main()
