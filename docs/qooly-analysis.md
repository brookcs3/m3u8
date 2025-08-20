# Qooly Extension M3U8 Detection Analysis

## Overview

This document provides a comprehensive analysis of how the Qooly Chrome extension detects M3U8 playlist files from web traffic. This analysis is based on reverse engineering the extension's background script (`bg.js`) and understanding its network interception mechanisms.

## Core Architecture

### 1. Network Request Interception

Qooly uses Chrome's `webRequest` API to intercept all network traffic:

```javascript
chrome.webRequest.onHeadersReceived.addListener(function(details) {
  // M3U8 detection logic here
}, { 
  urls: ["<all_urls>"] 
}, ["responseHeaders", "extraHeaders"]);
```

**Key Points:**
- Monitors **ALL** network requests across all websites
- Uses `onHeadersReceived` to inspect response headers
- Requires `responseHeaders` and `extraHeaders` permissions

### 2. Dual Detection Strategy

Qooly employs a two-pronged approach to detect M3U8 files:

#### A. URL-Based Detection
```javascript
details.url.match(".m3u8")
```

#### B. Content-Type Header Detection
```javascript
const contentType = details.responseHeaders.find(header => 
  header.name.toLowerCase() === "content-type"
)?.value;

const m3u8ContentTypes = [
  "application/vnd.apple.mpegurl",
  "audio/mpegurl", 
  "application/mpegurl",
  "application/x-mpegurl",
  "audio/x-mpegurl",
  "application/vnd.apple.mpegurl.audio"
];

const isM3U8ContentType = m3u8ContentTypes.includes(contentType);
```

**Detection Logic:**
```javascript
if (details.url.match(".m3u8") || isM3U8ContentType) {
  // Process as M3U8
}
```

### 3. M3U8 Content Analysis

When an M3U8 is detected, Qooly fetches and analyzes the playlist content:

#### Step 1: Fetch Playlist Content
```javascript
fetch(details.url)
  .then(response => response.text())
  .then(content => {
    // Parse M3U8 content
  });
```

#### Step 2: Parse Master Playlists
For master playlists containing multiple quality variants:

```javascript
if (content.match(/#EXT-X-STREAM-INF:/)) {
  const segments = content.split(/#EXT-X-STREAM-INF:/);
  
  segments.forEach(segment => {
    const parts = segment.split(/\s|,/);
    let quality = "";
    let url = "";
    
    parts.forEach(part => {
      if (part.match("RESOLUTION=")) {
        quality = part.split("=")[1]; // e.g., "1920x1080"
      }
      if (part.match(/\.m3u8/)) {
        url = extractUrl(part);
      }
    });
    
    // Create video link object
    const videoLink = {
      url: url,
      quality: quality,
      playlist: true,
      stream: isLiveStream,
      hostname: details.initiator,
      fileName: tabTitle,
      id: generateId(),
      isAdditional: false
    };
  });
}
```

#### Step 3: Parse Media Playlists
For media playlists containing individual segments:

```javascript
if (content.match(/#EXTINF/)) {
  const videoLink = {
    url: details.url,
    quality: "",
    playlist: true,
    stream: isLiveStream,
    hostname: details.initiator,
    fileName: tabTitle,
    id: generateId(),
    isAdditional: false
  };
}
```

### 4. URL Resolution Logic

Qooly handles different URL formats in M3U8 playlists:

#### Absolute URLs
```javascript
if (url.match(/^https?:\/\//)) {
  // Use URL as-is
  resolvedUrl = url;
}
```

#### Relative URLs (same directory)
```javascript
else if (url.match(/^\./) || !url.match(/^\.?\//)) {
  const baseMatch = baseUrl.match(/\/[^\/]+\.m3u8/i);
  if (baseMatch?.index >= 0) {
    resolvedUrl = baseUrl.slice(0, baseMatch.index) + "/" + 
                  url.replace(/^\.?\//, "");
  }
}
```

#### Root-relative URLs
```javascript
else {
  const hostname = extractHostname(baseUrl);
  resolvedUrl = "https://" + hostname + "/" + url.replace(/^\//, "");
}
```

### 5. Live Stream Detection

Qooly determines if a stream is live or VOD by analyzing playlist content:

```javascript
async function isStream(tab, url) {
  try {
    const content = await fetch(url).then(r => r.text());
    
    // VOD indicators
    if (content.match("#EXT-X-ENDLIST")) return false;
    if (content.match("#EXT-X-PLAYLIST-TYPE:VOD")) return false;
    
    // Live indicators  
    if (content.match("#EXT-X-PLAYLIST-TYPE:LIVE")) return true;
    if (content.match("#EXT-X-PLAYLIST-TYPE:EVENT")) return true;
    
    // Site-specific live detection
    if (tab.url.match(/^https?:\/\/play\.afreecatv\.com/)) return true;
    if (tab.url.match(/^https?:\/\/www\.mildom\.com/)) return true;
    if (tab.url.match(/^https?:\/\/tv\.kakao\.com/)) return true;
    // ... more site-specific rules
    
    return false; // Default to VOD
  } catch (error) {
    return false;
  }
}
```

### 6. Request Deduplication

To prevent processing the same request multiple times:

```javascript
if (this.fetching[details.requestId]) {
  return; // Already processing this request
}
this.fetching[details.requestId] = true;

// Process request...

// Cleanup
fetch(url).finally(() => {
  delete this.fetching[details.requestId];
});
```

### 7. Header Preservation

Qooly preserves original request headers when fetching M3U8 content:

```javascript
chrome.webRequest.onBeforeSendHeaders.addListener((details) => {
  this.requests[details.requestId] = {
    requestHeaders: details.requestHeaders
  };
}, { urls: ["<all_urls>"] }, ["requestHeaders", "extraHeaders"]);

// Later, when fetching M3U8:
const originalHeaders = this.requests[details.requestId]?.requestHeaders || [];
await this.setHeaders(url, originalHeaders);
```

## Domain Filtering

Qooly ignores certain domains to avoid unnecessary processing:

```javascript
const ignoredDomains = [
  /^https?:\/\/(.*\.)?youtube\.com/,
  /^https?:\/\/(.*\.)?globo\.com/,
  /^https?:\/\/qooly\.com/,
  /^https?:\/\/bastyon\.com/,
  /^https?:\/\/vimeo\.com/
];
```

## Data Structure

Each detected M3U8 is stored with this structure:

```javascript
const videoLink = {
  url: "https://example.com/playlist.m3u8",
  quality: "1920x1080",           // Resolution or quality indicator
  playlist: true,                 // Always true for M3U8
  stream: false,                  // true for live, false for VOD
  hostname: "https://site.com",   // Initiator/referrer
  fileName: "Video Title",        // Tab title or extracted name
  id: "abc123",                   // Unique identifier
  isAdditional: false             // Classification flag
};
```

## Key Insights for Implementation

### 1. Comprehensive Detection
- Must check both URL patterns AND Content-Type headers
- Content-Type detection catches M3U8s that don't have `.m3u8` in URL

### 2. Content Parsing is Essential
- URL detection alone is insufficient
- Must fetch and parse playlist content to extract quality variants
- Need to handle both master playlists and media playlists

### 3. URL Resolution is Complex
- M3U8 playlists often contain relative URLs
- Need robust URL resolution logic for different scenarios

### 4. Live vs VOD Detection
- Important for user experience
- Requires parsing playlist markers and site-specific rules

### 5. Performance Considerations
- Request deduplication prevents redundant processing
- Domain filtering reduces unnecessary overhead
- Header preservation ensures successful fetches

## Implementation Challenges in QtWebEngine

1. **No Direct webRequest API**: Must use `QWebEngineUrlRequestInterceptor`
2. **Limited Header Access**: QtWebEngine provides less header information
3. **JavaScript Context**: May need to combine network interception with content script injection
4. **Async Processing**: Need to handle async M3U8 content fetching properly

## Recommended Approach for PySide6

1. Use `QWebEngineUrlRequestInterceptor` for initial URL detection
2. Implement content fetching and parsing in Python
3. Add JavaScript injection for additional detection coverage
4. Create proper async handling for M3U8 content analysis
5. Implement the same URL resolution logic as Qooly
6. Add domain filtering for performance optimization

This analysis provides the foundation for implementing Qooly-equivalent M3U8 detection in a PySide6 application.