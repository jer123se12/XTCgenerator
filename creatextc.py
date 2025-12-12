import os
import sys
import glob
import struct
from PIL import Image

# --- Configuration ---
# 1 = Right to Left (Manga), 0 = Left to Right
READING_DIRECTION = 1 
TARGET_SIZE = (480, 800)

def get_sorted_files():
    """Finds page_XXXX.png files and sorts them numerically."""
    files = glob.glob("output_images/page_*.png")
    # Extract numbers to sort correctly (page_2 vs page_10)
    files.sort(key=lambda x: int(''.join(filter(str.isdigit, x)) or 0))
    return files

def create_xtg_blob(image):
    """
    Converts a PIL Image to an XTG binary blob (Header + Data).
    Spec: 1-bit monochrome, 0=Black, 1=White, MSB first.
    """
    # 1. Convert to 1-bit Monochrome (Dithering is applied by default)
    # PIL '1' mode: 0=Black, 1=White.
    img_mono = image.convert('1')
    
    width, height = img_mono.size
    
    # 2. Get packed binary data
    # PIL tobytes() for mode '1' packs 8 pixels per byte, MSB first.
    # This matches the XTG spec exactly.
    pixel_data = img_mono.tobytes()
    
    # Calculate expected data size according to spec
    # dataSize = ((width + 7) / 8) * height
    row_bytes = (width + 7) // 8
    data_size = row_bytes * height
    
    # Sanity check
    if len(pixel_data) != data_size:
        # This usually implies the width wasn't byte-aligned, 
        # but 480 is divisible by 8, so this should pass.
        raise ValueError(f"Data size mismatch. Expected {data_size}, got {len(pixel_data)}")

    # 3. Create XTG Header (22 bytes)
    # Struct fmt: < I H H B B I Q
    # < : Little Endian
    # I : mark (4 bytes)
    # H : width (2 bytes)
    # H : height (2 bytes)
    # B : colorMode (1 byte)
    # B : compression (1 byte)
    # I : dataSize (4 bytes)
    # Q : md5 (8 bytes, optional/zero)
    
    MARK_XTG = 0x00475458  # "XTG\0"
    COLOR_MODE = 0         # Monochrome
    COMPRESSION = 0        # Uncompressed
    MD5_PLACEHOLDER = 0
    
    header = struct.pack('<IHHBBIQ', 
                         MARK_XTG, 
                         width, 
                         height, 
                         COLOR_MODE, 
                         COMPRESSION, 
                         data_size, 
                         MD5_PLACEHOLDER)
    
    return header + pixel_data

def create_metadata_block(page_count):
    """
    Creates the 256-byte metadata block.
    """
    # Create empty buffer
    data = bytearray(256)
    
    # Fill Title (Optional, putting "Comic" here)
    title = "Converted Comic".encode('utf-8')[:127]
    data[0:len(title)] = title
    
    # Fill Create Time (Offset 0xF0) - Just putting 0 for now
    # Fill Chapter Count (Offset 0xF6) - 0
    
    return bytes(data)

def main(OUTPUT_FILENAME):
    files = get_sorted_files()
    
    if not files:
        print("No 'page_XXXX.png' files found.")
        return

    print(f"Found {len(files)} pages. Processing...")

    # Store processed XTG blobs in memory to calculate offsets
    xtg_blobs = []
    
    for fname in files:
        try:
            with Image.open(fname) as img:
                if img.size != TARGET_SIZE:
                    print(f"Resizing {fname} {img.size} -> {TARGET_SIZE}",end="\r")
                    img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
                
                blob = create_xtg_blob(img)
                xtg_blobs.append(blob)
        except Exception as e:
            print(f"Error processing {fname}: {e}")
            return

    print()
    num_pages = len(xtg_blobs)
    
    # --- Calculate Offsets ---
    # File Layout:
    # [Header: 56]
    # [Metadata: 256]
    # [Chapters: 0] (Not using)
    # [Index Table: num_pages * 16]
    # [Data Area: sum(blobs)]
    
    HEADER_SIZE = 56
    METADATA_SIZE = 256
    INDEX_ENTRY_SIZE = 16
    
    offset_metadata = HEADER_SIZE
    offset_index = offset_metadata + METADATA_SIZE
    offset_data_start = offset_index + (num_pages * INDEX_ENTRY_SIZE)
    
    # These are unused features in this script, set to 0
    offset_thumbnails = 0
    offset_chapters = 0

    # --- Write XTC File ---
    with open(OUTPUT_FILENAME, 'wb') as f:
        print("Writing header...")
        
        # 1. XTC Header (56 bytes)
        # Struct: < I H H B B B B I Q Q Q Q Q
        MARK_XTC = 0x00435458  # "XTC\0"
        VERSION = 0x0100       # v1.0
        HAS_METADATA = 1
        HAS_THUMBNAILS = 0
        HAS_CHAPTERS = 0
        CURRENT_PAGE = 0
        
        header = struct.pack('<IHHBBBBIQQQQQ',
                             MARK_XTC,
                             VERSION,
                             num_pages,
                             READING_DIRECTION,
                             HAS_METADATA,
                             HAS_THUMBNAILS,
                             HAS_CHAPTERS,
                             CURRENT_PAGE,
                             offset_metadata,
                             offset_index,
                             offset_data_start,
                             offset_thumbnails,
                             offset_chapters)
        f.write(header)
        
        # 2. Metadata
        print("Writing metadata...")
        f.write(create_metadata_block(num_pages))
        
        # 3. Page Index Table
        print("Writing index table...")
        current_blob_offset = offset_data_start
        
        for blob in xtg_blobs:
            # Parse blob header back just to get width/height/size safely
            # XTG header is first 22 bytes
            blob_header = blob[:22]
            _, w, h, _, _, data_len, _ = struct.unpack('<IHHBBIQ', blob_header)
            
            total_blob_size = len(blob) # Header + Data
            
            # Index Entry: < Q I H H (16 bytes)
            # offset (abs), size, width, height
            index_entry = struct.pack('<QIHH', 
                                      current_blob_offset,
                                      total_blob_size,
                                      w,
                                      h)
            f.write(index_entry)
            
            # Increment offset for next file
            current_blob_offset += total_blob_size
            
        # 4. Data Area
        print("Writing page data...")
        for i, blob in enumerate(xtg_blobs):
            f.write(blob)
            if i % 10 == 0:
                print(f"  Written page {i+1}/{num_pages}",end="\r")
        print()

    print(f"Success! Saved to {OUTPUT_FILENAME}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please provide the PDF path.")
        print("Usage: python your_script.py <path_to_pdf>")
        sys.exit(1)
    main(sys.argv[1])
