import os
from PIL import Image
import numpy as np

folder = "whatsapp_stickers_ready"
files = sorted([f for f in os.listdir(folder) if f.endswith(".webp")])

print(f"Scanning {len(files)} files for transparency leaks inside character bodies...")

for f in files:
    path = os.path.join(folder, f)
    img = Image.open(path)
    arr = np.array(img)
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3]
    
    # Find bounding box of non-transparent area
    y_indices, x_indices = np.where(alpha > 0)
    if len(y_indices) == 0:
        print(f"[{f}] ERROR: Fully transparent image!")
        continue
        
    min_y, max_y = np.min(y_indices), np.max(y_indices)
    min_x, max_x = np.min(x_indices), np.max(x_indices)
    
    sub_alpha = alpha[min_y:max_y+1, min_x:max_x+1]
    sub_rgb = rgb[min_y:max_y+1, min_x:max_x+1]
    
    # Calculate ratio of opaque white pixels to total non-transparent bounding box pixels
    total_non_transparent = np.sum(alpha > 0)
    white_opaque = np.sum((alpha == 255) & (rgb[:, :, 0] > 200) & (rgb[:, :, 1] > 200) & (rgb[:, :, 2] > 200))
    
    # If the white opaque pixels are very low compared to total opaque area, it's a leak!
    ratio = white_opaque / total_non_transparent
    print(f"{f:50} -> Total non-transparent: {total_non_transparent:6}, White opaque: {white_opaque:6} (Ratio: {ratio:.2f})")
    
    if ratio < 0.15:
         print(f"   >>> LEAK DETECTED in {f}!")
