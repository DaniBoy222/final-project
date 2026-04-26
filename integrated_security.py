"""
Integrated Security Monitor

Uses your existing modules to:
- Detect movement from the camera (using your frame difference + AI logic)
- When movement is significant/unnatural, detect what moved (face detection)
- If it's a human face, compare it against a folder of known faces (your "database")
- If the face is unknown, send an email with the face image attached via Gmail

Reuses:
- frame_difference.py
- amount_of_change.py
- similarity_analysis.py
- movement_classifier.py
- face_and_object_detection (1).py
- face_comparison.py
"""

import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import tensorflow as tf
import time
from datetime import datetime, timedelta
from pathlib import Path

import cv2
from email.message import EmailMessage
import smtplib
import ssl

from frame_difference import check_if_movement_happened
from movement_classifier import classify_movement
from amount_of_change import calculate_amount_of_change
from similarity_analysis import calculate_similarity_and_magnitude
from face_comparison import compare_faces

import importlib.util


def _load_face_detection_module():
    """
    Load your existing 'face_and_object_detection (1).py' as a module,
    even though the filename has spaces/parentheses.
    """
    here = Path(__file__).resolve().parent
    face_file = here / "face_and_object_detection (1).py"
    if not face_file.exists():
        raise FileNotFoundError(f"Face detection file not found: {face_file}")

    spec = importlib.util.spec_from_file_location("face_and_object_detection", face_file)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def load_known_face_paths(known_faces_dir: str = "pics"):
    """
    Treat a folder of images as your "database" of known faces.
    Each image file name (without extension) is the person's name.
    """
    base = Path(known_faces_dir)
    if not base.is_dir():
        print(f"[INFO] Known faces directory '{known_faces_dir}' not found. No known faces loaded.")
        return []

    paths = []
    for p in base.iterdir():
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            paths.append(p)
    if not paths:
        print(f"[INFO] No image files found in '{known_faces_dir}'.")
    else:
        print(f"[INFO] Loaded {len(paths)} known face image(s) from '{known_faces_dir}'.")
    return paths


def identify_face_against_database(face_image_bgr, known_face_paths, tolerance: float = 0.6):
    """
    Compare a detected face (numpy array, BGR) against all images
    in your known-faces folder using your existing face_comparison.compare_faces.

    Returns (name, confidence, is_known).
    """
    if not known_face_paths:
        return "Unknown", 0.0, False

    best_name = "Unknown"
    best_conf = 0.0
    is_known = False

    for path in known_face_paths:
        result = compare_faces(str(path), face_image_bgr, tolerance=tolerance)
        same = bool(result.get("same_person", False))
        conf = float(result.get("confidence", 0.0))
        if conf > best_conf:
            best_conf = conf
            if same:
                best_name = path.stem
                is_known = True
            else:
                best_name = "Unknown"
                is_known = False

    return best_name, best_conf, is_known


def send_alert_email_with_face (
    face_image_bgr,
    smtp_user,
    smtp_password,
    sender_email,
    recipient_email,
    subject="Security Alert: Unknown Face Detected"
):
    """
    Send an email with the given face image attached, using Gmail SMTP.
    """
    sender_email = "dani.mantin@gmail.com"       # your Gmail address
    receiver_email = "danielmantin678@gmail.com" # recipient
    password = "zoca rtxv joji uvyf"         # Gmail App Password
    subject = "Camera Capture Test"
    # -----------------------------

    # 2. Encode the frame to PNG in memory
    success, buffer = cv2.imencode(".png", face_image_bgr)
    if not success:
        raise RuntimeError("Failed to encode image")

    image_bytes = buffer.tobytes()
    image_cid = "camera_image"

    # 3. Create email message
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    # HTML body referencing the image via CID
    msg.add_alternative(f"""
    <html>
    <body>
        <p>Here is the image captured from the camera:</p>
        <img src="cid:{image_cid}">
    </body>
    </html>
    """, subtype="html")

    # Attach the image in memory
    msg.get_payload()[0].add_related(
        image_bytes,
        maintype="image",
        subtype="png",
        cid=image_cid
    )

    # 4. Send email via Gmail SMTP
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.send_message(msg)

    print("Email sent successfully!")

import cv2

def is_blurry(frame, threshold=100):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    return sharpness < threshold


def run_integrated_security_monitor(
    camera_index=0,
    threshold=42,
    frame_interval=0.5,
    min_change_percentage=0.7,
    known_faces_dir="pics",
    alert_cooldown_seconds=0,
    smtp_user="dani",
    smtp_password="zoca rtxv joji uvyf",
    sender_email="dani.mantin@gmail.com",
    recipient_email="danielmantin678@gmail.com",
):
    """
    Main loop:
    - Uses your movement detection + classification to decide when something important moved.
    - When important movement is detected, uses your face detector to find faces.
    - For each face, compares against database of known faces using your compare_faces().
    - For unknown faces, sends an email with the face image (rate-limited).
    """
    unknown_count = 0
    known_count = 0
    
    # Load helper modules / data
    face_module = _load_face_detection_module()
    known_face_paths = load_known_face_paths(known_faces_dir)

    # Basic email config validation
    email_enabled = all([smtp_user, smtp_password, sender_email, recipient_email])
    if not email_enabled:
        print("[WARN] Email not fully configured. Unknown faces will NOT trigger an email.")

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[ERROR] Could not open camera {camera_index}")
        return

    print("Camera opened successfully!")
    print("Calibrating camera (waiting 3 seconds for stabilization)...")

    for _ in range(10):
        ret, _ = cap.read()
        if ret:
            time.sleep(0.1)

    print("Camera ready! Press 'q' to quit")
    print("-" * 50)

    ret, previous_frame = cap.read()
    if not ret:
        print("Error: Could not read first frame")
        cap.release()
        return

    frame_count = 0
    last_alert_time = datetime.min

    try:
        while True:
            ret, current_frame = cap.read()
            if not ret:
                print("Error: Could not read frame")
                break

            frame_count += 1
            time.sleep(frame_interval)

            has_movement = check_if_movement_happened(previous_frame, current_frame, threshold)

            if has_movement:
                classification = classify_movement(previous_frame, current_frame, threshold)
                change_percentage = calculate_amount_of_change(previous_frame, current_frame, threshold)
                similarity_data = calculate_similarity_and_magnitude(previous_frame, current_frame, threshold)

                should_report = False
                if change_percentage >= min_change_percentage:
                    if change_percentage > 1.5:
                        should_report = True
                    elif classification != "natural":
                        should_report = True

                if should_report:
                    print(f"\n[MOVEMENT DETECTED - Frame {frame_count}]")
                    print(f"  Classification: {classification}")
                    print(f"  Change percentage: {change_percentage:.2f}%")
                    print(f"  Similarity: {similarity_data['similarity']:.3f}")
                    print(f"  Magnitude: {similarity_data['magnitude']}")

                    # Face detection on the current frame
                    faces = face_module.detect_faces(current_frame)

                    if not faces:
                        print("  No faces detected in this frame.")
                    else:
                        print(f"  Detected {len(faces)} face(s).")

                    for face in faces:
                        x1, y1, x2, y2 = face["bbox"]
                        # Clamp coordinates to frame bounds
                        h, w = current_frame.shape[:2]
                        x1 = max(0, min(w - 1, x1))
                        x2 = max(0, min(w, x2))
                        y1 = max(0, min(h - 1, y1))
                        y2 = max(0, min(h, y2))

                        if x2 <= x1 or y2 <= y1:
                            continue

                        face_roi = current_frame[y1:y2, x1:x2]

                        if is_blurry(face_roi):
                            print("    Face detected but image is blurry, skipping recognition.")
                            continue
                        
                        else:
                            name, conf, is_known = identify_face_against_database(
                                face_roi, known_face_paths, tolerance=0.4)
                                
                                
                        status = "KNOWN" if is_known else "UNKNOWN"
                        print(f"    Face: {status} (name: {name}, confidence: {conf:.2f})")

                        # Draw box + label on the live view
                        color = (0, 255, 0) if is_known else (0, 0, 255)
                        cv2.rectangle(current_frame, (x1, y1), (x2, y2), color, 2)
                        label = f"{name} ({conf:.2f})"
                        cv2.putText(
                            current_frame,
                            label,
                            (x1, max(0, y1 - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            color,
                            1,
                            cv2.LINE_AA,
                        )

                        # If unknown and email configured + cooldown passed → alert
                        if not is_known and email_enabled:
                            print("    -> Unknown face detected, sending email alert...")
                            send_alert_email_with_face(
                                face_roi,
                                smtp_user=smtp_user,
                                smtp_password=smtp_password,
                                sender_email=sender_email,
                                recipient_email=recipient_email,
                                )

                    print("-" * 50)
                else:
                    print(f"Frame {frame_count}: Change detected but filtered (natural/lighting)")
            else:
                print(f"Frame {frame_count}: No movement detected")

            previous_frame = current_frame.copy()

            cv2.imshow("Integrated Security Monitor", current_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("[INFO] Quitting...")
                break

    except KeyboardInterrupt:
        print("\n\nStopped by user")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("\nCamera released. Goodbye!")


if __name__ == "__main__":
    # TODO: Fill in your real Gmail app credentials here
    # (recommended: load from environment variables instead of hard-coding)

    run_integrated_security_monitor(
        camera_index=0,
        threshold=42,
        frame_interval=0.5,
        min_change_percentage=0.7,
        known_faces_dir="pics",
        alert_cooldown_seconds=60,
        smtp_user="dani",
        smtp_password="zoca rtxv joji uvyf",
        sender_email="dani.mantin@gmail.com",
        recipient_email="danielmantin678@gmail.com",
    )

