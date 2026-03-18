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


def load_known_face_paths(known_faces_dir: str = "known_faces"):
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


def send_alert_email_with_face(
    face_image_bgr,
    smtp_user: str,
    smtp_password: str,
    sender_email: str,
    recipient_email: str,
    subject: str = "Security Alert: Unknown Person Detected",
):
    """
    Send an email via Gmail with the face image attached.
    Reuses the same approach as your existing gmail.py, but as a function.
    """
    success, buffer = cv2.imencode(".png", face_image_bgr)
    if not success:
        print("[ERROR] Failed to encode face image for email.")
        return

    image_bytes = buffer.tobytes()
    image_cid = "unknown_face"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.add_alternative(
        f"""
<html>
  <body>
    <p>An unknown person was detected by your camera:</p>
    <img src="cid:{image_cid}">
  </body>
</html>
""",
        subtype="html",
    )

    msg.get_payload()[0].add_related(
        image_bytes,
        maintype="image",
        subtype="png",
        cid=image_cid,
    )

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("[INFO] Alert email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send alert email: {e}")


def run_integrated_security_monitor(
    camera_index: int = 0,
    threshold: int = 40,
    frame_interval: float = 0.5,
    min_change_percentage: float = 0.5,
    known_faces_dir: str = "known_faces",
    alert_cooldown_seconds: int = 60,
    smtp_user: str = "",
    smtp_password: str = "",
    sender_email: str = "",
    recipient_email: str = "",
):
    """
    Main loop:
    - Uses your movement detection + classification to decide when something important moved.
    - When important movement is detected, uses your face detector to find faces.
    - For each face, compares against database of known faces using your compare_faces().
    - For unknown faces, sends an email with the face image (rate-limited).
    """
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

                        name, conf, is_known = identify_face_against_database(
                            face_roi, known_face_paths, tolerance=0.6
                        )

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
                            now = datetime.now()
                            if now - last_alert_time >= timedelta(seconds=alert_cooldown_seconds):
                                print("    -> Unknown face detected, sending email alert...")
                                send_alert_email_with_face(
                                    face_roi,
                                    smtp_user=smtp_user,
                                    smtp_password=smtp_password,
                                    sender_email=sender_email,
                                    recipient_email=recipient_email,
                                )
                                last_alert_time = now
                            else:
                                remaining = alert_cooldown_seconds - (now - last_alert_time).seconds
                                print(f"    -> Alert cooldown active ({remaining}s remaining), no email sent.")

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
    SMTP_USER = os.environ.get("GMAIL_USER", "")
    SMTP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
    SENDER_EMAIL = os.environ.get("GMAIL_SENDER", SMTP_USER)
    RECIPIENT_EMAIL = os.environ.get("GMAIL_RECIPIENT", SMTP_USER)

    run_integrated_security_monitor(
        camera_index=0,
        threshold=42,
        frame_interval=0.5,
        min_change_percentage=0.7,
        known_faces_dir="known_faces",
        alert_cooldown_seconds=60,
        smtp_user=SMTP_USER,
        smtp_password=SMTP_PASSWORD,
        sender_email=SENDER_EMAIL,
        recipient_email=RECIPIENT_EMAIL,
    )

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


def load_known_face_paths(known_faces_dir: str = "known_faces"):
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


def send_alert_email_with_face(
    face_image_bgr,
    smtp_user: str,
    smtp_password: str,
    sender_email: str,
    recipient_email: str,
    subject: str = "Security Alert: Unknown Person Detected",
):
    """
    Send an email via Gmail with the face image attached.
    Reuses the same approach as your existing gmail.py, but as a function.
    """
    success, buffer = cv2.imencode(".png", face_image_bgr)
    if not success:
        print("[ERROR] Failed to encode face image for email.")
        return

    image_bytes = buffer.tobytes()
    image_cid = "unknown_face"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    msg.add_alternative(
        f"""
<html>
  <body>
    <p>An unknown person was detected by your camera:</p>
    <img src="cid:{image_cid}">
  </body>
</html>
""",
        subtype="html",
    )

    msg.get_payload()[0].add_related(
        image_bytes,
        maintype="image",
        subtype="png",
        cid=image_cid,
    )

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("[INFO] Alert email sent successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to send alert email: {e}")


def run_integrated_security_monitor(
    camera_index: int = 0,
    threshold: int = 40,
    frame_interval: float = 0.5,
    min_change_percentage: float = 0.5,
    known_faces_dir: str = "known_faces",
    alert_cooldown_seconds: int = 60,
    smtp_user: str = "",
    smtp_password: str = "",
    sender_email: str = "",
    recipient_email: str = "",
):
    """
    Main loop:
    - Uses your movement detection + classification to decide when something important moved.
    - When important movement is detected, uses your face detector to find faces.
    - For each face, compares against database of known faces using your compare_faces().
    - For unknown faces, sends an email with the face image (rate-limited).
    """
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

                        name, conf, is_known = identify_face_against_database(
                            face_roi, known_face_paths, tolerance=0.6
                        )

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
                            now = datetime.now()
                            if now - last_alert_time >= timedelta(seconds=alert_cooldown_seconds):
                                print("    -> Unknown face detected, sending email alert...")
                                send_alert_email_with_face(
                                    face_roi,
                                    smtp_user=smtp_user,
                                    smtp_password=smtp_password,
                                    sender_email=sender_email,
                                    recipient_email=recipient_email,
                                )
                                last_alert_time = now
                            else:
                                remaining = alert_cooldown_seconds - (now - last_alert_time).seconds
                                print(f"    -> Alert cooldown active ({remaining}s remaining), no email sent.")

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
    SMTP_USER = os.environ.get("GMAIL_USER", "")
    SMTP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")
    SENDER_EMAIL = os.environ.get("GMAIL_SENDER", SMTP_USER)
    RECIPIENT_EMAIL = os.environ.get("GMAIL_RECIPIENT", SMTP_USER)

    run_integrated_security_monitor(
        camera_index=0,
        threshold=42,
        frame_interval=0.5,
        min_change_percentage=0.7,
        known_faces_dir="known_faces",
        alert_cooldown_seconds=60,
        smtp_user=SMTP_USER,
        smtp_password=SMTP_PASSWORD,
        sender_email=SENDER_EMAIL,
        recipient_email=RECIPIENT_EMAIL,
    )

