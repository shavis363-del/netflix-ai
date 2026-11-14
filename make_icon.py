"""Generates netflix_icon.png (red 'N' ribbon on black) used as the browser-tab icon."""
from PIL import Image, ImageDraw

S = 256
img = Image.new("RGBA", (S, S), (20, 20, 20, 255))
d = ImageDraw.Draw(img)
x0, x1, top, bot, w = 78, 178, 36, 220, 28
d.rectangle([x0, top, x0 + w, bot], fill=(185, 9, 11, 255))          # left bar
d.rectangle([x1 - w, top, x1, bot], fill=(185, 9, 11, 255))          # right bar
d.polygon([(x0, top), (x0 + w, top), (x1, bot), (x1 - w, bot)], fill=(229, 9, 20, 255))  # diagonal
img.save("netflix_icon.png")
