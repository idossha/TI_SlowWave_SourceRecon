#!/usr/bin/env python3
''' 
Script that takes an image input and spits a .svg vectorized file.
Ido Haber
July 2024

'''

import cv2
import numpy as np
import svgwrite
from PIL import Image
import argparse

def vectorize_image(input_image_path, output_svg_path):
    # Load the image
    image = Image.open(input_image_path)
    
    # Convert the image to RGBA (including alpha channel)
    rgba_image = image.convert('RGBA')
    rgba_array = np.array(rgba_image)
    
    # Convert the image to grayscale
    gray_image = np.array(image.convert('L'))
    
    # Apply edge detection
    edges = cv2.Canny(gray_image, threshold1=100, threshold2=150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Create an SVG drawing
    dwg = svgwrite.Drawing(output_svg_path, profile='tiny')
    
    # Function to add colored contours to the SVG
    def add_colored_contours(dwg, contours, color_array):
        for contour in contours:
            path_data = ""
            for i, point in enumerate(contour):
                x, y = int(point[0][0]), int(point[0][1])
                if i == 0:
                    path_data += f"M{x},{y} "
                else:
                    path_data += f"L{x},{y} "
            path_data += "Z"  # Close the path
            color = color_array[contour[0][0][1], contour[0][0][0]]
            stroke_color = svgwrite.rgb(color[0], color[1], color[2])
            dwg.add(dwg.path(d=path_data, fill='none', stroke=stroke_color))
    
    # Add the colored contours to the SVG drawing
    add_colored_contours(dwg, contours, rgba_array)
    
    # Save the SVG file
    dwg.save()

def main():
    parser = argparse.ArgumentParser(description='Vectorize an image and save as SVG.')
    parser.add_argument('input', help='Input image file path')
    parser.add_argument('output', help='Output SVG file path')
    
    args = parser.parse_args()
    
    vectorize_image(args.input, args.output)

if __name__ == '__main__':
    main()
