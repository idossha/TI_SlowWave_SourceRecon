'''
to do:

change naming of images
change path to be dynamic
make two slides per subject
double check layout 
add default names for images 
'''


import os
import sys
import argparse
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from PIL import Image
from collections import defaultdict
import math

# Define available layouts
LAYOUTS = {
    'single': {'type': 'grid', 'cols': 1, 'rows': 1, 'title': True},
    '2x2': {'type': 'grid', 'cols': 2, 'rows': 2, 'title': True},
    '3x2': {'type': 'grid', 'cols': 3, 'rows': 2, 'title': True},
    '1x2x2': {'type': 'custom', 'structure': [
        {'cols': 2, 'rows': 1, 'span_cols': 2},  # Top image spanning 2 columns
        {'cols': 1, 'rows': 1},  # Middle left
        {'cols': 1, 'rows': 1},  # Middle right
        {'cols': 1, 'rows': 1},  # Bottom left
        {'cols': 1, 'rows': 1}   # Bottom right
    ], 'title': True}
    # Add more layouts here as needed
}

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate PDF from project directory images with multiple layout options.")
    parser.add_argument("project_dir", help="Path to the project directory.")
    parser.add_argument("--subjects", nargs='+', required=True, help="List of subjects to include.")
    parser.add_argument("--nights", nargs='+', required=True, help="List of nights to include.")
    parser.add_argument("--images", nargs='+', required=True, help="List of image filenames to include.")
    parser.add_argument("--output_pdf", default="output.pdf", help="Output PDF file name.")
    parser.add_argument("--layout", choices=LAYOUTS.keys(), default='2x2', help="Layout style for the PDF pages.")
    parser.add_argument("--page_orientation", choices=['portrait', 'landscape'], default='landscape', help="Orientation of the PDF pages.")
    parser.add_argument("--margin", type=float, default=0.5, help="Margin size in inches.")
    return parser.parse_args()

def collect_images(project_dir, subjects, nights, images):
    collected_images = defaultdict(lambda: defaultdict(list))  # collected_images[subject][night] = [image_paths]
    for subject in subjects:
        subject_path = os.path.join(project_dir, subject)
        if not os.path.isdir(subject_path):
            print(f"Warning: Subject directory '{subject}' does not exist in '{project_dir}'. Skipping.")
            continue
        for night in nights:
            night_path = os.path.join(subject_path, night, "output/Strength_127_N1_forSW")
            if not os.path.isdir(night_path):
                print(f"Warning: Night directory '{night}' does not exist under '{subject_path}'. Skipping.")
                continue
            for img in images:
                img_path = os.path.join(night_path, img)
                if os.path.isfile(img_path):
                    collected_images[subject][night].append(img_path)
                else:
                    print(f"Warning: Image '{img}' not found in '{night_path}'. Skipping.")
    return collected_images

def create_pdf(collected_images, output_pdf, layout, orientation, margin_inch):
    if not collected_images:
        print("No images to add to PDF.")
        return

    # Determine page size and orientation
    if orientation == 'landscape':
        page_size = landscape(A4)
    else:
        page_size = portrait(A4)
    width, height = page_size

    # Initialize PDF canvas
    c = canvas.Canvas(output_pdf, pagesize=page_size)

    # Calculate margins
    margin = margin_inch * inch
    usable_width = width - 2 * margin
    usable_height = height - 2 * margin

    # Get layout configuration
    layout_config = LAYOUTS[layout]
    include_title = layout_config.get('title', False)

    # Handle different layout types
    if layout_config['type'] == 'grid':
        cols = layout_config['cols']
        rows = layout_config['rows']
        images_per_page = cols * rows

        img_width = usable_width / cols
        img_height = (usable_height - (0.5 * inch if include_title else 0)) / rows  # Reserve space for title if needed

        for subject, nights_dict in collected_images.items():
            for night, images in nights_dict.items():
                if not images:
                    continue

                # Group images into chunks based on the layout
                for i in range(0, len(images), images_per_page):
                    chunk = images[i:i + images_per_page]

                    # Add title if required
                    if include_title:
                        title_text = f"Subject: {subject} | Night: {night}"
                        c.setFont("Helvetica-Bold", 16)
                        c.setFillColor(colors.black)
                        c.drawString(margin, height - margin - 0.5 * inch, title_text)

                    # Calculate starting y position
                    y_start = height - margin - (0.75 * inch if include_title else margin)

                    for idx, img_path in enumerate(chunk):
                        row = idx // cols
                        col = idx % cols

                        x = margin + col * img_width
                        y = y_start - (row + 1) * img_height

                        try:
                            with Image.open(img_path) as img:
                                img_ratio = img.width / img.height
                                box_ratio = img_width / img_height

                                if img_ratio > box_ratio:
                                    display_width = img_width
                                    display_height = img_width / img_ratio
                                else:
                                    display_height = img_height
                                    display_width = img_height * img_ratio

                                # Center the image in the allocated space
                                x_offset = x + (img_width - display_width) / 2
                                y_offset = y + (img_height - display_height) / 2

                                c.drawImage(img_path, x_offset, y_offset,
                                            width=display_width, height=display_height, preserveAspectRatio=True)
                        except Exception as e:
                            print(f"Error adding image '{img_path}' to PDF: {e}")

                    c.showPage()  # Move to the next page after adding images

    elif layout_config['type'] == 'custom' and layout == '1x2x2':
        # Define the custom layout structure
        # structure is a list where each item defines how to place an image
        # 'span_cols' indicates if the image spans multiple columns
        structure = layout_config['structure']
        total_cols = max(item.get('span_cols', 1) for item in structure)
        total_rows = len(structure)

        # Precompute image allocation per page
        for subject, nights_dict in collected_images.items():
            for night, images in nights_dict.items():
                if not images:
                    continue

                # Group images into chunks based on the layout (5 images per page)
                images_per_page = len(structure)
                for i in range(0, len(images), images_per_page):
                    chunk = images[i:i + images_per_page]

                    # Add title if required
                    if include_title:
                        title_text = f"Subject: {subject} | Night: {night}"
                        c.setFont("Helvetica-Bold", 16)
                        c.setFillColor(colors.black)
                        c.drawString(margin, height - margin - 0.5 * inch, title_text)

                    # Calculate usable height after title
                    y_start = height - margin - (0.75 * inch if include_title else margin)

                    current_y = y_start

                    for idx, img_path in enumerate(structure):
                        if idx >= len(chunk):
                            break  # No more images to place

                        img = chunk[idx]
                        span_cols = img.get('span_cols', 1) if isinstance(img, dict) else 1

                        if layout == '1x2x2' and idx == 0:
                            # First image spans all columns
                            img_width = usable_width
                            img_height = usable_height / 3  # Allocate one third for the top image
                            x = margin
                        else:
                            # Remaining images are in a grid of 2 columns
                            img_width = usable_width / 2
                            img_height = usable_height / 3  # Allocate remaining two thirds for two rows
                            col = (idx - 1) % 2
                            row = math.floor((idx - 1) / 2)
                            x = margin + col * img_width
                            y = y_start - img_height - row * img_height
                            # Update current_y for y position
                            y = y_start - (row + 1) * img_height
                            img_width = usable_width / 2
                            img_height = usable_height / 3

                        if layout == '1x2x2' and idx == 0:
                            # Special handling for the top image
                            try:
                                with Image.open(img) as img_obj:
                                    img_ratio = img_obj.width / img_obj.height
                                    box_ratio = img_width / img_height

                                    if img_ratio > box_ratio:
                                        display_width = img_width
                                        display_height = img_width / img_ratio
                                    else:
                                        display_height = img_height
                                        display_width = img_height * img_ratio

                                    # Center the image
                                    x_offset = margin + (usable_width - display_width) / 2
                                    y_offset = current_y - display_height

                                    c.drawImage(img, x_offset, y_offset,
                                                width=display_width, height=display_height, preserveAspectRatio=True)
                            except Exception as e:
                                print(f"Error adding image '{img}' to PDF: {e}")
                        else:
                            try:
                                with Image.open(img) as img_obj:
                                    img_ratio = img_obj.width / img_obj.height
                                    box_ratio = img_width / img_height

                                    if img_ratio > box_ratio:
                                        display_width = img_width
                                        display_height = img_width / img_ratio
                                    else:
                                        display_height = img_height
                                        display_width = img_height * img_ratio

                                    # Center the image in the allocated space
                                    x_offset = x + (img_width - display_width) / 2
                                    y_offset = y + (img_height - display_height) / 2

                                    c.drawImage(img, x_offset, y_offset,
                                                width=display_width, height=display_height, preserveAspectRatio=True)
                            except Exception as e:
                                print(f"Error adding image '{img}' to PDF: {e}")

                    c.showPage()  # Move to the next page after adding images

    else:
        print(f"Unsupported layout type: {layout_config['type']}")
        return

    c.save()
    print(f"PDF '{output_pdf}' created successfully.")

def main():
    args = parse_arguments()
    collected_images = collect_images(args.project_dir, args.subjects, args.nights, args.images)
    create_pdf(collected_images, args.output_pdf, args.layout, args.page_orientation, args.margin)

if __name__ == "__main__":
    main()
