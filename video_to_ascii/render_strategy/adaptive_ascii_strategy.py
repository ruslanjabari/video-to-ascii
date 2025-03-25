"""
This module contains AdaptiveAsciiStrategy class for enhanced video frame processing
with adaptive contrast, edge enhancement, and better character mapping
"""

import cv2
import numpy as np
from . import ascii_strategy as strategy
import sys

if sys.platform != 'win32':
    from . import image_processor as ipe
else:
    from . import image_processor_win as ipe

class AdaptiveAsciiStrategy(strategy.AsciiStrategy):
    """Render video with enhanced edge detection and adaptive contrast"""

    def resize_frame(self, frame, dimensions=strategy.DEFAULT_TERMINAL_SIZE):
        """
        Resize frame with adaptive contrast enhancement and edge detection
        """
        # First resize the frame using the parent method
        resized = super().resize_frame(frame, dimensions)
        
        # Convert to LAB color space for better color processing
        lab = cv2.cvtColor(resized, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        
        # Merge the CLAHE enhanced L-channel back with A and B channels
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        # Apply bilateral filter to reduce noise while preserving edges
        smoothed = cv2.bilateralFilter(enhanced, 9, 75, 75)
        
        # Detect edges using Canny
        gray = cv2.cvtColor(smoothed, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate the edges to make them more visible
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)
        
        # Create final enhanced image by combining the smoothed image with edges
        result = smoothed.copy()
        for i in range(3):
            result[:,:,i] = cv2.addWeighted(smoothed[:,:,i], 0.7, edges, 0.3, 0)
        
        return result

    def apply_pixel_to_ascii_strategy(self, pixel):
        """
        Apply enhanced pixel to ASCII conversion for better visibility
        """
        # Increase saturation for more vibrant colors
        bgr = tuple(float(x) for x in pixel[:3])
        rgb = tuple(reversed(bgr))
        
        # Increase color saturation for better visibility
        h, s, v = ipe.colorsys.rgb_to_hsv(*rgb)
        s = min(s * 1.4, 1.0)  # Increase saturation by 40%
        v = min(v * 1.1, 1.0)  # Slight boost to value/brightness
        rgb_enhanced = ipe.colorsys.hsv_to_rgb(h, s, v)
        
        # Use detailed character set (CHARS_DETAILED) for better differentiation
        bright = ipe.rgb_to_brightness(*rgb_enhanced)
        
        # We want to use the detailed character set (density=3)
        return ipe.pixel_to_ascii(pixel, density=3) 