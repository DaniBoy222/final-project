"""
Face and Object Detection
Uses RetinaFace (via DeepFace) for face detection and YOLO (Ultralytics) for object detection.
"""
import cv2
from pathlib import Path

# Fallback Haar cascade path (used only if RetinaFace / DeepFace is unavailable)
_CASCADE_PATH = Path(cv2.__file__).parent / "data" / "haarcascade_frontalface_default.xml"


def _detect_faces_retina(image_input):
    """
    Detect faces using DeepFace + RetinaFace.
    Returns list of dicts in the same format as detect_faces().
    """
    try:
        from deepface import DeepFace
    except ImportError:
        return None  # Signal to caller to fallback

    # Prepare image input
    if isinstance(image_input, str):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_input}")
        img_arg = str(path)
    else:
        img_arg = image_input

    try:
        results = DeepFace.extract_faces(
            img_path=img_arg,
            detector_backend="retinaface",
            enforce_detection=False,
        )
    except Exception:
        # Any runtime error → let caller fallback
        return None

    faces = []
    for r in results or []:
        facial_area = r.get("facial_area") or {}
        x = int(facial_area.get("x", 0))
        y = int(facial_area.get("y", 0))
        w = int(facial_area.get("w", 0))
        h = int(facial_area.get("h", 0))
        if w <= 0 or h <= 0:
            continue
        score = float(r.get("confidence", 1.0))
        faces.append(
            {
                "bbox": [x, y, x + w, y + h],
                "score": score,
                "landmarks": {},  # DeepFace can provide landmarks, but we keep API simple here
            }
        )
    return faces


def _detect_faces_haar(image_input):
    """
    Original OpenCV Haar-based face detector as a safe fallback.
    """
    if isinstance(image_input, str):
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_input}")
        img = cv2.imread(str(path))
    else:
        img = image_input

    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(str(_CASCADE_PATH))
    if cascade.empty():
        return []

    rects = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    faces = []
    for (x, y, w, h) in rects:
        faces.append(
            {
                "bbox": [int(x), int(y), int(x + w), int(y + h)],
                "score": 1.0,
                "landmarks": {},
            }
        )
    return faces


def detect_faces(image_input, min_confidence=0.5):
    """
    Detect faces in an image using RetinaFace (DeepFace).
    Falls back to OpenCV Haar cascade if DeepFace/RetinaFace is not available.

    Args:
        image_input: Path to image (str) OR numpy array (BGR)
        min_confidence: Minimum confidence for RetinaFace detections (0–1). Ignored for Haar.

    Returns:
        list of dicts, each with:
            - "bbox": [x1, y1, x2, y2] (left, top, right, bottom)
            - "score": float (confidence score if available)
            - "landmarks": {} (kept for API compatibility)
        Empty list if no faces or on error.
    """
    # Try RetinaFace first
    faces = _detect_faces_retina(image_input)
    if faces is not None:
        # Optionally filter by min_confidence
        filtered = [f for f in faces if f.get("score", 1.0) >= min_confidence]
        return filtered

    # Fallback to Haar if RetinaFace is not available
    return _detect_faces_haar(image_input)


# Alias so old code using "detect_faces_retina" still works
detect_faces_retina = detect_faces


def detect_objects_yolo(image_input, model_size="n", confidence=0.25, classes=None):
    """
    Detect objects in an image using YOLO (Ultralytics).

    Args:
        image_input: Path to image (str) OR numpy array (BGR).
        model_size: One of "n", "s", "m", "l", "x" for model size (n=nano, fastest).
        confidence: Minimum confidence for detections (0–1). Default 0.25.
        classes: Optional list of class IDs to keep (e.g. [0] for person only). None = all.

    Returns:
        list of dicts, each with:
            - "bbox": [x1, y1, x2, y2]
            - "confidence": float
            - "class_id": int
            - "class_name": str
        Empty list if no detections.
    """
    from ultralytics import YOLO

    # Use YOLOv8 by default (yolo11 may not be in all ultralytics versions)
    model_name = f"yolov8{model_size}.pt"
    model = YOLO(model_name)

    if isinstance(image_input, str):
        results = model.predict(source=image_input, conf=confidence, classes=classes, verbose=False)
    else:
        results = model.predict(source=image_input, conf=confidence, classes=classes, verbose=False)

    detections = []
    for r in results:
        if r.boxes is None:
            continue
        names = r.names or {}
        for box in r.boxes:
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = [int(v) for v in xyxy]
            conf = float(box.conf[0].cpu().numpy())
            cid = int(box.cls[0].cpu().numpy())
            detections.append({
                "bbox": [x1, y1, x2, y2],
                "confidence": conf,
                "class_id": cid,
                "class_name": names.get(cid, f"class_{cid}"),
            })
    return detections


def draw_faces_on_image(image, faces, color=(0, 255, 0), thickness=2):
    """Draw face bounding boxes and optional landmarks on a copy of the image."""
    img = image.copy()
    for face in faces:
        x1, y1, x2, y2 = face["bbox"]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        score = face.get("score", 0)
        cv2.putText(
            img, f"face {score:.2f}", (x1, y1 - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA
        )
        for name, pt in (face.get("landmarks") or {}).items():
            if isinstance(pt, (list, tuple)) and len(pt) >= 2:
                cx, cy = int(pt[0]), int(pt[1])
                cv2.circle(img, (cx, cy), 2, (0, 255, 255), -1)
    return img


def draw_objects_on_image(image, detections, color=(0, 165, 255), thickness=2):
    """Draw YOLO bounding boxes and labels on a copy of the image."""
    img = image.copy()
    for d in detections:
        x1, y1, x2, y2 = d["bbox"]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        label = f"{d.get('class_name', '')} {d.get('confidence', 0):.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(img, (x1, y1 - th - 8), (x1 + tw, y1), color, -1)
        cv2.putText(
            img, label, (x1, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA
        )
    return img


def run_detection_on_image(
    image_path,
    detect_faces=True,
    detect_objects=True,
    min_face_confidence=0.5,
    yolo_confidence=0.25,
    save_path=None,
):
    """
    Run both face detection (OpenCV) and YOLO on an image and optionally save the annotated result.

    Args:
        image_path: Path to the image file.
        detect_faces: If True, run face detection.
        detect_objects: If True, run YOLO.
        min_face_confidence: Threshold for face detection.
        yolo_confidence: Threshold for YOLO.
        save_path: If set, save the drawn image to this path.

    Returns:
        dict with "image" (numpy array), "faces" (list), "objects" (list).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    out = {"image": img, "faces": [], "objects": []}

    if detect_faces:
        out["faces"] = detect_faces(image_path, min_confidence=min_face_confidence)
        img = draw_faces_on_image(img, out["faces"])

    if detect_objects:
        out["objects"] = detect_objects_yolo(image_path, confidence=yolo_confidence)
        img = draw_objects_on_image(img, out["objects"])

    out["image"] = img
    if save_path:
        cv2.imwrite(save_path, img)

    return out


def upload_and_analyze(image_path, save_path="detection_result.png", yolo_confidence=0.25):
    """
    Upload a picture: print what objects are in it, and if there's a person,
    draw a square around each face and save the image.

    How it works:
    1. YOLO scans the image and labels every object (person, car, dog, etc.).
    2. We print each object name and confidence.
    3. If YOLO found a "person", we run face detection and draw green boxes
       around each face, then save the image to save_path.

    Args:
        image_path: Path to your image (e.g. "C:\\Users\\You\\photo.jpg").
        save_path: Where to save the image with face boxes drawn. Default "detection_result.png".
        yolo_confidence: Minimum confidence (0–1) for object detection. Default 0.25.

    Returns:
        dict with "objects", "faces", "image", "has_person".
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Step 1: Detect all objects with YOLO
    objects = detect_objects_yolo(image_path, confidence=yolo_confidence)
    has_person = any(d.get("class_name") == "person" for d in objects)

    # Step 2: Print what objects are in the picture
    print("Objects in this image:")
    if not objects:
        print("  (none detected)")
    else:
        for d in objects:
            print(f"  - {d['class_name']} (confidence: {d['confidence']:.2f})")

    # Step 3: If there's a person, detect faces and draw squares around them
    faces = []
    if has_person:
        faces = detect_faces(image_path)
        img = draw_faces_on_image(img, faces)
        print(f"\nPerson detected → drew a square around {len(faces)} face(s).")
        cv2.imwrite(save_path, img)
        print(f"Saved image with face boxes to: {save_path}")
    else:
        print("\nNo person detected → no face boxes drawn.")

    return {"objects": objects, "faces": faces, "image": img, "has_person": has_person}


# Example usage: upload a picture, print objects, draw face box if human
if __name__ == "__main__":
    import sys

    image_path = r"C:\cover.png"

    if not Path(image_path).exists():
        print("Usage: py face_and_object_detection.py <path_to_your_image>")
        print("Example: py face_and_object_detection.py C:\\Users\\You\\Pictures\\photo.jpg")
        print(f"\nImage not found: {image_path}")
        sys.exit(1)

    print(f"Analyzing: {image_path}\n")
    upload_and_analyze(image_path, save_path="detection_result.png")
