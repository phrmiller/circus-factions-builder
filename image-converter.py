import os
from PIL import Image
import glob

def convert_to_webp(source_folder, output_folder):
    # Ensure output folder exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Get all jpg, png and jpeg files in the source folder
    image_files = glob.glob(os.path.join(source_folder, "*.[jpJ][pnP][gG]*"))

    for image_file in image_files:
        file_name = os.path.splitext(os.path.basename(image_file))[0]
        
        # Open the image
        img = Image.open(image_file)
        
        # Convert and save as WebP
        webp_path = os.path.join(output_folder, f"{file_name}.webp")
        img.save(webp_path, format="WebP", quality=80)
        
        print(f"Converted {image_file} to {webp_path}")

# Usage
source_folder = "./test-image-source"
output_folder = "./test-image-output"
convert_to_webp(source_folder, output_folder)