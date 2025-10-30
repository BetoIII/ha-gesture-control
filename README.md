# HA Gesture Control

**Control your Home Assistant smart home devices with hand gestures!**

A comprehensive gesture-based control system that enables touchless interaction with your smart home using MediaPipe hand gesture recognition, connected to Home Assistant through the Model Context Protocol (MCP), with a polished web-based interface for real-time visual feedback.

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

---

## Features

### Core Functionality
- ✋ **Real-time hand gesture recognition** using Google MediaPipe
- 🏠 **Direct Home Assistant integration** via MCP protocol
- 🎮 **7 pre-trained gestures** for intuitive control
- ⚡ **Fast action execution** (<1 second latency)
- 🎯 **Configurable mappings** for any exposed Home Assistant entity

### Web Interface
- 🖥️ **Modern web-based UI** with real-time updates
- 📹 **Live camera feed** with hand landmark visualization
- 🔔 **Visual feedback** (toasts, animations, status indicators)
- 📊 **Gesture detection panel** showing confidence scores
- ⚙️ **Configuration management** via intuitive interface

### Advanced Features
- 🛡️ **Debouncing** to prevent duplicate triggers
- ⏱️ **Hold time validation** for gesture confirmation
- 🎚️ **Configurable thresholds** for confidence and cooldowns
- 👐 **Multi-hand support** (detect up to 2 hands simultaneously)
- 📝 **Comprehensive logging** for debugging

---

## Quick Start

### 1. Install Dependencies

```bash
# Clone repository
git clone <repo-url>
cd ha-gesture-control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Download MediaPipe Model

```bash
cd gesture_recognition
wget https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task
cd ..
```

### 3. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your Home Assistant token
nano .env
```

### 4. Start the System

**Terminal 1: Flask Web Server**
```bash
cd web_server
python app.py
```

**Terminal 2: Gesture Recognition**
```bash
cd gesture_recognition
python gesture_stream.py
```

**Terminal 3: Goose Controller**
```bash
cd goose_controller
python main.py
```

### 5. Open Web Interface

Navigate to `http://localhost:5000` in your browser and enable gesture mode!

---

## Available Gestures

| Gesture | Icon | Recommended Use | Example |
|---------|------|-----------------|---------|
| **Open Palm** | ✋ | Turn ON | Light ON |
| **Closed Fist** | ✊ | Turn OFF | Light OFF |
| **Pointing Up** | ☝️ | Increase | Brightness +20% |
| **Thumb Down** | 👎 | Decrease | Brightness -20% |
| **Thumb Up** | 👍 | Positive Action | Warm White |
| **Victory** | ✌️ | Alternate Mode | Cool White |
| **I Love You** | 🤟 | Special Action | Set Red Color |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                   (Web Browser)                              │
└───────────────┬──────────────────────┬──────────────────────┘
                │ HTTP/WebSocket       │ Hand Gestures
                ▼                      ▼
┌─────────────────────────────────────────────────────────────┐
│             Flask Web Server + Socket.IO                     │
│  - Serves web UI (HTML/CSS/JS)                              │
│  - MJPEG camera stream endpoint                             │
│  - WebSocket for real-time updates                          │
│  - REST API for configuration CRUD                          │
└─────────┬───────────────────────────┬───────────────────────┘
          │ Gesture Events            │ Camera Feed
          ▼                            ▼
┌─────────────────────────────────────────────────────────────┐
│              MediaPipe Gesture Recognition                   │
│  - Detects gestures with confidence scores                  │
│  - Sends events via TCP socket                              │
│  - Generates MJPEG stream with landmarks                    │
└────────────────────┬────────────────────────────────────────┘
                     │ TCP Socket
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                Goose MCP Client/Controller                   │
│  - Receives gesture events                                  │
│  - Applies gesture-to-device mappings                       │
│  - Debouncing and hold time validation                      │
│  - Translates to Home Assistant actions                     │
└────────────────────┬────────────────────────────────────────┘
                     │ MCP Protocol (SSE)
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           Home Assistant MCP Server                          │
│  - Exposes entities via MCP protocol                        │
│  - Executes service calls                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ha-gesture-control/
├── gesture_recognition/      # MediaPipe gesture detection
│   ├── gesture_stream.py     # Main gesture recognizer
│   ├── gesture_recognizer.task  # MediaPipe model (download)
│   └── requirements.txt       # Python dependencies
├── web_server/                # Flask web application
│   ├── app.py                 # Flask entry point
│   ├── camera_feed.py         # MJPEG streaming
│   ├── websocket_handler.py   # Socket.IO handlers
│   ├── templates/
│   │   └── index.html         # Main UI template
│   └── static/
│       ├── css/styles.css     # Custom styles
│       └── js/
│           ├── app.js         # Main frontend logic
│           └── websocket.js   # WebSocket client
├── goose_controller/          # Gesture processing middleware
│   ├── main.py                # Controller entry point
│   ├── gesture_handler.py     # Gesture event processor
│   ├── ha_mcp_client.py       # Home Assistant MCP client
│   ├── config_manager.py      # Configuration management
│   └── debouncer.py           # Debouncing logic
├── config/
│   └── gesture_config.yaml    # Gesture mappings config
├── docs/
│   ├── setup.md               # Setup instructions
│   └── usage.md               # Usage guide
├── requirements.txt           # All Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

---

## Configuration Example

Edit `config/gesture_config.yaml` to customize gesture mappings:

```yaml
gesture_mappings:
  - name: "Kitchen Light On"
    gesture: "Open_Palm"
    hand: "Right"
    confidence: 0.8
    action:
      entity_id: "light.kitchen"
      service: "turn_on"
      data: {}

  - name: "Increase Brightness"
    gesture: "Pointing_Up"
    hand: "Left"
    confidence: 0.8
    action:
      entity_id: "light.kitchen"
      service: "turn_on"
      data:
        brightness_step_pct: 20
```

---

## Requirements

### Hardware
- Computer with webcam (720p or higher)
- Minimum 4GB RAM (8GB recommended)
- Home Assistant instance (local network access)

### Software
- Python 3.10 or higher
- Home Assistant 2023.x+ with MCP Server integration
- Modern web browser (Chrome, Firefox, Safari)

---

## Documentation

- **[Setup Guide](docs/setup.md)** - Complete installation and configuration instructions
- **[Usage Guide](docs/usage.md)** - How to use the system, gestures, and features
- **[Configuration Reference](config/gesture_config.yaml)** - YAML configuration examples

---

## Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Flask web server with Socket.IO
- [x] MediaPipe gesture recognition
- [x] MJPEG camera streaming
- [x] WebSocket communication
- [x] Basic UI with toggle switch

### Phase 2: UI Development ✅
- [x] Side panel with gesture list
- [x] Detection feedback panel
- [x] Toast notifications
- [x] Status indicators
- [x] Camera feed with landmarks

### Phase 3: Home Assistant Integration ✅
- [x] MCP client implementation
- [x] Debouncing logic
- [x] Configuration manager
- [x] Gesture-to-action execution

### Phase 4: Configuration UI (In Progress)
- [ ] REST API for CRUD operations
- [ ] Configuration modal
- [ ] Device auto-discovery
- [ ] Live configuration reload

### Future Enhancements
- [ ] Multi-gesture sequences
- [ ] Context-aware actions (time of day, device state)
- [ ] Voice command integration
- [ ] Mobile-responsive design
- [ ] Dark mode
- [ ] Multi-user support
- [ ] Custom gesture training

---

## Troubleshooting

### Camera Not Working
- Check camera permissions in browser
- Verify camera index in `.env` (try different values)
- Close other apps using the camera

### Connection Failed
- Verify Home Assistant is accessible
- Check token in `.env` is correct
- Ensure MCP Server integration is installed

### Gestures Not Triggering
- Check entity is exposed in Home Assistant
- Verify entity ID matches exactly
- Improve lighting conditions
- Lower confidence threshold

For more help, see [Setup Guide](docs/setup.md) troubleshooting section.

---

## Performance Tips

1. **Lighting**: Face a light source for best recognition
2. **Distance**: Stand 1-2 meters from camera
3. **Clarity**: Make deliberate, clear gestures
4. **Cooldown**: Wait 2 seconds between same gesture
5. **Camera**: Use 720p or higher webcam

---

## Security Considerations

- 🔒 Home Assistant token stored in environment variable (never in code)
- 🌐 Flask server runs on localhost by default
- 🔐 No video recording (all processing is real-time)
- 🎥 Camera access requires browser permission
- 🚫 No data sent to external services

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## License

MIT License - see LICENSE file for details

---

## Acknowledgments

- **MediaPipe** by Google for gesture recognition
- **Home Assistant** for smart home platform
- **Flask** and **Socket.IO** for web framework
- **Tailwind CSS** for UI styling

---

## Support

- **Issues**: Open a GitHub issue
- **Discussions**: Use GitHub Discussions
- **Documentation**: See `docs/` directory

---

## Screenshots

### Main Interface (Gesture Mode Active)
```
┌────────────────────────────────────────────────────────┐
│ HA Gesture Control    [Gesture Mode: ON] [Settings]   │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌──────────────────────────────┐   │
│  │ ● ACTIVE    │  │                              │   │
│  │             │  │  [Camera feed with hand      │   │
│  │ Available:  │  │   landmarks overlay]         │   │
│  │             │  │                              │   │
│  │ ✋ → Light  │  │   ┌──────────────────┐      │   │
│  │    ON       │  │   │ PALM OPEN        │      │   │
│  │             │  │   │ Confidence: 92%  │      │   │
│  │ ✊ → Light  │  │   └──────────────────┘      │   │
│  │    OFF      │  │                              │   │
│  │             │  │                              │   │
│  │ [+ Add]     │  │                              │   │
│  └─────────────┘  └──────────────────────────────┘   │
│                                                         │
├────────────────────────────────────────────────────────┤
│ ● Connected          Last: Kitchen Light ON (2s ago)  │
└────────────────────────────────────────────────────────┘
```

---

**Made with ❤️ for the Home Assistant Community**

**Start controlling your smart home with gestures today!** 👋
