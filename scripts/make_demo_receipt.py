"""Generate a synthetic receipt image for demo/screenshot purposes."""
from PIL import Image, ImageDraw, ImageFont

W, H = 640, 900
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

try:
    font_l = ImageFont.truetype("arial.ttf", 34)
    font   = ImageFont.truetype("arial.ttf", 24)
    font_s = ImageFont.truetype("arial.ttf", 20)
except Exception:
    font_l = font = font_s = ImageFont.load_default()

center = W // 2
d.text((center, 40), "CAMPUS PRINT HUB", font=font_l, fill="black", anchor="ma")
d.text((center, 85), "Block C, University Road", font=font_s, fill="black", anchor="ma")
d.text((center, 112), "Bengaluru 560001", font=font_s, fill="black", anchor="ma")
d.line((40, 150, W - 40, 150), fill="black", width=2)

rows = [
    ("Date", "24/10/2026"),
    ("Receipt #", "CPH-00431"),
    ("Cashier", "R. Kumar"),
]
y = 175
for k, v in rows:
    d.text((50, y), k, font=font_s, fill="black")
    d.text((W - 50, y), v, font=font_s, fill="black", anchor="ra")
    y += 34

d.line((40, y + 10, W - 40, y + 10), fill="black", width=1)

items = [
    ("A3 Colour Print x40", "240.00"),
    ("Binding (spiral) x12", "120.00"),
    ("Lamination x8", "71.50"),
]
y += 30
for name, amount in items:
    d.text((50, y), name, font=font_s, fill="black")
    d.text((W - 50, y), amount, font=font_s, fill="black", anchor="ra")
    y += 34

d.line((40, y + 10, W - 40, y + 10), fill="black", width=1)
y += 30
d.text((50, y), "SUBTOTAL", font=font, fill="black")
d.text((W - 50, y), "431.50", font=font, fill="black", anchor="ra")
y += 42
d.text((50, y), "TOTAL (RM)", font=font_l, fill="black")
d.text((W - 50, y), "431.50", font=font_l, fill="black", anchor="ra")

d.text((center, H - 90), "Thank you for your business", font=font_s, fill="black", anchor="ma")
d.text((center, H - 60), "GST Reg: 29ABCDE1234F1Z5", font=font_s, fill="black", anchor="ma")

img.save("screenshots/_demo_receipt.png")
print("wrote screenshots/_demo_receipt.png")
