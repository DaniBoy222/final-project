import cv2
from email.message import EmailMessage
import smtplib, ssl

# -----------------------------
# CONFIGURE THESE
# -----------------------------
sender_email = "dani.mantin@gmail.com"       # your Gmail address
receiver_email = "danielmantin678@gmail.com" # recipient
password = "zoca rtxv joji uvyf"         # Gmail App Password
subject = "Camera Capture Test"
# -----------------------------

# 1. Capture one frame from the camera
cam = cv2.VideoCapture(0)  # 0 = default webcam
ret, frame = cam.read()
cam.release()

if not ret:
    raise RuntimeError("Failed to grab frame from camera")

# 2. Encode the frame to PNG in memory
success, buffer = cv2.imencode(".png", frame)
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
"commit works"
