"""
Similarity Analysis
Calculates similarity of change and magnitude of change
All calculations done manually - YOUR AI logic!
"""

from frame_difference import get_frame_differences
import math


def calculate_mean(values):
    """
    Calculate mean (average) manually - YOUR calculation!
    
    Args:
        values: List or array of numbers
        
    Returns:
        Mean (average) value
    """
    if len(values) == 0:
        return 0.0
    
    # YOUR LOGIC: Sum all values, divide by count
    total = 0.0
    count = 0
    for value in values:
        total += float(value)
        count += 1
    
    return total / count if count > 0 else 0.0


def calculate_standard_deviation(values, mean):
    """
    Calculate standard deviation manually - YOUR calculation!
    
    Args:
        values: List or array of numbers
        mean: Mean (average) of the values
        
    Returns:
        Standard deviation
    """
    if len(values) == 0:
        return 0.0
    
    # YOUR LOGIC: Standard deviation formula
    # sqrt of (sum of (each value - mean)^2 / count)
    sum_squared_diff = 0.0
    count = 0
    
    for value in values:
        diff = float(value) - mean
        sum_squared_diff += diff * diff  # (value - mean)^2
        count += 1
    
    variance = sum_squared_diff / count if count > 0 else 0.0
    std_deviation = math.sqrt(variance)
    
    return std_deviation


def calculate_similarity_and_magnitude(image1, image2, 
                                      threshold: int = 30):
    """
    Calculate similarity of change and magnitude (how much pixels changed).
    All calculations done manually - YOUR AI!
    
    Args:
        image1: Path to first image (str) OR numpy array (from camera)
        image2: Path to second image (str) OR numpy array (from camera)
        threshold: Minimum difference to consider a pixel as "changed"
        
    Returns:
        Dictionary with:
        - 'similarity': float (0-1) - How uniform the changes are
                       Higher = more uniform (likely natural lighting)
                       Lower = less uniform (likely movement)
        - 'magnitude': str - "small" or "significant"
                      "small" = natural (gradual lighting change)
                      "significant" = unnatural (sudden movement)
        - 'mean_change': float - Average amount of change (YOUR calculation)
        - 'std_change': float - Standard deviation (YOUR calculation)
    """
    # Get difference array
    diff_array = get_frame_differences(image1, image2)
    
    # Get only the pixels that changed significantly - YOUR logic
    changed_pixels = []
    for row in diff_array:
        for pixel_value in row:
            if pixel_value > threshold:
                changed_pixels.append(pixel_value)
    
    if len(changed_pixels) == 0:
        # No significant changes
        return {
            'similarity': 1.0,  # Perfect similarity (no change)
            'magnitude': 'small',
            'mean_change': 0.0,
            'std_change': 0.0
        }
    
    # Calculate statistics using YOUR functions
    mean_change = calculate_mean(changed_pixels)  # YOUR calculation
    std_change = calculate_standard_deviation(changed_pixels, mean_change)  # YOUR calculation
    
    # SIMILARITY: How uniform the changes are - YOUR FORMULA
    # Lower standard deviation relative to mean = higher similarity
    if mean_change > 0:
        coefficient_of_variation = std_change / mean_change
        # Convert to 0-1 scale (higher = more similar/uniform)
        # THIS IS YOUR FORMULA
        similarity = 1.0 / (1.0 + coefficient_of_variation)
    else:
        similarity = 1.0
    
    # MAGNITUDE: How much pixels changed overall - YOUR LOGIC
    # Small mean = gradual change (natural)
    # Large mean = sudden change (unnatural)
    if mean_change < 50:
        magnitude = "small"  # Natural (gradual lighting change)
    else:
        magnitude = "significant"  # Unnatural (sudden movement)
    
    return {
        'similarity': float(similarity),
        'magnitude': magnitude,
        'mean_change': float(mean_change),
        'std_change': float(std_change)
    }


# Example usage
if __name__ == "__main__":
    result = calculate_similarity_and_magnitude("frame1.jpg", "frame2.jpg", threshold=30)
    
    print(f"Similarity: {result['similarity']:.3f} (higher = more uniform)")
    print(f"Magnitude: {result['magnitude']} (small = natural, significant = unnatural)")
    print(f"Mean change: {result['mean_change']:.2f}")
    print(f"Standard deviation: {result['std_change']:.2f}")
