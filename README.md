<<<<<<< HEAD
## Security Monitor Script

This project provides a simple security camera script that:

- **Detects movement** using frame differencing on a webcam feed.
- **Detects faces** in the area where movement occurred.
- **Compares faces** against a folder of known faces.
- **Sends an email via Gmail** with a snapshot of the face if it is unknown.

The "database" of faces is simply a directory of labeled images for now.

### 1. Install dependencies

In a Python 3 virtual environment, run:

```bash
pip install -r requirements.txt
```

> Note: `face-recognition` depends on `dlib`, which may require build tools on Windows. You can search for prebuilt `dlib` wheels for your Python/Windows version if needed.

### 2. Prepare known faces

Create a folder named `known_faces` next to `security_monitor.py`, and put one or more images inside:

- **File name** (without extension) becomes the **person's name**.
- Supported formats: `.jpg`, `.jpeg`, `.png`

Example:

- `known_faces/Alice.jpg`
- `known_faces/Bob.png`

### 3. Configure Gmail settings

Gmail no longer allows basic username/password login for normal accounts. You should:

- Enable **2-Step Verification** on your Google account.
- Create an **App Password** (for "Mail" on "Windows" or similar).
- Use that app password in `security_monitor.py`.

Open `security_monitor.py` and set:

- **`smtp_user`** and **`sender_email`**: your Gmail address.
- **`smtp_password`**: the app password you generated.
- **`recipient_email`**: where alerts should be sent.

### 4. Run the script

From the project directory:

```bash
python security_monitor.py
```

- A window called `Security Monitor` will open.
- Press **`q`** to quit.

### 5. How it works (high level)

- **Motion detection**: compares the current grayscale frame to the previous one; if the difference is large enough, movement is assumed.
- **Face detection**: uses OpenCV's Haar cascade to locate faces.
- **Face recognition**: uses the `face_recognition` library to encode faces and compare them to encodings for images in `known_faces`.
- **Email alerts**: if the best match is not good enough, the face is treated as **Unknown** and an alert email with the face image attached is sent (rate-limited by a cooldown timer).

=======
## Security Monitor Script

This project provides a simple security camera script that:

- **Detects movement** using frame differencing on a webcam feed.
- **Detects faces** in the area where movement occurred.
- **Compares faces** against a folder of known faces.
- **Sends an email via Gmail** with a snapshot of the face if it is unknown.

The "database" of faces is simply a directory of labeled images for now.

### 1. Install dependencies

In a Python 3 virtual environment, run:

```bash
pip install -r requirements.txt
```

> Note: `face-recognition` depends on `dlib`, which may require build tools on Windows. You can search for prebuilt `dlib` wheels for your Python/Windows version if needed.

### 2. Prepare known faces

Create a folder named `known_faces` next to `security_monitor.py`, and put one or more images inside:

- **File name** (without extension) becomes the **person's name**.
- Supported formats: `.jpg`, `.jpeg`, `.png`

Example:

- `known_faces/Alice.jpg`
- `known_faces/Bob.png`

### 3. Configure Gmail settings

Gmail no longer allows basic username/password login for normal accounts. You should:

- Enable **2-Step Verification** on your Google account.
- Create an **App Password** (for "Mail" on "Windows" or similar).
- Use that app password in `security_monitor.py`.

Open `security_monitor.py` and set:

- **`smtp_user`** and **`sender_email`**: your Gmail address.
- **`smtp_password`**: the app password you generated.
- **`recipient_email`**: where alerts should be sent.

### 4. Run the script

From the project directory:

```bash
python security_monitor.py
```

- A window called `Security Monitor` will open.
- Press **`q`** to quit.

### 5. How it works (high level)

- **Motion detection**: compares the current grayscale frame to the previous one; if the difference is large enough, movement is assumed.
- **Face detection**: uses OpenCV's Haar cascade to locate faces.
- **Face recognition**: uses the `face_recognition` library to encode faces and compare them to encodings for images in `known_faces`.
- **Email alerts**: if the best match is not good enough, the face is treated as **Unknown** and an alert email with the face image attached is sent (rate-limited by a cooldown timer).

>>>>>>> 8642a2efbfc84bdb1545ee2dc104b2bbbba5dbd7
