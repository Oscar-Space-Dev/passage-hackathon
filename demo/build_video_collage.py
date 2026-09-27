"""Animated paper-collage explainer; the researcher narrates the agent workflow."""
from pathlib import Path
import json
import math
import random
import subprocess

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
W, H, FPS = 960, 540, 12
INK, TEAL, GREEN = '#17352F', '#176A60', '#33816C'
PAPER, CREAM, YELLOW, CORAL = '#EFE8D8', '#FFFDF5', '#F7D980', '#EEA483'


def font(size, bold=False):
    name = 'segoeuib.ttf' if bold else 'segoeui.ttf'
    return ImageFont.truetype(str(Path('C:/Windows/Fonts') / name), size)


def text_lines(draw, value, xy, width, size, color=INK, bold=False, gap=1.18):
    face = font(size, bold)
    x, y = xy
    row = ''
    for word in value.split():
        trial = (row + ' ' + word).strip()
        if row and draw.textbbox((0, 0), trial, font=face)[2] > width:
            draw.text((x, y), row, font=face, fill=color)
            y += int(size * gap)
            row = word
        else:
            row = trial
    if row:
        draw.text((x, y), row, font=face, fill=color)
    return y + int(size * gap)


def ease(value):
    p = max(0, min(1, value))
    return p * p * (3 - 2 * p)


def card(canvas, label, detail, x, y, w=188, h=116, angle=0, color=CREAM, reveal=1):
    if reveal <= 0:
        return
    alpha = ease(reveal)
    block = Image.new('RGBA', (w + 32, h + 32))
    d = ImageDraw.Draw(block)
    d.rounded_rectangle((10, 13, w + 20, h + 22), radius=10, fill=(25, 39, 31, 35))
    d.rounded_rectangle((4, 4, w + 14, h + 14), radius=8, fill=color, outline='#D3C7B0', width=2)
    d.line((15, 9, w + 1, 9), fill='#E7DEC9', width=1)
    text_lines(d, label, (18, 23), w - 20, 21, INK, True)
    text_lines(d, detail, (18, 64), w - 18, 14, '#536B62')
    block = block.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True)
    if alpha < 1:
        block.putalpha(block.getchannel('A').point(lambda a: int(a * alpha)))
    canvas.alpha_composite(block, (int(x - block.width / 2), int(y - block.height / 2)))


def arrow(draw, start, end, progress=1, color=TEAL, width=5):
    if progress <= 0:
        return
    p = ease(progress)
    ex = start[0] + (end[0] - start[0]) * p
    ey = start[1] + (end[1] - start[1]) * p
    draw.line((start[0], start[1], ex, ey), fill=color, width=width, joint='curve')
    if p > .9:
        angle = math.atan2(ey - start[1], ex - start[0])
        back = (ex - 15 * math.cos(angle), ey - 15 * math.sin(angle))
        side = 8
        draw.polygon([(ex, ey), (back[0] + side * math.sin(angle), back[1] - side * math.cos(angle)),
                      (back[0] - side * math.sin(angle), back[1] + side * math.cos(angle))], fill=color)


def stamp(draw, label, x, y, color=TEAL):
    d = draw.textbbox((0, 0), label, font=font(17, True))
    width = d[2] + 28
    draw.rounded_rectangle((x, y, x + width, y + 32), radius=15, fill=color)
    draw.text((x + 14, y + 5), label, font=font(17, True), fill='white')


def orb(draw, x, y, r, label, fill=TEAL):
    draw.ellipse((x-r+3, y-r+5, x+r+3, y+r+5), fill='#C9C0AC')
    draw.ellipse((x-r, y-r, x+r, y+r), fill=fill, outline='#F9F5EB', width=3)
    bbox = draw.textbbox((0, 0), label, font=font(15, True))
    draw.text((x-(bbox[2]-bbox[0])/2, y-10), label, font=font(15, True), fill='white')


def polygon_sheet(draw, x, y, w, h):
    draw.polygon([(x, y+5), (x+w*.29, y), (x+w*.6, y+5), (x+w, y+1),
                  (x+w-5, y+h*.4), (x+w, y+h), (x+w*.6, y+h-3),
                  (x+w*.31, y+h+3), (x, y+h-2)], fill=CREAM, outline='#CFC4AE')


def draw_scene(img, scene, p, t, man, woman):
    d = ImageDraw.Draw(img)
    margin = 26
    d.text((margin, 16), 'PASSAGE', font=font(21, True), fill=TEAL)
    d.line((margin, 48, W-margin, 48), fill='#C8BCAB', width=2)
    headings = [
        ('Un problème de recherche', 'Une personne garde le fil de son projet'),
        ('Marguerite propose', 'Le plan attend la décision du chercheur'),
        ('La vraie question', 'Un texte unique ou une équipe qui agit ?'),
        ('Des agents qui coopèrent', 'Chaque spécialité contribue au même projet'),
        ('Et si quelque chose manque ?', 'Les hypothèses et les erreurs restent visibles'),
        ('Le travail devient vérifiable', 'Schéma, brouillon, sources et preuves circulent'),
        ('Partager sans tout exposer', 'Une tâche choisie et des droits explicites'),
        ('Une boucle de travail', 'Planifier, déléguer, relire et décider'),
        ('Un outil, plusieurs métiers', 'Chaque rôle mobilise ses agents dans son projet')]
    title, sub = headings[scene]
    d.text((margin, 64), title, font=font(32, True), fill=INK)
    d.text((margin, 105), sub, font=font(17), fill='#5D7268')
    # The recurring researcher is the narrator; Marguerite answers from the opposite edge.
    speaker = 'LE CHERCHEUR' if scene % 2 == 0 else 'MARGUERITE'
    stamp(d, speaker, 25, 478, TEAL if scene % 2 == 0 else '#BA684E')
    bob = int(4 * math.sin(t * 3.4))
    if scene % 2 == 0:
        img.alpha_composite(man, (17, 168 + bob))
    else:
        img.alpha_composite(woman, (W-woman.width-16, 165 + bob))
    if scene == 0:
        card(img, 'Sources', 'Articles et thèses', 360, 245, angle=-8, reveal=(p-.02)*5)
        card(img, 'Protocole', 'Étapes du test', 568, 270, angle=7, color='#E7F1DF', reveal=(p-.17)*5)
        card(img, 'Programme', 'Code et mesures', 710, 384, angle=-5, color='#F8EBCB', reveal=(p-.33)*5)
        arrow(d, (440, 288), (590, 352), (p-.5)*3)
        stamp(d, 'Un seul projet', 482, 394, '#BA684E')
    elif scene == 1:
        polygon_sheet(d, 48, 152, 615, 292)
        for i, (n, label) in enumerate([('01', 'Cadrer la question'), ('02', 'Ouvrir les tâches'), ('03', 'Choisir les agents')]):
            q = ease((p - i*.18)*5)
            if q:
                d.ellipse((89, 185+i*69, 129, 225+i*69), fill=TEAL)
                d.text((96, 191+i*69), n, font=font(17, True), fill='white')
                d.text((148, 190+i*69), label, font=font(22, True), fill=INK)
                d.line((148, 224+i*69, 518*q, 224+i*69), fill='#D1C3AA', width=2)
        if p > .68:
            stamp(d, 'À VALIDER PAR VOUS', 298, 398, '#BA684E')
    elif scene == 2:
        card(img, 'Une réponse ?', 'Un texte isolé', 414, 289, angle=-7, color='#F7E5D9', reveal=(p-.1)*4)
        card(img, 'Une équipe ?', 'Des rôles et des livrables', 653, 292, angle=6, color='#DAEBDF', reveal=(p-.33)*4)
        if p > .55:
            d.line((492, 187, 575, 406), fill='#BA684E', width=6)
            stamp(d, 'Choisir la coopération', 445, 423)
    elif scene == 3:
        center = (325, 305)
        orb(d, *center, 77, 'PROJET', '#BA684E')
        agents = [('Sources', 549, 193), ('Protocole', 611, 300), ('Code', 540, 416)]
        for i, (name, x, y) in enumerate(agents):
            q = ease((p - .08 - i*.12)*4)
            if q:
                arrow(d, (398, 305), (x-63, y), q)
                orb(d, x, y, 58, name, TEAL)
                if p > .6:
                    arrow(d, (x-2, y+42), (396, 337), (p-.6)*3, '#D28E55', 3)
        if p > .32:
            arrow(d, (570, 242), (588, 254), (p-.32)*3, '#BA684E', 5)
            d.text((592, 216), 'extraits', font=font(14, True), fill='#A45742')
        if p > .52:
            arrow(d, (584, 349), (566, 367), (p-.52)*3, '#BA684E', 5)
            d.text((608, 360), 'critères', font=font(14, True), fill='#A45742')
        if p > .68:
            phase = (t * .65) % 1
            d.ellipse((486+100*phase, 279, 498+100*phase, 291), fill=YELLOW)
        stamp(d, 'Les sorties deviennent des entrées', 310, 451)
    elif scene == 4:
        polygon_sheet(d, 260, 162, 463, 286)
        d.text((291, 190), 'SCHÉMA DU TEST', font=font(21, True), fill=TEAL)
        d.rounded_rectangle((298, 260, 413, 308), radius=7, outline=TEAL, width=4)
        d.text((311, 272), 'Données', font=font(17, True), fill=INK)
        arrow(d, (413, 284), (494, 284), (p-.1)*4)
        d.polygon([(545, 245), (594, 283), (545, 321), (495, 283)], outline='#BA684E', width=4)
        d.text((524, 273), '?', font=font(29, True), fill='#BA684E')
        arrow(d, (595, 283), (665, 283), (p-.4)*4)
        d.text((306, 371), 'Une hypothèse absente = question à poser', font=font(18), fill='#A45742')
    elif scene == 5:
        for i, (name, detail) in enumerate([('Schéma', 'Excalidraw'), ('Brouillon', 'Protocole / .mthds'), ('Preuves', 'Données datées')]):
            card(img, name, detail, 120+i*192, 263+i*(10 if i==1 else 0), 173, 118,
                 angle=(-6, 5, -4)[i], reveal=(p-i*.16)*4)
            if i < 2:
                arrow(d, (212+i*192, 262), (230+i*192, 262), (p-.3)*3, '#BA684E', 3)
        if p > .65:
            stamp(d, 'Relecture humaine', 245, 415, '#BA684E')
    elif scene == 6:
        polygon_sheet(d, 250, 169, 475, 267)
        d.text((282, 197), 'TÂCHE PARTAGÉE', font=font(24, True), fill=TEAL)
        d.text((284, 240), 'Directeur : avis sur cette version', font=font(18), fill=INK)
        d.line((284, 280, 668, 280), fill='#C7BBA5', width=2)
        d.text((284, 303), 'Conversations : privées', font=font(18, True), fill='#A45742')
        d.text((284, 347), 'Outils : accès explicites', font=font(18, True), fill=TEAL)
        stamp(d, 'Dust  ·  Pipelex  ·  Gradium  ·  Jinkō', 262, 392)
    elif scene == 7:
        center = (447, 293)
        orb(d, *center, 52, 'VOUS', '#BA684E')
        nodes = [('PLAN', 423, 182), ('AGENTS', 593, 226), ('PREUVES', 603, 377),
                 ('RELECTURE', 365, 415), ('DÉCISION', 255, 295)]
        for i, (name, x, y) in enumerate(nodes):
            q = ease((p - i*.1)*4)
            if q:
                orb(d, x, y, 43 if name!='RELECTURE' else 48, name, TEAL if i < 3 else '#9A7050')
                nxt = nodes[(i+1)%len(nodes)]
                arrow(d, (x, y), (nxt[1], nxt[2]), (p-.25-i*.06)*2, '#D28E55', 2)
        stamp(d, 'Le projet avance, le chercheur décide', 220, 467)
    else:
        uses = [('Direction de thèse', 'Relire et commenter'),
                ('Laboratoire', 'Coordonner une équipe'),
                ('Ingénierie', 'Tester et documenter'),
                ('Entreprise', 'Explorer le transfert')]
        for i, (role, use) in enumerate(uses):
            x = 392 + (i % 2) * 250
            y = 228 + (i // 2) * 143
            card(img, role, use, x, y, 218, 102,
                 angle=(-4, 3, 2, -3)[i],
                 color=('#FFFDF5', '#E7F1DF', '#F8EBCB', '#F7E5D9')[i],
                 reveal=(p - i * .15) * 4)
        if p > .67:
            stamp(d, 'Des agents au service du travail réel', 295, 454)
    # Small moving paper fragments give the collage a continuous handmade motion.
    for i in range(12):
        x = int((i*77 + 17 + t*6) % W)
        y = int((i*43 + 149 + 3*math.sin(t+i)) % H)
        d.line((x, y, x+7, y+2), fill='#D8CBB8', width=1)


def main():
    timing = json.loads((ROOT / 'dialogue_timing-v2.json').read_text(encoding='utf-8'))
    audio = ROOT / 'voix-off-v2.wav'
    output = ROOT / 'Passage_demo_collage.mp4'
    man = Image.open(ROOT / 'scientifique-homme-v2.png').convert('RGBA')
    woman = Image.open(ROOT / 'scientifique.png').convert('RGBA')
    man = man.crop(man.getchannel('A').getbbox())
    woman = woman.crop(woman.getchannel('A').getbbox())
    man.thumbnail((205, 315), Image.Resampling.LANCZOS)
    woman.thumbnail((205, 315), Image.Resampling.LANCZOS)
    random.seed(12)
    background = Image.new('RGBA', (W, H), PAPER)
    b = ImageDraw.Draw(background)
    for i in range(2500):
        x, y = random.randrange(W), random.randrange(H)
        b.point((x, y), fill=random.choice(['#ECE3D3', '#E5DAC8', '#F4EDE0']))
    duration = sum(item['duration'] for item in timing)
    if duration >= 119:
        raise RuntimeError(f'Dialogue trop long : {duration:.1f} s')
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
           '-s', f'{W}x{H}', '-r', str(FPS), '-i', 'pipe:0', '-i', str(audio),
           '-vf', 'scale=1280:720:flags=lanczos', '-c:v', 'libx264', '-preset', 'veryfast',
           '-crf', '21', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
           '-shortest', '-movflags', '+faststart', str(output)]
    process = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for scene, item in enumerate(timing):
        first = round(item['start'] * FPS)
        last = round((item['start'] + item['duration']) * FPS)
        for frame in range(first, last):
            absolute = frame / FPS
            p = (absolute - item['start']) / max(item['duration'], .001)
            image = background.copy()
            draw_scene(image, scene, p, absolute, man, woman)
            try:
                process.stdin.write(image.convert('RGB').tobytes())
            except BrokenPipeError:
                raise RuntimeError('FFmpeg a arrêté le rendu ; vérifier le filtre et la sortie.')
        print(f'Scène {scene+1}/{len(timing)} rendue', flush=True)
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError('Échec du montage FFmpeg.')
    print(f'{output} · {duration:.1f} s')


if __name__ == '__main__':
    main()
