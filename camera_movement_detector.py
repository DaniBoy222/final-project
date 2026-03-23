"""
Camera Movement Detector
Takes pictures from connected camera and detects movement using YOUR AI logic
"""

import cv2
import time
from frame_difference import check_if_movement_happened
from movement_classifier import classify_movement
from amount_of_change import calculate_amount_of_change
from similarity_analysis import calculate_similarity_and_magnitude


def detect_movement_from_camera(camera_index=0, threshold=40, frame_interval=0.5, min_change_percentage=0.5):
    """
    Capture frames from camera and detect movement using YOUR AI logic.
    
    Args:
        camera_index: Camera device index (usually 0 for default camera)
        threshold: Threshold for detecting changes (default: 40, higher = less sensitive)
        frame_interval: Time in seconds between frame captures (default: 0.5)
        min_change_percentage: Minimum % of frame that must change to report movement (default: 0.5%)
    """
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    
    print("Camera opened successfully!")
    print("Calibrating camera (waiting 3 seconds for stabilization)...")
    
    # Let camera stabilize - capture a few frames to let auto-exposure adjust
    for _ in range(10):
        ret, _ = cap.read()
        if ret:
            time.sleep(0.1)
    
    print("Camera ready! Press 'q' to quit")
    print("-" * 50)
    
    # Capture first frame as reference after stabilization
    ret, previous_frame = cap.read()
    if not ret:
        print("Error: Could not read first frame")
        cap.release()
        return
    
    frame_count = 0
    
    try:
        while True:
            # Capture current frame
            ret, current_frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            frame_count += 1
            
            # Wait for the specified interval
            time.sleep(frame_interval)
            
            # Use YOUR AI logic to check for movement
            has_movement = check_if_movement_happened(previous_frame, current_frame, threshold)
            
            if has_movement:
                # Get detailed classification using YOUR AI
                classification = classify_movement(previous_frame, current_frame, threshold)
                
                # Get additional metrics
                change_percentage = calculate_amount_of_change(previous_frame, current_frame, threshold)
                similarity_data = calculate_similarity_and_magnitude(previous_frame, current_frame, threshold)
                
                # Only report movement if:
                # 1. Change percentage is above minimum threshold
                # 2. If change is significant (>1.5%), report it even if "natural" (real movement might be misclassified)
                # 3. Otherwise, only report if classification is "unnatural"
                should_report = False
                if change_percentage >= min_change_percentage:
                    if change_percentage > 1.5:
                        # High change = likely real movement, report even if classified as natural
                        should_report = True
                    elif classification != "natural":
                        # Lower change, but classified as unnatural = report it
                        should_report = True
                
                if should_report:
                    # Print movement detection results
                    print(f"\n[MOVEMENT DETECTED - Frame {frame_count}]")
                    print(f"  Classification: {classification}")
                    print(f"  Change percentage: {change_percentage:.2f}%")
                    print(f"  Similarity: {similarity_data['similarity']:.3f}")
                    print(f"  Magnitude: {similarity_data['magnitude']}")
                    print("-" * 50)
                else:
                    # Movement detected but filtered out (likely natural/lighting)
                    print(f"Frame {frame_count}: Change detected but filtered (natural/lighting)")
            else:
                # No significant movement detected
                print(f"Frame {frame_count}: No movement detected")
            
            # Update previous frame for next comparison
            previous_frame = current_frame.copy()
            
            # Check for 'q' key press to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        # Release camera
        cap.release()
        cv2.destroyAllWindows()
        print("\nCamera released. Goodbye!")


if __name__ == "__main__":
    # Start movement detection
    # You can adjust these parameters:
    # - camera_index: 0 for default camera, 1 for second camera, etc.
    # - threshold: Lower = more sensitive (default: 30)
    # - frame_interval: Time between comparisons in seconds (default: 0.5)
    
    detect_movement_from_camera(
        camera_index=0,
        threshold=42,  # Slightly increased to reduce false positives
        frame_interval=0.5,
        min_change_percentage=0.7  # Slightly increased minimum change required
    )

"""
Camera Movement Detector
Takes pictures from connected camera and detects movement using YOUR AI logic
"""

import cv2
import time
from frame_difference import check_if_movement_happened
from movement_classifier import classify_movement
from amount_of_change import calculate_amount_of_change
from similarity_analysis import calculate_similarity_and_magnitude


def detect_movement_from_camera(camera_index=0, threshold=40, frame_interval=0.5, min_change_percentage=0.5):
    """
    Capture frames from camera and detect movement using YOUR AI logic.
    
    Args:
        camera_index: Camera device index (usually 0 for default camera)
        threshold: Threshold for detecting changes (default: 40, higher = less sensitive)
        frame_interval: Time in seconds between frame captures (default: 0.5)
        min_change_percentage: Minimum % of frame that must change to report movement (default: 0.5%)
    """
    # Initialize camera
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print(f"Error: Could not open camera {camera_index}")
        return
    
    print("Camera opened successfully!")
    print("Calibrating camera (waiting 3 seconds for stabilization)...")
    
    # Let camera stabilize - capture a few frames to let auto-exposure adjust
    for _ in range(10):
        ret, _ = cap.read()
        if ret:
            time.sleep(0.1)
    
    print("Camera ready! Press 'q' to quit")
    print("-" * 50)
    
    # Capture first frame as reference after stabilization
    ret, previous_frame = cap.read()
    if not ret:
        print("Error: Could not read first frame")
        cap.release()
        return
    
    frame_count = 0
    
    try:
        while True:
            # Capture current frame
            ret, current_frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break
            
            frame_count += 1
            
            # Wait for the specified interval
            time.sleep(frame_interval)
            
            # Use YOUR AI logic to check for movement
            has_movement = check_if_movement_happened(previous_frame, current_frame, threshold)
            
            if has_movement:
                # Get detailed classification using YOUR AI
                classification = classify_movement(previous_frame, current_frame, threshold)
                
                # Get additional metrics
                change_percentage = calculate_amount_of_change(previous_frame, current_frame, threshold)
                similarity_data = calculate_similarity_and_magnitude(previous_frame, current_frame, threshold)
                
                # Only report movement if:
                # 1. Change percentage is above minimum threshold
                # 2. If change is significant (>1.5%), report it even if "natural" (real movement might be misclassified)
                # 3. Otherwise, only report if classification is "unnatural"
                should_report = False
                if change_percentage >= min_change_percentage:
                    if change_percentage > 1.5:
                        # High change = likely real movement, report even if classified as natural
                        should_report = True
                    elif classification != "natural":
                        # Lower change, but classified as unnatural = report it
                        should_report = True
                
                if should_report:
                    # Print movement detection results
                    print(f"\n[MOVEMENT DETECTED - Frame {frame_count}]")
                    print(f"  Classification: {classification}")
                    print(f"  Change percentage: {change_percentage:.2f}%")
                    print(f"  Similarity: {similarity_data['similarity']:.3f}")
                    print(f"  Magnitude: {similarity_data['magnitude']}")
                    print("-" * 50)
                else:
                    # Movement detected but filtered out (likely natural/lighting)
                    print(f"Frame {frame_count}: Change detected but filtered (natural/lighting)")
            else:
                # No significant movement detected
                print(f"Frame {frame_count}: No movement detected")
            
            # Update previous frame for next comparison
            previous_frame = current_frame.copy()
            
            # Check for 'q' key press to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        # Release camera
        cap.release()
        cv2.destroyAllWindows()
        print("\nCamera released. Goodbye!")


if __name__ == "__main__":
    # Start movement detection
    # You can adjust these parameters:
    # - camera_index: 0 for default camera, 1 for second camera, etc.
    # - threshold: Lower = more sensitive (default: 30)
    # - frame_interval: Time between comparisons in seconds (default: 0.5)
    
    detect_movement_from_camera(
        camera_index=0,
        threshold=42,  # Slightly increased to reduce false positives
        frame_interval=0.5,
        min_change_percentage=0.7  # Slightly increased minimum change required
    )

