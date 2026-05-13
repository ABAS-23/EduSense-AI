import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QFrame,
    QVBoxLayout, QGraphicsDropShadowEffect, QProgressBar
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer

# --- إعدادات المسارات الاحترافية ---
def resource_path(relative_path):
    """ تجلب المسار الصحيح للملفات لضمان عمل الأيقونات والصور بعد التحويل لـ EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

BG_FOLDER = "bg_images"
BG_IMAGE = "mountain.jpg"

class WelcomeScreen(QWidget):
    def __init__(self):
        super().__init__()
        # 1. إعدادات النافذة الأساسية
        self.setWindowTitle("EduSense AI - System Initialize")
        self.setFixedSize(1280, 760) # تثبيت الحجم يعطي شعوراً بالاستقرار في شاشة الترحيب
        
        #  سطر الأيقونة الاحترافي
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # -------------------- الخلفية --------------------
        self.bg_label = QLabel(self)
        self.bg_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_label.setScaledContents(True)

        img_full_path = resource_path(os.path.join(BG_FOLDER, BG_IMAGE))
        if os.path.exists(img_full_path):
            self.bg_label.setPixmap(QPixmap(img_full_path))

        # -------------------- Overlay النيون --------------------
        self.overlay = QLabel(self)
        self.overlay.setGeometry(0, 0, self.width(), self.height())
        self.overlay.setStyleSheet("""
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 rgba(10, 10, 30, 240),
                stop:1 rgba(26, 26, 46, 210)
            );
        """)

        # -------------------- صندوق المحتوى --------------------
        self.center_box = QFrame(self)
        self.center_box.setFixedSize(700, 450)
        
        self.layout = QVBoxLayout(self.center_box)
        self.layout.setSpacing(10)

        # العنوان بتأثير النيون الأخضر
        self.title_lbl = QLabel("EDUSENSE AI")
        self.title_lbl.setFont(QFont("Orbitron", 50, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("color: #00ff99; letter-spacing: 5px;")

        self.subtitle = QLabel("NEURAL NETWORK ENGINE v1.0")
        self.subtitle.setFont(QFont("Consolas", 14))
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("color: #00e5ff; font-weight: 200;")

        # -------------------- شريط التحميل المدمج --------------------
        self.pbar = QProgressBar()
        self.pbar.setFixedSize(400, 6)
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: #d500f9;
                border-radius: 3px;
            }
        """)
        self.pbar.hide()

        self.status_lbl = QLabel("SYSTEM READY")
        self.status_lbl.setFont(QFont("Consolas", 10))
        self.status_lbl.setStyleSheet("color: #888;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.hide()

        # -------------------- زر التفعيل --------------------
        self.start_btn = QPushButton("INITIALIZE SYSTEM")
        self.start_btn.setFixedSize(300, 65)
        self.start_btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #00ff99;
                border: 2px solid #00ff99;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 153, 0.1);
                border: 2px solid #00e5ff;
                color: #00e5ff;
            }
        """)

        # إضافة العناصر
        self.layout.addStretch()
        self.layout.addWidget(self.title_lbl)
        self.layout.addWidget(self.subtitle)
        self.layout.addSpacing(40)
        self.layout.addWidget(self.start_btn, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.pbar, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.status_lbl, alignment=Qt.AlignCenter)
        self.layout.addStretch()

        self.start_btn.clicked.connect(self.start_loading_sequence)
        
        # توسيط الصندوق يدوياً في البداية
        self.center_box.move((1280 - 700) // 2, (760 - 450) // 2)

    def start_loading_sequence(self):
        self.start_btn.hide()
        self.pbar.show()
        self.status_lbl.show()
        
        self.progress_value = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(40) 

    def update_progress(self):
        self.progress_value += 1
        self.pbar.setValue(self.progress_value)
        
        if self.progress_value == 15: self.status_lbl.setText("LOADING AI MODELS...")
        if self.progress_value == 45: self.status_lbl.setText("BOOTING GPU ACCELERATION...")
        if self.progress_value == 75: self.status_lbl.setText("OPTIMIZING INTERFACE...")
        if self.progress_value == 95: self.status_lbl.setText("SYSTEM ONLINE.")

        if self.progress_value >= 100:
            self.timer.stop()
            self.open_dashboard()

    def open_dashboard(self):
        try:
            from dashboard import Dashboard
            self.dashboard_window = Dashboard()
            self.dashboard_window.show()
            self.close()
        except ImportError:
            print("Dashboard file not found! Make sure dashboard.py exists.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = WelcomeScreen()
    win.show()
    sys.exit(app.exec_())