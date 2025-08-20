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

        # Browser in drawer
        self.web_view = QWebEngineView()
        self.drawer_layout.addWidget(self.web_view)
        
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
        
        self.web_view.setUrl(QUrl(url))