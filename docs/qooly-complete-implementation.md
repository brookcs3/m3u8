# Complete Qooly Implementation Analysis

## Core Architecture

Qooly is a Chrome extension with multiple detection engines working in parallel to capture M3U8 playlists and video content from web pages.

## Main Detection Methods

### 1. Network Request Interception (Primary Method)

The core M3U8 detection happens via `chrome.webRequest.onHeadersReceived` listener:

```javascript
chrome.webRequest.onHeadersReceived.addListener(function(details) {
    // Check for M3U8 URLs by:
    // 1. URL pattern matching (.m3u8 extension)
    // 2. Content-Type header detection
    
    var isM3u8ContentType = function() {
        var contentType = details.responseHeaders.find(h => 
            h.name.toLowerCase() === 'content-type'
        )?.value;
        
        return contentType && [
            "application/vnd.apple.mpegurl",
            "audio/mpegurl", 
            "application/mpegurl",
            "application/x-mpegurl",
            "audio/x-mpegurl",
            "application/vnd.apple.mpegurl.audio"
        ].includes(contentType);
    };
    
    // Detect M3U8 by URL pattern OR content-type
    if (details.url.match(".m3u8") || isM3u8ContentType()) {
        // Process M3U8 playlist
        processM3u8Playlist(details);
    }
}, {urls: ["<all_urls>"]}, ["responseHeaders", "extraHeaders"]);
```

### 2. Domain-Specific Detection

Qooly has specific handlers for certain domains:

```javascript
// Domain whitelist for additional video detection
this.domains = [
    "youku.com", 
    "www.ixigua.com", 
    "bastyon.com",
    "hugh.cdn.rumble.cloud", 
    "rumble.com",
    "www.douyin.com", 
    "v3-dy-o.zjcdn.com",
    /tiktok\.com/,
    "theoptimizer.wistia.com",
    "www.xiaohongshu.com"
];
```

### 3. Content-Type Based Video Detection

For non-M3U8 video files, qooly detects by response headers:

```javascript
getVideoType(responseHeaders) {
    var videoType = null;
    
    responseHeaders.some(header => {
        if (header.name.toLowerCase() === "content-type") {
            ["mp4", "flv", "mov", "webm"].forEach(format => {
                if (header.value.indexOf(format) !== -1 && 
                    !/^audio/i.test(header.value)) {
                    videoType = format;
                    return true;
                }
            });
            return true;
        }
    });
    
    return videoType;
}
```

## M3U8 Processing Engine

### Playlist Type Detection

```javascript
async isStream(tab, m3u8Url) {
    try {
        const playlistContent = await fetch(m3u8Url).then(r => r.text());
        
        // Check for live stream indicators
        if (playlistContent.match("#EXT-X-ENDLIST")) return false; // VOD
        if (playlistContent.match("#EXT-X-PLAYLIST-TYPE:VOD")) return false;
        if (playlistContent.match("#EXT-X-PLAYLIST-TYPE:LIVE")) return true;
        if (playlistContent.match("#EXT-X-PLAYLIST-TYPE:EVENT")) return true;
        
        // Additional domain-specific stream detection
        if (tab.url.match(/^https?:\/\/play\.afreecatv\.com/)) return true;
        if (tab.url.match(/^https?:\/\/www\.mildom\.com/)) return true;
        if (tab.url.match(/^https?:\/\/tv\.kakao\.com/)) return true;
        // ... more stream detection rules
        
    } catch (error) {
        return false;
    }
}
```

### Master Playlist Processing

For master playlists (variant playlists), qooly extracts individual stream URLs:

```javascript
if (playlistContent.match(/#EXT-X-STREAM-INF:/)) {
    const variants = playlistContent.split(/#EXT-X-STREAM-INF:/);
    
    variants.forEach(variant => {
        if (variant.match(".m3u8")) {
            const videoData = {
                url: "",
                quality: "",
                playlist: true,
                stream: await this.isStream(tab, url),
                hostname: details.initiator,
                fileName: tab.title || "",
                id: generateId(),
                isAdditional: false
            };
            
            // Extract quality and URL from variant
            const parts = variant.split(/\s|,/);
            parts.forEach(part => {
                if (part.match("RESOLUTION=")) {
                    videoData.quality = part.split("=")[1];
                }
                if (part.match(/\.m3u8/)) {
                    // Handle relative/absolute URL resolution
                    videoData.url = resolveUrl(part, baseUrl);
                }
            });
            
            if (videoData.url) {
                addVideoLink(videoData);
            }
        }
    });
}
```

### URL Resolution Logic

```javascript
function resolveUrl(segmentUrl, baseUrl) {
    if (segmentUrl.match(/^https?:\/\//)) {
        return segmentUrl; // Absolute URL
    } else if (segmentUrl.match(/^\./) || !segmentUrl.match(/^\.?\//)) {
        // Relative to current directory
        const match = baseUrl.match(/\/[^\/]+\.m3u8/i);
        if (match?.index >= 0) {
            return baseUrl.slice(0, match.index) + "/" + segmentUrl.replace(/^\.?\//, "");
        }
    } else {
        // Relative to domain root
        return "https://" + getHostname(baseUrl) + "/" + segmentUrl.replace(/^\//, "");
    }
}
```

## Download System Architecture

### Video Link Data Structure

```javascript
const videoLink = {
    url: "https://example.com/video.m3u8",
    quality: "1080p", // or resolution like "1920x1080"
    playlist: true,   // true for M3U8, false for direct video
    stream: false,    // true for live streams, false for VOD
    hostname: "https://example.com",
    fileName: "Video Title",
    id: generateUniqueId(),
    isAdditional: false, // false for main videos, true for additional formats
    size: 1048576,    // file size in bytes
    extension: ".mp4" // or .m3u8 for playlists
};
```

### Download Process

1. **M3U8 Playlist Download**: Direct browser download of .m3u8 file
2. **Segment Processing**: User must manually process segments (qooly doesn't auto-download segments)
3. **FFmpeg Integration**: External tool required for segment concatenation

```javascript
downloadVideoLink(url, fileName) {
    const filename = fileName + ".mp4";
    chrome.downloads.download({
        url: url,
        filename: filename
    });
}
```

## Advanced Features

### Header Preservation

Qooly preserves request headers for authenticated content:

```javascript
async setHeaders(url, requestHeaders) {
    if (!requestHeaders?.length) return;
    
    const origin = new URL(url).origin;
    const headerModifications = requestHeaders.map(h => ({
        header: h.name,
        operation: "set", 
        value: h.value
    }));
    
    // Use Chrome's declarativeNetRequest API to modify headers
    chrome.declarativeNetRequest.updateSessionRules({
        addRules: [{
            id: generateRuleId(),
            priority: 1,
            action: {
                type: "modifyHeaders",
                requestHeaders: headerModifications
            },
            condition: {
                urlFilter: origin
            }
        }]
    });
}
```

### Tab Data Management

```javascript
class TabDataManager {
    constructor() {
        this.tabsData = {};
    }
    
    addVideoLinkToTab(videoLink, tabId, tabUrl) {
        if (!this.tabsData[tabId]) {
            this.tabsData[tabId] = {
                videoLinks: [],
                additionalLinks: [],
                url: ""
            };
        }
        
        // Reset data if URL changed
        if (tabUrl !== this.tabsData[tabId].url) {
            this.tabsData[tabId].videoLinks = [];
            this.tabsData[tabId].additionalLinks = [];
            this.tabsData[tabId].url = tabUrl;
        }
        
        // Add to appropriate category
        if (videoLink.isAdditional) {
            this.tabsData[tabId].additionalLinks.push(videoLink);
        } else {
            this.tabsData[tabId].videoLinks.push(videoLink);
        }
        
        this.updateExtensionIcon(tabId);
    }
}
```

## Site-Specific Integrations

### Vimeo Integration

```javascript
addVimeoLinkToTabsData(data, tabId, tabUrl) {
    const configUrl = `https://player.vimeo.com/video/${data.vid}/config`;
    
    fetch(configUrl).then(response => response.json()).then(config => {
        const videos = [];
        
        // Progressive downloads (direct MP4)
        if (config.request.files.progressive) {
            config.request.files.progressive.forEach(video => {
                videos.push({
                    fileName: data.title,
                    url: video.url,
                    quality: video.width + "p"
                });
            });
        }
        
        // HLS streams (M3U8)
        if (config.request.files.hls?.cdns) {
            for (let cdn in config.request.files.hls.cdns) {
                const url = config.request.files.hls.cdns[cdn].url;
                videos.push({
                    fileName: data.title,
                    url: url,
                    playlist: true,
                    quality: config.video?.height + "p" || "N/A"
                });
            }
        }
        
        this.addVideoLinks(videos, tabId, tabUrl);
    });
}
```

### Instagram Integration

```javascript
async fetchVideoDetails(shortcode, tabId) {
    const graphqlUrl = `https://www.instagram.com/graphql/query/?query_hash=55a3c4bad29e4e20c20ff4cdfd80f5b4&variables={"shortcode":"${shortcode}"}`;
    
    const response = await fetch(graphqlUrl);
    return response.json();
}
```

## Key Implementation Requirements for PySide6

1. **Network Request Interception**: Use `QWebEngineUrlRequestInterceptor`
2. **Header Preservation**: Store and replay authentication headers
3. **Content-Type Detection**: Monitor response headers for M3U8 MIME types
4. **Playlist Processing**: Parse M3U8 content to extract segments
5. **URL Resolution**: Handle relative URLs in playlists
6. **Stream Detection**: Identify live vs VOD content
7. **Download Management**: Queue and track download progress

This complete analysis shows that qooly's power comes from its comprehensive network monitoring, intelligent M3U8 processing, and robust URL resolution - all of which can be implemented in PySide6 using QtWebEngine's network interception capabilities.