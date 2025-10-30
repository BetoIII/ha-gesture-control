# Setup Guide - HA Gesture Control

This guide will walk you through setting up the HA Gesture Control system to control your Home Assistant devices using hand gestures.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Home Assistant Configuration](#home-assistant-configuration)
5. [MediaPipe Model Download](#mediapipe-model-download)
6. [Configuration](#configuration)
7. [Running the System](#running-the-system)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Hardware
- **Computer**: Linux, macOS, or Windows
- **Webcam**: Any USB or built-in webcam (720p or higher recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **CPU**: Modern multi-core processor (gesture recognition is CPU-intensive)

### Software
- **Python**: 3.10 or higher
- **Home Assistant**: 2023.x or later with MCP Server integration
- **Web Browser**: Chrome, Firefox, or Safari (latest version)
- **Network**: Local network access to Home Assistant instance

---

## Prerequisites

### 1. Home Assistant Setup

You must have Home Assistant running with the MCP Server integration installed.

**Install MCP Server Integration:**

1. Navigate to Home Assistant Settings → Integrations
2. Click "Add Integration"
3. Search for "Model Context Protocol (MCP) Server"
4. Follow the installation prompts
5. Note the MCP endpoint URL (usually `http://YOUR_HA_IP:8123/mcp_server/sse`)

### 2. Long-Lived Access Token

Generate a long-lived access token for API authentication:

1. Navigate to your Home Assistant profile: `http://YOUR_HA_IP:8123/profile`
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Give it a name (e.g., "Gesture Control")
5. Copy the token (you won't be able to see it again!)

### 3. Expose Entities

Expose the entities you want to control via gestures:

1. Navigate to Settings → Voice assistants → Expose
2. Select the entities you want to control (e.g., `light.9_kitchen_shelf_lamp`)
3. Save changes

---

## Installation

### 1. Clone the Repository

```bash
cd /your/desired/location
git clone <repository-url>
cd ha-gesture-control
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all Python dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

**Expected packages:**
- flask (3.0.0)
- flask-socketio (5.3.5)
- mediapipe (0.10.21)
- opencv-python (4.8.1.78)
- numpy (1.26.4)
- pyyaml (6.0.1)
- mcp (0.9.0)
- httpx (0.25.2)

---

## Home Assistant Configuration

### 1. Verify MCP Server

Test that your MCP server is accessible:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://YOUR_HA_IP:8123/api/

# Should return: {"message": "API running."}
```

### 2. Test Entity Access

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://YOUR_HA_IP:8123/api/states/light.9_kitchen_shelf_lamp

# Should return entity state JSON
```

---

## MediaPipe Model Download

The gesture recognizer requires a pre-trained MediaPipe model file.

### Download the Model

```bash
cd gesture_recognition

# Download using wget
wget https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task

# Or using curl
curl -o gesture_recognizer.task \
  https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task

cd ..
```

**Verify the file exists:**
```bash
ls -lh gesture_recognition/gesture_recognizer.task
# Should show ~10MB file
```

---

## Configuration

### 1. Create Environment File

```bash
# Copy example environment file
cp .env.example .env

# Edit with your favorite editor
nano .env
```

### 2. Configure Environment Variables

Edit `.env` and set the following:

```bash
# Home Assistant Configuration
HA_TOKEN=your_long_lived_access_token_here
HA_MCP_URL=http://localhost:8123/mcp_server/sse
HA_BASE_URL=http://localhost:8123

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Gesture Recognition
GESTURE_CONFIDENCE_THRESHOLD=0.8
GESTURE_COOLDOWN_SECONDS=2

# Camera Configuration
CAMERA_INDEX=0
CAMERA_WIDTH=640
CAMERA_HEIGHT=480
CAMERA_FPS=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/gesture_control.log
```

**Important:** Replace `your_long_lived_access_token_here` with your actual token!

### 3. Configure Gesture Mappings

Edit `config/gesture_config.yaml` to customize gesture-to-device mappings.

**Example: Add a new gesture**

```yaml
gesture_mappings:
  - name: "Living Room Light On"
    gesture: "Open_Palm"
    hand: "Right"
    confidence: 0.8
    action:
      entity_id: "light.living_room"
      service: "turn_on"
      data: {}
```

**Available Gestures:**
- `Closed_Fist` (✊) - Recommended for "Off" actions
- `Open_Palm` (✋) - Recommended for "On" actions
- `Pointing_Up` (☝️) - Recommended for "Increase" actions
- `Thumb_Down` (👎) - Recommended for "Decrease" actions
- `Thumb_Up` (👍) - Recommended for positive actions
- `Victory` (✌️) - Recommended for alternate modes
- `ILoveYou` (🤟) - Recommended for special actions

---

## Running the System

The system has three components that need to run together:

### 1. Start Flask Web Server

In terminal 1:

```bash
cd ha-gesture-control
source venv/bin/activate  # If not already activated

cd web_server
python app.py
```

**Expected output:**
```
INFO - Starting Flask server on 0.0.0.0:5000
INFO - Debug mode: False
```

### 2. Start Gesture Recognition

In terminal 2:

```bash
cd ha-gesture-control
source venv/bin/activate

cd gesture_recognition
python gesture_stream.py
```

**Expected output:**
```
INFO - MediaPipe initialized successfully
INFO - Camera 0 initialized successfully
INFO - Connected to socket localhost:5555
INFO - Gesture recognition running
```

### 3. Start Goose Controller

In terminal 3:

```bash
cd ha-gesture-control
source venv/bin/activate

cd goose_controller
python main.py
```

**Expected output:**
```
============================================================
HA Gesture Control - Initializing
============================================================
INFO - Configuration loaded successfully from gesture_config.yaml
INFO - Home Assistant connection successful
INFO - Starting socket server on localhost:5555...
============================================================
HA Gesture Control - Running
============================================================
```

### 4. Access Web Interface

Open your web browser and navigate to:

```
http://localhost:5000
```

You should see the HA Gesture Control interface!

---

## Testing the Installation

### 1. Test Camera

1. Enable gesture mode using the toggle switch
2. Verify your camera feed appears
3. Check that hand landmarks are drawn when you show your hand

### 2. Test Gesture Recognition

1. Make an "Open Palm" gesture with your right hand
2. Hold for 1 second
3. Check the detection panel appears showing the gesture name and confidence

### 3. Test Home Assistant Integration

1. Make the gesture mapped to your test device
2. Check for toast notification showing success
3. Verify your device actually changes state in Home Assistant

---

## Troubleshooting

### Camera Not Working

**Problem:** "Camera not available" error

**Solutions:**
1. Check camera permissions (browser may need permission)
2. Verify camera index in `.env` (try CAMERA_INDEX=1 if 0 doesn't work)
3. Test camera with: `python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"`
4. Close other applications using the camera (Zoom, Skype, etc.)

### Connection Failed

**Problem:** "Failed to connect to Home Assistant"

**Solutions:**
1. Verify Home Assistant is running: `curl http://YOUR_HA_IP:8123/api/`
2. Check token is correct in `.env` file
3. Ensure network connectivity to Home Assistant
4. Check firewall rules

### Gestures Not Triggering Actions

**Problem:** Gestures detected but actions don't execute

**Solutions:**
1. Check entity is exposed in Home Assistant (Settings → Voice assistants → Expose)
2. Verify entity ID in `config/gesture_config.yaml` matches exactly
3. Check Home Assistant logs for errors
4. Test service call manually in Home Assistant Developer Tools

### Low Confidence Scores

**Problem:** Gestures detected with low confidence (<0.8)

**Solutions:**
1. Improve lighting conditions
2. Position yourself 1-2 meters from camera
3. Make gestures clearly and deliberately
4. Lower `GESTURE_CONFIDENCE_THRESHOLD` in `.env` (try 0.7)

### Python Package Errors

**Problem:** Import errors or missing packages

**Solutions:**
1. Ensure virtual environment is activated
2. Reinstall packages: `pip install -r requirements.txt --force-reinstall`
3. Check Python version: `python --version` (should be 3.10+)

---

## Next Steps

Once everything is working:

1. Read [Usage Guide](usage.md) for detailed usage instructions
2. Customize gesture mappings in `config/gesture_config.yaml`
3. Explore advanced features in the web interface
4. Set up automatic startup (systemd/launchd) for production use

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs: `logs/gesture_control.log`
2. Enable debug logging: Set `LOG_LEVEL=DEBUG` in `.env`
3. Review Home Assistant logs
4. Open an issue on GitHub with logs and error messages

---

**Congratulations!** Your gesture control system is now set up and ready to use! 🎉
