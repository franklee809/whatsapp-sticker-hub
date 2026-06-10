from rembg import remove
from PIL import Image
import os

# Put your downloaded Pinterest images here
INPUT_FOLDER = "pinterest_raw"
# The script will spit out the WhatsApp-ready files here
OUTPUT_FOLDER = "whatsapp_stickers_ready"

os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def process_images():
    files = [f for f in os.listdir(INPUT_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    if not files:
        print(f"No images found in '{INPUT_FOLDER}' directory. Please add some images first!")
        return

    print(f"Found {len(files)} image(s) in '{INPUT_FOLDER}' to process.")
    for filename in files:
        input_path = os.path.join(INPUT_FOLDER, filename)
        
        # WhatsApp requires files to be exactly .webp
        output_name = filename.rsplit('.', 1)[0] + '.webp'
        output_path = os.path.join(OUTPUT_FOLDER, output_name)
        
        print(f"Applying AI cut-out to {filename}...")
        
        try:
            # 1. Let the AI remove the background
            input_img = Image.open(input_path)
            # Ensure it is in RGBA mode for transparency removal
            transparent_img = remove(input_img)
            
            # 2. Resize keeping aspect ratio, max 512x512
            transparent_img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            
            # 3. Paste onto a perfect 512x512 transparent canvas
            canvas = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            x_offset = (512 - transparent_img.width) // 2
            y_offset = (512 - transparent_img.height) // 2
            canvas.paste(transparent_img, (x_offset, y_offset))
            
            # 4. Save as WebP (WhatsApp requirement) with compression
            canvas.save(output_path, "WEBP", quality=80)
            print(f"Saved sticker to: {output_path}")
            
        except Exception as e:
            print(f"Skipped {filename} due to error: {e}")
            
    print("[SUCCESS] All images processed!")

if __name__ == "__main__":
    process_images()
