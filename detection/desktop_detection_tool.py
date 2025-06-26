#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Insect Detection Tool
เครื่องมือตรวจจับแมลงแบบ desktop application
"""

import sys
import os
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional

try:
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *
except ImportError:
    print("PySide6 not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6"])
    from PySide6.QtWidgets import *
    from PySide6.QtCore import *
    from PySide6.QtGui import *

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:
    print("Ultralytics not installed. Please install it first.")
    YOLO = None

class DetectionThread(QThread):
    """Thread for running detection"""
    
    frame_ready = Signal(np.ndarray, list)  # Signal for new frame with detections
    fps_updated = Signal(float)  # Signal for FPS update
    error_occurred = Signal(str)  # Signal for errors
    
    def __init__(self, model_path, source, confidence_threshold=0.5):
        super().__init__()
        self.model_path = model_path
        self.source = source  # Camera ID or image/video path
        self.confidence_threshold = confidence_threshold
        self.running = False
        self.model = None
        
    def run(self):
        """Run detection"""
        try:
            # Load model
            if YOLO is None:
                self.error_occurred.emit("YOLO not available. Please install ultralytics.")
                return
                
            self.model = YOLO(self.model_path)
            
            # Open source
            if isinstance(self.source, int):
                # Camera
                cap = cv2.VideoCapture(self.source)
                if not cap.isOpened():
                    self.error_occurred.emit(f"Cannot open camera {self.source}")
                    return
            else:
                # Image or video file
                source_path = Path(self.source)
                if not source_path.exists():
                    self.error_occurred.emit(f"File not found: {self.source}")
                    return
                    
                if source_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                    # Single image
                    self.process_single_image(source_path)
                    return
                else:
                    # Video file
                    cap = cv2.VideoCapture(str(source_path))
                    if not cap.isOpened():
                        self.error_occurred.emit(f"Cannot open video: {self.source}")
                        return
            
            # Process frames
            self.running = True
            fps_counter = 0
            fps_start_time = time.time()
            
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Run detection
                results = self.model(frame, conf=self.confidence_threshold, verbose=False)
                
                # Process results
                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = self.model.names[class_id]
                            
                            detections.append({
                                'bbox': (x1, y1, x2, y2),
                                'confidence': confidence,
                                'class_id': class_id,
                                'class_name': class_name
                            })
                
                # Emit frame with detections
                self.frame_ready.emit(frame, detections)
                
                # Calculate FPS
                fps_counter += 1
                current_time = time.time()
                if current_time - fps_start_time >= 1.0:
                    fps = fps_counter / (current_time - fps_start_time)
                    self.fps_updated.emit(fps)
                    fps_counter = 0
                    fps_start_time = current_time
                
                # Small delay to prevent overwhelming
                self.msleep(30)
            
            cap.release()
            
        except Exception as e:
            self.error_occurred.emit(f"Detection error: {str(e)}")
    
    def process_single_image(self, image_path):
        """Process single image"""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                self.error_occurred.emit(f"Cannot load image: {image_path}")
                return
            
            # Run detection
            results = self.model(image, conf=self.confidence_threshold, verbose=False)
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        detections.append({
                            'bbox': (x1, y1, x2, y2),
                            'confidence': confidence,
                            'class_id': class_id,
                            'class_name': class_name
                        })
            
            # Emit result
            self.frame_ready.emit(image, detections)
            
        except Exception as e:
            self.error_occurred.emit(f"Image processing error: {str(e)}")
    
    def stop(self):
        """Stop detection"""
        self.running = False


class DetectionTool(QMainWindow):
    """Main detection tool window"""
    
    def __init__(self):
        super().__init__()
        self.detection_thread = None
        self.current_frame = None
        self.current_detections = []
        self.detection_history = []
        self.model_path = None
        
        # Statistics
        self.total_detections = 0
        self.class_counts = {}
        self.session_start_time = time.time()
        
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("🐛 เครื่องมือตรวจจับแมลง - Insect Detection Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Controls
        self.create_left_panel(main_layout)
        
        # Center panel - Video display
        self.create_center_panel(main_layout)
        
        # Right panel - Results
        self.create_right_panel(main_layout)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("พร้อมใช้งาน - เลือกโมเดลและแหล่งข้อมูลเพื่อเริ่มตรวจจับ")
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('ไฟล์')
        
        load_model_action = QAction('โหลดโมเดล', self)
        load_model_action.setShortcut('Ctrl+M')
        load_model_action.triggered.connect(self.load_model)
        file_menu.addAction(load_model_action)
        
        file_menu.addSeparator()
        
        save_results_action = QAction('บันทึกผลลัพธ์', self)
        save_results_action.setShortcut('Ctrl+S')
        save_results_action.triggered.connect(self.save_results)
        file_menu.addAction(save_results_action)
        
        export_stats_action = QAction('ส่งออกสถิติ', self)
        export_stats_action.triggered.connect(self.export_statistics)
        file_menu.addAction(export_stats_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('ออก', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Detection menu
        detection_menu = menubar.addMenu('ตรวจจับ')
        
        camera_action = QAction('เริ่มตรวจจับจากกล้อง', self)
        camera_action.triggered.connect(self.start_camera_detection)
        detection_menu.addAction(camera_action)
        
        image_action = QAction('ตรวจจับจากรูปภาพ', self)
        image_action.triggered.connect(self.detect_from_image)
        detection_menu.addAction(image_action)
        
        video_action = QAction('ตรวจจับจากวิดีโอ', self)
        video_action.triggered.connect(self.detect_from_video)
        detection_menu.addAction(video_action)
        
        detection_menu.addSeparator()
        
        stop_action = QAction('หยุดตรวจจับ', self)
        stop_action.setShortcut('Esc')
        stop_action.triggered.connect(self.stop_detection)
        detection_menu.addAction(stop_action)
        
    def create_left_panel(self, main_layout):
        """Create left control panel"""
        left_widget = QWidget()
        left_widget.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        
        # Model section
        model_group = QGroupBox("🤖 โมเดล")
        model_layout = QVBoxLayout(model_group)
        
        self.model_path_label = QLabel("ยังไม่ได้เลือกโมเดล")
        self.model_path_label.setWordWrap(True)
        self.model_path_label.setStyleSheet("color: red;")
        model_layout.addWidget(self.model_path_label)
        
        load_model_btn = QPushButton("📁 โหลดโมเดล")
        load_model_btn.clicked.connect(self.load_model)
        model_layout.addWidget(load_model_btn)
        
        left_layout.addWidget(model_group)
        
        # Detection settings
        settings_group = QGroupBox("⚙️ การตั้งค่า")
        settings_layout = QVBoxLayout(settings_group)
        
        # Confidence threshold
        settings_layout.addWidget(QLabel("Confidence Threshold:"))
        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setRange(10, 90)
        self.confidence_slider.setValue(50)
        self.confidence_slider.valueChanged.connect(self.update_confidence_label)
        settings_layout.addWidget(self.confidence_slider)
        
        self.confidence_label = QLabel("0.50")
        self.confidence_label.setAlignment(Qt.AlignCenter)
        settings_layout.addWidget(self.confidence_label)
        
        left_layout.addWidget(settings_group)
        
        # Source selection
        source_group = QGroupBox("📹 แหล่งข้อมูล")
        source_layout = QVBoxLayout(source_group)
        
        camera_btn = QPushButton("📷 กล้อง")
        camera_btn.clicked.connect(self.start_camera_detection)
        source_layout.addWidget(camera_btn)
        
        image_btn = QPushButton("🖼️ รูปภาพ")
        image_btn.clicked.connect(self.detect_from_image)
        source_layout.addWidget(image_btn)
        
        video_btn = QPushButton("🎥 วิดีโอ")
        video_btn.clicked.connect(self.detect_from_video)
        source_layout.addWidget(video_btn)
        
        batch_btn = QPushButton("📁 ไฟล์หลายไฟล์")
        batch_btn.clicked.connect(self.batch_detection)
        source_layout.addWidget(batch_btn)
        
        left_layout.addWidget(source_group)
        
        # Control buttons
        control_group = QGroupBox("🎮 การควบคุม")
        control_layout = QVBoxLayout(control_group)
        
        self.start_stop_btn = QPushButton("▶️ เริ่มตรวจจับ")
        self.start_stop_btn.clicked.connect(self.toggle_detection)
        self.start_stop_btn.setEnabled(False)
        control_layout.addWidget(self.start_stop_btn)
        
        save_frame_btn = QPushButton("📸 บันทึกเฟรม")
        save_frame_btn.clicked.connect(self.save_current_frame)
        control_layout.addWidget(save_frame_btn)
        
        clear_results_btn = QPushButton("🗑️ ล้างผลลัพธ์")
        clear_results_btn.clicked.connect(self.clear_results)
        control_layout.addWidget(clear_results_btn)
        
        left_layout.addWidget(control_group)
        
        left_layout.addStretch()
        main_layout.addWidget(left_widget)
        
    def create_center_panel(self, main_layout):
        """Create center display panel"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # Info bar
        info_layout = QHBoxLayout()
        
        self.fps_label = QLabel("FPS: 0")
        self.fps_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(self.fps_label)
        
        info_layout.addStretch()
        
        self.detection_count_label = QLabel("ตรวจพบ: 0")
        self.detection_count_label.setStyleSheet("font-weight: bold; color: green;")
        info_layout.addWidget(self.detection_count_label)
        
        center_layout.addLayout(info_layout)
        
        # Video display
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("border: 2px solid gray; background-color: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setText("📺 แสดงผลการตรวจจับที่นี่")
        self.video_label.setScaledContents(True)
        
        center_layout.addWidget(self.video_label)
        
        main_layout.addWidget(center_widget, 1)
        
    def create_right_panel(self, main_layout):
        """Create right results panel"""
        right_widget = QWidget()
        right_widget.setMaximumWidth(300)
        right_layout = QVBoxLayout(right_widget)
        
        # Current detections
        current_group = QGroupBox("🎯 การตรวจจับปัจจุบัน")
        current_layout = QVBoxLayout(current_group)
        
        self.current_detections_list = QListWidget()
        current_layout.addWidget(self.current_detections_list)
        
        right_layout.addWidget(current_group)
        
        # Statistics
        stats_group = QGroupBox("📊 สถิติ")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setReadOnly(True)
        self.update_statistics_display()
        stats_layout.addWidget(self.stats_text)
        
        export_stats_btn = QPushButton("📤 ส่งออกสถิติ")
        export_stats_btn.clicked.connect(self.export_statistics)
        stats_layout.addWidget(export_stats_btn)
        
        right_layout.addWidget(stats_group)
        
        # Detection history
        history_group = QGroupBox("📝 ประวัติการตรวจจับ")
        history_layout = QVBoxLayout(history_group)
        
        self.history_list = QListWidget()
        history_layout.addWidget(self.history_list)
        
        save_history_btn = QPushButton("💾 บันทึกประวัติ")
        save_history_btn.clicked.connect(self.save_detection_history)
        history_layout.addWidget(save_history_btn)
        
        right_layout.addWidget(history_group)
        
        main_layout.addWidget(right_widget)
        
    def load_model(self):
        """Load YOLO model"""
        file_dialog = QFileDialog()
        model_path, _ = file_dialog.getOpenFileName(
            self, "เลือกโมเดล YOLO", "",
            "YOLO models (*.pt);;All files (*.*)"
        )
        
        if model_path:
            self.model_path = model_path
            self.model_path_label.setText(f"โมเดล: {Path(model_path).name}")
            self.model_path_label.setStyleSheet("color: green;")
            self.start_stop_btn.setEnabled(True)
            self.status_bar.showMessage(f"โหลดโมเดล: {Path(model_path).name}")
    
    def update_confidence_label(self, value):
        """Update confidence threshold label"""
        confidence = value / 100.0
        self.confidence_label.setText(f"{confidence:.2f}")
    
    def start_camera_detection(self):
        """Start camera detection"""
        if not self.model_path:
            QMessageBox.warning(self, "คำเตือน", "กรุณาโหลดโมเดลก่อน")
            return
        
        # Ask for camera ID
        camera_id, ok = QInputDialog.getInt(
            self, "เลือกกล้อง", "Camera ID:", 0, 0, 10
        )
        
        if ok:
            self.start_detection(camera_id)
    
    def detect_from_image(self):
        """Detect from single image"""
        if not self.model_path:
            QMessageBox.warning(self, "คำเตือน", "กรุณาโหลดโมเดลก่อน")
            return
        
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self, "เลือกรูปภาพ", "",
            "Image files (*.jpg *.jpeg *.png *.bmp *.tiff)"
        )
        
        if image_path:
            self.start_detection(image_path)
    
    def detect_from_video(self):
        """Detect from video file"""
        if not self.model_path:
            QMessageBox.warning(self, "คำเตือน", "กรุณาโหลดโมเดลก่อน")
            return
        
        file_dialog = QFileDialog()
        video_path, _ = file_dialog.getOpenFileName(
            self, "เลือกวิดีโอ", "",
            "Video files (*.mp4 *.avi *.mov *.mkv)"
        )
        
        if video_path:
            self.start_detection(video_path)
    
    def batch_detection(self):
        """Batch detection from multiple files"""
        if not self.model_path:
            QMessageBox.warning(self, "คำเตือน", "กรุณาโหลดโมเดลก่อน")
            return
        
        folder_path = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์รูปภาพ")
        
        if folder_path:
            # Show batch detection dialog
            dialog = BatchDetectionDialog(self.model_path, folder_path, self)
            dialog.exec()
    
    def start_detection(self, source):
        """Start detection thread"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.stop_detection()
        
        confidence = self.confidence_slider.value() / 100.0
        
        self.detection_thread = DetectionThread(self.model_path, source, confidence)
        self.detection_thread.frame_ready.connect(self.on_frame_ready)
        self.detection_thread.fps_updated.connect(self.on_fps_updated)
        self.detection_thread.error_occurred.connect(self.on_error_occurred)
        self.detection_thread.finished.connect(self.on_detection_finished)
        
        self.detection_thread.start()
        
        self.start_stop_btn.setText("⏹️ หยุดตรวจจับ")
        self.status_bar.showMessage("กำลังตรวจจับ...")
    
    def stop_detection(self):
        """Stop detection"""
        if self.detection_thread:
            self.detection_thread.stop()
            self.detection_thread.wait()
        
        self.start_stop_btn.setText("▶️ เริ่มตรวจจับ")
        self.status_bar.showMessage("หยุดการตรวจจับ")
    
    def toggle_detection(self):
        """Toggle detection on/off"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.stop_detection()
        else:
            self.start_camera_detection()
    
    def on_frame_ready(self, frame, detections):
        """Handle new frame with detections"""
        self.current_frame = frame.copy()
        self.current_detections = detections
        
        # Draw detections on frame
        annotated_frame = self.draw_detections(frame, detections)
        
        # Convert to Qt format and display
        height, width, channel = annotated_frame.shape
        bytes_per_line = 3 * width
        q_image = QImage(annotated_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        
        # Scale to fit display
        video_size = self.video_label.size()
        scaled_pixmap = QPixmap.fromImage(q_image).scaled(
            video_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        
        self.video_label.setPixmap(scaled_pixmap)
        
        # Update current detections list
        self.update_current_detections_list(detections)
        
        # Update statistics
        self.update_detection_statistics(detections)
        
        # Add to history
        if detections:
            timestamp = time.strftime("%H:%M:%S")
            for det in detections:
                history_item = f"[{timestamp}] {det['class_name']}: {det['confidence']:.2f}"
                self.history_list.addItem(history_item)
                self.detection_history.append({
                    'timestamp': timestamp,
                    'detection': det
                })
        
        # Scroll to bottom
        self.history_list.scrollToBottom()
    
    def draw_detections(self, frame, detections):
        """Draw detections on frame"""
        annotated_frame = frame.copy()
        
        # Generate colors for different classes
        colors = [
            (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0),
            (128, 0, 255), (0, 128, 255)
        ]
        
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            class_name = det['class_name']
            confidence = det['confidence']
            class_id = det['class_id']
            
            # Select color
            color = colors[class_id % len(colors)]
            
            # Draw bounding box
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            
            # Background for label
            cv2.rectangle(annotated_frame, 
                         (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), 
                         color, -1)
            
            # Label text
            cv2.putText(annotated_frame, label, 
                       (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, 
                       (255, 255, 255), 2)
        
        return annotated_frame
    
    def update_current_detections_list(self, detections):
        """Update current detections list"""
        self.current_detections_list.clear()
        
        for i, det in enumerate(detections):
            item_text = f"{det['class_name']}: {det['confidence']:.2f}"
            self.current_detections_list.addItem(item_text)
        
        self.detection_count_label.setText(f"ตรวจพบ: {len(detections)}")
    
    def update_detection_statistics(self, detections):
        """Update detection statistics"""
        for det in detections:
            class_name = det['class_name']
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
            self.total_detections += 1
        
        self.update_statistics_display()
    
    def update_statistics_display(self):
        """Update statistics display"""
        elapsed_time = time.time() - self.session_start_time
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        stats_text = f"""📊 สถิติเซสชันปัจจุบัน:

⏱️ เวลา: {hours:02d}:{minutes:02d}:{seconds:02d}
🎯 การตรวจจับทั้งหมด: {self.total_detections}

📈 การกระจายตามคลาส:
"""
        
        for class_name, count in self.class_counts.items():
            percentage = (count / self.total_detections * 100) if self.total_detections > 0 else 0
            stats_text += f"  • {class_name}: {count} ({percentage:.1f}%)\n"
        
        if not self.class_counts:
            stats_text += "  ยังไม่มีการตรวจจับ\n"
        
        self.stats_text.setPlainText(stats_text)
    
    def on_fps_updated(self, fps):
        """Handle FPS update"""
        self.fps_label.setText(f"FPS: {fps:.1f}")
    
    def on_error_occurred(self, error_message):
        """Handle error"""
        QMessageBox.critical(self, "ข้อผิดพลาด", error_message)
        self.status_bar.showMessage(f"ข้อผิดพลาด: {error_message}")
    
    def on_detection_finished(self):
        """Handle detection finished"""
        self.start_stop_btn.setText("▶️ เริ่มตรวจจับ")
        self.status_bar.showMessage("การตรวจจับเสร็จสิ้น")
    
    def save_current_frame(self):
        """Save current frame"""
        if self.current_frame is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"detection_{timestamp}.jpg"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "บันทึกเฟรม", filename,
                "Image files (*.jpg *.png)"
            )
            
            if file_path:
                # Draw detections and save
                annotated_frame = self.draw_detections(self.current_frame, self.current_detections)
                cv2.imwrite(file_path, annotated_frame)
                QMessageBox.information(self, "เสร็จสิ้น", f"บันทึกเฟรมไปที่: {file_path}")
    
    def clear_results(self):
        """Clear all results"""
        reply = QMessageBox.question(self, "ยืนยัน", "คุณแน่ใจหรือไม่ที่จะล้างผลลัพธ์ทั้งหมด?")
        if reply == QMessageBox.Yes:
            self.current_detections_list.clear()
            self.history_list.clear()
            self.detection_history.clear()
            self.total_detections = 0
            self.class_counts.clear()
            self.session_start_time = time.time()
            self.update_statistics_display()
            self.detection_count_label.setText("ตรวจพบ: 0")
    
    def save_detection_history(self):
        """Save detection history"""
        if not self.detection_history:
            QMessageBox.information(self, "แจ้งเตือน", "ไม่มีประวัติการตรวจจับ")
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"detection_history_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกประวัติ", filename,
            "JSON files (*.json)"
        )
        
        if file_path:
            data = {
                'session_info': {
                    'start_time': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.session_start_time)),
                    'total_detections': self.total_detections,
                    'class_counts': self.class_counts
                },
                'detections': self.detection_history
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "เสร็จสิ้น", f"บันทึกประวัติไปที่: {file_path}")
    
    def export_statistics(self):
        """Export statistics"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"detection_statistics_{timestamp}.txt"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "ส่งออกสถิติ", filename,
            "Text files (*.txt)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.stats_text.toPlainText())
            
            QMessageBox.information(self, "เสร็จสิ้น", f"ส่งออกสถิติไปที่: {file_path}")
    
    def save_results(self):
        """Save current detection results"""
        if not hasattr(self, 'detection_history') or not self.detection_history:
            QMessageBox.warning(self, "คำเตือน", "ไม่มีข้อมูลการตรวจจับให้บันทึก")
            return
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"detection_results_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกผลลัพธ์", filename,
            "JSON files (*.json)"
        )
        
        if file_path:
            # Create results data
            results_data = {
                'timestamp': timestamp,
                'session_duration': time.time() - self.session_start_time,
                'total_detections': self.total_detections,
                'class_counts': self.class_counts,
                'detection_history': self.detection_history[-100:]  # Last 100 detections
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "เสร็จสิ้น", f"บันทึกผลลัพธ์ไปที่: {file_path}")
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.stop_detection()
        event.accept()


class BatchDetectionDialog(QDialog):
    """Dialog for batch detection"""
    
    def __init__(self, model_path, folder_path, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.folder_path = Path(folder_path)
        self.results = []
        
        self.init_ui()
        self.start_batch_detection()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("การตรวจจับแบบกลุ่ม")
        self.setGeometry(200, 200, 600, 400)
        
        layout = QVBoxLayout(self)
        
        # Progress section
        layout.addWidget(QLabel("ความคืบหน้า:"))
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("เตรียมการ...")
        layout.addWidget(self.status_label)
        
        # Results section
        layout.addWidget(QLabel("ผลลัพธ์:"))
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(self.results_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 บันทึกผลลัพธ์")
        self.save_btn.clicked.connect(self.save_results)
        self.save_btn.setEnabled(False)
        button_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("ปิด")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def start_batch_detection(self):
        """Start batch detection"""
        # Find all image files
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        image_files = []
        
        for ext in image_extensions:
            image_files.extend(self.folder_path.glob(f"*{ext}"))
            image_files.extend(self.folder_path.glob(f"*{ext.upper()}"))
        
        if not image_files:
            self.status_label.setText("ไม่พบไฟล์รูปภาพ")
            return
        
        self.progress_bar.setMaximum(len(image_files))
        
        # Load model
        try:
            model = YOLO(self.model_path)
        except Exception as e:
            self.status_label.setText(f"ไม่สามารถโหลดโมเดล: {e}")
            return
        
        # Process images
        total_detections = 0
        class_counts = {}
        
        for i, image_file in enumerate(image_files):
            self.status_label.setText(f"กำลังประมวลผล: {image_file.name}")
            self.progress_bar.setValue(i)
            
            try:
                # Load and process image
                image = cv2.imread(str(image_file))
                if image is None:
                    continue
                
                results = model(image, conf=0.5, verbose=False)
                
                detections = []
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            class_id = int(box.cls[0].cpu().numpy())
                            class_name = model.names[class_id]
                            confidence = float(box.conf[0].cpu().numpy())
                            
                            detections.append({
                                'class_name': class_name,
                                'confidence': confidence
                            })
                            
                            class_counts[class_name] = class_counts.get(class_name, 0) + 1
                            total_detections += 1
                
                self.results.append({
                    'file': image_file.name,
                    'detections': len(detections),
                    'details': detections
                })
                
            except Exception as e:
                self.results.append({
                    'file': image_file.name,
                    'error': str(e)
                })
            
            QApplication.processEvents()
        
        self.progress_bar.setValue(len(image_files))
        self.status_label.setText("เสร็จสิ้น!")
        
        # Show results
        results_text = f"📊 สรุปผลการตรวจจับแบบกลุ่ม\n\n"
        results_text += f"📁 โฟลเดอร์: {self.folder_path.name}\n"
        results_text += f"🖼️ ไฟล์ทั้งหมด: {len(image_files)}\n"
        results_text += f"🎯 การตรวจจับทั้งหมด: {total_detections}\n\n"
        
        results_text += f"📈 การกระจายตามคลาส:\n"
        for class_name, count in class_counts.items():
            percentage = (count / total_detections * 100) if total_detections > 0 else 0
            results_text += f"  • {class_name}: {count} ({percentage:.1f}%)\n"
        
        results_text += f"\n📝 รายละเอียดแต่ละไฟล์:\n"
        for result in self.results:
            if 'error' in result:
                results_text += f"❌ {result['file']}: {result['error']}\n"
            else:
                results_text += f"✅ {result['file']}: {result['detections']} การตรวจจับ\n"
        
        self.results_text.setPlainText(results_text)
        self.save_btn.setEnabled(True)

    def save_results(self):
        """Save batch results"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"batch_detection_{timestamp}.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกผลลัพธ์", filename,
            "JSON files (*.json)"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(self, "เสร็จสิ้น", f"บันทึกผลลัพธ์ไปที่: {file_path}")


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Insect Detection Tool")
    app.setApplicationVersion("1.0")
    
    # Check if model exists
    models_dir = Path("../training/models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.pt"))
        if model_files:
            print(f"Found {len(model_files)} model(s) in {models_dir}")
    
    window = DetectionTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
