"""
JavaScript Templates
Contains JavaScript code templates for M3U8 detection
Based on qooly's detection methods
"""

# XMLHttpRequest hook template (from qooly)
XHR_HOOK_TEMPLATE = """
// Hook XMLHttpRequest to catch M3U8 requests
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        if (url.toLowerCase().includes('.m3u8')) {
            console.log('M3U8_DETECTED_XHR: ' + url);
        }
        return originalOpen.apply(this, arguments);
    };
})();
"""

# Fetch API hook template (from qooly) 
FETCH_HOOK_TEMPLATE = """
// Hook fetch API to catch M3U8 requests
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const url = args[0];
        if (typeof url === 'string' && url.toLowerCase().includes('.m3u8')) {
            console.log('M3U8_DETECTED_FETCH: ' + url);
        }
        return originalFetch.apply(this, arguments);
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