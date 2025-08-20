# Reference Materials

This directory contains reference implementations and analysis documentation for the M3U8 downloader project.

## Qooly Chrome Extension

The `qooly-extension/` directory contains the complete source code of the Qooly Chrome extension, which serves as our reference implementation for M3U8 detection and downloading functionality.

### Key Files

- **bg_beautified.js** - Main background script with core M3U8 detection logic
- **inject_beautified.js** - Content script (minimal functionality)  
- **popup_beautified.js** - UI popup script (Vue.js interface)
- **manifest.json** - Extension manifest and permissions

### Analysis Documents

The analysis of this reference implementation is documented in:
- `/docs/qooly-complete-implementation.md` - Complete functionality analysis
- `/docs/pyside6-implementation-plan.md` - PySide6 adaptation guide
- `/docs/qooly-analysis.md` - Initial M3U8 detection analysis
- `/docs/m3u8-formats.md` - M3U8 format specifications

## Usage

These files are for reference only. The actual implementation is in the root directory files:
- `main.py` - Application entry point
- `gui.py` - PySide6 GUI implementation  
- `downloader.py` - M3U8 download engine
- `utils.py` - Utility functions