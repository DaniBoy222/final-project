"""
Frame Difference Detection
Finds differences between two frames and returns pixel differences
"""
import cv2
# Note: cv2.absdiff returns numpy array, but we do all calculations manually


def get_frame_differences(image1, image2):
    """
    Compare two frames and return pixel differences.
    
    Args:
        image1: Path to first image (str) OR numpy array (from camera)
        image2: Path to second image (str) OR numpy array (from camera)
        
    Returns:
        numpy array (2D) where each value represents how much that pixel changed.
        Array shape is (height, width) - same as the images.
        
        Meaning of numbers in the array:
        - 0 = pixel didn't change (same brightness in both frames)
        - 1-255 = pixel changed by that amount
          * Small numbers (1-30) = small change (likely natural lighting)
          * Large numbers (50-255) = large change (likely movement)
        - Higher number = bigger difference between the two frames at that pixel
    """
    # Load images (handle both file paths and numpy arrays)
    if isinstance(image1, str):
        img1 = cv2.imread(image1)
        if img1 is None:
            raise ValueError(f"Could not load image: {image1}")
    else:
        img1 = image1  # Already a numpy array
    
    if isinstance(image2, str):
        img2 = cv2.imread(image2)
        if img2 is None:
            raise ValueError(f"Could not load image: {image2}")
    else:
        img2 = image2  # Already a numpy array

    # Resize to same size if needed
    if img1.shape != img2.shape:
        h, w = min(img1.shape[0], img2.shape[0]), min(img1.shape[1], img2.shape[1])
        img1 = cv2.resize(img1, (w, h))
        img2 = cv2.resize(img2, (w, h))
    
    # Convert to grayscale (brightness only, easier to compare)
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Calculate absolute difference between pixels
    # This gives us how much each pixel changed
    difference_array = cv2.absdiff(gray1, gray2)
    
    return difference_array


def check_if_movement_happened(image1, image2, threshold: int = 30) -> bool:
    """
    Quick check to see if there's any significant movement between frames.
    Use this before running other analysis functions to save time.
    
    Args:
        image1: Path to first image (str) OR numpy array (from camera)
        image2: Path to second image (str) OR numpy array (from camera)
        threshold: Minimum difference value to count as "changed" (default: 30)
        
    Returns:
        True if movement detected, False if no significant movement
    """
    # Get difference array
    diff_array = get_frame_differences(image1, image2)
    
    # Count how many pixels changed significantly - YOUR LOGIC
    changed_pixels = 0
    total_pixels = 0
    
    for row in diff_array:
        for pixel_value in row:
            total_pixels += 1
            if pixel_value > threshold:
                changed_pixels += 1
    
    # If more than 0.1% of pixels changed, consider it movement - YOUR THRESHOLD
    movement_percentage = (changed_pixels / total_pixels) * 100 if total_pixels > 0 else 0.0
    return movement_percentage > 0.1


# Example usage
if __name__ == "__main__":
    # Example: Get difference array
    diff_array = get_frame_differences("frame1.jpg", "frame2.jpg")
    
    # The array contains difference values for each pixel
    # diff_array[100][200] = 45 means pixel at row 100, column 200 changed by 45 brightness units
    
    print(f"Difference array shape: {diff_array.shape}")
    
    # Calculate min, max, mean manually for example
    min_val = float('inf')
    max_val = float('-inf')
    total = 0.0
    count = 0
    for row in diff_array:
        for val in row:
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val
            total += val
            count += 1
    mean_val = total / count if count > 0 else 0.0
    
    print(f"Min difference: {min_val}")
    print(f"Max difference: {max_val}")
    print(f"Mean difference: {mean_val:.2f}")
    
    # Check if movement happened
    has_movement = check_if_movement_happened("frame1.jpg", "frame2.jpg")
    print(f"Movement detected: {has_movement}")

