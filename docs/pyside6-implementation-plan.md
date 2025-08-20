# PySide6 M3U8 Downloader Implementation Plan

Based on the complete qooly analysis, here's how to implement the same functionality in PySide6.

## Core Architecture

```python
from PySide6.QtCore import QObject, Signal, QUrl, QTimer
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEngineUrlRequestInfo
from PySide6.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PySide6.QtNetwork import QNetworkRequest, QNetworkReply
import requests
import re
import json
from urllib.parse import urljoin, urlparse

class M3U8Interceptor(QWebEngineUrlRequestInterceptor):
    """Network request interceptor that captures M3U8 playlists"""
    
    m3u8_detected = Signal(dict)  # Emits M3U8 data when found
    
    def __init__(self):
        super().__init__()
        self.video_formats = ['mp4', 'flv', 'mov', 'webm']
        self.m3u8_content_types = [
            "application/vnd.apple.mpegurl",
            "audio/mpegurl", 
            "application/mpegurl",
            "application/x-mpegurl",
            "audio/x-mpegurl",
            "application/vnd.apple.mpegurl.audio"
        ]
        
    def interceptRequest(self, info: QWebEngineUrlRequestInfo):
        """Intercept all network requests to detect M3U8 content"""
        url = info.requestUrl().toString()
        
        # Skip our own extension requests
        if 'qooly' in url.lower():
            return
            
        # Store request info for header processing
        self._store_request_headers(info)
        
    def _store_request_headers(self, info):
        """Store request headers for later use in response processing"""
        # This would be handled by connecting to response signals
        pass
```

## Main Application Class

```python
class M3U8DownloaderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_web_engine()
        self.setup_data_structures()
        
    def setup_data_structures(self):
        """Initialize data storage similar to qooly's tabsData"""
        self.tab_data = {
            'video_links': [],
            'additional_links': [],
            'url': '',
            'is_stream': False
        }
        
    def setup_web_engine(self):
        """Setup web engine with M3U8 detection"""
        self.web_view = QWebEngineView()
        self.page = M3U8DetectionPage()
        self.web_view.setPage(self.page)
        
        # Connect M3U8 detection signals
        self.page.m3u8_detected.connect(self.handle_m3u8_detected)
        
        # Setup request interceptor
        self.interceptor = M3U8Interceptor()
        self.page.profile().setUrlRequestInterceptor(self.interceptor)
```

## Custom Web Engine Page

```python
class M3U8DetectionPage(QWebEnginePage):
    """Custom page that monitors network responses for M3U8 content"""
    
    m3u8_detected = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.setup_network_monitoring()
        
    def setup_network_monitoring(self):
        """Monitor network responses for M3U8 detection"""
        # Note: QWebEnginePage doesn't provide direct response header access
        # We need to use JavaScript injection for response monitoring
        self.loadFinished.connect(self.inject_monitoring_script)
        
    def inject_monitoring_script(self):
        """Inject JavaScript to monitor network responses"""
        monitoring_script = """
        // Override fetch to monitor responses
        const originalFetch = window.fetch;
        window.fetch = async function(...args) {
            const response = await originalFetch(...args);
            
            // Check for M3U8 content
            const contentType = response.headers.get('content-type');
            const url = response.url;
            
            if (url.includes('.m3u8') || 
                (contentType && [
                    'application/vnd.apple.mpegurl',
                    'audio/mpegurl',
                    'application/mpegurl',
                    'application/x-mpegurl'
                ].some(type => contentType.includes(type)))) {
                
                // Send M3U8 data to Python
                window.qt.webChannelTransport.send({
                    type: 'm3u8_detected',
                    url: url,
                    contentType: contentType,
                    pageUrl: window.location.href,
                    pageTitle: document.title
                });
            }
            
            return response;
        };
        
        // Also monitor XMLHttpRequest
        const originalXHR = window.XMLHttpRequest;
        window.XMLHttpRequest = function() {
            const xhr = new originalXHR();
            xhr.addEventListener('readystatechange', function() {
                if (this.readyState === 4) {
                    const contentType = this.getResponseHeader('content-type');
                    const url = this.responseURL;
                    
                    if (url.includes('.m3u8') || 
                        (contentType && [
                            'application/vnd.apple.mpegurl',
                            'audio/mpegurl'
                        ].some(type => contentType.includes(type)))) {
                        
                        window.qt.webChannelTransport.send({
                            type: 'm3u8_detected',
                            url: url,
                            contentType: contentType,
                            pageUrl: window.location.href,
                            pageTitle: document.title
                        });
                    }
                }
            });
            return xhr;
        };
        """
        
        self.runJavaScript(monitoring_script)
```

## M3U8 Processing Engine

```python
class M3U8Processor:
    """Processes M3U8 playlists similar to qooly's implementation"""
    
    def __init__(self):
        self.session = requests.Session()
        
    async def process_m3u8_url(self, url, page_url, page_title):
        """Main M3U8 processing function"""
        try:
            # Fetch M3U8 content
            response = self.session.get(url, timeout=10)
            playlist_content = response.text
            
            # Determine if this is a stream or VOD
            is_stream = self.detect_stream_type(playlist_content, page_url)
            
            # Process master playlist or media playlist
            if self.is_master_playlist(playlist_content):
                return self.process_master_playlist(
                    playlist_content, url, page_url, page_title, is_stream
                )
            else:
                return self.process_media_playlist(
                    url, page_url, page_title, is_stream
                )
                
        except Exception as e:
            print(f"Error processing M3U8: {e}")
            return []
            
    def detect_stream_type(self, content, page_url):
        """Detect if M3U8 is live stream or VOD based on qooly's logic"""
        # VOD indicators
        if "#EXT-X-ENDLIST" in content:
            return False
        if "#EXT-X-PLAYLIST-TYPE:VOD" in content:
            return False
            
        # Live stream indicators  
        if "#EXT-X-PLAYLIST-TYPE:LIVE" in content:
            return True
        if "#EXT-X-PLAYLIST-TYPE:EVENT" in content:
            return True
            
        # Domain-specific stream detection
        stream_domains = [
            r'https?://play\.afreecatv\.com',
            r'https?://www\.mildom\.com', 
            r'https?://tv\.kakao\.com',
            r'https?://tv\.naver\.com/l/',
            r'https?://chzzk\.naver\.com',
            r'https?://(www\.)?twitch\.tv'
        ]
        
        for domain_pattern in stream_domains:
            if re.match(domain_pattern, page_url):
                return True
                
        return False
        
    def is_master_playlist(self, content):
        """Check if playlist is a master playlist (has variants)"""
        return "#EXT-X-STREAM-INF:" in content
        
    def process_master_playlist(self, content, base_url, page_url, page_title, is_stream):
        """Process master playlist to extract variant streams"""
        video_links = []
        
        # Split by stream info markers
        variants = re.split(r'#EXT-X-STREAM-INF:', content)[1:]  # Skip first empty part
        
        for variant in variants:
            if '.m3u8' not in variant:
                continue
                
            video_data = {
                'url': '',
                'quality': '',
                'playlist': True,
                'stream': is_stream,
                'hostname': urlparse(base_url).netloc,
                'fileName': page_title or 'Unknown',
                'isAdditional': False
            }
            
            # Extract resolution and URL
            lines = variant.split('\n')
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Extract resolution
                if 'RESOLUTION=' in line:
                    resolution_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                    if resolution_match:
                        width = resolution_match.group(1).split('x')[0]
                        video_data['quality'] = f"{width}p"
                
                # Extract M3U8 URL
                if line.endswith('.m3u8'):
                    video_data['url'] = self.resolve_url(line, base_url)
                    break
                    
            if video_data['url']:
                video_links.append(video_data)
                
        return video_links
        
    def process_media_playlist(self, url, page_url, page_title, is_stream):
        """Process media playlist (single stream)"""
        return [{
            'url': url,
            'quality': '',
            'playlist': True,
            'stream': is_stream,
            'hostname': urlparse(url).netloc,
            'fileName': page_title or 'Unknown',
            'isAdditional': False
        }]
        
    def resolve_url(self, segment_url, base_url):
        """Resolve relative URLs based on qooly's logic"""
        segment_url = segment_url.strip().strip('"').strip("'")
        
        if segment_url.startswith(('http://', 'https://')):
            return segment_url  # Absolute URL
            
        if segment_url.startswith('./') or not segment_url.startswith('/'):
            # Relative to current directory
            base_dir = '/'.join(base_url.split('/')[:-1])
            return f"{base_dir}/{segment_url.lstrip('./')}"
        else:
            # Relative to domain root
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{segment_url}"
```

## Download Management

```python
class DownloadManager(QObject):
    """Manages M3U8 and video downloads"""
    
    download_progress = Signal(str, int)  # url, progress
    download_complete = Signal(str)  # url
    
    def __init__(self):
        super().__init__()
        self.active_downloads = {}
        
    def download_m3u8(self, video_data):
        """Download M3U8 playlist file"""
        url = video_data['url']
        filename = f"{video_data['fileName']}.m3u8"
        
        # Use QNetworkAccessManager for download
        self._start_download(url, filename)
        
    def download_segments(self, m3u8_content, base_url, output_dir):
        """Download M3U8 segments (similar to qooly's approach)"""
        segments = self.extract_segments(m3u8_content, base_url)
        
        for i, segment_url in enumerate(segments):
            filename = f"segment_{i:04d}.ts"
            self._download_segment(segment_url, output_dir / filename)
            
    def extract_segments(self, content, base_url):
        """Extract segment URLs from M3U8 content"""
        segments = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # This is a segment URL
                if line.startswith(('http://', 'https://')):
                    segments.append(line)
                else:
                    segments.append(self.resolve_url(line, base_url))
                    
        return segments
```

## Integration with Main GUI

```python
def handle_m3u8_detected(self, m3u8_data):
    """Handle M3U8 detection from web page"""
    url = m3u8_data['url'] 
    page_url = m3u8_data['pageUrl']
    page_title = m3u8_data['pageTitle']
    
    # Process M3U8 in background thread
    QTimer.singleShot(0, lambda: self.process_m3u8_async(url, page_url, page_title))
    
def process_m3u8_async(self, url, page_url, page_title):
    """Process M3U8 asynchronously"""
    processor = M3U8Processor()
    video_links = processor.process_m3u8_url(url, page_url, page_title)
    
    # Add to video list UI
    for video_link in video_links:
        self.add_video_link_to_ui(video_link)
        
def add_video_link_to_ui(self, video_link):
    """Add detected video link to the UI list"""
    # Create list item with download button
    item_widget = VideoLinkWidget(video_link)
    item_widget.download_requested.connect(self.start_download)
    
    self.video_list.addWidget(item_widget)
```

## Key Implementation Notes

1. **Network Monitoring**: Use JavaScript injection since PySide6 doesn't provide direct response header access
2. **URL Resolution**: Implement qooly's exact URL resolution logic for relative paths  
3. **Stream Detection**: Use content analysis and domain patterns to identify live vs VOD
4. **Header Preservation**: Store request headers for authenticated downloads
5. **Segment Processing**: Download segments to temp directory, then concatenate with FFmpeg
6. **Error Handling**: Robust error handling for network failures and parsing errors

This implementation replicates qooly's core functionality while adapting to PySide6's architecture and capabilities.