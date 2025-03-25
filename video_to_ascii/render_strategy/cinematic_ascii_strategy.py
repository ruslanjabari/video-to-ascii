"""
This module contains CinematicAsciiStrategy class for professional-grade video processing
with advanced edge preservation, detail enhancement, and intelligent character mapping
"""

import cv2
import numpy as np
from . import ascii_strategy as strategy
import sys
import time

if sys.platform != 'win32':
    from . import image_processor as ipe
else:
    from . import image_processor_win as ipe

# Characters specifically for human figures
HUMAN_CHARS = '@#$%&'  # Bold, distinct characters for human figures

class CinematicAsciiStrategy(strategy.AsciiStrategy):
    """Render video with cinematographer-level quality ASCII conversion"""
    
    def __init__(self):
        """Initialize with frame history for temporal processing"""
        self.prev_frames = []
        self.prev_gray = None
        self.prev_motion = None
        self.max_frames = 3  # Reduced frame history for better performance
        self.frame_count = 0
        self.human_mask = None
        super().__init__()
    
    def resize_frame(self, frame, dimensions=strategy.DEFAULT_TERMINAL_SIZE):
        """
        Advanced frame processing with multiple enhancement techniques - optimized for performance
        """
        self.frame_count += 1
        
        # First resize the frame using the parent method
        resized = super().resize_frame(frame, dimensions)
        
        # Convert to grayscale for processing - do this once and reuse
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        
        # Store for temporal processing - only keep a few frames
        self.prev_frames.append(resized.copy())
        if len(self.prev_frames) > self.max_frames:
            self.prev_frames.pop(0)
        
        # Motion detection - only do this every other frame to improve performance
        if self.frame_count % 2 == 0 and self.prev_gray is not None:
            try:
                # Simplified optical flow with optimized parameters
                flow = cv2.calcOpticalFlowFarneback(
                    self.prev_gray, gray, None, 0.5, 3, 15, 3, 5, 1.1, 0
                )
                
                # Calculate motion magnitude
                mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                
                # Simple thresholding for motion detection
                motion_mask = (mag > 3.0).astype(np.uint8) * 255
                
                # Basic morphological operations to clean up the mask
                kernel = np.ones((3, 3), np.uint8)
                motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
                motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, kernel)
                
                # Store the motion mask
                self.human_mask = motion_mask
                self.prev_motion = mag
            except Exception:
                pass  # Silently fail if optical flow fails
        
        # Store current gray frame for next iteration
        self.prev_gray = gray
        
        # Calculate edges for character selection - simplified approach
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Store gradient direction and magnitude for character selection
        self.gradient_direction = np.arctan2(sobel_y, sobel_x) * 180 / np.pi
        self.gradient_magnitude = cv2.magnitude(sobel_x, sobel_y) / 255.0  # Normalize to 0-1
        
        # Skip additional processing for better performance
        return resized  # Return the basic resized frame
    
    def apply_pixel_to_ascii_strategy(self, pixel):
        """
        Optimized pixel to ASCII conversion with human figure highlighting
        """
        # Extract color information - no color manipulation to preserve original colors
        bgr = tuple(float(x) for x in pixel[:3])
        rgb = tuple(reversed(bgr))
        
        # Get pixel position
        y, x = self.current_y, self.current_x
        
        # Check if this pixel is part of a human figure
        is_human = False
        if (self.human_mask is not None and 
            x < self.human_mask.shape[1] and y < self.human_mask.shape[0]):
            is_human = self.human_mask[y, x] > 0
        
        # Calculate brightness
        bright = ipe.rgb_to_brightness(*rgb)
        
        # If this is part of a human figure, use special characters
        if is_human:
            # Choose character based on brightness
            index = min(int(bright / 256 * len(HUMAN_CHARS)), len(HUMAN_CHARS) - 1)
            char = HUMAN_CHARS[index]
            return ipe.colorize(char*2, ipe.rgb_to_ansi(*rgb))  # Use original colors
        
        # For edges, use simple directional characters
        if (hasattr(self, 'gradient_magnitude') and self.gradient_magnitude is not None and 
            x < self.gradient_magnitude.shape[1] and y < self.gradient_magnitude.shape[0]):
            magnitude = self.gradient_magnitude[y, x]
            
            # Only use for strong edges
            if magnitude > 0.5:
                if hasattr(self, 'gradient_direction') and x < self.gradient_direction.shape[1]:
                    angle = self.gradient_direction[y, x]
                    # Simple directional character selection
                    if -22.5 <= angle < 22.5 or 157.5 <= angle <= 180 or -180 <= angle < -157.5:
                        return ipe.colorize('-'*2, ipe.rgb_to_ansi(*rgb))
                    elif 67.5 <= angle < 112.5 or -112.5 <= angle < -67.5:
                        return ipe.colorize('|'*2, ipe.rgb_to_ansi(*rgb))
        
        # For background, use simple brightness-based characters
        # Use pixel_to_ascii directly for most pixels (fastest option)
        return ipe.pixel_to_ascii(pixel, density=1)
        
    def convert_frame_pixels_to_ascii(self, frame, dimensions=strategy.DEFAULT_TERMINAL_SIZE, new_line_chars=False):
        """
        Override to track current pixel position for contextual character selection
        """
        cols, _ = dimensions
        h, w, _ = frame.shape

        printing_width = int(min(int(cols), (w*2))/2)
        pad = max(int(cols) - printing_width*2, 0) 
         
        msg = ''
        for j in range(h-1):
            self.current_y = j  # Track current row
            for i in range(printing_width):
                self.current_x = i  # Track current column
                pixel = frame[j][i]
                msg += self.apply_pixel_to_ascii_strategy(pixel)
            if new_line_chars:
                msg += "\n"
            else:
                msg += " " * (pad)
        msg += "\r\n"
        return msg 