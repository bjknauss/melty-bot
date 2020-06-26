import os
import glob

from PIL import Image, ImageDraw, ImageFilter

pfp_img = Image.open('img/pfp.png')
welcome = Image.open('img/welcome_small.jpg').convert('RGBA')

mask = Image.new("L", pfp_img.size, 0)

draw = ImageDraw.Draw(mask)
draw.ellipse((0, 0, pfp_img.size[0], pfp_img.size[1]), fill=255)

pfp = pfp_img.copy()
pfp.putalpha(mask)
print(pfp.mode)
print(welcome.mode)


def set_pfp(pfp_img, welcome_img, x, y):
    welcome = welcome_img.copy()
    size = 195
    pfp = pfp_img.resize((size, size))
    welcome.alpha_composite(pfp, (x, y))
    welcome.save('out/welcome.png')


set_pfp(pfp, welcome, 77, 45)