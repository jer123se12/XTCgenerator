import os
import io
import warnings
from ebooklib import epub, ITEM_DOCUMENT
from PIL import Image
from weasyprint import HTML, CSS
import glob, sys, fitz

OUTPUT_DIR = "output_images"
TARGET_WIDTH=480
TARGET_HEIGHT=800


def convert_pdf_to_images(pdf, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


    print("Converting PDF pages to Images...")
    doc=fitz.open(pdf)


    for i, page in enumerate(doc):
        image_name = f"page_{i + 1:04d}.png"
        output_path = os.path.join(output_dir, image_name)
        pix = page.get_pixmap(colorspace=fitz.csGRAY)
        img = Image.frombytes("L", [pix.width, pix.height], pix.samples)
        bw_img = img.convert("1") 
        bw_img.save(output_path)
    print("Done!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide the PDF path.")
        print("Usage: python your_script.py <path_to_pdf>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    convert_pdf_to_images(pdf_path, OUTPUT_DIR)
