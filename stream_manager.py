"""
Stream Management
Manages detected streams and coordinates between detection, processing, and downloading
"""

from PySide6.QtCore import QObject, Signal

class StreamManager(QObject):
    """
    Central manager for detected M3U8 streams
    Coordinates between detection, processing, and downloading
    """
    
    # Signals
    stream_added = Signal(dict)  # New stream detected
    stream_updated = Signal(dict)  # Stream info updated
    
    def __init__(self):
        super().__init__()
        self.detected_streams = []
        
    def add_detected_stream(self, stream_info):
        """
        Add a newly detected M3U8 stream
        TODO: Implement stream management
        """
        pass
        
    def get_streams(self):
        """
        Get all detected streams
        """
        return self.detected_streams
        
    def clear_streams(self):
        """
        Clear all detected streams
        """
        self.detected_streams.clear()