# M3U8 Detection Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing Qooly-style M3U8 detection in a PySide6 application, based on the analysis of the Qooly Chrome extension.

## Core Implementation Strategy

### 1. Network Request Interception Layer

Replace the current basic interceptor with a comprehensive one:

```python
class M3U8Interceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.fetching = {}  # Request deduplication
        self.ignored_domains = [
            r'^https?://(.*\.)?youtube\.com',
            r'^https?://(.*\.)?globo\.com', 
            r'^https?://qooly\.com',
            r'^https?://bastyon\.com',
            r'^https?://vimeo\.com'
        ]
        
    def interceptRequest(self, info):
        url = info.requestUrl().toString()
        
        # Domain filtering
        if self._is_ignored_domain(url):
            return
            
        # Check for M3U8 in URL
        if '.m3u8' in url.lower():
            self._process_m3u8_url(url, info)
            
        # Note: Content-Type checking requires additional approach
        # since QWebEngineUrlRequestInterceptor doesn't provide response headers
        
    def _is_ignored_domain(self, url):
        import re
        for pattern in self.ignored_domains:
            if re.match(pattern, url):
                return True
        return False
        
    def _process_m3u8_url(self, url, info):
        request_id = id(info)  # Use object id as request identifier
        
        if request_id in self.fetching:
            return  # Already processing
            
        self.fetching[request_id] = True
        
        # Async processing to avoid blocking
        QTimer.singleShot(0, lambda: self._fetch_and_parse_m3u8(url, request_id))
        
    def _fetch_and_parse_m3u8(self, url, request_id):
        try:
            # This should be done in a separate thread for production
            self.main_window.process_detected_m3u8(url)
        finally:
            self.fetching.pop(request_id, None)
```

### 2. Enhanced JavaScript Injection

Expand the JavaScript detection to match Qooly's approach:

```python
def inject_m3u8_detection_script(self):
    js_code = """
    (function() {
        // Override XMLHttpRequest for request/response monitoring
        const originalXHROpen = XMLHttpRequest.prototype.open;
        const originalXHRSend = XMLHttpRequest.prototype.send;
        
        XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
            this._url = url;
            this._method = method;
            return originalXHROpen.apply(this, arguments);
        };
        
        XMLHttpRequest.prototype.send = function(data) {
            const xhr = this;
            
            // Check URL for M3U8
            if (xhr._url && xhr._url.toLowerCase().includes('.m3u8')) {
                console.log('M3U8_URL_DETECTED: ' + xhr._url);
            }
            
            // Hook response to check Content-Type
            const originalOnReadyStateChange = xhr.onreadystatechange;
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 2) { // Headers received
                    const contentType = xhr.getResponseHeader('Content-Type');
                    if (contentType && isM3U8ContentType(contentType)) {
                        console.log('M3U8_CONTENT_TYPE_DETECTED: ' + xhr._url);
                    }
                }
                if (originalOnReadyStateChange) {
                    return originalOnReadyStateChange.apply(this, arguments);
                }
            };
            
            return originalXHRSend.apply(this, arguments);
        };
        
        // Override fetch API  
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const url = args[0];
            
            if (typeof url === 'string' && url.toLowerCase().includes('.m3u8')) {
                console.log('M3U8_FETCH_DETECTED: ' + url);
            }
            
            // Hook response to check headers
            const fetchPromise = originalFetch.apply(this, arguments);
            fetchPromise.then(response => {
                const contentType = response.headers.get('Content-Type');
                if (contentType && isM3U8ContentType(contentType)) {
                    console.log('M3U8_CONTENT_TYPE_DETECTED: ' + response.url);
                }
            }).catch(() => {}); // Ignore errors
            
            return fetchPromise;
        };
        
        // M3U8 Content-Type checker
        function isM3U8ContentType(contentType) {
            const m3u8Types = [
                'application/vnd.apple.mpegurl',
                'audio/mpegurl',
                'application/mpegurl', 
                'application/x-mpegurl',
                'audio/x-mpegurl',
                'application/vnd.apple.mpegurl.audio'
            ];
            return m3u8Types.some(type => contentType.toLowerCase().includes(type));
        }
        
        console.log('Enhanced M3U8 detection script injected');
    })();
    """
    
    self.custom_page.runJavaScript(js_code)
```

### 3. M3U8 Content Parser

Implement the core parsing logic that matches Qooly's behavior:

```python
import requests
import re
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class M3U8Stream:
    url: str
    quality: str = ""
    playlist: bool = True
    stream: bool = False
    hostname: str = ""
    filename: str = ""
    id: str = ""
    is_additional: bool = False

class M3U8Parser:
    def __init__(self):
        self.session = requests.Session()
        
    async def fetch_and_parse(self, url: str, tab_title: str = "", initiator: str = "") -> List[M3U8Stream]:
        """Main entry point that mirrors Qooly's processing"""
        try:
            # Fetch M3U8 content
            response = self.session.get(url)
            response.raise_for_status()
            content = response.text
            
            streams = []
            is_live = self._detect_live_stream(content, url)
            
            # Check if it's a master playlist (multiple qualities)
            if self._is_master_playlist(content):
                streams.extend(self._parse_master_playlist(content, url, tab_title, initiator, is_live))
            else:
                # Single media playlist
                stream = M3U8Stream(
                    url=url,
                    quality="",
                    playlist=True,
                    stream=is_live,
                    hostname=initiator,
                    filename=tab_title,
                    id=self._generate_id(),
                    is_additional=False
                )
                streams.append(stream)
                
            return streams
            
        except Exception as e:
            print(f"Error parsing M3U8 {url}: {e}")
            return []
    
    def _is_master_playlist(self, content: str) -> bool:
        """Check if playlist contains stream variants"""
        return '#EXT-X-STREAM-INF:' in content
        
    def _parse_master_playlist(self, content: str, base_url: str, tab_title: str, initiator: str, is_live: bool) -> List[M3U8Stream]:
        """Parse master playlist to extract quality variants"""
        streams = []
        
        # Split by stream info markers
        segments = content.split('#EXT-X-STREAM-INF:')
        
        for segment in segments[1:]:  # Skip first empty segment
            if '.m3u8' not in segment:
                continue
                
            stream = M3U8Stream(
                url="",
                quality="",
                playlist=True,
                stream=is_live,
                hostname=initiator,
                filename=tab_title,
                id=self._generate_id(),
                is_additional=False
            )
            
            # Parse segment for resolution and URL
            parts = re.split(r'\s|,', segment)
            
            for part in parts:
                # Extract resolution/quality
                if 'RESOLUTION=' in part:
                    resolution = part.split('=')[1]
                    stream.quality = resolution
                    
                # Extract M3U8 URL
                if '.m3u8' in part:
                    url = self._clean_url(part)
                    stream.url = self._resolve_url(url, base_url)
                    
            if stream.url:
                streams.append(stream)
                
        return streams
    
    def _clean_url(self, url_part: str) -> str:
        """Clean URL from playlist line"""
        # Remove quotes and prefixes
        url = re.sub(r'^.*=("|\')', '', url_part)
        url = re.sub(r'("|\')\s*$', '', url)
        return url.strip()
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs using same logic as Qooly"""
        
        # Absolute URL
        if re.match(r'^https?://', url):
            return url
            
        # Relative URL (same directory or with ./)
        if url.startswith('./') or not url.startswith('/'):
            # Find the directory part of base URL
            base_match = re.search(r'/[^/]+\.m3u8', base_url, re.IGNORECASE)
            if base_match and base_match.start() >= 0:
                base_dir = base_url[:base_match.start()]
                return base_dir + '/' + url.lstrip('./')
                
        # Root-relative URL (starts with /)  
        else:
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}/{url.lstrip('/')}"
            
        return url
    
    def _detect_live_stream(self, content: str, url: str) -> bool:
        """Detect if stream is live using same logic as Qooly"""
        
        # VOD indicators
        if '#EXT-X-ENDLIST' in content:
            return False
        if '#EXT-X-PLAYLIST-TYPE:VOD' in content:
            return False
            
        # Live indicators
        if '#EXT-X-PLAYLIST-TYPE:LIVE' in content:
            return True
        if '#EXT-X-PLAYLIST-TYPE:EVENT' in content:
            return True
            
        # Site-specific detection (from Qooly's logic)
        live_sites = [
            r'^https?://play\.afreecatv\.com',
            r'^https?://www\.mildom\.com',
            r'^https?://tv\.kakao\.com',
            r'^https?://tv\.naver\.com/l/',
            r'^https?://chzzk\.naver\.com',
        ]
        
        for pattern in live_sites:
            if re.match(pattern, url):
                return True
                
        return False  # Default to VOD
    
    def _generate_id(self) -> str:
        """Generate unique ID for stream"""
        import uuid
        return str(uuid.uuid4())[:8]
```

### 4. Integration with Main Window

Update the main window to use the enhanced detection:

```python
def process_detected_m3u8(self, url: str):
    """Process detected M3U8 URL using Qooly's approach"""
    print(f"🔍 Processing M3U8: {url}")
    
    # Get current tab info
    current_url = self.web_view.url().toString()
    tab_title = self.web_view.page().title()
    
    # Parse M3U8 asynchronously
    def parse_async():
        parser = M3U8Parser()
        streams = asyncio.run(parser.fetch_and_parse(url, tab_title, current_url))
        
        # Update UI on main thread
        QTimer.singleShot(0, lambda: self._display_streams(streams))
    
    # Run in thread to avoid blocking UI
    import threading
    threading.Thread(target=parse_async, daemon=True).start()

def _display_streams(self, streams: List[M3U8Stream]):
    """Display detected streams in the text area"""
    if not streams:
        return
        
    current_text = self.content_area.toPlainText()
    if "M3U8 DETECTION READY" in current_text or not current_text.strip():
        new_text = "🎯 DETECTED M3U8 STREAMS:\n\n"
    else:
        new_text = current_text + "\n"
    
    for stream in streams:
        stream_type = "🔴 LIVE" if stream.stream else "📹 VOD"
        quality_info = f" ({stream.quality})" if stream.quality else ""
        
        new_text += f"{stream_type} M3U8{quality_info}\n"
        new_text += f"   📺 {stream.url}\n"
        new_text += f"   🌐 From: {stream.hostname}\n"
        new_text += f"   📁 {stream.filename}\n"
        new_text += "-" * 60 + "\n"
    
    self.content_area.setText(new_text)
    
    # Scroll to bottom
    cursor = self.content_area.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    self.content_area.setTextCursor(cursor)
```

### 5. Enhanced Console Message Handler

Update the JavaScript console handler to process the new detection types:

```python
def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
    print(f"🔍 JS Console: {message}")
    
    if 'M3U8_URL_DETECTED:' in message:
        url = message.replace('M3U8_URL_DETECTED: ', '').strip()
        self.main_window.process_detected_m3u8(url)
        
    elif 'M3U8_CONTENT_TYPE_DETECTED:' in message:
        url = message.replace('M3U8_CONTENT_TYPE_DETECTED: ', '').strip()  
        self.main_window.process_detected_m3u8(url)
        
    elif 'M3U8_FETCH_DETECTED:' in message:
        url = message.replace('M3U8_FETCH_DETECTED: ', '').strip()
        self.main_window.process_detected_m3u8(url)
```

## Testing Strategy

### 1. Test Sites
- **Live Streams**: Twitch, YouTube Live, news sites
- **VOD Content**: Video hosting sites, educational platforms  
- **Various Formats**: Different quality variants, relative URLs

### 2. Expected Results
- URLs ending in `.m3u8` should be detected
- Content-Type header detection should catch hidden M3U8s
- Master playlists should be parsed into quality variants
- Live vs VOD classification should be accurate

### 3. Performance Validation
- No excessive network requests
- Smooth UI interaction
- Proper memory cleanup

## Deployment Considerations

1. **Dependencies**: Add `requests` and `asyncio` to requirements
2. **Threading**: Ensure M3U8 parsing doesn't block UI
3. **Error Handling**: Graceful handling of network failures
4. **Logging**: Comprehensive debug output for troubleshooting

This implementation provides Qooly-equivalent M3U8 detection capabilities in a PySide6 application.