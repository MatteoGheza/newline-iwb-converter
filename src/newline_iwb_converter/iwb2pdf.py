#!/usr/bin/env python3

"""Convert Newline IWB files to PDF format."""

import sys
import argparse
import tempfile
import logging

from newline_iwb_converter import iwb2svg, __version__, configure_logging
from newline_iwb_converter.pdf_engines import InkscapeEngine, SvglibEngine

logger = logging.getLogger("newline_iwb_converter.iwb2pdf")


def get_pdf_engine(use_inkscape=None):
    """
    Get the appropriate PDF conversion engine.

    Args:
        use_inkscape: If True, use Inkscape. If False, use svglib.
                      If None, auto-detect (prefer Inkscape if available).

    Returns:
        An instance of the selected PDF engine.
    """
    # Auto-detect Inkscape if not explicitly specified
    if use_inkscape is None:
        inkscape_engine = InkscapeEngine()
        use_inkscape = inkscape_engine.is_available()

    if use_inkscape:
        inkscape_engine = InkscapeEngine()
        if inkscape_engine.is_available():
            inkscape_path = inkscape_engine.find_inkscape()
            logger.info(f"Using Inkscape for SVG to PDF conversion: {inkscape_path}")
            return inkscape_engine
        else:
            logger.warning("Inkscape requested but not found, falling back to svglib")

    logger.debug("Using svglib for PDF conversion")
    return SvglibEngine()


def combine_svgs_to_pdf(svg_dir, output_pdf, uniform_size=False, use_inkscape=None):
    """
    Combine multiple SVG files from a directory into a single PDF.
    
    Args:
        svg_dir: Directory containing SVG files
        output_pdf: Path to output PDF file
        uniform_size: If True, all pages have the size of the largest page.
                      If False, each page is sized independently (default).
        use_inkscape: If True, use Inkscape for conversion. If False, use svglib.
                      If None, auto-detect (use Inkscape if available).
    """
    logger.debug(f"Combining SVGs from {svg_dir} into {output_pdf}")
    engine = get_pdf_engine(use_inkscape)
    engine.combine_svgs_to_pdf(svg_dir, output_pdf, uniform_size=uniform_size)


def extract_iwb_to_pdf(iwb_path, output_pdf, fix_fills=True, fix_size=True, delete_background=False, uniform_size=False, use_inkscape=None):
    """
    Extract an IWB file and convert it to PDF.
    
    Args:
        iwb_path: Path to input .iwb file
        output_pdf: Path to output PDF file
        fix_fills: Whether to remove fills from shapes
        fix_size: Whether to fix SVG size if content extends beyond dimensions
        delete_background: Whether to remove background image elements
        uniform_size: If True, all pages have the size of the largest page
        use_inkscape: If True, use Inkscape for conversion. If False, use svglib.
                      If None, auto-detect (use Inkscape if available).
    """
    logger.info(f"Starting IWB to PDF conversion: {iwb_path} -> {output_pdf}")
    # Create temporary directory for SVG extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.debug(f"Extracting SVGs to temporary directory: {temp_dir}")
        
        # Extract SVGs using iwb2svg
        iwb2svg.extract_iwb_to_svg(
            iwb_path,
            temp_dir,
            fix_fills=fix_fills,
            fix_size=fix_size,
            images_mode="data_uri",
            delete_background=delete_background,
        )
        
        logger.debug(f"Converting SVGs to PDF: {output_pdf}")
        
        # Combine SVGs to PDF
        combine_svgs_to_pdf(temp_dir, output_pdf, uniform_size=uniform_size, use_inkscape=use_inkscape)
    
    logger.info(f"Successfully created PDF: {output_pdf}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert IWB files to PDF format."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging"
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

    engine_group = parser.add_mutually_exclusive_group()
    engine_group.add_argument(
        "--use-inkscape",
        dest="use_inkscape",
        action="store_true",
        help="Use Inkscape for SVG to PDF conversion (if available)",
    )
    engine_group.add_argument(
        "--use-svglib",
        dest="use_inkscape",
        action="store_false",
        help="Use svglib for SVG to PDF conversion (default if Inkscape not available)",
    )

    parser.set_defaults(fix_fills=True, fix_size=True, delete_background=False, uniform_size=False, use_inkscape=None)
    args = parser.parse_args()
    
    # Configure logging based on verbosity
    log_level = logging.DEBUG if args.verbose else logging.INFO
    configure_logging(level=log_level)

    try:
        extract_iwb_to_pdf(
            args.iwb_file,
            args.output,
            fix_fills=args.fix_fills,
            fix_size=args.fix_size,
            delete_background=args.delete_background,
            uniform_size=args.uniform_size,
            use_inkscape=args.use_inkscape,
        )
    except Exception as e:
        logger.error(f"Failed to convert IWB to PDF: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
