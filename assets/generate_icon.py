"""
Generates modern, sleek application icons for WorkBOXig
"""
import os
from PIL import Image, ImageDraw

def create_app_icon():
    os.makedirs("assets", exist_ok=True)
    sizes = [256, 128, 64, 48, 32, 16]
    images = []

    for size in sizes:
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Rounded background rectangle with gradient-like look
        # Modern indigo / violet gradient background
        pad = int(size * 0.08)
        radius = int(size * 0.22)
        
        # Background plate: Deep sleek slate/indigo
        draw.rounded_rectangle(
            [pad, pad, size - pad, size - pad],
            radius=radius,
            fill=(26, 29, 36, 255),
            outline=(99, 102, 241, 230),
            width=max(1, int(size * 0.03))
        )
        
        # Draw stylized "W" & book/box geometric motif
        accent_color = (99, 102, 241, 255) # Indigo
        secondary_color = (56, 189, 248, 255) # Sky blue
        
        # Draw central motif: stylized notebook/check box
        cx = size / 2
        cy = size / 2
        
        # Inner book / box shape
        b_pad = int(size * 0.24)
        draw.rounded_rectangle(
            [b_pad, b_pad, size - b_pad, size - b_pad],
            radius=int(size * 0.1),
            fill=(34, 38, 49, 255),
            outline=secondary_color,
            width=max(1, int(size * 0.025))
        )
        
        # Elegant checkmark or notebook lines inside
        p1 = (cx - size * 0.14, cy)
        p2 = (cx - size * 0.03, cy + size * 0.12)
        p3 = (cx + size * 0.16, cy - size * 0.10)
        
        lw = max(2, int(size * 0.05))
        draw.line([p1, p2, p3], fill=accent_color, width=lw, joint="curve")
        
        images.append(img)
        
    # Save PNG and ICO
    images[0].save("assets/icon.png", format="PNG")
    images[0].save("assets/icon.ico", format="ICO", sizes=[(s, s) for s in sizes])
    print("Icons successfully generated at assets/icon.ico and assets/icon.png")

if __name__ == "__main__":
    create_app_icon()
