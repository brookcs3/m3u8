# M3U8 Video Downloader

A PySide6 application for detecting and downloading M3U8 video streams, inspired by the Qooly Chrome extension.

## Features

- **M3U8 Detection**: Automatically detects M3U8 playlist URLs from websites
- **Embedded Browser**: Built-in web browser with sliding drawer interface  
- **Network Interception**: Captures M3U8 URLs from network requests
- **JavaScript Injection**: Hooks into web page video players for detection
- **Download Management**: Process and download M3U8 streams
- **Multiple Detection Methods**: URL patterns, Content-Type headers, and JavaScript monitoring

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

## Project Structure

```
m3u8/
├── main.py              # Application entry point
├── gui.py               # PySide6 GUI with browser integration
├── downloader.py        # M3U8 download engine  
├── utils.py             # Utility functions
├── requirements.txt     # Python dependencies
├── docs/                # Implementation documentation
├── reference/           # Qooly extension source code (reference only)
└── README.md           # This file
```

## Usage

1. **Launch Application**: Run `python main.py`
2. **Open Browser**: Click "Open Browser" to reveal the embedded web browser
3. **Navigate to Video Site**: Enter a URL and browse to video content
4. **Play Video**: Start playing video content on the website
5. **View Detected Streams**: M3U8 URLs will appear automatically in the main area
6. **Download**: Use the detected URLs to download video streams

## How It Works

The application uses multiple detection methods based on the Qooly Chrome extension:

### Network Request Interception
- Monitors all network requests via `QWebEngineUrlRequestInterceptor`
- Detects URLs containing `.m3u8` extensions
- Captures M3U8 content-type headers

### JavaScript Injection
- Hooks `XMLHttpRequest` and `fetch` APIs
- Monitors video element `src` attribute changes
- Watches for dynamically added video elements

### M3U8 Processing
- Parses master playlists for variant streams
- Resolves relative URLs to absolute URLs
- Detects live streams vs VOD content

## Development

### Adding New Detection Methods
See `docs/pyside6-implementation-plan.md` for detailed implementation patterns.

### Reference Implementation
The original Qooly Chrome extension source code is available in `reference/qooly-extension/` for comparison.

## Dependencies

- **PySide6**: Qt framework for Python GUI
- **requests**: HTTP library for playlist fetching
- **m3u8**: M3U8 playlist parsing library

## Documentation

- `/docs/qooly-complete-implementation.md` - Complete Qooly functionality analysis
- `/docs/pyside6-implementation-plan.md` - PySide6 adaptation guide  
- `/docs/m3u8-formats.md` - M3U8 format specifications
- `/reference/README.md` - Reference materials guide

## License

This project is for educational and research purposes.