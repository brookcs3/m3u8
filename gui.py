import sys
from PySide6.QtCore import QUrl, Slot
from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QLineEdit,
    QHBoxLayout,
    QFrame,
    QTextEdit,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile
from m3u8_detector import M3U8Detector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M3U8 Video Downloader")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Main content area
        self.main_content = QWidget()
        self.content_layout = QVBoxLayout(self.main_content)
        
        self.browser_button = QPushButton("Open Browser")
        self.browser_button.clicked.connect(self.toggle_drawer)
        self.content_layout.addWidget(self.browser_button)
        
        self.content_area = QTextEdit()
        self.content_area.setPlaceholderText("🎯 M3U8 Video Downloader\n\n1. Click 'Open Browser'\n2. Navigate to a video site\n3. Detected streams will appear here")
        self.content_layout.addWidget(self.content_area)
        
        self.main_layout.addWidget(self.main_content)

        # Browser drawer (initially hidden)
        self.drawer = QFrame()
        self.drawer.setFixedWidth(500)
        self.drawer.setStyleSheet("QFrame { border-left: 1px solid #ccc; background-color: #f5f5f5; }")
        
        self.drawer_layout = QVBoxLayout(self.drawer)
        
        # Close button in drawer
        self.close_button = QPushButton("Close Browser")
        self.close_button.clicked.connect(self.toggle_drawer)
        self.drawer_layout.addWidget(self.close_button)
        
        # URL input in drawer
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter URL")
        self.url_input.returnPressed.connect(self.navigate_to_url)
        
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.navigate_to_url)
        
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.go_button)
        self.drawer_layout.addLayout(url_layout)

        # Browser in drawer with M3U8 detection
        self.web_view = QWebEngineView()
        
        # Set up M3U8 detector
        self.profile = QWebEngineProfile.defaultProfile()
        self.m3u8_detector = M3U8Detector()
        self.profile.setUrlRequestInterceptor(self.m3u8_detector)
        
        # Connect detector signal to our handler
        self.m3u8_detector.m3u8_detected.connect(self.on_m3u8_detected)
        
        self.drawer_layout.addWidget(self.web_view)
        
        # Store detected streams
        self.detected_streams = []
        
        self.main_layout.addWidget(self.drawer)
        
        # Initially hide drawer
        self.drawer_visible = False
        self.drawer.setVisible(False)

    def toggle_drawer(self):
        if self.drawer_visible:
            # Hide drawer and shrink window
            self.drawer.setVisible(False)
            self.browser_button.setText("Open Browser")
            self.drawer_visible = False
            
            # Shrink window
            current_geometry = self.geometry()
            new_width = current_geometry.width() - 500
            self.resize(new_width, current_geometry.height())
            
        else:
            # Show drawer and expand window
            self.drawer.setVisible(True)
            self.browser_button.setText("Browser Open")
            self.drawer_visible = True
            
            # Expand window
            current_geometry = self.geometry()
            new_width = current_geometry.width() + 500
            self.resize(new_width, current_geometry.height())

    def navigate_to_url(self):
        url = self.url_input.text()
        if not url:
            return
            
        if not url.startswith("http"):
            url = "http://" + url
        
        # Clear previous detections when navigating to new page
        self.m3u8_detector.clear_detected_urls()
        self.detected_streams.clear()
        
        self.web_view.setUrl(QUrl(url))
        
        # Update content area to show we're ready for detection
        self.content_area.setText("🎯 M3U8 Detection Active\n\nNavigating to: " + url + "\n\nWaiting for M3U8 streams to be detected...")
        
    @Slot(dict)
    def on_m3u8_detected(self, stream_info):
        """
        Handler for when M3U8 stream is detected
        """
        # Add current page context to stream info
        current_url = self.web_view.url().toString()
        current_title = self.web_view.page().title()
        
        stream_info['page_url'] = current_url
        stream_info['page_title'] = current_title
        
        # Add to our detected streams list
        self.detected_streams.append(stream_info)
        
        # Update the display
        self.update_streams_display()
        
        print(f"🎯 GUI: M3U8 stream detected from {stream_info['detection_method']}: {stream_info['url']}")
        
    def update_streams_display(self):
        """
        Update the content area with detected streams
        """
        if not self.detected_streams:
            self.content_area.setText("🎯 M3U8 Detection Active\n\nNo streams detected yet...")
            return
            
        # Build display text
        display_text = f"🎯 DETECTED M3U8 STREAMS ({len(self.detected_streams)})\n"
        display_text += "=" * 50 + "\n\n"
        
        for i, stream in enumerate(self.detected_streams, 1):
            display_text += f"📺 Stream #{i}\n"
            display_text += f"   URL: {stream['url']}\n"
            display_text += f"   Method: {stream['detection_method']}\n"
            display_text += f"   Page: {stream['page_title']}\n"
            display_text += f"   From: {stream['page_url']}\n"
            display_text += "-" * 40 + "\n\n"
            
        self.content_area.setText(display_text)
        
        # Auto-scroll to bottom to show latest detection
        cursor = self.content_area.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.content_area.setTextCursor(cursor)