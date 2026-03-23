"""
Movement Classifier - YOUR AI
Decides if detected movement is natural or unnatural based on your analysis
"""

from frame_difference import get_frame_differences, check_if_movement_happened
from amount_of_change import calculate_amount_of_change
from similarity_analysis import calculate_similarity_and_magnitude


def classify_movement(image1, image2, threshold: int = 30) -> str:
    """
    YOUR AI that classifies movement as natural or unnatural.
    This is where YOUR decision-making logic lives!
    
    Args:
        image1: Path to first image (str) OR numpy array (from camera)
        image2: Path to second image (str) OR numpy array (from camera)
        threshold: Threshold for detecting changes
        
    Returns:
        "natural" or "unnatural"
    """
    # Quick check: is there any movement?
    if not check_if_movement_happened(image1, image2, threshold):
        return "no_movement"
    
    # Get all the metrics
    amount = calculate_amount_of_change(image1, image2, threshold)
    similarity_data = calculate_similarity_and_magnitude(image1, image2, threshold)
    
    similarity = similarity_data['similarity']
    magnitude = similarity_data['magnitude']
    
    # ============================================
    # YOUR CLASSIFICATION LOGIC
    # Adjust these rules based on your testing
    # ============================================
    
    # Rule 1: Small change = natural (lighting changes gradually)
    if amount < 5 and magnitude == "small":
        return "natural"
    
    # Rule 2: Large change with high similarity = natural (uniform lighting change)
    if amount > 10 and similarity > 0.7:
        return "natural"
    
    # Rule 3: Large change with low similarity = unnatural (localized movement)
    if amount > 10 and similarity < 0.5:
        return "unnatural"
    
    # Rule 4: Significant magnitude change = unnatural (sudden movement)
    if magnitude == "significant":
        return "unnatural"
    
    # Rule 5: Medium change, check similarity
    if 5 <= amount <= 10:
        if similarity > 0.6:
            return "natural"  # Uniform change = lighting
        else:
            return "unnatural"  # Non-uniform = movement
    
    # Default: if unsure, classify as unnatural (safer for emergency detection)
    return "unnatural"


# Example usage
if __name__ == "__main__":
    classification = classify_movement("frame1.jpg", "frame2.jpg")
    print(f"Movement classification: {classification}")

