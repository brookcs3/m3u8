# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an M3U8 video downloader with a PySide6 GUI interface that replicates the functionality of the Qooly Chrome extension. The application uses a hybrid Python + JavaScript approach for comprehensive M3U8 stream detection and downloading.

## Key Breakthroughs & Learning

### Major Discovery: Qooly Extension Analysis
We performed a complete analysis of the Qooly Chrome extension source code (`reference/qooly-extension/bg_beautified.js`) and discovered their comprehensive M3U8 detection strategy:

**Qooly's Three Detection Methods:**
1. **Network Request Interception** - Monitors all network requests for `.m3u8` URLs
2. **Content-Type Header Detection** - Catches M3U8 streams by MIME type even without `.m3u8` in URL
3. **JavaScript Injection** - Hooks XMLHttpRequest, fetch API, and video elements for dynamic detection

**Critical Content-Type Headers for M3U8:**
- `application/vnd.apple.mpegurl`
- `audio/mpegurl`
- `application/mpegurl` 
- `application/x-mpegurl`
- `audio/x-mpegurl`
- `application/vnd.apple.mpegurl.audio`

### Architecture Decision: Hybrid Python + JavaScript
**Why we chose this approach:**
- **Python alone** can only detect network requests and headers
- **JavaScript injection** is required to catch dynamically loaded M3U8 URLs (modern video players)
- **PySide6 QtWebEngine** seamlessly supports Python/JavaScript communication
- **Still self-contained** - no external dependencies, single executable app

### Clean Slate Strategy
We deliberately removed all old implementation code and created clean scaffolds to avoid mixing old/new approaches. This ensures:
- No legacy code interference
- Clear separation of concerns
- Step-by-step implementation approach

## Architecture

### Current Implementation Status
**✅ Completed:**
- Basic PySide6 app with sliding browser drawer interface
- Clean project structure with scaffold files
- Complete Qooly reference analysis and documentation

**🔧 In Progress:**
Following step-by-step implementation plan (see todo list in code)

### Core Components

**main.py**: Entry point that launches the PySide6 application

**gui.py**: Main GUI with sliding drawer browser - clean interface without detection complexity

**m3u8_detector.py**: Python-based M3U8 detection engine
- Network request interception via `QWebEngineUrlRequestInterceptor`
- Content-Type header analysis
- URL pattern matching

**js_injector.py**: JavaScript injection manager
- Manages injecting M3U8 detection scripts into web pages
- Handles communication between JavaScript and Python

**js_templates.py**: JavaScript detection code templates
- XMLHttpRequest hooks (catches AJAX M3U8 requests)
- Fetch API hooks (catches modern fetch M3U8 requests)
- Video element monitoring (catches src attribute changes)

**m3u8_processor.py**: M3U8 playlist processing engine
- Master playlist parsing (variant streams)
- Media playlist processing (segment extraction)
- URL resolution for relative paths
- Live vs VOD detection

**downloader.py**: Download engine
- Segment downloading with progress tracking
- FFmpeg integration for segment combination
- Temporary file management

**stream_manager.py**: Central coordinator
- Manages detected streams
- Coordinates between detection, processing, and downloading
- Provides unified interface for GUI

### Key Implementation Patterns

**Three-Step Detection Process:**
1. **Network Level** (Python) - Intercept requests, check headers
2. **JavaScript Level** (JS Injection) - Hook dynamic loading
3. **Processing Level** (Python) - Parse and validate M3U8 content

**Signal-Slot Communication:**
Uses Qt signals for loose coupling between components:
- `m3u8_detected` signals from detector to stream manager
- `download_progress` signals from downloader to GUI
- `js_m3u8_detected` signals from JavaScript to Python

**URL Resolution Logic:**
Based on Qooly's implementation:
- Handle absolute URLs (http/https)
- Resolve relative URLs to current directory
- Resolve root-relative URLs to domain root

## Reference Materials

**`reference/qooly-extension/`**: Complete Qooly Chrome extension source code
- `bg_beautified.js` - Main background script with core detection logic
- `inject_beautified.js` - Content script (minimal functionality)
- `popup_beautified.js` - UI popup (Vue.js interface)

**`docs/`**: Implementation analysis and guides
- `qooly-complete-implementation.md` - Complete functionality analysis
- `pyside6-implementation-plan.md` - PySide6 adaptation guide
- `m3u8-formats.md` - M3U8 format specifications

## Development Approach

### Step-by-Step Implementation Strategy
We use a careful, incremental approach with detailed todo tracking:
1. Basic URL pattern detection (Python)
2. GUI integration and display
3. Content-Type header detection
4. JavaScript injection integration  
5. M3U8 playlist processing
6. Download functionality
7. Error handling and polish

### Version Control
Repository: https://github.com/brookcs3/m3u8.git
- Clean commits for each implementation step
- Reference materials preserved in `reference/` directory
- Documentation maintained in `docs/` directory

## Common Development Commands

```bash
# Run the application
python3 main.py

# Install dependencies  
pip3 install -r requirements.txt
```

## Critical Implementation Notes

**JavaScript Communication Pattern:**
```python
# Inject JavaScript
self.web_page.runJavaScript(detection_script)

# Handle JavaScript messages
self.web_page.javaScriptConsoleMessage.connect(self.handle_js_message)

# Parse M3U8 URLs from console messages starting with 'M3U8_DETECTED:'
```

**Network Interception Pattern:**
```python
# Set up interceptor
interceptor = M3U8Detector()
profile.setUrlRequestInterceptor(interceptor)

# Check both URL patterns AND content-type headers
def interceptRequest(self, info):
    url = info.requestUrl().toString()
    # Check .m3u8 in URL AND response headers for content-type
```

**Key Success Factors:**
1. **Comprehensive Detection** - Must use all three methods like Qooly
2. **Proper URL Resolution** - Critical for relative M3U8 URLs
3. **JavaScript Integration** - Essential for modern video sites
4. **Clean Architecture** - Separation of concerns for maintainability

## Recovery Context
If this session crashes, the key context is:
- We analyzed Qooly completely and understand their detection methods
- We chose hybrid Python+JavaScript approach for maximum coverage
- We have clean scaffolds ready for step-by-step implementation
- Current focus: implementing basic URL pattern detection first
- All reference materials and analysis are preserved in repository