#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desktop Insect Annotation Tool
เครื่องมือ annotate แมลงแบบ desktop application
"""

import sys
import os
import json
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

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

class AnnotationTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_image = None
        self.current_image_path = None
        self.annotations = []
        self.selected_annotation = -1
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.scale_factor = 1.0
        
        # Paths
        self.dataset_dir = Path("../dataset")
        self.images_dir = self.dataset_dir / "images"
        self.annotations_dir = self.dataset_dir / "annotations" 
        self.classes_file = self.dataset_dir / "classes.txt"
        
        # Create directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.annotations_dir.mkdir(parents=True, exist_ok=True)
        
        # Load classes
        self.classes = self.load_classes()
        
        self.init_ui()
        self.load_image_list()
        
    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("🐛 เครื่องมือ Annotation แมลง - Insect Annotation Tool")
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel - Image list and controls
        self.create_left_panel(main_layout)
        
        # Center panel - Image canvas
        self.create_center_panel(main_layout)
        
        # Right panel - Annotation controls
        self.create_right_panel(main_layout)
        
        # Menu bar
        self.create_menu_bar()
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("พร้อมใช้งาน - เลือกรูปภาพเพื่อเริ่ม annotation")
        
    def create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('ไฟล์')
        
        open_action = QAction('เปิดโฟลเดอร์รูปภาพ', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_image_folder)
        file_menu.addAction(open_action)
        
        add_images_action = QAction('เพิ่มรูปภาพ', self)
        add_images_action.setShortcut('Ctrl+A')
        add_images_action.triggered.connect(self.add_images)
        file_menu.addAction(add_images_action)
        
        file_menu.addSeparator()
        
        save_action = QAction('บันทึก Annotation', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_annotations)
        file_menu.addAction(save_action)
        
        export_action = QAction('ส่งออกข้อมูล', self)
        export_action.triggered.connect(self.export_dataset)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('ออก', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu('แก้ไข')
        
        clear_action = QAction('ลบ Annotation ทั้งหมด', self)
        clear_action.triggered.connect(self.clear_annotations)
        edit_menu.addAction(clear_action)
        
        delete_action = QAction('ลบ Annotation ที่เลือก', self)
        delete_action.setShortcut('Delete')
        delete_action.triggered.connect(self.delete_selected_annotation)
        edit_menu.addAction(delete_action)
        
        # Classes menu
        classes_menu = menubar.addMenu('คลาส')
        
        add_class_action = QAction('เพิ่มคลาสใหม่', self)
        add_class_action.triggered.connect(self.add_class_dialog)
        classes_menu.addAction(add_class_action)
        
        manage_classes_action = QAction('จัดการคลาส', self)
        manage_classes_action.triggered.connect(self.manage_classes_dialog)
        classes_menu.addAction(manage_classes_action)
        
    def create_left_panel(self, main_layout):
        """Create left panel with image list"""
        left_widget = QWidget()
        left_widget.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_widget)
        
        # Image list title
        list_title = QLabel("📁 รายการรูปภาพ")
        list_title.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        left_layout.addWidget(list_title)
        
        # Image list
        self.image_list = QListWidget()
        self.image_list.itemClicked.connect(self.load_selected_image)
        left_layout.addWidget(self.image_list)
        
        # Add buttons
        buttons_layout = QVBoxLayout()
        
        add_images_btn = QPushButton("📁 เพิ่มรูปภาพ")
        add_images_btn.clicked.connect(self.add_images)
        buttons_layout.addWidget(add_images_btn)
        
        open_folder_btn = QPushButton("📂 เปิดโฟลเดอร์")
        open_folder_btn.clicked.connect(self.open_image_folder)
        buttons_layout.addWidget(open_folder_btn)
        
        left_layout.addLayout(buttons_layout)
        main_layout.addWidget(left_widget)
        
    def create_center_panel(self, main_layout):
        """Create center panel with image canvas"""
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.zoom_in_btn = QPushButton("🔍+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        toolbar_layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = QPushButton("🔍-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        toolbar_layout.addWidget(self.zoom_out_btn)
        
        self.reset_zoom_btn = QPushButton("🔄 Reset")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        toolbar_layout.addWidget(self.reset_zoom_btn)
        
        toolbar_layout.addStretch()
        
        self.image_info_label = QLabel("ไม่มีรูปภาพ")
        self.image_info_label.setStyleSheet("font-weight: bold;")
        toolbar_layout.addWidget(self.image_info_label)
        
        center_layout.addLayout(toolbar_layout)
        
        # Scroll area for image
        self.scroll_area = QScrollArea()
        self.image_label = ImageLabel()
        self.image_label.annotation_tool = self
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(800, 600)
        
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        center_layout.addWidget(self.scroll_area)
        
        main_layout.addWidget(center_widget, 1)
        
    def create_right_panel(self, main_layout):
        """Create right panel with annotation controls"""
        right_widget = QWidget()
        right_widget.setMaximumWidth(300)
        right_layout = QVBoxLayout(right_widget)
        
        # Mode selection
        mode_group = QGroupBox("🛠️ โหมดการทำงาน")
        mode_layout = QVBoxLayout(mode_group)
        
        self.mode_group = QButtonGroup()
        self.select_mode = QRadioButton("👆 เลือก/แก้ไข")
        self.select_mode.setChecked(True)
        self.draw_mode = QRadioButton("✏️ วาด Bounding Box")
        
        self.mode_group.addButton(self.select_mode, 0)
        self.mode_group.addButton(self.draw_mode, 1)
        
        mode_layout.addWidget(self.select_mode)
        mode_layout.addWidget(self.draw_mode)
        right_layout.addWidget(mode_group)
        
        # Class selection
        class_group = QGroupBox("🏷️ เลือกชนิดแมลง")
        class_layout = QVBoxLayout(class_group)
        
        self.class_combo = QComboBox()
        self.update_class_combo()
        class_layout.addWidget(self.class_combo)
        right_layout.addWidget(class_group)
        
        # Action buttons
        actions_group = QGroupBox("⚡ การกระทำ")
        actions_layout = QVBoxLayout(actions_group)
        
        save_btn = QPushButton("💾 บันทึก Annotation")
        save_btn.clicked.connect(self.save_annotations)
        save_btn.setStyleSheet("QPushButton { background-color: #28a745; color: white; font-weight: bold; }")
        actions_layout.addWidget(save_btn)
        
        clear_btn = QPushButton("🗑️ ลบทั้งหมด")
        clear_btn.clicked.connect(self.clear_annotations)
        clear_btn.setStyleSheet("QPushButton { background-color: #ffc107; color: black; }")
        actions_layout.addWidget(clear_btn)
        
        delete_btn = QPushButton("❌ ลบที่เลือก")
        delete_btn.clicked.connect(self.delete_selected_annotation)
        delete_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        actions_layout.addWidget(delete_btn)
        
        right_layout.addWidget(actions_group)
        
        # Annotation list
        ann_group = QGroupBox("📋 รายการ Annotation")
        ann_layout = QVBoxLayout(ann_group)
        
        self.annotation_list = QListWidget()
        self.annotation_list.itemClicked.connect(self.select_annotation_from_list)
        ann_layout.addWidget(self.annotation_list)
        right_layout.addWidget(ann_group)
        
        # Statistics
        stats_group = QGroupBox("📊 สถิติ")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("ยังไม่มีข้อมูล")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        export_btn = QPushButton("📤 ส่งออกสถิติ")
        export_btn.clicked.connect(self.export_dataset)
        stats_layout.addWidget(export_btn)
        
        right_layout.addWidget(stats_group)
        
        right_layout.addStretch()
        main_layout.addWidget(right_widget)
        
    def load_classes(self):
        """Load classes from file"""
        default_classes = [
            'butterfly', 'bee', 'ant', 'dragonfly', 'beetle',
            'mosquito', 'fly', 'spider', 'grasshopper', 'moth'
        ]
        
        if self.classes_file.exists():
            with open(self.classes_file, 'r', encoding='utf-8') as f:
                classes = [line.strip() for line in f.readlines() if line.strip()]
                return classes if classes else default_classes
        else:
            # Create default classes file
            with open(self.classes_file, 'w', encoding='utf-8') as f:
                for cls in default_classes:
                    f.write(f"{cls}\n")
            return default_classes
    
    def save_classes(self):
        """Save classes to file"""
        with open(self.classes_file, 'w', encoding='utf-8') as f:
            for cls in self.classes:
                f.write(f"{cls}\n")
    
    def update_class_combo(self):
        """Update class combobox"""
        self.class_combo.clear()
        for cls in self.classes:
            self.class_combo.addItem(cls)
    
    def load_image_list(self):
        """Load image list"""
        self.image_list.clear()
        
        if not self.images_dir.exists():
            return
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        for image_file in self.images_dir.iterdir():
            if image_file.suffix.lower() in image_extensions:
                # Check if annotation exists
                annotation_file = self.annotations_dir / f"{image_file.stem}.txt"
                
                item = QListWidgetItem()
                if annotation_file.exists():
                    item.setText(f"✅ {image_file.name}")
                    item.setBackground(QColor(200, 255, 200))
                else:
                    item.setText(f"⭕ {image_file.name}")
                
                item.setData(Qt.UserRole, str(image_file))
                self.image_list.addItem(item)
    
    def add_images(self):
        """Add images to dataset"""
        file_dialog = QFileDialog()
        file_paths, _ = file_dialog.getOpenFileNames(
            self, "เลือกรูปภาพ", "",
            "Image files (*.jpg *.jpeg *.png *.bmp *.tiff)"
        )
        
        if file_paths:
            for file_path in file_paths:
                src_path = Path(file_path)
                dst_path = self.images_dir / src_path.name
                
                # Copy file if not exists
                if not dst_path.exists():
                    shutil.copy2(src_path, dst_path)
            
            self.load_image_list()
            QMessageBox.information(self, "เสร็จสิ้น", f"เพิ่มรูปภาพ {len(file_paths)} ไฟล์แล้ว")
    
    def open_image_folder(self):
        """Open folder to select images"""
        folder_path = QFileDialog.getExistingDirectory(self, "เลือกโฟลเดอร์รูปภาพ")
        
        if folder_path:
            folder = Path(folder_path)
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
            
            copied_count = 0
            for image_file in folder.iterdir():
                if image_file.suffix.lower() in image_extensions:
                    dst_path = self.images_dir / image_file.name
                    if not dst_path.exists():
                        shutil.copy2(image_file, dst_path)
                        copied_count += 1
            
            self.load_image_list()
            QMessageBox.information(self, "เสร็จสิ้น", f"คัดลอกรูปภาพ {copied_count} ไฟล์แล้ว")
    
    def load_selected_image(self, item):
        """Load selected image"""
        image_path = Path(item.data(Qt.UserRole))
        self.load_image(image_path)
    
    def load_image(self, image_path):
        """Load image and annotations"""
        self.current_image_path = image_path
        
        # Load image
        self.current_image = cv2.imread(str(image_path))
        if self.current_image is None:
            QMessageBox.warning(self, "ข้อผิดพลาด", f"ไม่สามารถโหลดรูปภาพ: {image_path}")
            return
        
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        
        # Load annotations
        self.load_annotations_for_image(image_path)
        
        # Display image
        self.display_image(rgb_image)
        
        # Update info
        self.image_info_label.setText(f"{image_path.name} ({rgb_image.shape[1]}×{rgb_image.shape[0]})")
        self.status_bar.showMessage(f"โหลดรูปภาพ: {image_path.name}")
        
        # Update annotation list
        self.update_annotation_list()
    
    def load_annotations_for_image(self, image_path):
        """Load annotations for specific image"""
        self.annotations = []
        annotation_file = self.annotations_dir / f"{image_path.stem}.txt"
        
        if annotation_file.exists():
            with open(annotation_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        class_id, x_center, y_center, width, height = map(float, parts)
                        self.annotations.append({
                            'class_id': int(class_id),
                            'x_center': x_center,
                            'y_center': y_center,
                            'width': width,
                            'height': height
                        })
    
    def display_image(self, rgb_image):
        """Display image in label"""
        height, width, channel = rgb_image.shape
        bytes_per_line = 3 * width
        
        # Create QImage
        q_image = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        
        # Scale image
        scaled_size = QSize(int(width * self.scale_factor), int(height * self.scale_factor))
        scaled_pixmap = QPixmap.fromImage(q_image).scaled(scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.original_size = QSize(width, height)
        self.image_label.scaled_size = scaled_size
    
    def zoom_in(self):
        """Zoom in image"""
        self.scale_factor *= 1.2
        if self.current_image is not None:
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            self.display_image(rgb_image)
    
    def zoom_out(self):
        """Zoom out image"""
        self.scale_factor /= 1.2
        if self.current_image is not None:
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            self.display_image(rgb_image)
    
    def reset_zoom(self):
        """Reset zoom to fit"""
        self.scale_factor = 1.0
        if self.current_image is not None:
            rgb_image = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
            self.display_image(rgb_image)
    
    def update_annotation_list(self):
        """Update annotation list widget"""
        self.annotation_list.clear()
        
        for i, ann in enumerate(self.annotations):
            class_name = self.classes[ann['class_id']] if ann['class_id'] < len(self.classes) else 'Unknown'
            item_text = f"{i+1}. {class_name} ({ann['x_center']:.2f}, {ann['y_center']:.2f})"
            
            item = QListWidgetItem(item_text)
            if i == self.selected_annotation:
                item.setBackground(QColor(100, 150, 255))
            self.annotation_list.addItem(item)
    
    def select_annotation_from_list(self, item):
        """Select annotation from list"""
        self.selected_annotation = self.annotation_list.row(item)
        self.update_annotation_list()
        self.image_label.update()
    
    def save_annotations(self):
        """Save annotations to file"""
        if not self.current_image_path:
            QMessageBox.warning(self, "คำเตือน", "กรุณาเลือกรูปภาพก่อน")
            return
        
        annotation_file = self.annotations_dir / f"{self.current_image_path.stem}.txt"
        
        with open(annotation_file, 'w') as f:
            for ann in self.annotations:
                f.write(f"{ann['class_id']} {ann['x_center']} {ann['y_center']} {ann['width']} {ann['height']}\n")
        
        # Update image list
        self.load_image_list()
        
        QMessageBox.information(self, "เสร็จสิ้น", "บันทึก annotation เรียบร้อยแล้ว")
        self.status_bar.showMessage("บันทึก annotation เรียบร้อยแล้ว")
    
    def clear_annotations(self):
        """Clear all annotations"""
        if self.annotations:
            reply = QMessageBox.question(self, "ยืนยัน", "คุณแน่ใจหรือไม่ที่จะลบ annotation ทั้งหมด?")
            if reply == QMessageBox.Yes:
                self.annotations = []
                self.selected_annotation = -1
                self.update_annotation_list()
                self.image_label.update()
    
    def delete_selected_annotation(self):
        """Delete selected annotation"""
        if self.selected_annotation >= 0:
            self.annotations.pop(self.selected_annotation)
            self.selected_annotation = -1
            self.update_annotation_list()
            self.image_label.update()
    
    def add_class_dialog(self):
        """Show add class dialog"""
        text, ok = QInputDialog.getText(self, 'เพิ่มคลาสใหม่', 'ชื่อคลาส:')
        if ok and text.strip():
            if text.strip() not in self.classes:
                self.classes.append(text.strip())
                self.save_classes()
                self.update_class_combo()
                QMessageBox.information(self, "เสร็จสิ้น", f"เพิ่มคลาส '{text.strip()}' เรียบร้อยแล้ว")
            else:
                QMessageBox.warning(self, "คำเตือน", "คลาสนี้มีอยู่แล้ว")
    
    def manage_classes_dialog(self):
        """Show manage classes dialog"""
        dialog = ClassManagerDialog(self.classes, self)
        if dialog.exec() == QDialog.Accepted:
            self.classes = dialog.get_classes()
            self.save_classes()
            self.update_class_combo()
    
    def export_dataset(self):
        """Export dataset statistics"""
        stats = self.calculate_statistics()
        
        # Show statistics dialog
        dialog = StatisticsDialog(stats, self)
        dialog.exec()


class ImageLabel(QLabel):
    """Custom QLabel for image display and annotation"""
    
    def __init__(self):
        super().__init__()
        self.annotation_tool = None
        self.drawing = False
        self.start_point = None
        self.end_point = None
        self.original_size = None
        self.scaled_size = None
        
    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if not self.annotation_tool or not self.annotation_tool.current_image_path:
            return
        
        if event.button() == Qt.LeftButton:
            pos = self.get_normalized_position(event.pos())
            
            if self.annotation_tool.draw_mode.isChecked():
                # Start drawing
                self.drawing = True
                self.start_point = pos
                self.end_point = pos
            else:
                # Select annotation
                self.select_annotation_at_position(pos)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if self.drawing and self.start_point:
            self.end_point = self.get_normalized_position(event.pos())
            self.update()
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if self.drawing and self.start_point and self.end_point:
            # Create annotation
            self.create_annotation()
            self.drawing = False
            self.start_point = None
            self.end_point = None
            self.update()
    
    def get_normalized_position(self, pos):
        """Convert widget position to normalized image coordinates"""
        if not self.original_size or not self.scaled_size:
            return QPointF(0, 0)
        
        # Get image rect in widget
        widget_size = self.size()
        image_rect = QRect(
            (widget_size.width() - self.scaled_size.width()) // 2,
            (widget_size.height() - self.scaled_size.height()) // 2,
            self.scaled_size.width(),
            self.scaled_size.height()
        )
        
        # Convert to image coordinates
        if image_rect.contains(pos):
            rel_x = (pos.x() - image_rect.x()) / image_rect.width()
            rel_y = (pos.y() - image_rect.y()) / image_rect.height()
            return QPointF(rel_x, rel_y)
        
        return QPointF(0, 0)
    
    def select_annotation_at_position(self, pos):
        """Select annotation at given position"""
        if not self.annotation_tool:
            return
        
        for i, ann in enumerate(self.annotation_tool.annotations):
            left = ann['x_center'] - ann['width'] / 2
            right = ann['x_center'] + ann['width'] / 2
            top = ann['y_center'] - ann['height'] / 2
            bottom = ann['y_center'] + ann['height'] / 2
            
            if left <= pos.x() <= right and top <= pos.y() <= bottom:
                self.annotation_tool.selected_annotation = i
                self.annotation_tool.update_annotation_list()
                self.update()
                return
        
        # No annotation found, deselect
        self.annotation_tool.selected_annotation = -1
        self.annotation_tool.update_annotation_list()
        self.update()
    
    def create_annotation(self):
        """Create annotation from drawn rectangle"""
        if not self.start_point or not self.end_point:
            return
        
        # Calculate bounding box
        x1, y1 = self.start_point.x(), self.start_point.y()
        x2, y2 = self.end_point.x(), self.end_point.y()
        
        x_center = (x1 + x2) / 2
        y_center = (y1 + y2) / 2
        width = abs(x2 - x1)
        height = abs(y2 - y1)
        
        # Minimum size check
        if width < 0.01 or height < 0.01:
            return
        
        # Get selected class
        class_id = self.annotation_tool.class_combo.currentIndex()
        
        # Create annotation
        annotation = {
            'class_id': class_id,
            'x_center': x_center,
            'y_center': y_center,
            'width': width,
            'height': height
        }
        
        self.annotation_tool.annotations.append(annotation)
        self.annotation_tool.update_annotation_list()
    
    def paintEvent(self, event):
        """Custom paint event to draw annotations"""
        super().paintEvent(event)
        
        if not self.annotation_tool or not self.original_size or not self.scaled_size:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get image rect
        widget_size = self.size()
        image_rect = QRect(
            (widget_size.width() - self.scaled_size.width()) // 2,
            (widget_size.height() - self.scaled_size.height()) // 2,
            self.scaled_size.width(),
            self.scaled_size.height()
        )
        
        # Draw existing annotations
        for i, ann in enumerate(self.annotation_tool.annotations):
            self.draw_annotation(painter, image_rect, ann, i == self.annotation_tool.selected_annotation)
        
        # Draw current drawing
        if self.drawing and self.start_point and self.end_point:
            self.draw_current_drawing(painter, image_rect)
    
    def draw_annotation(self, painter, image_rect, annotation, selected=False):
        """Draw single annotation"""
        # Calculate rectangle in widget coordinates
        left = annotation['x_center'] - annotation['width'] / 2
        top = annotation['y_center'] - annotation['height'] / 2
        width = annotation['width']
        height = annotation['height']
        
        x = image_rect.x() + left * image_rect.width()
        y = image_rect.y() + top * image_rect.height()
        w = width * image_rect.width()
        h = height * image_rect.height()
        
        rect = QRectF(x, y, w, h)
        
        # Set colors
        if selected:
            pen_color = QColor(255, 0, 0)  # Red for selected
            brush_color = QColor(255, 0, 0, 50)
        else:
            pen_color = QColor(0, 255, 0)  # Green for normal
            brush_color = QColor(0, 255, 0, 30)
        
        # Draw rectangle
        painter.setPen(QPen(pen_color, 2))
        painter.setBrush(QBrush(brush_color))
        painter.drawRect(rect)
        
        # Draw label
        if annotation['class_id'] < len(self.annotation_tool.classes):
            class_name = self.annotation_tool.classes[annotation['class_id']]
            painter.setPen(QPen(pen_color))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.drawText(rect.topLeft() + QPointF(2, -5), class_name)
    
    def draw_current_drawing(self, painter, image_rect):
        """Draw currently being drawn rectangle"""
        x1 = image_rect.x() + self.start_point.x() * image_rect.width()
        y1 = image_rect.y() + self.start_point.y() * image_rect.height()
        x2 = image_rect.x() + self.end_point.x() * image_rect.width()
        y2 = image_rect.y() + self.end_point.y() * image_rect.height()
        
        rect = QRectF(QPointF(x1, y1), QPointF(x2, y2)).normalized()
        
        painter.setPen(QPen(QColor(0, 0, 255), 2))  # Blue for current drawing
        painter.setBrush(QBrush(QColor(0, 0, 255, 30)))
        painter.drawRect(rect)


class ClassManagerDialog(QDialog):
    """Dialog for managing classes"""
    
    def __init__(self, classes, parent=None):
        super().__init__(parent)
        self.classes = classes.copy()
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("จัดการคลาสแมลง")
        self.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout(self)
        
        # Class list
        self.class_list = QListWidget()
        self.update_class_list()
        layout.addWidget(QLabel("รายการคลาส:"))
        layout.addWidget(self.class_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_btn = QPushButton("เพิ่ม")
        add_btn.clicked.connect(self.add_class)
        button_layout.addWidget(add_btn)
        
        edit_btn = QPushButton("แก้ไข")
        edit_btn.clicked.connect(self.edit_class)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("ลบ")
        delete_btn.clicked.connect(self.delete_class)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        # Dialog buttons
        dialog_buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)
    
    def update_class_list(self):
        """Update class list"""
        self.class_list.clear()
        for cls in self.classes:
            self.class_list.addItem(cls)
    
    def add_class(self):
        """Add new class"""
        text, ok = QInputDialog.getText(self, 'เพิ่มคลาส', 'ชื่อคลาส:')
        if ok and text.strip():
            if text.strip() not in self.classes:
                self.classes.append(text.strip())
                self.update_class_list()
            else:
                QMessageBox.warning(self, "คำเตือน", "คลาสนี้มีอยู่แล้ว")
    
    def edit_class(self):
        """Edit selected class"""
        current_item = self.class_list.currentItem()
        if current_item:
            old_name = current_item.text()
            text, ok = QInputDialog.getText(self, 'แก้ไขคลาส', 'ชื่อคลาส:', text=old_name)
            if ok and text.strip() and text.strip() != old_name:
                if text.strip() not in self.classes:
                    index = self.classes.index(old_name)
                    self.classes[index] = text.strip()
                    self.update_class_list()
                else:
                    QMessageBox.warning(self, "คำเตือน", "คลาสนี้มีอยู่แล้ว")
    
    def delete_class(self):
        """Delete selected class"""
        current_item = self.class_list.currentItem()
        if current_item:
            class_name = current_item.text()
            reply = QMessageBox.question(self, "ยืนยัน", f"คุณแน่ใจหรือไม่ที่จะลบคลาส '{class_name}'?")
            if reply == QMessageBox.Yes:
                self.classes.remove(class_name)
                self.update_class_list()
    
    def get_classes(self):
        """Get updated classes"""
        return self.classes


class StatisticsDialog(QDialog):
    """Dialog for showing dataset statistics"""
    
    def __init__(self, stats, parent=None):
        super().__init__(parent)
        self.stats = stats
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setWindowTitle("สถิติข้อมูล Dataset")
        self.setGeometry(200, 200, 500, 400)
        
        layout = QVBoxLayout(self)
        
        # Statistics text
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        
        text = f"""
📊 สถิติข้อมูล Dataset

📁 ข้อมูลทั่วไป:
   • รูปภาพทั้งหมด: {self.stats['total_images']} รูป
   • รูปที่ annotate แล้ว: {self.stats['annotated_images']} รูป
   • จำนวน annotation ทั้งหมด: {self.stats['total_annotations']} อัน
   • จำนวนคลาส: {self.stats['total_classes']} คลาส

📈 การกระจายตามคลาส:
"""
        
        for class_name, count in self.stats['class_distribution'].items():
            if count > 0:
                percentage = (count / self.stats['total_annotations'] * 100) if self.stats['total_annotations'] > 0 else 0
                text += f"   • {class_name}: {count} อัน ({percentage:.1f}%)\n"
        
        text += f"\n💡 แนะนำ:\n"
        text += f"   • ควรมีข้อมูลอย่างน้อย 100+ annotation ต่อคลาส\n"
        text += f"   • ข้อมูลควรมีความหลากหลายในมุมมอง แสง และพื้นหลัง\n"
        text += f"   • ยิ่งมีข้อมูลมาก โมเดลจะแม่นยำมากขึ้น\n"
        
        stats_text.setPlainText(text)
        layout.addWidget(stats_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("💾 ส่งออกเป็นไฟล์")
        export_btn.clicked.connect(self.export_to_file)
        button_layout.addWidget(export_btn)
        
        close_btn = QPushButton("ปิด")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def export_to_file(self):
        """Export statistics to file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "บันทึกสถิติ", "dataset_statistics.json",
            "JSON files (*.json);;Text files (*.txt)"
        )
        
        if file_path:
            if file_path.endswith('.json'):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.stats, f, indent=2, ensure_ascii=False)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.generate_text_report())
            
            QMessageBox.information(self, "เสร็จสิ้น", f"บันทึกสถิติไปที่: {file_path}")
    
    def generate_text_report(self):
        """Generate text report"""
        return f"""สถิติข้อมูล Dataset - {QDateTime.currentDateTime().toString()}

ข้อมูลทั่วไป:
- รูปภาพทั้งหมด: {self.stats['total_images']} รูป
- รูปที่ annotate แล้ว: {self.stats['annotated_images']} รูป  
- จำนวน annotation ทั้งหมด: {self.stats['total_annotations']} อัน
- จำนวนคลาส: {self.stats['total_classes']} คลาส

การกระจายตามคลาส:
""" + "\n".join([f"- {name}: {count} อัน" for name, count in self.stats['class_distribution'].items() if count > 0])


def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Insect Annotation Tool")
    app.setApplicationVersion("1.0")
    
    # Set application icon (if available)
    # app.setWindowIcon(QIcon("icon.png"))
    
    window = AnnotationTool()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
