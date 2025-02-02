
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
# For concatenating PDFs:
from PyPDF2 import PdfMerger

# Define available layouts + how many images each one requires
LAYOUTS = {
    'single': {
        'type': 'grid',
        'cols': 1,
        'rows': 1,
        'title': True,
        'images_required': 1
    },
    '2x2': {
        'type': 'grid',
        'cols': 2,
        'rows': 2,
        'title': True,
        'images_required': 4
    },
    '1x2': {
        'type': 'grid',
        'cols': 1,
        'rows': 2,
        'title': True,
        'images_required': 2
    },
    '3x1': {
        'type': 'grid',
        'cols': 3,
        'rows': 1,
        'title': True,
        'images_required': 3
    },
     '3x2': {
        'type': 'grid',
        'cols': 3,
        'rows': 2,
        'title': True,
        'images_required': 6
    },   '3x3': {
        'type': 'grid',
        'cols': 3,
        'rows': 3,
        'title': True,
        'images_required': 9
    },
    '1x2x2': {
        'type': 'custom',
        'structure': [
            {'cols': 2, 'rows': 1, 'span_cols': 2},  # top image spanning 2 columns
            {'cols': 1, 'rows': 1},  # middle-left
            {'cols': 1, 'rows': 1},  # middle-right
            {'cols': 1, 'rows': 1},  # bottom-left
            {'cols': 1, 'rows': 1}   # bottom-right
        ],
        'title': True,
        'images_required': 5  # 1 on top, 4 in bottom 2x2
    }
}

def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate PDF from images with strict layout-based image counts.")
    parser.add_argument("project_dir", help="Path to the project directory.")
    parser.add_argument("--subjects", nargs='+', required=True, help="List of subjects to include.")
    parser.add_argument("--nights", nargs='+', required=True, help="List of nights to include.")
    parser.add_argument("--images", nargs='+', required=True, help="List of image filenames to include.")
    parser.add_argument(
        "--layouts",
        nargs='+',
        choices=LAYOUTS.keys(),
        default=['2x2'],
        help="One or more layouts (e.g. single, 2x2, 1x2, 3x2, 1x2x2)."
    )
    parser.add_argument("--page_orientation", choices=['portrait', 'landscape'], default='landscape',
                        help="Orientation of the PDF pages.")
    parser.add_argument("--margin", type=float, default=0.5, help="Margin size in inches.")
    return parser.parse_args()

def collect_images(project_dir, subjects, nights, images):
    """
    Collect images in a dictionary keyed by [subject][night].
    Structure: collected_images[subject][night] = [list_of_image_paths]
    """
    from collections import defaultdict
    collected_images = defaultdict(lambda: defaultdict(list))

    for subject in subjects:
        subject_path = os.path.join(project_dir, subject)
        if not os.path.isdir(subject_path):
            print(f"Warning: Subject directory '{subject}' does not exist in '{project_dir}'. Skipping.")
            continue

        for night in nights:
            # Use an f-string to insert subject/night into the directory name.
            night_path = os.path.join(subject_path, night, f"output/")

            if not os.path.isdir(night_path):
                print(f"Warning: Night directory '{night_path}' does not exist. Skipping.")
                continue

            for img in images:
                img_path = os.path.join(night_path, img)
                if os.path.isfile(img_path):
                    collected_images[subject][night].append(img_path)
                else:
                    print(f"Warning: Image '{img}' not found in '{night_path}'. Skipping.")
    return collected_images

def draw_single_slide_layout(c, subject, night, images, layout_config, margin, width, height):
    """
    Draw exactly ONE PDF page (slide) using the given layout with the given images (which must match
    the required count). If 'images' is empty, skip (no page).
    """
    include_title = layout_config.get('title', False)

    # Reserve space for title if needed
    title_space = 0.8 * inch if include_title else 0.0

    # Draw the title
    if include_title:
        title_text = f"Subject: {subject} | Night: {night}"
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(colors.black)
        c.drawString(margin, height - margin - 0.5 * inch, title_text)

    layout_type = layout_config['type']

    # 1) GRID LAYOUTS
    if layout_type == 'grid':
        cols = layout_config['cols']
        rows = layout_config['rows']
        usable_width = width - 2 * margin
        usable_height = height - 2 * margin - title_space

        img_width = usable_width / cols
        img_height = usable_height / rows

        max_images = cols * rows
        for idx, img_path in enumerate(images[:max_images]):
            row = idx // cols
            col = idx % cols

            x = margin + col * img_width
            y_top = (height - margin - title_space) - row * img_height
            y = y_top - img_height

            try:
                with Image.open(img_path) as img_obj:
                    img_ratio = img_obj.width / img_obj.height
                    box_ratio = img_width / img_height

                    if img_ratio > box_ratio:
                        display_width = img_width
                        display_height = img_width / img_ratio
                    else:
                        display_height = img_height
                        display_width = img_height * img_ratio

                    x_offset = x + (img_width - display_width) / 2
                    y_offset = y + (img_height - display_height) / 2

                    c.drawImage(
                        img_path, x_offset, y_offset,
                        width=display_width, height=display_height,
                        preserveAspectRatio=True
                    )
            except Exception as e:
                print(f"Error adding image '{img_path}' to PDF: {e}")

    # 2) CUSTOM LAYOUT (1x2x2)
    elif layout_type == 'custom' and layout_config == LAYOUTS['1x2x2']:
        # We expect exactly 5 images in 1x2x2 layout
        usable_height = height - 2 * margin - title_space
        top_height = usable_height / 3
        bottom_height = (usable_height * 2) / 3

        # Top image: images[0]
        if len(images) > 0:
            top_img = images[0]
            try:
                box_w = width - 2 * margin
                box_h = top_height
                x_top = margin
                y_top = height - margin - title_space - box_h

                with Image.open(top_img) as img_obj:
                    img_ratio = img_obj.width / img_obj.height
                    box_ratio = box_w / box_h

                    if img_ratio > box_ratio:
                        display_width = box_w
                        display_height = box_w / img_ratio
                    else:
                        display_height = box_h
                        display_width = box_h * img_ratio

                    x_offset = x_top + (box_w - display_width) / 2
                    y_offset = y_top + (box_h - display_height) / 2

                    c.drawImage(
                        top_img, x_offset, y_offset,
                        width=display_width, height=display_height,
                        preserveAspectRatio=True
                    )
            except Exception as e:
                print(f"Error adding top image '{top_img}' to PDF: {e}")

        # Bottom 4 images: images[1..4]
        bottom_imgs = images[1:5]
        cols = 2
        rows = 2
        cell_w = (width - 2 * margin) / cols
        cell_h = bottom_height / rows

        for idx, img_path in enumerate(bottom_imgs):
            row = idx // cols
            col = idx % cols
            x = margin + col * cell_w
            y_top = (height - margin - title_space - top_height) - row * cell_h
            y = y_top - cell_h

            try:
                with Image.open(img_path) as img_obj:
                    img_ratio = img_obj.width / img_obj.height
                    box_ratio = cell_w / cell_h

                    if img_ratio > box_ratio:
                        display_width = cell_w
                        display_height = cell_w / img_ratio
                    else:
                        display_height = cell_h
                        display_width = cell_h * img_ratio

                    x_offset = x + (cell_w - display_width) / 2
                    y_offset = y + (cell_h - display_height) / 2

                    c.drawImage(
                        img_path, x_offset, y_offset,
                        width=display_width, height=display_height,
                        preserveAspectRatio=True
                    )
            except Exception as e:
                print(f"Error adding image '{img_path}' to PDF: {e}")

    # Finalize the page
    c.showPage()

def main():
    args = parse_arguments()
    collected_images = collect_images(
        project_dir=args.project_dir,
        subjects=args.subjects,
        nights=args.nights,
        images=args.images
    )

    # Decide page size/orientation
    if args.page_orientation == 'landscape':
        page_size = landscape(A4)
    else:
        page_size = portrait(A4)

    # Total images required for the chosen layouts
    total_required = sum(LAYOUTS[l]['images_required'] for l in args.layouts)

    # We'll store references to all created PDF paths in this list
    pdfs_created = []

    for subject, nights_dict in collected_images.items():
        for night, all_image_paths in nights_dict.items():
            if not all_image_paths:
                # No images for this subject/night, skip
                continue

            if len(all_image_paths) != total_required:
                msg = (
                    f"ERROR: For {subject}, {night}, you provided {len(all_image_paths)} images, "
                    f"but the layouts ({args.layouts}) require {total_required} total images."
                )
                print(msg)
                sys.exit(1)  # or 'continue' if you want to skip instead of exiting

            # 1) Create the deliverables directory: project_dir/subject/night/deliverables
            deliverables_dir = os.path.join(args.project_dir, subject, night, "deliverables")
            os.makedirs(deliverables_dir, exist_ok=True)

            # 2) Construct the PDF filename & path
            pdf_filename = f"{subject}_{night}_summary.pdf"
            output_pdf = os.path.join(deliverables_dir, pdf_filename)

            print(f"Creating PDF for {subject}, {night} → {output_pdf}")

            # Create a new PDF canvas
            c = canvas.Canvas(output_pdf, pagesize=page_size)
            margin_pt = args.margin * inch

            # Partition the images in the exact order of layouts
            current_index = 0
            for layout_key in args.layouts:
                layout_config = LAYOUTS[layout_key]
                images_needed = layout_config['images_required']

                chunk = all_image_paths[current_index:current_index + images_needed]
                current_index += images_needed

                # Draw this chunk on a new page
                draw_single_slide_layout(
                    c=c,
                    subject=subject,
                    night=night,
                    images=chunk,
                    layout_config=layout_config,
                    margin=margin_pt,
                    width=page_size[0],
                    height=page_size[1]
                )

            # Finalize and save
            c.save()
            print(f"PDF '{output_pdf}' created successfully.")
            pdfs_created.append(output_pdf)

    # ---------------------------------------------------------------
    # After generating all PDFs, if multiple PDFs exist, concatenate
    # them into one summary_all.pdf inside project_dir
    # ---------------------------------------------------------------
    if len(pdfs_created) > 1:
        merged_pdf_path = os.path.join(args.project_dir, "summary_all.pdf")
        print(f"Concatenating all PDFs into {merged_pdf_path} ...")

        merger = PdfMerger()
        for pdf_path in pdfs_created:
            merger.append(pdf_path)

        merger.write(merged_pdf_path)
        merger.close()

        print(f"All PDFs have been concatenated into: {merged_pdf_path}")
    else:
        print("Only one (or zero) PDF created; skipping concatenation step.")

if __name__ == "__main__":
    main()

