#!/usr/bin/env python3

"""Base class for PDF conversion engines."""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("newline_iwb_converter.pdf_engines")


class BasePDFEngine(ABC):
    """Abstract base class for PDF conversion engines."""

    @abstractmethod
    def combine_svgs_to_pdf(self, svg_dir, output_pdf, **kwargs):
        """
        Combine multiple SVG files into a single PDF.

        Args:
            svg_dir: Directory containing SVG files
            output_pdf: Path to output PDF file
            **kwargs: Engine-specific options
        """
        pass

    @abstractmethod
    def is_available(self):
        """
        Check if the engine is available on the system.

        Returns:
            True if available, False otherwise
        """
        pass

    def get_name(self):
        """Get the name of the engine."""
        engine_name = self.__class__.__name__
        logger.debug(f"PDF engine: {engine_name}")
        return engine_name
