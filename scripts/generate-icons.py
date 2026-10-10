"""Generate geometric pp icons (development-only Pillow dependency)."""
from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1] / 'frontend/public'
image = Image.new('RGB', (2048,2048), '#285C47')
draw = ImageDraw.Draw(image)
cream = '#F7F6F2'
for x in (151,279):
    draw.ellipse(((x-12)*4,145*4,(x+108)*4,265*4),fill=cream)
    draw.ellipse(((x+13)*4,170*4,(x+83)*4,240*4),fill='#285C47')
    draw.rounded_rectangle(((x-12)*4,198*4,(x+12)*4,355*4),radius=48,fill=cream)
draw.line([(315*4,212*4),(327*4,224*4),(353*4,195*4)],fill=cream,width=13*4)
for size in (180,192,512):
    image.resize((size,size),Image.Resampling.LANCZOS).save(root/f'icon-{size}.png')
