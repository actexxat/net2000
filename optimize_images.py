import os
from PIL import Image

def optimize_directory(directory, max_size=(600, 600), quality=75):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue

        # Skip non-image files
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            continue

        try:
            with Image.open(filepath) as img:
                # Convert RGBA to RGB if saving as JPEG
                if img.mode in ("RGBA", "P") and ext != '.png':
                    img = img.convert("RGB")
                
                # Resize
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save back (overwrite)
                if ext in ['.jpg', '.jpeg']:
                    img.save(filepath, "JPEG", optimize=True, quality=quality)
                elif ext == '.png':
                    img.save(filepath, "PNG", optimize=True)
                elif ext == '.webp':
                    img.save(filepath, "WEBP", quality=quality)
                
                new_size = os.path.getsize(filepath)
                print(f"Optimized {filename}: {new_size} bytes")
        except Exception as e:
            print(f"Failed to optimize {filename}: {e}")

if __name__ == "__main__":
    media_dir = os.path.join('media', 'items')
    optimize_directory(media_dir)
