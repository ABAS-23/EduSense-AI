import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QGraphicsDropShadowEffect, QVBoxLayout
from PyQt5.QtGui import QPixmap, QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer

# --- دالة جلب المسارات لضمان عمل الأيقونة في الـ EXE ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

DASHBOARD_IMG_FOLDER = "dashboard_images"
DASHBOARD_BG_FILES = ["1.jpg", "2.jpg", "3.jpg"]
SLIDE_INTERVAL = 8000

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduSense AI - Dashboard")
        self.setGeometry(100, 100, 1280, 760)
        
        # 🔥 إضافة الأيقونة للصفحة
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.bg_index = 0

        # ------------------ الخلفية ------------------
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())

        # ------------------ Overlay متدرج ------------------
        self.overlay = QLabel(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setStyleSheet("""
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, 
            stop:0 rgba(0, 0, 0, 220), stop:0.5 rgba(0, 0, 0, 80), stop:1 rgba(0, 0, 0, 120));
        """)
        self.overlay.lower()

        # ------------------ النصوص (Brand) ------------------
        self.title_label = QLabel("EduSense AI", self)
        self.title_label.setFont(QFont("Orbitron", 55, QFont.Bold)) # استخدام Orbitron للتناسق
        self.title_label.setStyleSheet("color: #00ff99; background: transparent;") 
        
        self.subtitle_label = QLabel("", self)
        self.subtitle_label.setFont(QFont("Segoe UI", 16))
        self.subtitle_label.setStyleSheet("color: #E0E0E0; background: transparent;")

        # ------------------ زر GET LIVE المطور ------------------
        self.get_btn = QPushButton("GET STARTED LIVE", self)
        self.get_btn.setFixedSize(280, 70)
        self.get_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.get_btn.setCursor(Qt.PointingHandCursor)
        self.get_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ff99;
                border: 3px solid #00ff99;
                border-radius: 15px;
            }
            QPushButton:hover {
                background-color: #00ff99;
                color: #0d0d0d;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(25)
        shadow.setColor(QColor(0, 255, 153, 150))
        shadow.setOffset(0, 0)
        self.get_btn.setGraphicsEffect(shadow)

        self.get_btn.clicked.connect(self.on_get_live)

        # ------------------ تحميل الخلفيات ------------------
        self.bg_paths = []
        if not os.path.exists(DASHBOARD_IMG_FOLDER): os.makedirs(DASHBOARD_IMG_FOLDER)
        for f in DASHBOARD_BG_FILES:
            path = os.path.join(DASHBOARD_IMG_FOLDER, f)
            if os.path.exists(path): self.bg_paths.append(path)

        if self.bg_paths:
            self.update_background()
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.next_background)
            self.timer.start(SLIDE_INTERVAL)

        self.arrange_widgets()

    def arrange_widgets(self):
        margin_left = int(self.width() * 0.08)
        self.title_label.move(margin_left, int(self.height() * 0.25))
        self.subtitle_label.move(margin_left, int(self.height() * 0.42))
        self.get_btn.move(margin_left, int(self.height() * 0.60))
        
        self.title_label.raise_()
        self.subtitle_label.raise_()
        self.get_btn.raise_()

    def resizeEvent(self, event):
        self.bg_label.resize(self.size())
        self.overlay.resize(self.size())
        self.arrange_widgets()

    def update_background(self):
        if not self.bg_paths: return
        pix = QPixmap(self.bg_paths[self.bg_index])
        scaled = pix.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self.bg_label.setPixmap(scaled)
        self.bg_label.lower()

    def next_background(self):
        if not self.bg_paths: return
        self.bg_index = (self.bg_index + 1) % len(self.bg_paths)
        self.update_background()

    def on_get_live(self):
        try:
            from app import EduSenseAI
            self.analysis_page = EduSenseAI()
            self.analysis_page.show()
            self.close()
        except Exception as e:
            print(f"Error opening analysis page: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Dashboard()
    win.show()
    sys.exit(app.exec_())