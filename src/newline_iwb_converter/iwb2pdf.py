#!/usr/bin/env python3

"""Convert Newline IWB files to PDF format."""

import sys
import argparse
import tempfile
from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from newline_iwb_converter import iwb2svg


def svg_to_pdf_page(svg_path):
    """
    Convert an SVG file to a ReportLab drawing.
    
    Args:
        svg_path: Path to the SVG file
        
    Returns:
        ReportLab drawing object or None if conversion failed
    """
    try:
        drawing = svg2rlg(svg_path)
        return drawing
    except Exception as e:
        print(f"Warning: Could not convert {svg_path} to drawing: {e}", file=sys.stderr)
        return None


def combine_svgs_to_pdf(svg_dir, output_pdf, uniform_size=False):
    """
    Combine multiple SVG files from a directory into a single PDF.
    
    Args:
        svg_dir: Directory containing SVG files
        output_pdf: Path to output PDF file
        uniform_size: If True, all pages have the size of the largest page.
                      If False, each page is sized independently (default).
    """
    # Get all SVG files, sorted by name
    svg_files = sorted(
        Path(svg_dir).glob("page_*.svg"),
        key=lambda x: int(x.stem.split("_")[1])
    )
    
    if not svg_files:
        print(f"No SVG files found in {svg_dir}", file=sys.stderr)
        sys.exit(1)
    
    # If uniform size is requested, first pass to find max dimensions
    max_width = 0
    max_height = 0
    drawings = []
    
    for svg_file in svg_files:
        drawing = svg_to_pdf_page(str(svg_file))
        if drawing is None:
            print(f"Skipping {svg_file}", file=sys.stderr)
            drawings.append(None)
            continue
        drawings.append(drawing)
        if uniform_size:
            max_width = max(max_width, drawing.width)
            max_height = max(max_height, drawing.height)
    
    if uniform_size:
        padding = 10
        uniform_page_width = max_width + padding * 2
        uniform_page_height = max_height + padding * 2
    
    # Create PDF
    pdf_canvas = canvas.Canvas(output_pdf)
    
    for idx, (svg_file, drawing) in enumerate(zip(svg_files, drawings)):
        if drawing is None:
            continue
        
        # Get SVG dimensions
        svg_width = drawing.width
        svg_height = drawing.height
        
        if uniform_size:
            page_width = uniform_page_width
            page_height = uniform_page_height
            padding = 10
        else:
            # Set page size to match SVG dimensions (with small padding)
            padding = 10
            page_width = svg_width + padding * 2
            page_height = svg_height + padding * 2
        
        pdf_canvas.setPageSize((page_width, page_height))
        
        # Draw SVG on the page
        if uniform_size:
            # Center SVG on the page
            x_offset = (page_width - svg_width) / 2
            y_offset = (page_height - svg_height) / 2
            pdf_canvas.saveState()
            pdf_canvas.translate(x_offset, y_offset)
        else:
            # Just add padding
            pdf_canvas.saveState()
            pdf_canvas.translate(padding, padding)
        
        renderPDF.draw(drawing, pdf_canvas, 0, 0)
        pdf_canvas.restoreState()
        
        # Add new page for next SVG (except for the last one)
        if idx < len(drawings) - 1:
            pdf_canvas.showPage()
        
        if uniform_size:
            print(f"Added to PDF: {svg_file.name} (centered on {page_width}x{page_height})")
        else:
            print(f"Added to PDF: {svg_file.name} ({page_width}x{page_height})")
    
    pdf_canvas.save()
    print(f"Saved PDF: {output_pdf}")


def extract_iwb_to_pdf(iwb_path, output_pdf, fix_fills=True, fix_size=True, delete_background=False, uniform_size=False):
    """
    Extract an IWB file and convert it to PDF.
    
    Args:
        iwb_path: Path to input .iwb file
        output_pdf: Path to output PDF file
        fix_fills: Whether to remove fills from shapes
        fix_size: Whether to fix SVG size if content extends beyond dimensions
        delete_background: Whether to remove background image elements
        uniform_size: If True, all pages have the size of the largest page
    """
    # Create temporary directory for SVG extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"Extracting SVGs to temporary directory: {temp_dir}")
        
        # Extract SVGs using iwb2svg
        iwb2svg.extract_iwb_to_svg(
            iwb_path,
            temp_dir,
            fix_fills=fix_fills,
            fix_size=fix_size,
            images_mode="data_uri",
            delete_background=delete_background,
        )
        
        print(f"Converting SVGs to PDF: {output_pdf}")
        
        # Combine SVGs to PDF
        combine_svgs_to_pdf(temp_dir, output_pdf, uniform_size=uniform_size)


def main():
    parser = argparse.ArgumentParser(
        description="Convert IWB files to PDF format."
    )
    parser.add_argument("iwb_file", help="Path to input .iwb file")
    parser.add_argument("-o", "--output", default="output.pdf", help="Output PDF file")

    fix_group = parser.add_mutually_exclusive_group()
    fix_group.add_argument(
        "--fix-fills",
        dest="fix_fills",
        action="store_true",
        help="Remove fill from shapes (default)",
    )
    fix_group.add_argument(
        "--no-fix-fills",
        dest="fix_fills",
        action="store_false",
        help="Do NOT modify fill behavior",
    )

    size_group = parser.add_mutually_exclusive_group()
    size_group.add_argument(
        "--fix-size",
        dest="fix_size",
        action="store_true",
        help="Fix SVG size if content extends beyond dimensions (default)",
    )
    size_group.add_argument(
        "--no-fix-size",
        dest="fix_size",
        action="store_false",
        help="Do NOT fix SVG size",
    )

    parser.add_argument(
        "--delete-background",
        dest="delete_background",
        action="store_true",
        help="Remove background image elements (id starting with 'backgroundImage')",
    )

    page_group = parser.add_mutually_exclusive_group()
    page_group.add_argument(
        "--uniform-size",
        dest="uniform_size",
        action="store_true",
        help="Make all pages the same size (size of the largest page)",
    )
    page_group.add_argument(
        "--independent-size",
        dest="uniform_size",
        action="store_false",
        help="Each page size is independent based on its content (default)",
    )

    parser.set_defaults(fix_fills=True, fix_size=True, delete_background=False, uniform_size=False)
    args = parser.parse_args()

    extract_iwb_to_pdf(
        args.iwb_file,
        args.output,
        fix_fills=args.fix_fills,
        fix_size=args.fix_size,
        delete_background=args.delete_background,
        uniform_size=args.uniform_size,
    )


if __name__ == "__main__":
    main()
