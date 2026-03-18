"""
Face Comparison
Compares two face images to determine if they are the same person.
"""
from pathlib import Path

import cv2


def compare_faces(image1_input, image2_input, tolerance=0.6):
    """
    Compare two face images and determine if they are the same person.
py -3.12 -m pip install opencv-python ultralytics

    Uses DeepFace when available (Python 3.12+), otherwise OpenCV fallback.

    Args:
        image1_input: Path to first image (str) OR numpy array (BGR).
        image2_input: Path to second image (str) OR numpy array (BGR).
        tolerance: DeepFace: distance threshold (lower=stricter). OpenCV: similarity threshold.

    Returns:
        dict with "same_person", "confidence", "message", "error".
    """
    try:
        from deepface import DeepFace
        return _compare_faces_deepface(image1_input, image2_input, tolerance)
    except ImportError:
        return _compare_faces_opencv(image1_input, image2_input, tolerance)


def _compare_faces_deepface(image1_input, image2_input, tolerance=0.6):
    """Compare using DeepFace (requires TensorFlow, use Python 3.12)."""
    import tempfile
    path1 = _ensure_path(image1_input)
    path2 = _ensure_path(image2_input)
    if path1 is None or path2 is None:
        return {"same_person": False, "confidence": 0.0, "message": "Could not load images.", "error": "Image load failed"}

    try:
        from deepface import DeepFace
        result = DeepFace.verify(path1, path2, model_name="Facenet", enforce_detection=True)
    except Exception as e:
        err = str(e).lower()
        if "no face" in err or "face could not be detected" in err:
            return {"same_person": False, "confidence": 0.0, "message": "No face found in one or both images.", "error": None}
        return {"same_person": False, "confidence": 0.0, "message": str(e), "error": str(e)}
    finally:
        _cleanup_temp(path1, image1_input)
        _cleanup_temp(path2, image2_input)

    same = result["verified"]
    distance = result.get("distance", 0)
    confidence = 1.0 - min(distance, 1.0) if same else max(0, 1.0 - distance)
    return {
        "same_person": bool(same),
        "confidence": round(float(confidence), 2),
        "distance": round(float(distance), 4),
        "message": "Same person." if same else "Different person.",
        "error": None,
    }


def _ensure_path(input_val):
    """Return file path; if numpy array, save to temp file."""
    import tempfile, os
    if isinstance(input_val, str) and Path(input_val).exists():
        return str(input_val)
    img = _load_image(input_val)
    if img is None:
        return None
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    cv2.imwrite(path, img)
    return path


def _cleanup_temp(path, original_input):
    if not isinstance(original_input, str) and path and Path(path).exists():
        try:
            Path(path).unlink()
        except OSError:
            pass


def _load_image(input_val):
    """Load image from path or return numpy array as-is (BGR)."""
    if isinstance(input_val, str):
        path = Path(input_val)
        if not path.exists():
            return None
        img = cv2.imread(str(path))
        return img
    return input_val


def _compare_faces_opencv(image1_input, image2_input, tolerance=0.5):
    """Compare faces using OpenCV Haar cascade + ORB features + histogram."""
    img1 = _load_image(image1_input)
    img2 = _load_image(image2_input)
    if img1 is None or img2 is None:
        return {
            "same_person": False,
            "confidence": 0.0,
            "message": "Could not load one or both images.",
            "error": "Image load failed",
        }

    cascade_path = Path(cv2.__file__).parent / "data" / "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(str(cascade_path))
    if cascade.empty():
        return {
            "same_person": False,
            "confidence": 0.0,
            "message": "OpenCV face detector failed.",
            "error": "Cascade load failed",
        }

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    faces1 = cascade.detectMultiScale(gray1, 1.1, 5, minSize=(30, 30))
    faces2 = cascade.detectMultiScale(gray2, 1.1, 5, minSize=(30, 30))

    if len(faces1) == 0:
        return {"same_person": False, "confidence": 0.0, "message": "No face in first image.", "error": None}
    if len(faces2) == 0:
        return {"same_person": False, "confidence": 0.0, "message": "No face in second image.", "error": None}

    x1, y1, w1, h1 = faces1[0]
    x2, y2, w2, h2 = faces2[0]
    size = (150, 150)  # Larger for better feature extraction
    face1 = cv2.resize(gray1[y1 : y1 + h1, x1 : x1 + w1], size)
    face2 = cv2.resize(gray2[y2 : y2 + h2, x2 : x2 + w2], size)

    # 1) ORB feature matching - robust for same-person verification
    orb = cv2.ORB_create(nfeatures=200)
    kp1, desc1 = orb.detectAndCompute(face1, None)
    kp2, desc2 = orb.detectAndCompute(face2, None)

    if desc1 is None or desc2 is None or len(kp1) < 5 or len(kp2) < 5:
        # Fallback to histogram only
        similarity = _hist_similarity(face1, face2)
    else:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(desc1, desc2)
        matches = sorted(matches, key=lambda m: m.distance)
        # Good matches: distance below threshold
        good = [m for m in matches if m.distance < 50]
        match_ratio = len(good) / max(len(kp1), len(kp2), 1)
        hist_sim = _hist_similarity(face1, face2)
        # Combine: match_ratio (0-1) and hist_sim (0-1), weight toward features
        similarity = 0.7 * min(1.0, match_ratio * 3) + 0.3 * max(0, hist_sim)

    same = similarity > tolerance
    return {
        "same_person": same,
        "confidence": round(max(0, min(1, similarity)), 2),
        "message": "Same person." if same else "Different person.",
        "error": None,
    }


def _hist_similarity(face1, face2):
    """Histogram correlation between two grayscale face patches."""
    hist1 = cv2.calcHist([face1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([face2], [0], None, [256], [0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    return float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL))


if __name__ == "__main__":
    import sys

    img1_path = r"C:\tst.png"
    img2_path = r"C:\tst2.png"

    for p in (img1_path, img2_path):    
        if not Path(p).exists():
            print(f"Error: File not found: {p}")
            sys.exit(1)

    result = compare_faces(img1_path, img2_path)
    print(f"Result: {result['message']}")
    print(f"Same person: {result['same_person']}")
    print(f"Confidence: {result['confidence']}")
    if result.get("distance") is not None:
        print(f"Face distance: {result['distance']}")
