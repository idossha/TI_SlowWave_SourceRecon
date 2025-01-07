
#!/usr/bin/env python3

import sys
from PyPDF2 import PdfMerger

def main():
    if len(sys.argv) < 2:
        print("Usage: python stitch.py file1.pdf file2.pdf file3.pdf ...")
        sys.exit(1)

    pdf_files = sys.argv[1:]  # Collect PDF file paths from command-line arguments
    merger = PdfMerger()

    # Append each PDF file to the merger
    for pdf_file in pdf_files:
        try:
            merger.append(pdf_file)
            print(f"Added {pdf_file}")
        except FileNotFoundError:
            print(f"Error: {pdf_file} not found. Skipping.")
    
    # Write out the merged PDF
    merger.write("combined_output.pdf")
    merger.close()
    print("Merging complete! Output file: combined_output.pdf")

if __name__ == "__main__":
    main()
