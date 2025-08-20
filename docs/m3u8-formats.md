# M3U8 Playlist Format Reference

## Overview

This document provides a comprehensive reference for M3U8 playlist formats, based on analysis of the Qooly extension and HLS specifications. Understanding these formats is crucial for proper M3U8 detection and parsing.

## M3U8 File Types

### 1. Master Playlist (Multivariant)

Contains multiple quality variants or alternate streams.

#### Example Structure:
```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=1280000,RESOLUTION=720x480
chunklist_w1280000.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2560000,RESOLUTION=1280x720  
chunklist_w2560000.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=7680000,RESOLUTION=1920x1080
chunklist_w7680000.m3u8
```

#### Key Tags:
- `#EXT-X-STREAM-INF:` - Defines a quality variant
- `BANDWIDTH=` - Bitrate in bits per second
- `RESOLUTION=` - Video resolution (width x height)
- `CODECS=` - Audio/video codec information

### 2. Media Playlist (Variant)

Contains actual video segments for playback.

#### Example Structure:
```m3u8
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:10
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:9.009,
segment_000.ts
#EXTINF:9.009,
segment_001.ts
#EXTINF:9.009,
segment_002.ts
#EXT-X-ENDLIST
```

#### Key Tags:
- `#EXTINF:` - Segment duration and optional title
- `#EXT-X-TARGETDURATION:` - Maximum segment duration
- `#EXT-X-MEDIA-SEQUENCE:` - Sequence number of first segment
- `#EXT-X-ENDLIST` - Indicates end of playlist (VOD content)

## Content-Type Detection

### Standard MIME Types

Qooly checks for these Content-Type headers:

```
application/vnd.apple.mpegurl
audio/mpegurl
application/mpegurl
application/x-mpegurl  
audio/x-mpegurl
application/vnd.apple.mpegurl.audio
```

### Implementation:
```python
M3U8_CONTENT_TYPES = [
    "application/vnd.apple.mpegurl",
    "audio/mpegurl", 
    "application/mpegurl",
    "application/x-mpegurl",
    "audio/x-mpegurl",
    "application/vnd.apple.mpegurl.audio"
]

def is_m3u8_content_type(content_type):
    if not content_type:
        return False
    return any(mime_type in content_type.lower() for mime_type in M3U8_CONTENT_TYPES)
```

## Live vs VOD Detection

### VOD (Video on Demand) Indicators

**Definitive VOD markers:**
```m3u8
#EXT-X-ENDLIST
#EXT-X-PLAYLIST-TYPE:VOD
```

### Live Stream Indicators

**Definitive Live markers:**
```m3u8
#EXT-X-PLAYLIST-TYPE:LIVE
#EXT-X-PLAYLIST-TYPE:EVENT
```

**Absence of VOD markers also suggests live content.**

### Implementation:
```python
def detect_stream_type(content, url):
    # VOD indicators
    if '#EXT-X-ENDLIST' in content:
        return 'vod'
    if '#EXT-X-PLAYLIST-TYPE:VOD' in content:
        return 'vod'
    
    # Live indicators
    if '#EXT-X-PLAYLIST-TYPE:LIVE' in content:
        return 'live'
    if '#EXT-X-PLAYLIST-TYPE:EVENT' in content:
        return 'live'
    
    # Site-specific detection
    live_sites = [
        r'play\.afreecatv\.com',
        r'www\.mildom\.com', 
        r'tv\.kakao\.com',
        r'tv\.naver\.com/l/',
        r'chzzk\.naver\.com'
    ]
    
    for site_pattern in live_sites:
        if re.search(site_pattern, url):
            return 'live'
    
    return 'vod'  # Default assumption
```

## URL Resolution Patterns

### Absolute URLs
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
https://example.com/streams/720p.m3u8
```

### Relative URLs (Same Directory)
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
720p.m3u8
```

### Relative URLs (With Path)
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
./streams/720p.m3u8
```

### Root-Relative URLs
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
/streams/720p.m3u8
```

### Resolution Algorithm:
```python
def resolve_m3u8_url(url, base_url):
    # Absolute URL
    if re.match(r'^https?://', url):
        return url
    
    # Relative URL (same directory or with ./)
    if url.startswith('./') or not url.startswith('/'):
        # Extract base directory from master playlist URL
        base_match = re.search(r'/[^/]+\.m3u8', base_url, re.IGNORECASE)
        if base_match:
            base_dir = base_url[:base_match.start()]
            return f"{base_dir}/{url.lstrip('./')}"
    
    # Root-relative URL
    else:
        parsed = urlparse(base_url)
        return f"{parsed.scheme}://{parsed.netloc}/{url.lstrip('/')}"
    
    return url
```

## Quality Extraction

### Resolution Parsing
```python
def extract_quality_info(stream_inf_line):
    quality_info = {}
    
    # Extract resolution
    resolution_match = re.search(r'RESOLUTION=(\d+)x(\d+)', stream_inf_line)
    if resolution_match:
        width, height = resolution_match.groups()
        quality_info['resolution'] = f"{width}x{height}"
        quality_info['height'] = int(height)
        quality_info['width'] = int(width)
    
    # Extract bandwidth
    bandwidth_match = re.search(r'BANDWIDTH=(\d+)', stream_inf_line)
    if bandwidth_match:
        quality_info['bandwidth'] = int(bandwidth_match.group(1))
    
    # Extract frame rate
    framerate_match = re.search(r'FRAME-RATE=([\d.]+)', stream_inf_line)
    if framerate_match:
        quality_info['framerate'] = float(framerate_match.group(1))
    
    # Extract codecs
    codecs_match = re.search(r'CODECS="([^"]+)"', stream_inf_line)
    if codecs_match:
        quality_info['codecs'] = codecs_match.group(1)
    
    return quality_info
```

## Common Patterns and Edge Cases

### 1. Quoted URLs
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
"720p.m3u8"
```

### 2. URLs with Parameters
```m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1280000
720p.m3u8?token=abc123&expires=1234567890
```

### 3. Audio-Only Streams
```m3u8
#EXT-X-MEDIA:TYPE=AUDIO,GROUP-ID="audio",NAME="English",LANGUAGE="en",URI="audio_en.m3u8"
```

### 4. Subtitle Streams
```m3u8
#EXT-X-MEDIA:TYPE=SUBTITLES,GROUP-ID="subs",NAME="English",LANGUAGE="en",URI="subtitles_en.m3u8"
```

## Parsing Implementation

### Complete Parser Structure:
```python
class M3U8Parser:
    def parse_playlist(self, content, base_url):
        if self.is_master_playlist(content):
            return self.parse_master_playlist(content, base_url)
        else:
            return self.parse_media_playlist(content, base_url)
    
    def is_master_playlist(self, content):
        return '#EXT-X-STREAM-INF:' in content
    
    def parse_master_playlist(self, content, base_url):
        streams = []
        lines = content.strip().split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('#EXT-X-STREAM-INF:'):
                # Parse quality info
                quality_info = self.extract_quality_info(line)
                
                # Get URL from next non-comment line
                i += 1
                while i < len(lines) and lines[i].strip().startswith('#'):
                    i += 1
                
                if i < len(lines):
                    url = self.clean_url(lines[i].strip())
                    resolved_url = self.resolve_url(url, base_url)
                    
                    stream = {
                        'url': resolved_url,
                        'quality': quality_info.get('resolution', ''),
                        'bandwidth': quality_info.get('bandwidth', 0),
                        'type': 'master_variant'
                    }
                    streams.append(stream)
            
            i += 1
        
        return streams
    
    def parse_media_playlist(self, content, base_url):
        # For media playlists, return the playlist itself
        stream_type = self.detect_stream_type(content, base_url)
        
        return [{
            'url': base_url,
            'type': 'media_playlist',
            'stream_type': stream_type,
            'segments': self.count_segments(content)
        }]
    
    def count_segments(self, content):
        return len([line for line in content.split('\n') if line.strip().startswith('#EXTINF:')])
```

## Validation Rules

### Valid M3U8 Characteristics:
1. Must start with `#EXTM3U`
2. Must contain either `#EXT-X-STREAM-INF:` (master) or `#EXTINF:` (media)
3. URLs should resolve to valid endpoints
4. Master playlists should have variant streams
5. Media playlists should have segments

### Invalid Patterns to Reject:
```python
def is_valid_m3u8_url(url):
    # Reject known non-M3U8 patterns
    invalid_patterns = [
        r'\.twimg\.com.*pl/mp4a',
        r'\.twimg\.com.*pl/avc1',
        r'video\.twimg\.com.*pl/'
    ]
    
    for pattern in invalid_patterns:
        if re.search(pattern, url):
            return False
    
    return True
```

This comprehensive format reference enables robust M3U8 detection and parsing that matches professional tools like Qooly.