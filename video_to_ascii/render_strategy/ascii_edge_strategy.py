"""
This module contains a class AsciiEdgeStrategy, to process video frames with edge enhancement
"""

import cv2
import numpy as np
from . import ascii_strategy as strategy
import sys

if sys.platform != 'win32':
    from . import image_processor as ipe
else:
    from . import image_processor_win as ipe

class AsciiEdgeStrategy(strategy.AsciiStrategy):
    """Print each frame in the terminal using edge-enhanced ascii characters"""

    def resize_frame(self, frame, dimensions=strategy.DEFAULT_TERMINAL_SIZE):
        """
        Resize a frame and enhance edges for better visibility
        """
        # First resize the frame using the parent method
        resized = super().resize_frame(frame, dimensions)
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate the edges to make them more visible
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Enhance the original image by emphasizing edges
        enhanced = resized.copy()
        for i in range(3):  # For each color channel
            enhanced[:,:,i] = cv2.addWeighted(resized[:,:,i], 0.8, edges, 0.2, 0)
            
        return enhanced

    def apply_pixel_to_ascii_strategy(self, pixel):
        """
        Define a pixel parsing strategy with a wider range of characters
        """
        # Use more varied characters for better distinction
        return ipe.pixel_to_ascii(pixel, colored=True, density=1)