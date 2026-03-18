"""
Amount of Change Calculation
Calculates how many pixels changed between two frames
All calculations done manually - YOUR AI logic!
"""

from frame_difference import get_frame_differences


def calculate_amount_of_change(image1, image2, 
                              threshold: int = 30, return_percentage: bool = True):
    """
    Calculate how many pixels changed between two frames.
    All counting done manually - YOUR logic!
    
    Args:
        image1: Path to first image (str) OR numpy array (from camera)
        image2: Path to second image (str) OR numpy array (from camera)
        threshold: Minimum difference value to count as "changed" (default: 30)
                  Pixels with difference > threshold are considered "changed"
        return_percentage: If True, returns percentage (0-100)
                         If False, returns number of pixels
                         
    Returns:
        If return_percentage=True: float (0-100) representing percentage of frame that changed
        If return_percentage=False: int representing number of pixels that changed
    """
    # Get difference array
    diff_array = get_frame_differences(image1, image2)
    
    # Count pixels that changed significantly - YOUR LOGIC
    # Go through each pixel and count if it's above threshold
    changed_pixels = 0
    total_pixels = 0
    
    for row in diff_array:
        for pixel_value in row:
            total_pixels += 1
            if pixel_value > threshold:
                changed_pixels += 1
    
    if return_percentage:
        # Calculate percentage - YOUR FORMULA
        percentage = (changed_pixels / total_pixels) * 100 if total_pixels > 0 else 0.0
        return float(percentage)
    else:
        # Return as number of pixels
        return int(changed_pixels)


# Example usage
if __name__ == "__main__":
    # Get amount of change as percentage
    percentage = calculate_amount_of_change("frame1.jpg", "frame2.jpg", threshold=30)
    print(f"Amount of change: {percentage:.2f}%")
    
    # Get amount of change as number of pixels
    pixel_count = calculate_amount_of_change("frame1.jpg", "frame2.jpg", 
                                            threshold=30, return_percentage=False)
    print(f"Number of changed pixels: {pixel_count}")
