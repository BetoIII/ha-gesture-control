## Usage Guide - HA Gesture Control

This guide explains how to use the HA Gesture Control system to control your smart home devices with hand gestures.

## Table of Contents

1. [Accessing the Web Interface](#accessing-the-web-interface)
2. [Using Gesture Mode](#using-gesture-mode)
3. [Understanding Gestures](#understanding-gestures)
4. [Managing Gesture Mappings](#managing-gesture-mappings)
5. [Visual Feedback](#visual-feedback)
6. [Best Practices](#best-practices)
7. [Advanced Usage](#advanced-usage)

---

## Accessing the Web Interface

### Opening the Interface

1. Ensure all three components are running (Flask server, gesture recognition, Goose controller)
2. Open your web browser
3. Navigate to: `http://localhost:5000`

**For remote access:**
- Use your computer's IP address: `http://YOUR_IP:5000`
- Ensure firewall allows connections on port 5000

### Interface Overview

The web interface consists of several key areas:

```
┌─────────────────────────────────────────────────────┐
│  HA Gesture Control      [Gesture Mode] [Settings]  │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────────┐  ┌────────────────────────────┐  │
│  │ Side Panel   │  │ Camera Feed                │  │
│  │              │  │                            │  │
│  │ - Status     │  │  [Your hand with           │  │
│  │ - Available  │  │   landmarks overlay]       │  │
│  │   Gestures   │  │                            │  │
│  │              │  │  [Detection Panel]         │  │
│  │ [+ Add]      │  │                            │  │
│  └──────────────┘  └────────────────────────────┘  │
│                                                      │
├─────────────────────────────────────────────────────┤
│  [Connection Status]        [Last Action]           │
└─────────────────────────────────────────────────────┘
```

---

## Using Gesture Mode

### Activating Gesture Mode

1. **Toggle Switch**: Click the "Gesture Mode" toggle in the header
   - OFF (gray): System inactive, no gesture recognition
   - ON (blue): System active, gestures will trigger actions

2. **Camera Activation**:
   - When you enable gesture mode, the camera feed automatically starts
   - You should see yourself in the camera feed
   - If prompted, grant camera permissions to your browser

3. **Status Indicator**:
   - Green dot: "Gesture Detection: ACTIVE"
   - Camera status shows "Active" or "Inactive"

### Performing Gestures

**Step-by-step:**

1. **Position Yourself**:
   - Stand 1-2 meters (3-6 feet) from the camera
   - Ensure good lighting (face a light source)
   - Keep your hand clearly visible in the frame

2. **Make the Gesture**:
   - Form the desired gesture with your hand
   - Hold the gesture steady for about 1 second
   - Keep your hand in the camera's view

3. **Wait for Feedback**:
   - Detection panel appears showing gesture name and confidence
   - Camera border flashes (blue: detected, green: action success)
   - Toast notification confirms action execution

4. **Cooldown Period**:
   - After triggering an action, there's a 2-second cooldown
   - Same gesture won't trigger again during cooldown
   - This prevents accidental multiple triggers

### Deactivating Gesture Mode

1. Toggle the "Gesture Mode" switch to OFF
2. Camera feed stops
3. No gestures will trigger actions

---

## Understanding Gestures

### Available Gestures (7 pre-trained)

MediaPipe recognizes these 7 hand gestures:

#### 1. Open Palm (✋)
**Description:** All fingers extended, palm facing camera
**Recommended for:** Turning devices ON
**Example mapping:** Kitchen light ON

**How to perform:**
- Extend all five fingers
- Keep palm flat and facing camera
- Fingers spread slightly apart

#### 2. Closed Fist (✊)
**Description:** All fingers curled into fist
**Recommended for:** Turning devices OFF
**Example mapping:** Kitchen light OFF

**How to perform:**
- Curl all fingers into your palm
- Thumb wrapped around fingers
- Keep fist facing camera

#### 3. Pointing Up (☝️)
**Description:** Index finger extended upward
**Recommended for:** Increasing values (brightness, volume)
**Example mapping:** Increase brightness by 20%

**How to perform:**
- Extend index finger upward
- Keep other fingers curled
- Thumb can be out or tucked

#### 4. Thumb Down (👎)
**Description:** Thumb pointing downward
**Recommended for:** Decreasing values
**Example mapping:** Decrease brightness by 20%

**How to perform:**
- Make a fist
- Extend thumb downward
- Keep palm facing camera

#### 5. Thumb Up (👍)
**Description:** Thumb pointing upward
**Recommended for:** Positive actions, confirmations
**Example mapping:** Set warm white color

**How to perform:**
- Make a fist
- Extend thumb upward
- Keep palm facing camera

#### 6. Victory (✌️)
**Description:** Index and middle fingers extended in V shape
**Recommended for:** Alternate modes, secondary actions
**Example mapping:** Set cool white color

**How to perform:**
- Extend index and middle fingers
- Keep them separated in V shape
- Other fingers curled
- Palm facing camera

#### 7. I Love You (🤟)
**Description:** Thumb, index, and pinky extended
**Recommended for:** Special actions
**Example mapping:** Set red color

**How to perform:**
- Extend thumb, index, and pinky fingers
- Keep middle and ring fingers curled
- Palm facing camera

### Left Hand vs Right Hand

Each gesture can be configured for:
- **Left hand only**: Only left hand triggers the action
- **Right hand only**: Only right hand triggers the action
- **Either hand**: Both hands can trigger the action

**Use cases:**
- Use right hand for primary controls (on/off)
- Use left hand for adjustments (brightness, color)
- This allows simultaneous control of different aspects

---

## Managing Gesture Mappings

### Viewing Current Mappings

When gesture mode is active, the left side panel shows all configured gesture mappings:

```
┌─────────────────────────┐
│ Gesture Detection: ●    │
│ ACTIVE                  │
├─────────────────────────┤
│ Available Gestures:     │
│                         │
│ Open Palm (✋)          │
│ → Turn On Kitchen Light │
│                         │
│ Closed Fist (✊)        │
│ → Turn Off Kitchen Lght │
│                         │
│ Pointing Up (☝️)        │
│ → Increase Brightness   │
│                         │
│ [+ Add Gesture Mapping] │
└─────────────────────────┘
```

### Adding New Mappings

**Option 1: Via Configuration File**

1. Open `config/gesture_config.yaml` in a text editor
2. Add a new mapping under `gesture_mappings`:

```yaml
- name: "Living Room Light On"
  gesture: "Open_Palm"
  hand: "Right"
  confidence: 0.8
  action:
    entity_id: "light.living_room"
    service: "turn_on"
    data: {}
```

3. Save the file
4. Reload configuration (or restart Goose controller)

**Option 2: Via Web Interface** (Coming in Phase 4)

1. Click "+ Add Gesture Mapping" button
2. Select gesture from dropdown
3. Choose hand (Left/Right/Either)
4. Select device from Home Assistant entities
5. Choose action/service
6. Save

### Editing Mappings

**Via Configuration File:**

1. Open `config/gesture_config.yaml`
2. Find the mapping you want to edit
3. Modify the fields:
   - `name`: Display name
   - `gesture`: Gesture name (must match available gestures)
   - `hand`: Left, Right, or Either
   - `confidence`: Minimum confidence (0.0-1.0)
   - `action.entity_id`: Device entity ID
   - `action.service`: Service name (turn_on, turn_off, etc.)
   - `action.data`: Additional parameters
4. Save and reload configuration

### Removing Mappings

1. Open `config/gesture_config.yaml`
2. Delete the entire mapping block (including all fields)
3. Save and reload configuration

---

## Visual Feedback

The system provides multiple types of visual feedback:

### 1. Detection Panel

**When:** Gesture is detected
**Location:** Centered at top of camera feed
**Duration:** 2 seconds
**Shows:**
- Gesture name (e.g., "PALM OPEN")
- Confidence percentage (e.g., "90%")

### 2. Camera Border Flash

**When:** Gesture detected or action executed
**Location:** Border around camera feed
**Duration:** 500ms
**Colors:**
- **Blue**: Gesture detected
- **Green**: Action executed successfully
- **Red**: Action failed

### 3. Toast Notifications

**When:** Action executed
**Location:** Top-right corner
**Duration:** 5 seconds
**Types:**
- **Green (✓)**: Success - "Kitchen Light turned ON"
- **Red (✗)**: Error - "Failed to execute action"
- **Yellow (⚠)**: Warning - Connection issues
- **Blue (ℹ)**: Info - System messages

### 4. Status Bar

**When:** Always visible
**Location:** Bottom of screen
**Shows:**
- Connection status (Connected/Disconnected)
- Last action executed with timestamp

### 5. Hand Landmarks

**When:** Hand detected in frame
**Location:** Overlaid on camera feed
**Shows:**
- 21 hand landmarks connected by lines
- Green lines and points
- Shows all detected hands (up to 2)

---

## Best Practices

### For Optimal Gesture Recognition

1. **Lighting**:
   - Face a light source (window, lamp)
   - Avoid backlighting (light behind you)
   - Use consistent, bright lighting
   - Avoid shadows on your hand

2. **Positioning**:
   - Stand 1-2 meters from camera
   - Keep hand clearly visible in frame
   - Center hand in camera view
   - Don't move hand too quickly

3. **Gesture Clarity**:
   - Make deliberate, clear gestures
   - Hold gesture steady for 1 second
   - Avoid partial or ambiguous gestures
   - Practice each gesture until confident

4. **Cooldown Awareness**:
   - Wait 2 seconds between same gesture
   - Use different gestures for sequential actions
   - Check status bar for last action time

### For Reliable Operation

1. **Camera Care**:
   - Keep camera lens clean
   - Ensure camera is stable (not moving)
   - Check camera permissions in browser

2. **System Maintenance**:
   - Keep gesture mappings organized
   - Test new mappings before relying on them
   - Monitor logs for errors
   - Reload configuration after changes

3. **Network Stability**:
   - Use wired connection when possible
   - Ensure stable Wi-Fi if wireless
   - Check Home Assistant is responsive

---

## Advanced Usage

### Brightness Control

**Absolute Brightness:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    brightness: 200  # 0-255
```

**Brightness Percentage:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    brightness_pct: 75  # 0-100%
```

**Relative Brightness Change:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    brightness_step_pct: 20  # Increase by 20%
```

### Color Control

**RGB Color:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    rgb_color: [255, 0, 0]  # Red
```

**Color Temperature (Mireds):**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    color_temp: 370  # Warm white (370 mireds)
```

**Color Temperature (Kelvin):**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    kelvin: 3000  # Warm white (3000K)
```

**Named Colors:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    color_name: "red"  # Named color
```

### Transition Effects

**Smooth Transition:**
```yaml
action:
  entity_id: "light.living_room"
  service: "turn_on"
  data:
    brightness: 255
    transition: 3  # 3 seconds
```

### Multiple Entity Control

Control multiple entities with one gesture by using groups:

1. Create a group in Home Assistant
2. Use the group entity ID in your mapping

```yaml
action:
  entity_id: "group.living_room_lights"
  service: "turn_on"
```

### Scene Activation

```yaml
action:
  entity_id: "scene.movie_time"
  service: "turn_on"
```

### Switch Control

Works the same as lights:

```yaml
action:
  entity_id: "switch.coffee_maker"
  service: "turn_on"
```

---

## Troubleshooting During Use

### Gestures Not Being Detected

- Check hand is clearly visible in camera
- Improve lighting conditions
- Make gesture more deliberate
- Check detection panel shows gesture name

### Actions Not Executing

- Verify device is exposed in Home Assistant
- Check entity ID is correct
- Test device manually in Home Assistant
- Check status bar for error messages

### Low Confidence Scores

- Adjust `GESTURE_CONFIDENCE_THRESHOLD` in `.env`
- Practice gesture until consistent
- Improve camera angle and lighting

---

## Keyboard Shortcuts

- **Space**: Toggle gesture mode (when interface has focus)
- **Esc**: Close modal dialogs
- **F11**: Fullscreen mode (browser)

---

## Tips and Tricks

1. **Quick On/Off**: Use right hand open palm (on) and closed fist (off) for fastest control

2. **Brightness Presets**: Map multiple gestures to different brightness levels

3. **Color Scenes**: Map gestures to different color temperatures for mood lighting

4. **Safety**: Keep a traditional switch accessible for critical lights

5. **Guest Mode**: Disable gesture mode when others might trigger it accidentally

---

**Happy Gesturing!** 👋
