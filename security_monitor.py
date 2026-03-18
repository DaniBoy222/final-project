import cv2
import face_recognition
import numpy as np
import os
import smtplib
import ssl
from email.message import EmailMessage
from datetime import datetime, timedelta


def load_known_faces(known_faces_dir="known_faces"):
    """
    Load known faces from a directory.
    Each image file name (without extension) is treated as the person's name.
    """
    known_encodings = []
    known_names = []

    if not os.path.isdir(known_faces_dir):
        print(f"[INFO] Known faces directory '{known_faces_dir}' not found. No known faces loaded.")
        return known_encodings, known_names

    for file_name in os.listdir(known_faces_dir):
        file_path = os.path.join(known_faces_dir, file_name)
        if not os.path.isfile(file_path):
            continue

        name, ext = os.path.splitext(file_name)
        if ext.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        image = face_recognition.load_image_file(file_path)
        encodings = face_recognition.face_encodings(image)
        if len(encodings) == 0:
            print(f"[WARN] No face found in known face image: {file_name}")
            continue

        known_encodings.append(encodings[0])
        known_names.append(name)
        print(f"[INFO] Loaded known face for: {name}")

    return known_encodings, known_names


def send_alert_email(
    face_image_bgr,
    smtp_server,
    smtp_port,
    smtp_user,
    smtp_password,
    sender_email,
    recipient_email,
):
    """
    Send an alert email with the unknown face image attached.
    Uses basic SMTP (e.g. Gmail with an app password).
    """
    # Encode image to JPEG in memory
    success, buffer = cv2.imencode(".jpg", face_image_bgr)
    if not success:
        print("[ERROR] Failed to encode face image for email.")
        return

    img_bytes = buffer.tobytes()

    msg = EmailMessage()
    msg["Subject"] = "Security Alert: Unknown Person Detected"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.set_content(
        "An unknown person was detected by your security camera.\n"
        "See the attached image for details."
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"unknown_face_{timestamp}.jpg"
    msg.add_attachment(
        img_bytes,
        maintype="image",
        subtype="jpeg",
        filename=filename,
    )

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print("[INFO] Alert email sent.")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")


def detect_motion(prev_gray, curr_gray, motion_threshold=5000):
    """
    Return True if motion is detected between two grayscale frames.
    motion_threshold controls sensitivity (larger = less sensitive).
    """
    frame_delta = cv2.absdiff(prev_gray, curr_gray)
    thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
    thresh = cv2.dilate(thresh, None, iterations=2)
    contours, _ = cv2.findContours(
        thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    for contour in contours:
        if cv2.contourArea(contour) > motion_threshold:
            return True
    return False


def main():
    # --- USER CONFIGURATION (FILL THESE OUT) ---
    known_faces_dir = "known_faces"

    # Gmail SMTP configuration (use an app password, not your main password)
    smtp_server = "smtp.gmail.com"
    smtp_port = 465
    smtp_user = "your_email@gmail.com"       # Gmail address used to send email
    smtp_password = "your_app_password_here"  # App password from Google
    sender_email = "your_email@gmail.com"
    recipient_email = "recipient_email@gmail.com"

    # How often to send alerts for unknown faces (to avoid spamming)
    alert_cooldown_seconds = 60

    # -------------------------------------------

    known_encodings, known_names = load_known_faces(known_faces_dir)

    # Haar cascade for face detection (bundled with OpenCV)
    face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_cascade_path)

    print("[INFO] Starting video capture...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    prev_gray = None
    last_alert_time = datetime.min

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Failed to read frame from camera.")
                break

            # Resize for performance
            frame_resized = cv2.resize(frame, (640, 480))
            gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)

            motion_detected = False
            if prev_gray is not None:
                motion_detected = detect_motion(prev_gray, gray)

            prev_gray = gray

            if motion_detected:
                # Detect faces in the frame where motion was found
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
                )

                for (x, y, w, h) in faces:
                    face_roi_color = frame_resized[y : y + h, x : x + w]

                    # Convert to RGB for face_recognition
                    face_rgb = cv2.cvtColor(face_roi_color, cv2.COLOR_BGR2RGB)
                    encodings = face_recognition.face_encodings(face_rgb)

                    if len(encodings) == 0:
                        continue

                    face_encoding = encodings[0]

                    name = "Unknown"
                    if known_encodings:
                        matches = face_recognition.compare_faces(
                            known_encodings, face_encoding, tolerance=0.5
                        )
                        face_distances = face_recognition.face_distance(
                            known_encodings, face_encoding
                        )

                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_names[best_match_index]

                    # Draw box and label on frame
                    cv2.rectangle(
                        frame_resized, (x, y), (x + w, y + h), (0, 255, 0), 2
                    )
                    cv2.putText(
                        frame_resized,
                        name,
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    # If unknown and cooldown passed, send alert email
                    if name == "Unknown":
                        now = datetime.now()
                        if now - last_alert_time >= timedelta(
                            seconds=alert_cooldown_seconds
                        ):
                            print("[INFO] Unknown face detected, sending email alert...")
                            send_alert_email(
                                face_roi_color,
                                smtp_server,
                                smtp_port,
                                smtp_user,
                                smtp_password,
                                sender_email,
                                recipient_email,
                            )
                            last_alert_time = now

            # Show the video feed with annotations
            cv2.imshow("Security Monitor", frame_resized)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                print("[INFO] Quitting...")
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

