# ✋ Gesture-Control System

This project enables **hand gesture-based control** using **MediaPipe** and **OpenCV**. It supports multiple modes such as **Slides**, **Volume**, **Air Canvas**, **Virtual Keyboard**, **Virtual Mouse**, and **Danger Sign Detection** — all working in real-time through your webcam.

---

## 🧠 Features

* **Slides**: Navigate presentation slides using hand gestures.
* **Volume**: Adjust system volume by changing the distance between thumb and index finger.
* **Air Canvas**: Draw on a virtual canvas with your index finger; pick colors from an on-screen palette.
* **Virtual Keyboard**: Type by hovering your fingertip over transparent keys; includes backspace and space.
* **Virtual Mouse**: Move the system mouse with your hand and perform click gestures.
* **Danger Detection**: Detect danger-related gestures (Fist, Open Palm, V Sign, Thumbs Up) and show alerts.

---

## ⚙️ Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/gesture-control.git
cd gesture-control
```

### 2. Create & Activate a Virtual Environment

#### Windows

```bash
python -m venv venv
venv/Scripts/activate
```

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies (from `requirements.txt`)

```bash
pip install -r requirements.txt
```

**Example `requirements.txt`**

```
opencv-python
mediapipe
numpy
pyautogui
pycaw
comtypes
```

> On non-Windows systems `pycaw` can be omitted (volume control will still show a HUD but won't change system volume).

---

## ▶️ Run the Application

```bash
python main.py
```

Make sure your webcam is connected and accessible. The app creates a GUI window showing the camera feed with overlays for the active mode.

---

## 📂 Project Structure

```
gesture-control/
├── main.py                 # Main entry point (mode switcher & loop)
├── requirements.txt
├── README.md
├── modes/                  # Mode modules
│   ├── slides.py
│   ├── volume.py
│   ├── canvas.py
│   ├── keyboard.py
│   ├── mouse.py
│   └── danger.py
└── utils/                  # optional helpers
    └── helpers.py
```

---

## 🧩 Libraries & Why They Are Used

* **opencv-python (cv2)** — capture webcam frames, draw UI elements and text, show window.
* **mediapipe** — fast and robust hand landmark detection (21 keypoints per hand).
* **numpy** — efficient numerical operations and array handling for frames/geometry.
* **pyautogui** — emulate keyboard and mouse events for Slides, Keyboard, and Mouse modes.
* **pycaw** — Windows Core Audio control for changing system volume (optional; Windows-only).
* **comtypes** — dependency used by Pycaw to interface with Windows COM APIs.
* **math / time** — simple helpers for geometry and timing/cooldowns.

---

## 🎮 Mode Controls & Gestures (complete)

> **Keyboard shortcuts** to switch modes while the app is running:
>
> * `1` → SLIDES
> * `2` → VOLUME
> * `3` → CANVAS
> * `4` → KEYBOARD
> * `5` → MOUSE
> * `6` → DANGER
> * `ESC` → Quit
> * `X` (when in Canvas) → Clear canvas

### 1) SLIDES (Presentation Control)

* **How it works**: MediaPipe handedness or position is used. Typical mapping used in this project:

  * **Right hand** detected → *Next slide* (presses keyboard `right` via PyAutoGUI)
  * **Left hand** detected → *Previous slide* (presses keyboard `left`)
* **Alternative fallback**: If handedness is unstable, the code can use the index fingertip horizontal position: left third = previous, right third = next.
* **Tips**: Hold your hand steady briefly after triggering to avoid rapid repeated events (cooldown present).

### 2) VOLUME

* **How it works**: Distance between thumb tip and index fingertip is mapped to 0–100% volume.

  * **Close** fingers → lower volume
  * **Spread** fingers → higher volume
* **System integration**: If `pycaw` is available (Windows), this will set the system master volume.
* **HUD**: A volume bar and percentage are shown on-screen when the mode is active.

### 3) CANVAS (Air Canvas)

* **How it works**:

  * **Index finger up alone** → draw (follows index fingertip)
  * **Index + Middle up** → pause / stop drawing
  * **Hover over palette** at the top to pick color (hover for a short hold time)
  * **Palm hold** (all five fingers up for a short duration) → clear canvas
  * **Mouse click** (optional) can also change palette
* **Palette**: A horizontal bar with color boxes appears below the header; the current color swatch shows selected color.
* **Persistence**: Drawings are kept on a separate canvas overlay so they persist while you move your hand.

### 4) KEYBOARD (Virtual Keyboard)

* **How it works**: Transparent on-screen keyboard grid is shown.

  * **Index fingertip hover** over a key for a short dwell time (e.g., 0.5s) triggers a press.
  * The special key `<` acts as Backspace.
  * Keyboard shows typed text in a small textbox above the keys.
* **Integration**: When a key is confirmed the script uses `pyautogui.press()` to emit the keystroke to the OS or app in focus.
* **Sizing**: Keyboard is laid out relative to the window; you can tweak `TOP_LEFT`, `KEY_SIZE`, and spacing in `keyboard.py` to fit your camera resolution.

### 5) MOUSE (Virtual Mouse)

* **How it works**:

  * **Move**: Map normalized index fingertip position to screen coordinates and move the mouse via `pyautogui.moveTo()`.
  * **Left Click**: Pinch gesture (thumb + index together) or a specific hold can simulate left click via `pyautogui.click()`.
  * **Right Click / Scroll**: (placeholders) - can be added later (e.g., two-finger hold for right-click).
* **Safety**: `pyautogui.FAILSAFE = False` may be set in code; be careful — you can re-enable if needed.

### 6) DANGER (Danger Sign Detection)

* **How it works**: Recognizes and labels the following gestures and displays the meaning on-screen:

  * **Fist** → `FIST (DANGER)`
  * **Open Palm** → `OPEN PALM (SAFE)`
  * **V Sign** → `V SIGN (VICTORY)`
  * **Thumbs Up** → `THUMBS UP (DISTRESS)`
* **Detection method**: Finger-up/down logic using landmark comparisons; includes small distance checks to make V sign more reliable.
* **Alerting**: The detected label is shown on-screen; you can also add sound or color flash for stronger alerts.

---

## 🧰 Troubleshooting & Tips

* **Lighting**: Good front lighting significantly improves landmark detection.
* **Background**: Plain backgrounds help; busy patterns may reduce accuracy.
* **Hand position**: Keep hand mostly facing the camera and within the frame.
* **Stability**: Hold gestures for ~0.5s to let the app register them (especially for keyboard hover and palette selection).
* **Permissions**: On some OSes, `pyautogui` may need accessibility or input control permissions.

---

## 🚀 Next Steps / Improvements

* Add multi-hand interactions (left for mouse, right for keyboard).
* Train ML models for more complex or subtle gestures.
* Add audible alerts (beep/siren) for danger gestures.
* Improve keyboard layout responsiveness and add modifier keys (Shift, Ctrl).

---

## 📝 License

MIT License — feel free to use and adapt.

---


