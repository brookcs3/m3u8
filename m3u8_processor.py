"""
M3U8 Playlist Processing Engine
Handles M3U8 playlist parsing and processing
"""

import requests
import re
from urllib.parse import urljoin, urlparse
from PySide6.QtCore import QObject, Signal

class M3U8Processor(QObject):
    """
    Processes M3U8 playlists to extract streams and segments
    Based on Qooly's processing logic
    """
    
    # Signal for processing updates
    processing_finished = Signal(dict)  # Emits processed stream info
    processing_failed = Signal(str, str)  # Emits url, error_message
    
    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        # Set a user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def process_playlist(self, url, page_url=None, page_title=None):
        """
        Main processing function for M3U8 playlists
        Step 5: Basic M3U8 playlist fetching and processing
        
        Args:
            url: M3U8 playlist URL
            page_url: URL of the page where M3U8 was detected
            page_title: Title of the page
            
        Returns:
            Dictionary with processing results
        """
        try:
            print(f"🔍 M3U8Processor: Fetching playlist from {url}")
            
            # Fetch the M3U8 playlist content
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            playlist_content = response.text
            
            # Basic validation that this is actually an M3U8 file
            if not self.is_valid_m3u8(playlist_content):
                error_msg = "Content is not a valid M3U8 playlist"
                print(f"❌ M3U8Processor: {error_msg}")
                self.processing_failed.emit(url, error_msg)
                return None
            
            # Determine playlist type and process accordingly
            if self.is_master_playlist(playlist_content):
                result = self.process_master_playlist(playlist_content, url, page_url, page_title)
            else:
                result = self.process_media_playlist(playlist_content, url, page_url, page_title)
                
            print(f"✅ M3U8Processor: Successfully processed playlist from {url}")
            self.processing_finished.emit(result)
            return result
            
        except Exception as e:
            error_msg = f"Failed to process M3U8 playlist: {str(e)}"
            print(f"❌ M3U8Processor: {error_msg}")
            self.processing_failed.emit(url, error_msg)
            return None
            
    def is_valid_m3u8(self, content):
        """
        Basic validation that content is a valid M3U8 playlist
        """
        if not content or not content.strip():
            return False
            
        # M3U8 files must start with #EXTM3U
        lines = content.strip().split('\n')
        return len(lines) > 0 and lines[0].strip() == '#EXTM3U'
        
    def is_master_playlist(self, content):
        """
        Check if playlist is a master playlist (has variants)
        Based on Qooly's detection logic
        """
        return '#EXT-X-STREAM-INF:' in content
        
    def process_master_playlist(self, content, base_url, page_url=None, page_title=None):
        """
        Process master playlist to extract variant streams
        Based on Qooly's variant extraction logic
        """
        variants = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXT-X-STREAM-INF:'):
                # Extract stream information
                stream_info = self.parse_stream_inf(line)
                
                # Next line should contain the URL
                if i + 1 < len(lines):
                    stream_url = lines[i + 1].strip()
                    if stream_url and not stream_url.startswith('#'):
                        # Resolve relative URL
                        full_url = self.resolve_url(stream_url, base_url)
                        
                        variant = {
                            'url': full_url,
                            'quality': stream_info.get('resolution', ''),
                            'bandwidth': stream_info.get('bandwidth', ''),
                            'codecs': stream_info.get('codecs', ''),
                            'is_master_playlist': False,  # These are media playlists
                            'page_url': page_url or '',
                            'page_title': page_title or '',
                            'stream_type': 'variant'
                        }
                        variants.append(variant)
                        
            i += 1
            
        return {
            'type': 'master_playlist',
            'url': base_url,
            'variants': variants,
            'page_url': page_url or '',
            'page_title': page_title or '',
            'is_live': self.detect_stream_type(content, page_url)
        }
        
    def process_media_playlist(self, content, url, page_url=None, page_title=None):
        """
        Process media playlist (single stream)
        """
        # Extract basic information about the media playlist
        segment_count = content.count('#EXTINF:')
        is_live = self.detect_stream_type(content, page_url)
        
        return {
            'type': 'media_playlist',
            'url': url,
            'segment_count': segment_count,
            'page_url': page_url or '',
            'page_title': page_title or '',
            'is_live': is_live,
            'quality': 'Unknown',  # Could be extracted from URL patterns
            'stream_type': 'direct'
        }
        
    def parse_stream_inf(self, stream_inf_line):
        """
        Parse EXT-X-STREAM-INF line to extract stream parameters
        """
        info = {}
        
        # Extract bandwidth
        bandwidth_match = re.search(r'BANDWIDTH=(\d+)', stream_inf_line)
        if bandwidth_match:
            info['bandwidth'] = bandwidth_match.group(1)
            
        # Extract resolution
        resolution_match = re.search(r'RESOLUTION=(\d+x\d+)', stream_inf_line)
        if resolution_match:
            info['resolution'] = resolution_match.group(1)
            
        # Extract codecs
        codecs_match = re.search(r'CODECS="([^"]+)"', stream_inf_line)
        if codecs_match:
            info['codecs'] = codecs_match.group(1)
            
        return info
        
    def detect_stream_type(self, content, page_url):
        """
        Detect if M3U8 is live stream or VOD
        Based on Qooly's stream detection logic
        """
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
            
        # Domain-specific stream detection (from Qooly)
        if page_url:
            live_patterns = [
                r'play\.afreecatv\.com',
                r'www\.mildom\.com',
                r'tv\.kakao\.com',
                r'tv\.naver\.com/l/',
                r'chzzk\.naver\.com',
                r'(www\.)?twitch\.tv'
            ]
            
            for pattern in live_patterns:
                if re.search(pattern, page_url):
                    return True
                    
        # Default: assume live if no ENDLIST tag
        return "#EXT-X-ENDLIST" not in content
        
    def resolve_url(self, segment_url, base_url):
        """
        Resolve relative URLs based on Qooly's logic
        """
        segment_url = segment_url.strip().strip('"').strip("'")
        
        if segment_url.startswith(('http://', 'https://')):
            return segment_url  # Already absolute
            
        if segment_url.startswith('./') or not segment_url.startswith('/'):
            # Relative to current directory
            base_dir = '/'.join(base_url.split('/')[:-1])
            return f"{base_dir}/{segment_url.lstrip('./')}"
        else:
            # Relative to domain root
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{segment_url}"