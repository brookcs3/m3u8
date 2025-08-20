"""
JavaScript Templates
Contains JavaScript code templates for M3U8 detection
Based on qooly's detection methods
"""

# XMLHttpRequest hook template (from qooly's actual implementation)
XHR_HOOK_TEMPLATE = """
// Hook XMLHttpRequest to catch M3U8 requests - Qooly's comprehensive approach
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        this._url = url;
        this._method = method;
        return originalOpen.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function(data) {
        const xhr = this;
        const url = this._url;
        
        // Qooly's URL pattern detection (broader than just .m3u8)
        if (url && (
            url.toLowerCase().includes('.m3u8') ||
            url.toLowerCase().includes('playlist') ||
            url.toLowerCase().includes('manifest') ||
            url.toLowerCase().includes('/hls/') ||
            url.toLowerCase().includes('master') ||
            url.toLowerCase().includes('stream')
        )) {
            console.log('M3U8_DETECTED_XHR: ' + url);
        }
        
        // Qooly's response header monitoring - THE KEY PART
        xhr.addEventListener('readystatechange', function() {
            if (xhr.readyState === 4 && xhr.status >= 200 && xhr.status < 300) {
                const contentType = xhr.getResponseHeader('content-type');
                if (contentType && [
                    'application/vnd.apple.mpegurl',
                    'application/x-mpegURL',
                    'application/mpegurl',
                    'audio/mpegurl',
                    'audio/x-mpegurl',
                    'application/vnd.apple.mpegurl.audio'
                ].some(type => contentType.toLowerCase().includes(type.toLowerCase()))) {
                    console.log('M3U8_DETECTED_XHR_CONTENT_TYPE: ' + url);
                }
            }
        });
        
        return originalSend.apply(this, arguments);
    };
})();
"""

# Fetch API hook template (from qooly's actual implementation)
FETCH_HOOK_TEMPLATE = """
// Hook fetch API to catch M3U8 requests - Qooly's comprehensive approach
(function() {
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        const url = typeof args[0] === 'string' ? args[0] : args[0]?.url;
        
        // Qooly's URL pattern detection (broader patterns)
        if (url && (
            url.toLowerCase().includes('.m3u8') ||
            url.toLowerCase().includes('playlist') ||
            url.toLowerCase().includes('manifest') ||
            url.toLowerCase().includes('/hls/') ||
            url.toLowerCase().includes('master') ||
            url.toLowerCase().includes('stream')
        )) {
            console.log('M3U8_DETECTED_FETCH: ' + url);
        }
        
        // Call original fetch and check response headers
        const response = await originalFetch.apply(this, args);
        
        // Qooly's response header monitoring - THE KEY PART
        if (response.ok) {
            const contentType = response.headers.get('content-type');
            if (contentType && [
                'application/vnd.apple.mpegurl',
                'application/x-mpegURL', 
                'application/mpegurl',
                'audio/mpegurl',
                'audio/x-mpegurl',
                'application/vnd.apple.mpegurl.audio'
            ].some(type => contentType.toLowerCase().includes(type.toLowerCase()))) {
                console.log('M3U8_DETECTED_FETCH_CONTENT_TYPE: ' + url);
            }
        }
        
        return response;
    };
})();
"""

# Video element monitoring template (from qooly)
VIDEO_MONITOR_TEMPLATE = """
// Monitor video element src changes
(function() {
    function hookVideoElements() {
        const videos = document.querySelectorAll('video');
        videos.forEach(video => {
            // Monitor src attribute changes
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'attributes' && mutation.attributeName === 'src') {
                        const src = video.src;
                        if (src && src.toLowerCase().includes('.m3u8')) {
                            console.log('M3U8_DETECTED_VIDEO: ' + src);
                        }
                    }
                });
            });
            observer.observe(video, { attributes: true });
            
            // Check current src
            if (video.src && video.src.toLowerCase().includes('.m3u8')) {
                console.log('M3U8_DETECTED_VIDEO: ' + video.src);
            }
        });
    }
    
    // Run immediately and watch for new video elements
    hookVideoElements();
    
    // Watch for dynamically added video elements
    const documentObserver = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // Element node
                    if (node.tagName === 'VIDEO') {
                        hookVideoElements();
                    } else if (node.querySelectorAll) {
                        const newVideos = node.querySelectorAll('video');
                        if (newVideos.length > 0) {
                            hookVideoElements();
                        }
                    }
                }
            });
        });
    });
    
    documentObserver.observe(document.body, { childList: true, subtree: true });
})();
"""

# Combined detection script
FULL_DETECTION_SCRIPT = f"""
// M3U8 Detection Script (Based on Qooly)
(function() {{
    {XHR_HOOK_TEMPLATE}
    {FETCH_HOOK_TEMPLATE}
    {VIDEO_MONITOR_TEMPLATE}
    
    console.log('M3U8 detection script fully loaded');
}})();
"""