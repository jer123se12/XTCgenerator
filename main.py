import os
import glob
import shutil
import convertpdf  # Your convertpdf.py
import creatextc   # Your creatextc.py
from pathlib import Path

# Configuration
SOURCE_DIR = "books"
TEMP_IMG_DIR = "output_images"
EXPORT_DIR = "exports"


def clear_image_directory(directory):
    """Deletes all files in the output directory to prevent mixing PDF pages."""
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(directory)


def main():
    # 1. Ensure directories exist
    if not os.path.exists(EXPORT_DIR):
        os.makedirs(EXPORT_DIR)
    if not os.path.exists(TEMP_IMG_DIR):
        os.makedirs(TEMP_IMG_DIR)

    # 2. Find all PDF files in the current directory
    # using glob ensures we find .pdf and .PDF
    pdf_files = [
        str(p) 
        for p in Path(SOURCE_DIR).rglob('*') 
        if p.suffix.lower() == '.pdf' and p.is_file()
    ]
    if not pdf_files:
        print("No PDF files found in this directory.")
        return

    print(f"Found {len(pdf_files)} PDFs to process.")

    # 3. Loop through each PDF
    for pdf_file in pdf_files:
        print("------------------------------------------------")
        print(f"Processing: {pdf_file}")

        # A. CLEANUP: Clear the shared images folder!
        # This is crucial so pages don't mix between books.
        print(f"Clearing {TEMP_IMG_DIR}...")
        clear_image_directory(TEMP_IMG_DIR)

        # B. CONVERT: PDF -> Images
        # We pass the shared 'output_images' folder
        try:
            convertpdf.convert_pdf_to_images(pdf_file, TEMP_IMG_DIR)
        except Exception as e:
            print(f"Error converting {pdf_file}: {e}")
            continue

        # C. CREATE XTC: Images -> XTC File
        # Determine the output filename (e.g., "book.pdf" -> "book.xtc")
        base_name = Path(pdf_file).stem
        xtc_filename = f"{base_name}.xtc"
        
        # Combine with the exports folder path
        final_output_path = os.path.join(EXPORT_DIR, xtc_filename)
        
        print(f"Creating XTC file at: {final_output_path}")
        
        try:
            # Call your creatextc script
            creatextc.main(final_output_path)
        except Exception as e:
            print(f"Error creating XTC for {pdf_file}: {e}")

    print("------------------------------------------------")
    print("All jobs done!")

if __name__ == "__main__":
    main()
