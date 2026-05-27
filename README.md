# KlipperScreen - TopTable Edition

A customized version of KlipperScreen with enhanced UI/UX design optimized for the TopTable theme, providing a modern and intuitive touchscreen interface for [Klipper](https://github.com/kevinOConnor/klipper) 3D printer control.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [TopTable Customization](#toptable-customization)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Developer Guide](#developer-guide)
- [Credits](#credits)

---

## Overview

**KlipperScreen** is a touchscreen GUI that interfaces with [Klipper](https://github.com/kevinOConnor/klipper) via [Moonraker](https://github.com/arksine/moonraker). This **TopTable Edition** provides a comprehensive redesign of the user interface with improved visual aesthetics, better touch optimization, and a modern color scheme.

### Core Capabilities

- 🌐 **Remote Access**: Run on any device and configure printer IP addresses for remote control
- 📱 **Hardware Flexible**: Compatible with touchscreens, tablets, and remote desktop applications
- 🎨 **TopTable UI**: Modern, clean interface with optimized touch controls
- ⚙️ **Moonraker Integration**: Real-time printer control and monitoring via Moonraker API

### Documentation

📚 [Original KlipperScreen Documentation](https://klipperscreen.readthedocs.io/en/latest/)

---

## Key Features

### Core KlipperScreen Features

| Feature | Description |
|---------|-------------|
| **Print Management** | Start, pause, resume, and stop prints with real-time progress tracking |
| **Temperature Control** | Monitor and adjust extruder and chamber temperatures |
| **Motion Control** | Move axes, extrude/retract, adjust speed and acceleration |
| **File Browser** | Browse and select files from network storage with metadata preview |
| **Macro Execution** | Execute custom G-code macros with one tap |
| **Camera Integration** | View live camera feeds during printing |
| **Network Management** | Configure WiFi and network settings directly from the interface |

### TopTable Customization Enhancements

- ✨ **Modern Color Scheme**: Clean white background with carefully selected accent colors
- 🎯 **Touch-Optimized**: Large buttons (204px height) and generous spacing for reliable touch input
- 🎨 **Professional Styling**: Rounded corners (10px radius) and smooth transitions
- 📝 **Custom Typography**: Premium fonts (ABC Ginto, Pretendard Variable) for enhanced readability
- 🌈 **Color-Coded Interface**: Visual hierarchy with distinct color buttons for different actions
- 🔄 **Responsive Layout**: Adapts to different screen sizes and orientations

### Special Panels

| Panel | Purpose |
|-------|---------|
| **Replace FoodInk** | Step-by-step material loading/unloading workflow with configurable capacity presets (25/50/75/100ml) |
| **Auto Leveling** | Automatic bed leveling and nozzle offset calibration |

---

## TopTable Customization

### Design Philosophy

The TopTable theme focuses on **usability and aesthetics** with a touch-first approach:

- **Color Palette**:
  - Primary Background: White (#ffffff)
  - Buttons: Light Gray (#dfdfdf) with hover states
  - Accent Yellow: #f5fd87 (action buttons)
  - Accent Blue: #b4c2fa (secondary actions)
  - Success Green & Error Red for status indicators

- **Typography**: 
  - Primary: ABC Ginto Normal
  - Secondary: Pretendard Variable
  - Optimized for 1080p+ displays with clear readability

- **Visual Style**:
  - Rounded corners (10px border-radius) for modern appearance
  - Flat design with subtle shadows for depth
  - Clear focus states for keyboard navigation support

### Theme Files

Located in `styles/toptable/`:

```
styles/toptable/
├── style.conf        # Graph colors configuration (extruder, bed, fan, sensor)
├── style.css         # Main CSS styling rules
├── images/           # Theme icons and assets
└── images_bu/        # Backup image resources
```

#### style.conf Structure

Defines color schemes for different temperature graph types:

```json
{
  "graph_colors": {
    "extruder": {"colors": ["#ff6b6b", ...]},
    "bed": {"colors": ["#4ecdc4", ...]},
    "fan": {"colors": ["#45b7d1", ...]},
    "sensor": {"colors": ["#96ceb4", ...]}
  }
}
```

#### style.css Highlights

- Button styling with visual feedback (active, hover, disabled states)
- Custom scrollbar appearance
- Modal and dialog styling
- Responsive grid layouts for different screen sizes
- Animation and transition definitions

---

## Project Structure

### Directory Overview

```
KlipperScreen/
├── screen.py                      # Main window and UI logic
├── ks_includes/                   # Core modules and utilities
│   ├── config.py                  # Configuration management
│   ├── printer.py                 # Printer state management
│   ├── KlippyWebsocket.py        # WebSocket connection
│   ├── KlippyRest.py             # REST API client
│   ├── functions.py               # Utility functions (DPMS, logging, etc.)
│   └── widgets/                   # Custom GTK widgets
├── panels/                        # Screen panels
│   ├── main_menu.py              # Main menu panel
│   ├── job_status.py             # Print monitoring
│   ├── temperature.py            # Temperature control
│   ├── move.py                   # Axis movement
│   ├── extrude.py                # Extrusion control
│   ├── bed_mesh.py               # Bed calibration
│   ├── zcalibrate.py             # Z-offset calibration
│   ├── input_shaper.py           # Input shaper configuration
│   ├── replacefoodink.py         # FoodInk material management
│   └── [other panels...]         # Additional functionality panels
├── styles/                        # Theme and styling
│   ├── base.css                  # Base CSS rules
│   ├── base.conf                 # Base color configuration
│   └── toptable/                 # TopTable theme (default)
│       ├── style.css
│       ├── style.conf
│       └── images/
├── docs/                          # Documentation and guides
├── scripts/                       # Installation and utility scripts
└── ks_includes/locales/          # Internationalization (i18n)
    └── [language folders]         # Multi-language support (20+ languages)
```

### Key Components

| File/Module | Purpose |
|------------|---------|
| `screen.py` | Main UI window and panel management |
| `ks_includes/printer.py` | Printer state tracking and updates |
| `ks_includes/KlippyWebsocket.py` | Real-time communication with Moonraker |
| `ks_includes/config.py` | User configuration parsing and management |
| `panels/base_panel.py` | Base class for all screen panels |
| `styles/toptable/` | **TopTable theme (customization point)** |

---

## Developer Guide

### Customizing the TopTable Theme

#### 1. Modify Color Scheme

Edit `styles/toptable/style.conf`:

```json
{
  "graph_colors": {
    "extruder": {
      "colors": ["#ff6b6b", "#ff8e72", "#ffa361"]
    }
  }
}
```

#### 2. Adjust CSS Styling

Edit `styles/toptable/style.css`:

```css
button {
  border-radius: 10px;      /* Adjust button corner radius */
  min-height: 204px;        /* Modify button height */
  background-color: #dfdfdf; /* Change button color */
}

button:hover {
  background-color: #c5c5c5;
}
```

#### 3. Update Theme Assets

Replace images in `styles/toptable/images/` with your custom assets.

### Creating Custom Panels

1. **Create a new panel file** in `panels/`:
   ```python
   # panels/my_custom_panel.py
   from panels.base_panel import BasePanel
   
   class MyCustomPanel(BasePanel):
       def initialize_content(self):
           # Build UI here
           pass
   
   def create_panel(screen, title, **kwargs):
       return MyCustomPanel(screen, title, **kwargs)
   ```

2. **Register in configuration** (`defaults.conf`):
   ```ini
   [menu __main]
   items = main_panel, my_custom, settings
   ```

### Modifying Screen Behavior

Key files for customization:

- `screen.py`: Main window behavior and panel transitions
- `ks_includes/printer.py`: Printer state management
- `ks_includes/functions.py`: Utility functions (DPMS, system calls)
- `ks_includes/config.py`: Configuration parsing logic

---

## Advanced Topics

### Multi-Language Support

KlipperScreen supports 20+ languages. Language files are in `ks_includes/locales/`:

- Supported: English, German, Spanish, French, Italian, Dutch, Polish, Russian, Hebrew, Hungarian, Chinese (Simplified & Traditional), Japanese, Korean, Turkish, Ukrainian, and more
- Currently, only English and Korean are supported

Set language in `KlipperScreen.conf`:
```ini
language = en
```

### Troubleshooting

Common issues and solutions can be found in `docs/Troubleshooting/`:

- Network connectivity issues
- Physical installation problems
- Console output errors
- Touch input issues

---

## Architecture Overview

### Communication Flow

```
KlipperScreen UI (GTK)
        ↓
ks_includes/printer.py (State Management)
        ↓
KlippyWebsocket.py (WebSocket)
        ↓
Moonraker API (localhost:7125)
        ↓
Klipper (localhost:7011)
```

### Data Update Cycle

1. WebSocket receives status update from Moonraker
2. Printer state object is updated
3. Subscribed panels receive `process_update()` callback
4. UI widgets refresh with new data
5. Screen re-renders

---

## Original Credits

KlipperScreen was created and maintained by:
- **Jordan Ruthe** (2020-2021) - Original creator
- **Alfredo Monclus (alfrix)** (2021-present) - Current maintainer

**TopTable Customization**: Optimizations for improved UI/UX and design consistency

Thanks to all contributors and the Klipper community for their support.

---

## Related Projects

- 🖨️ [Klipper](https://github.com/kevinOConnor/klipper) - 3D printer firmware
- 🌐 [Moonraker](https://github.com/arksine/moonraker) - API server for Klipper
- 📺 [OctoScreen](https://github.com/Z-Bolt/OctoScreen/) - Inspiration for KlipperScreen
- 🎨 [TopTable](styles/toptable/) - Modern UI theme

---

## License

See LICENSE file for details.

---

## Support

- 📖 [Documentation](https://klipperscreen.readthedocs.io/)
- 🐛 [Report Issues](https://github.com/KlipperScreen/KlipperScreen/issues)
- 💬 [Community Chat](https://discord.gg/Kj4fdBT5Js)

---

**Last Updated**: May 2026  
**Version**: TopTable Edition (KlipperScreen Customized)
