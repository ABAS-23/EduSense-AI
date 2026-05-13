import sys
import cv2
import numpy as np
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFrame, QListWidget, QListWidgetItem
)
from PyQt5.QtGui import QImage, QPixmap, QFont, QIcon
from PyQt5.QtCore import QTimer, Qt, QRect, QThread, pyqtSignal, pyqtSlot
from deepface import DeepFace
import pyqtgraph as pg

# --- إعدادات البيئة وجلب المسارات ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

def resource_path(relative_path):
    """ دالة جلب المسار الصحيح للأيقونة لضمان عملها بعد التحويل لـ EXE """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 1. خيط المعالجة الخلفي (AI Thread)
class AnalysisWorker(QThread):
    result_ready = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.frame = None
        self.is_running = True

    def update_frame(self, frame):
        self.frame = frame

    def run(self):
        while self.is_running:
            if self.frame is not None:
                try:
                    results = DeepFace.analyze(
                        self.frame,
                        actions=['emotion'],
                        enforce_detection=False,
                        detector_backend='opencv',
                        silent=True
                    )
                    if not isinstance(results, list):
                        results = [results]
                    self.result_ready.emit(results)
                    self.frame = None 
                except:
                    pass
            self.msleep(10)

# 2. هيكل بيانات الوجه
class FaceData:
    def __init__(self, face_id):
        self.face_id = face_id
        self.rect = QRect()
        self.emotions = {}
        self.dominant = "Neutral"

# 3. الواجهة الرئيسية للمحرك
class EduSenseAI(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_webcam)

        self.worker = AnalysisWorker()
        self.worker.result_ready.connect(self.on_analysis_received)
        self.worker.start()

        self.emotion_names = ['angry','disgust','fear','happy','sad','surprise','neutral']
        self.detected_faces = []
        self.selected_face_id = None
        self.frame_count = 0
        self.last_analysis_results = []

    def init_ui(self):
        self.setWindowTitle("🌌 EduSense AI - Analysis Engine")
        self.setGeometry(100, 50, 1400, 850)
        
        # إضافة الأيقونة
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # تنسيق Cyberpunk
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #0d0d0d, stop:1 #1a1a2e);
                color: #E0E0E0;
            }
            QPushButton {
                background-color: #00ff99;
                color: #0d0d0d;
                border-radius: 12px;
                font-weight: bold;
                padding: 10px;
                border: 1px solid #00ff99;
            }
            QPushButton:hover {
                background-color: #00e5ff;
                border: 1px solid #00e5ff;
            }
            QListWidget {
                background-color: rgba(26, 26, 46, 0.8);
                border: 2px solid #9c27b0;
                border-radius: 15px;
                color: #00ff99;
            }
            QListWidget::item:selected {
                background-color: #d500f9;
                color: white;
            }
        """)

        # تجميع الواجهة (Layouts)
        main_layout = QVBoxLayout(self)

        # الشريط العلوي
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("← EXIT")
        self.back_btn.setFixedSize(100, 40)
        self.back_btn.setCursor(Qt.PointingHandCursor)
        self.back_btn.clicked.connect(self.go_back)

        title = QLabel("EDUSENSE AI | LIVE ANALYTICS")
        title.setFont(QFont("Orbitron", 22, QFont.Bold))
        title.setStyleSheet("color: #00ff99;")
        
        top_bar.addWidget(self.back_btn)
        top_bar.addStretch()
        top_bar.addWidget(title)
        top_bar.addStretch()

        # منطقة العرض الوسطى
        content_layout = QHBoxLayout()

        # الكاميرا
        self.video_label = QLabel()
        self.video_label.setFixedSize(850, 600)
        self.video_label.setStyleSheet("border: 3px solid #9c27b0; border-radius: 20px; background: #000;")
        self.video_label.mousePressEvent = self.on_video_click

        self.overlay_label = QLabel("SYSTEM READY", self.video_label)
        self.overlay_label.setGeometry(15, 15, 250, 35)
        self.overlay_label.setStyleSheet("background-color: rgba(0, 229, 255, 180); color: #000; border-radius: 8px; padding: 5px; font-weight: bold;")

        # الجانب الأيمن (الرسم البياني والقائمة)
        right_panel = QVBoxLayout()
        
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('transparent')
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.setTitle("Select a student to track", color="#00ff99", size="12pt")

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)

        right_panel.addWidget(self.plot_widget, 2)
        right_panel.addWidget(self.sidebar, 1)

        content_layout.addWidget(self.video_label, 3)
        content_layout.addLayout(right_panel)

        # الأزرار السفلية
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ START CAMERA")
        self.btn_stop = QPushButton("⏹ STOP CAMERA")
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)

        main_layout.addLayout(top_bar)
        main_layout.addLayout(content_layout)
        main_layout.addLayout(btn_layout)

        self.btn_start.clicked.connect(self.start_camera)
        self.btn_stop.clicked.connect(self.stop_camera)

    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            self.timer.start(30)
            self.overlay_label.setText("SESSION ACTIVE")

    def stop_camera(self):
        self.timer.stop()
        if self.cap: self.cap.release(); self.cap = None
        self.video_label.clear()
        self.sidebar.clear()
        self.overlay_label.setText("SYSTEM IDLE")

    def process_webcam(self):
        if self.cap is None: return
        ret, frame = self.cap.read()
        if not ret: return

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (850, 600))
        self.frame_count += 1

        if self.frame_count % 5 == 0:
            self.worker.update_frame(frame.copy())

        self.detected_faces = []
        self.sidebar.clear()
        for i, res in enumerate(self.last_analysis_results):
            region = res['region']
            x, y, w, h = region['x'], region['y'], region['w'], region['h']
            face_id = f"Student {i+1}"
            is_selected = (self.selected_face_id == face_id)
            color = (0, 255, 153) if is_selected else (156, 39, 176)

            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, face_id, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            f_data = FaceData(face_id)
            f_data.rect = QRect(x, y, w, h)
            f_data.dominant = res['dominant_emotion']
            f_data.emotions = res['emotion']
            self.detected_faces.append(f_data)

            self.sidebar.addItem(f"💠 {face_id} | {f_data.dominant.upper()}")

            if is_selected:
                self.update_live_plot(f_data)
                self.overlay_label.setText(f"TRACKING: {face_id}")

        rgb_img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        q_img = QImage(rgb_img.data, 850, 600, 850*3, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

    @pyqtSlot(list)
    def on_analysis_received(self, results):
        self.last_analysis_results = results

    def on_video_click(self, event):
        for face in self.detected_faces:
            if face.rect.contains(event.pos()):
                self.selected_face_id = face.face_id
                break

    # 🔥 تحديث الجدول البياني بالعنوان الديناميكي المطور
    def update_live_plot(self, face):
        self.plot_widget.clear()
        
        # جلب القيم والأسماء
        vals = [face.emotions.get(e, 0) for e in self.emotion_names]
        
        # تحديد أعلى نسبة مئوية وتقريبها
        dominant_em = face.dominant.upper()
        max_val = round(max(vals), 1)
        
        # تحديث العنوان ليظهر: DOMINANT: HAPPY (75.5%)
        dynamic_title = f"DOMINANT: {dominant_em} ({max_val}%)"
        self.plot_widget.setTitle(dynamic_title, color="#00ff99", size="14pt")
        
        # رسم الأعمدة
        bar = pg.BarGraphItem(x=np.arange(len(self.emotion_names)), height=vals, width=0.5, brush='#00e5ff')
        self.plot_widget.addItem(bar)
        
        ax = self.plot_widget.getAxis('bottom')
        ax.setTicks([[(i, name.upper()) for i, name in enumerate(self.emotion_names)]])

    def go_back(self):
        self.stop_camera()
        self.close()

    def closeEvent(self, event):
        self.stop_camera()
        self.worker.is_running = False
        self.worker.wait()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EduSenseAI()
    window.show()
    sys.exit(app.exec_())