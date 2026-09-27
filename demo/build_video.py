"""Build an illustrated first-cut hackathon video with the real Gradium narration."""
from pathlib import Path
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FRAMES = ROOT / 'video_frames'
OUTPUT = ROOT / 'Passage_demo_76s.mp4'
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
    draw.text((1090, 65), 'X IA 2026', font=font(18, True), fill=GRAY)
    draw.text((76, 119), kicker.upper(), font=font(18, True), fill=GREEN)
    wrapped(draw, title, 76, 155, 1110, font(50, True), INK, 1.15)
    wrapped(draw, subtitle, 76, 244, 1110, font(25), GRAY, 1.25)
    draw.line((76, 654, 1204, 654), fill='#d8e3dc', width=2)
    draw.text((76, 663), 'Première version illustrée  ·  voix Gradium', font=font(17), fill=GRAY)
    return image, draw


def make_scenes():
    FRAMES.mkdir(exist_ok=True)
    scenes = []

    image, draw = base('Recherche doctorale', 'Conduire une thèse avec une équipe d’agents',
                       'Lire, expérimenter, comparer, coder et justifier les résultats.')
    pill(draw, 'Doctorant', 76, 360, True)
    pill(draw, 'Projet scientifique', 256, 360)
    pill(draw, 'Contrôle humain', 501, 360)
    wrapped(draw, 'Les agents proposent. Le chercheur décide.', 76, 477, 1030,
            font(37, True), INK)
    scenes.append((image, 8))

    image, draw = base('1  Cadrer', 'Un projet, des tâches scientifiques précises',
                       'Le parcours couvre la lecture, les expériences, la rédaction et le logiciel.')
    card(draw, 'Projet', 'Question de recherche et résultat attendu', 76, 350, 340, 235, '01')
    card(draw, 'Travail doctoral', 'Questions, pièces et étapes à vérifier', 448, 350, 340, 235, '02')
    card(draw, 'Livrable', 'Brouillon, preuves et validation', 820, 350, 384, 235, '03')
    scenes.append((image, 12))

    image, draw = base('2  Dialoguer', 'Marguerite propose avant d’agir',
                       'L’utilisateur décrit son objectif ; le plan reste visible avant exécution.')
    card(draw, 'Votre demande', '« Aide moi à organiser ma revue de littérature. »', 76, 350, 480, 240)
    card(draw, 'Plan de Marguerite', 'Créer le travail, choisir les sources, préparer le brouillon.',
         589, 350, 615, 240)
    pill(draw, 'Validation requise', 844, 522, True)
    scenes.append((image, 13))

    image, draw = base('3  Vérifier', 'Chaque résultat garde sa trace',
                       'Les étapes, sources autorisées et limites restent consultables dans le dossier.')
    card(draw, 'Questions et hypothèses', 'Ce que le chercheur veut établir.',
         76, 350, 345, 265, 'A')
    card(draw, 'Preuves et versions', 'Pièces datées et corrections conservées.',
         454, 350, 345, 265, 'B')
    card(draw, 'Décision humaine', 'Le livrable est relu puis validé.',
         832, 350, 372, 265, 'C')
    scenes.append((image, 13))

    image, draw = base('4  Dessiner', 'Du protocole dessiné au brouillon',
                       'Le schéma intégré aide à formaliser une méthode que le chercheur relit.')
    for x, title, note in [(76, 'Question', 'Objectif'), (460, 'Étapes', 'Processus'),
                           (844, 'Méthode', 'Brouillon')]:
        card(draw, title, note, x, 360, 300, 210)
    draw.line((376, 465, 450, 465), fill=GREEN, width=5)
    draw.line((760, 465, 834, 465), fill=GREEN, width=5)
    scenes.append((image, 11))

    image, draw = base('5  Configurer', 'Un cerveau et un harnais versionné',
                       'ChatGPT est le choix par défaut ; chaque agent possède une mission contrôlée.')
    card(draw, 'Cerveau', 'Compte ChatGPT personnel via Codex.', 76, 350, 495, 240)
    card(draw, 'Harnais', 'Skill, contexte, mémoire, outils et règles.',
         603, 350, 601, 240)
    scenes.append((image, 12))

    image, draw = base('6  Relier', 'Des partenaires autour du même projet',
                       'Les accès et les appels externes restent explicites et vérifiables.')
    pill(draw, 'Gradium · voix', 76, 364, True)
    pill(draw, 'Dust · outils MCP', 350, 364)
    pill(draw, 'Pipelex · méthodes', 683, 364)
    wrapped(draw, 'Passage réunit ces capacités au service du travail doctoral.',
            76, 478, 1050, font(34, True), INK)
    scenes.append((image, 7))

    for index, (frame, duration) in enumerate(scenes):
        frame.save(FRAMES / f'scene-{index:02d}.png', optimize=True)
    return scenes


def main():
    scenes = make_scenes()
    concat = FRAMES / 'scenes.txt'
    lines = []
    for index, (_, duration) in enumerate(scenes):
        lines += [f"file 'scene-{index:02d}.png'", f'duration {duration}']
    lines.append(f"file 'scene-{len(scenes) - 1:02d}.png'")
    concat.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0',
                    '-i', str(concat), '-i', str(ROOT / 'voix-off.wav'), '-c:v', 'libx264',
                    '-r', '30', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                    '-shortest', '-movflags', '+faststart', str(OUTPUT)], check=True)
    print(OUTPUT)


if __name__ == '__main__':
    main()
