#!/usr/bin/env python3

"""Inkscape PDF conversion engine."""

import shutil
import subprocess
import sys
import tempfile
import logging
from pathlib import Path

from newline_iwb_converter.pdf_engines.base import BasePDFEngine

logger = logging.getLogger("newline_iwb_converter.pdf_engines.inkscape")


class InkscapeEngine(BasePDFEngine):
    """PDF conversion engine using Inkscape."""

    def __init__(self):
        """Initialize the Inkscape engine."""
        self._inkscape_path = None

    def find_inkscape(self):
        """
        Find Inkscape executable in system PATH or common installation paths.

        Returns:
            Path to Inkscape executable if found, None otherwise
        """
        if self._inkscape_path:
            return self._inkscape_path

        # First, try to find in PATH
        inkscape_path = shutil.which("inkscape")
        if inkscape_path:
            self._inkscape_path = inkscape_path
            logger.debug(f"Found Inkscape in PATH: {inkscape_path}")
            return inkscape_path

        # Common installation paths for different operating systems
        common_paths = []

        if sys.platform == "win32":
            # Windows common paths
            common_paths = [
                r"C:\Program Files\Inkscape\bin\inkscape.exe",
                r"C:\Program Files (x86)\Inkscape\bin\inkscape.exe",
                r"C:\Program Files\Inkscape\inkscape.exe",
                r"C:\Program Files (x86)\Inkscape\inkscape.exe",
            ]
        elif sys.platform == "darwin":
            # macOS common paths
            common_paths = [
                "/Applications/Inkscape.app/Contents/MacOS/inkscape",
                "/usr/local/bin/inkscape",
                "/opt/homebrew/bin/inkscape",
            ]
        elif sys.platform == "linux":
            # Linux common paths
            common_paths = [
                "/usr/bin/inkscape",
                "/usr/local/bin/inkscape",
                "/snap/bin/inkscape",
            ]

        # Check each common path
        for path in common_paths:
            if Path(path).exists():
                self._inkscape_path = path
                logger.debug(f"Found Inkscape at: {path}")
                return path

        logger.warning("Inkscape not found in PATH or common installation paths")
        return None

    def is_available(self):
        """
        Check if Inkscape is available on the system.

        Returns:
            True if Inkscape is available, False otherwise
        """
        available = self.find_inkscape() is not None
        if available:
            logger.debug("Inkscape is available")
        else:
            logger.debug("Inkscape is not available")
        return available

    def combine_svgs_to_pdf(self, svg_dir, output_pdf, **kwargs):
        """
        Combine multiple SVG files into a single PDF using Inkscape.

        Args:
            svg_dir: Directory containing SVG files
            output_pdf: Path to output PDF file
            **kwargs: Unused for Inkscape engine
        """
        logger.info(f"Starting SVG to PDF conversion using Inkscape for: {svg_dir}")
        # Get all SVG files, sorted by name
        svg_files = sorted(
            Path(svg_dir).glob("page_*.svg"),
            key=lambda x: int(x.stem.split("_")[1])
        )

        if not svg_files:
            logger.error(f"No SVG files found in {svg_dir}")
            sys.exit(1)

        logger.info(f"Found {len(svg_files)} SVG file(s) to convert")
        inkscape_path = self.find_inkscape()
        pdf_files = []

        with tempfile.TemporaryDirectory() as temp_dir:
            logger.debug(f"Using temporary directory: {temp_dir}")
            # Convert each SVG to PDF using Inkscape
            for idx, svg_file in enumerate(svg_files, 1):
                temp_pdf = Path(temp_dir) / f"page_{svg_file.stem.split('_')[1]}.pdf"

                try:
                    logger.debug(f"Converting SVG to PDF: {svg_file.name}")
                    cmd = [
                        inkscape_path,
                        "--without-gui",
                        str(svg_file),
                        f"--export-filename={temp_pdf}",
                        f"--export-type=pdf",
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                    if result.returncode == 0:
                        pdf_files.append(temp_pdf)
                        logger.info(f"Converted ({idx}/{len(svg_files)}): {svg_file.name} -> {temp_pdf.name}")
                    else:
                        logger.error(f"Failed to convert {svg_file.name}: {result.stderr}")
                        sys.exit(1)

                except subprocess.TimeoutExpired:
                    logger.error(f"Inkscape conversion timed out for {svg_file.name}")
                    sys.exit(1)
                except Exception as e:
                    logger.error(f"Error converting {svg_file.name}: {e}", exc_info=True)
                    sys.exit(1)

            # Merge all PDFs into one
            try:
                logger.info(f"Merging {len(pdf_files)} PDF file(s) into {output_pdf}")
                from PyPDF2 import PdfMerger

                merger = PdfMerger()
                for pdf_file in pdf_files:
                    merger.append(str(pdf_file))
                merger.write(output_pdf)
                merger.close()
                logger.info(f"Successfully saved PDF: {output_pdf}")

            except ImportError:
                # Fallback: copy first PDF as a workaround
                logger.warning("PyPDF2 not available, using single-page fallback")

                if pdf_files:
                    import shutil
                    shutil.copy(str(pdf_files[0]), output_pdf)
                    logger.warning("Only first page saved. Install PyPDF2 for full merging: pip install PyPDF2")
                    logger.info(f"Saved PDF (single page): {output_pdf}")
