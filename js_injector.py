"""
JavaScript Injection Manager
Handles injecting M3U8 detection scripts into web pages
"""

from PySide6.QtCore import QObject, Signal
from js_templates import FULL_DETECTION_SCRIPT

class JSInjector(QObject):
    """
    Manages JavaScript injection for M3U8 detection
    Based on qooly's JavaScript hooks
    """
    
    # Signal emitted when JS detects M3U8
    js_m3u8_detected = Signal(dict)  # M3U8 URL and info from JavaScript
    
    def __init__(self):
        super().__init__()
        
    def get_detection_script(self):
        """
        Returns JavaScript code for M3U8 detection
        Uses templates from js_templates.py based on Qooly's implementation
        """
        return FULL_DETECTION_SCRIPT
        
    def inject_into_page(self, web_page):
        """
        Inject M3U8 detection script into web page
        Step 4: JavaScript injection implementation
        """
        script = self.get_detection_script()
        print("🔍 JSInjector: Injecting M3U8 detection script into page")
        web_page.runJavaScript(script)
        
    def handle_js_console_message(self, level, message, line_number, source_id):
        """
        Handle console messages from injected JavaScript
        Step 4: Parse M3U8 URLs from JS console messages
        """
        # Look for our M3U8 detection markers
        m3u8_markers = [
            'M3U8_DETECTED_XHR: ',
            'M3U8_DETECTED_FETCH: ', 
            'M3U8_DETECTED_VIDEO: '
        ]
        
        for marker in m3u8_markers:
            if marker in message:
                # Extract URL and detection method
                url = message.replace(marker, '').strip()
                method_map = {
                    'M3U8_DETECTED_XHR: ': 'javascript_xhr',
                    'M3U8_DETECTED_FETCH: ': 'javascript_fetch',
                    'M3U8_DETECTED_VIDEO: ': 'javascript_video_element'
                }
                
                detection_method = method_map.get(marker, 'javascript_unknown')
                
                # Create stream info dict
                stream_info = {
                    'url': url,
                    'detection_method': detection_method,
                    'page_url': '',  # Will be populated by GUI
                    'page_title': '',  # Will be populated by GUI
                    'quality': '',   # Will be determined in processing
                    'is_master_playlist': False,  # Will be determined in processing
                    'timestamp': None
                }
                
                print(f"🔍 JSInjector: Detected M3U8 via {detection_method}: {url}")
                self.js_m3u8_detected.emit(stream_info)
                return
                
        # Debug: Log other console messages (can be disabled later)
        if 'M3U8' in message.upper():
            print(f"🔍 JSInjector: Console message (may contain M3U8): {message}")
            
    def create_custom_detection_script(self, additional_patterns=None):
        """
        Create a customized detection script with additional patterns
        Can be used for site-specific detection if needed
        """
        base_script = self.get_detection_script()
        
        if additional_patterns:
            pattern_script = f"""
            // Additional M3U8 patterns
            const additionalPatterns = {additional_patterns};
            additionalPatterns.forEach(pattern => {{
                if (url.toLowerCase().includes(pattern)) {{
                    console.log('M3U8_DETECTED_PATTERN: ' + url);
                }}
            }});
            """
            return base_script + pattern_script
            
        return base_script