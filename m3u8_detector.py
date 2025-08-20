"""
M3U8 Detection Engine
Handles network request interception and M3U8 URL detection
"""

from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor, QWebEnginePage
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from urllib.parse import urlparse, parse_qs
import requests
from threading import Thread

class M3U8Detector(QWebEngineUrlRequestInterceptor):
    """
    Network request interceptor for detecting M3U8 streams
    Based on Qooly's detection methods
    """
    
    # Signal emitted when M3U8 stream is detected
    m3u8_detected = Signal(dict)  # Emits stream info dict
    
    def __init__(self):
        super().__init__()
        
        # M3U8 content types to detect (will be used in Step 3)
        self.m3u8_content_types = [
            "application/vnd.apple.mpegurl",
            "audio/mpegurl", 
            "application/mpegurl",
            "application/x-mpegurl",
            "audio/x-mpegurl",
            "application/vnd.apple.mpegurl.audio"
        ]
        
        # Keep track of detected URLs to avoid duplicates
        self.detected_urls = set()
        
    def interceptRequest(self, info):
        """
        Intercept network requests to detect M3U8 streams
        Step 1: Basic URL pattern detection
        Step 3: Content-Type header detection
        """
        url = info.requestUrl().toString()
        
        # Skip empty or invalid URLs
        if not url or url.startswith('data:') or url.startswith('blob:'):
            return
            
        # Check if URL contains M3U8 pattern
        if self.detect_from_url(url):
            # Create stream info dict
            stream_info = {
                'url': url,
                'detection_method': 'url_pattern',
                'page_url': '',  # Will be populated later from GUI
                'page_title': '',  # Will be populated later from GUI
                'quality': '',   # Will be determined in processing
                'is_master_playlist': False,  # Will be determined in processing
                'timestamp': None  # Could add timestamp later
            }
            
            # Only emit if we haven't seen this URL before
            if url not in self.detected_urls:
                self.detected_urls.add(url)
                print(f"🔍 M3U8Detector: Found M3U8 URL via pattern: {url}")
                self.m3u8_detected.emit(stream_info)
        else:
            # Step 3: Check Content-Type headers for URLs that don't match pattern
            # Do this in a background thread to avoid blocking
            Thread(target=self._check_content_type_async, args=(url,), daemon=True).start()
        
    def detect_from_url(self, url):
        """
        Detect M3U8 from URL pattern
        Based on Qooly's URL detection logic
        """
        if not isinstance(url, str):
            return False
            
        url_lower = url.lower()
        
        # Primary detection: .m3u8 extension
        if '.m3u8' in url_lower:
            return True
            
        # Secondary detection: common M3U8 URL patterns
        m3u8_patterns = [
            '/playlist.m3u8',
            '/index.m3u8', 
            '/master.m3u8',
            'manifest.m3u8',
            'm3u8',  # Query parameter or path segment
        ]
        
        for pattern in m3u8_patterns:
            if pattern in url_lower:
                return True
                
        # Query parameter detection (e.g., ?format=m3u8)
        try:
            parsed_url = urlparse(url)
            if parsed_url.query:
                query_params = parse_qs(parsed_url.query)
                for param_name, param_values in query_params.items():
                    for value in param_values:
                        if 'm3u8' in value.lower():
                            return True
        except Exception:
            # If URL parsing fails, continue with other checks
            pass
            
        return False
        
    def _check_content_type_async(self, url):
        """
        Check Content-Type headers in background thread
        Step 3: Content-Type header detection implementation
        """
        # Skip if already detected or if URL is clearly not video-related
        if url in self.detected_urls:
            return
            
        # Skip common non-video file types
        skip_extensions = ['.js', '.css', '.html', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.ttf']
        url_lower = url.lower()
        if any(ext in url_lower for ext in skip_extensions):
            return
            
        try:
            # Make HEAD request to check Content-Type without downloading content
            response = requests.head(url, timeout=5, allow_redirects=True)
            content_type = response.headers.get('content-type', '').lower()
            
            if self.detect_from_headers({'content-type': content_type}):
                # Create stream info dict
                stream_info = {
                    'url': url,
                    'detection_method': 'content_type_header',
                    'page_url': '',  # Will be populated later from GUI
                    'page_title': '',  # Will be populated later from GUI
                    'quality': '',   # Will be determined in processing
                    'is_master_playlist': False,  # Will be determined in processing
                    'timestamp': None,
                    'content_type': content_type  # Include the detected content type
                }
                
                # Only emit if we haven't seen this URL before
                if url not in self.detected_urls:
                    self.detected_urls.add(url)
                    print(f"🔍 M3U8Detector: Found M3U8 URL via Content-Type '{content_type}': {url}")
                    self.m3u8_detected.emit(stream_info)
                    
        except Exception as e:
            # Silently ignore network errors to avoid spam
            pass
        
    def detect_from_headers(self, headers):
        """
        Detect M3U8 from response headers
        Step 3: Content-Type header detection implementation
        """
        if not isinstance(headers, dict):
            return False
            
        content_type = headers.get('content-type', '').lower()
        
        # Check against Qooly's M3U8 content types
        for m3u8_type in self.m3u8_content_types:
            if m3u8_type.lower() in content_type:
                return True
                
        return False
        
    def clear_detected_urls(self):
        """
        Clear the cache of detected URLs (useful when navigating to new page)
        """
        self.detected_urls.clear()
        print("🔍 M3U8Detector: Cleared detected URLs cache")