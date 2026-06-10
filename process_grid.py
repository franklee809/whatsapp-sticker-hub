import cv2
import numpy as np
import os
from PIL import Image

INPUT_FOLDER = "pinterest_raw"
OUTPUT_FOLDER = "whatsapp_stickers_ready"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_grid():
    # Clear output folder of old webp files to prevent mixing old and new files
    for f in os.listdir(OUTPUT_FOLDER):
        if f.lower().endswith(".webp"):
            try:
                os.remove(os.path.join(OUTPUT_FOLDER, f))
            except Exception:
                pass

    # Scan input folder for images
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
    if not files:
        print(f"No images found in '{INPUT_FOLDER}' directory!")
        return

    print(f"Found {len(files)} sheet(s) to process: {files}")
    
    for filename in files:
        input_path = os.path.join(INPUT_FOLDER, filename)
        base_name = filename.rsplit('.', 1)[0]
        print(f"\n--- Processing Sheet: {filename} ---")
        
        img = cv2.imread(input_path)
        if img is None:
            print(f"Failed to read {filename}")
            continue
            
        h_orig, w_orig, _ = img.shape
        
        # 1. Convert to grayscale and threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
        
        # 2. Use a small 3x3 dilation kernel to join very close lines
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=1)
        
        # 3. Find raw contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter raw boxes > 60x60
        boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > 60 and h > 60:
                boxes.append((x, y, w, h))
                
        # 4. Merge overlapping/nested boxes (intersection area > 30% of smaller box)
        # This handles cases where parts of a character (like a phone, watch, or hat) are detached
        boxes = sorted(boxes, key=lambda b: b[2] * b[3], reverse=True)
        merged_boxes = []
        for box in boxes:
            x, y, w, h = box
            inside = False
            for idx, mb in enumerate(merged_boxes):
                mx, my, mw, mh = mb
                ix = max(x, mx)
                iy = max(y, my)
                iw = min(x + w, mx + mw) - ix
                ih = min(y + h, my + mh) - iy
                if iw > 0 and ih > 0:
                    intersection = iw * ih
                    smaller_area = min(w * h, mw * mh)
                    if intersection / smaller_area > 0.3:
                        # Merge the boxes together
                        nmx = min(x, mx)
                        nmy = min(y, my)
                        nmw = max(x + w, mx + mw) - nmx
                        nmh = max(y + h, my + mh) - nmy
                        merged_boxes[idx] = (nmx, nmy, nmw, nmh)
                        inside = True
                        break
            if not inside:
                merged_boxes.append(box)
                
        print(f"Found and separated {len(merged_boxes)} characters from sheet.")
        
        # 5. Sort the boxes top-to-bottom, then left-to-right (grid order)
        merged_boxes.sort(key=lambda b: b[1])
        rows = []
        for box in merged_boxes:
            box_y_center = box[1] + box[3]/2
            added = False
            for r in rows:
                row_y_center = sum(b[1] + b[3]/2 for b in r) / len(r)
                if abs(box_y_center - row_y_center) < 100:
                    r.append(box)
                    added = True
                    break
            if not added:
                rows.append([box])
                
        sorted_boxes = []
        for r in rows:
            r.sort(key=lambda b: b[0])
            sorted_boxes.extend(r)
            
        # 6. Process each character and save as a sticker
        for idx, (x, y, w, h) in enumerate(sorted_boxes):
            sticker_num = idx + 1
            
            # Crop exactly on the bounding box (no margin yet!)
            crop = img[y:y+h, x:x+w].copy()
            crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            
            # Binary threshold: 255 for white background, 0 for lines
            _, binary = cv2.threshold(crop_gray, 240, 255, cv2.THRESH_BINARY)
            
            # --- PREVENT LEAKAGE FIX ---
            # 1. Draw a 2-pixel black border (0) around the edges of the binary crop
            # This seals any open contours at the bottom/edges of the body outline
            binary[0:2, :] = 0
            binary[-2:, :] = 0
            binary[:, 0:2] = 0
            binary[:, -2:] = 0
            
            fh, fw = binary.shape
            
            # 2. Draw horizontal lines at multiple y levels near the bottom (y = fh - 10, fh - 15, fh - 20, etc.)
            # only between the leftmost and rightmost black outline pixels at each level.
            # This connects the left and right body outlines, sealing the open bottom,
            # but does NOT extend into the background outside the outlines!
            ff_binary = binary.copy()
            for y_offset in [10, 15, 20, 25, 30]:
                y_level = fh - y_offset
                if y_level > 0 and y_level < fh:
                    black_pixels = np.where(binary[y_level, :] == 0)[0]
                    if len(black_pixels) >= 2:
                        x_left = black_pixels[0]
                        x_right = black_pixels[-1]
                        ff_binary[y_level, x_left:x_right] = 0
            
            ff_mask = np.zeros((fh + 2, fw + 2), np.uint8)
            
            # 3. Run flood fill from the four corners, just inside the black border
            for seed_point in [(2, 2), (fw - 3, 2), (2, fh - 3), (fw - 3, fh - 3)]:
                if seed_point[0] >= 0 and seed_point[0] < fw and seed_point[1] >= 0 and seed_point[1] < fh:
                    if ff_binary[seed_point[1], seed_point[0]] == 255:
                        cv2.floodFill(ff_binary, ff_mask, seed_point, 127)
                    
            # 127 is background (transparent), others are foreground/body (opaque)
            alpha = np.ones_like(binary) * 255
            alpha[ff_binary == 127] = 0
            
            # Make the artificial black border fully transparent
            alpha[0:2, :] = 0
            alpha[-2:, :] = 0
            alpha[:, 0:2] = 0
            alpha[:, -2:] = 0
            
            # Merge color channels with alpha
            rgba_crop = cv2.merge([crop[:, :, 0], crop[:, :, 1], crop[:, :, 2], alpha])
            pil_crop = Image.fromarray(rgba_crop, "RGBA")
            
            # NOW add the margin (e.g. 15px padding) by pasting onto a larger transparent canvas
            margin = 15
            padded_w = pil_crop.width + 2 * margin
            padded_h = pil_crop.height + 2 * margin
            padded_img = Image.new("RGBA", (padded_w, padded_h), (0, 0, 0, 0))
            padded_img.paste(pil_crop, (margin, margin))
            
            # Resize keeping aspect ratio, max 470x470
            padded_img.thumbnail((470, 470), Image.Resampling.LANCZOS)
            
            # Paste onto a transparent 512x512 canvas
            canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            cx_offset = (512 - padded_img.width) // 2
            cy_offset = (512 - padded_img.height) // 2
            canvas.paste(padded_img, (cx_offset, cy_offset))
            
            # Save sticker WebP
            output_name = f"{base_name}_sticker_{sticker_num}.webp"
            output_path = os.path.join(OUTPUT_FOLDER, output_name)
            canvas.save(output_path, "WEBP", quality=90)
            
        print(f"[SUCCESS] Processed {len(sorted_boxes)} stickers for sheet: {filename}")

    print("\n[SUCCESS] All sheets processed successfully!")

if __name__ == "__main__":
    process_grid()
