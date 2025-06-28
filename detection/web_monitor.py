#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web-based Real-time Insect Detection System
ระบบตรวจจับแมลงแบบ Real-time ผ่าน Web Application
"""

import cv2
import numpy as np
import time
import json
import base64
from pathlib import Path
import threading
from datetime import datetime
import asyncio
import sys

try:
    from flask import Flask, render_template, Response, jsonify, request
    from flask_socketio import SocketIO, emit
except ImportError:
    print("Installing Flask and dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask", "flask-socketio", "eventlet"])
    from flask import Flask, render_template, Response, jsonify, request
    from flask_socketio import SocketIO, emit

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics not installed. Please run: pip install ultralytics")
    sys.exit(1)

class WebInsectDetector:
    def __init__(self, model_path=None):
        """Initialize web-based insect detector"""
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'insect_detection_secret_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='eventlet')
        
        # Detection settings
        self.model = None
        self.model_path = model_path
        self.confidence_threshold = 0.5
        self.camera_id = 0
        self.is_detecting = False
        self.camera = None
        
        # Statistics
        self.detection_stats = {
            'total_detections': 0,
            'class_counts': {},
            'session_start': datetime.now().isoformat(),
            'last_detection': None,
            'fps': 0
        }
        
        # Detection history (keep last 100 detections)
        self.detection_history = []
        self.max_history = 100
        
        # Auto-load YOLO11 model
        self.try_load_default_model()
        
        # Setup routes
        self.setup_routes()
        self.setup_socket_events()
        
    def try_load_default_model(self):
        """Try to load default YOLO11 model"""
        default_models = [
            Path("../training/models/yolo11_best.pt"),
            Path("training/models/yolo11_best.pt"),
            Path("../training/models/best.pt"),
            Path("training/models/best.pt"),
            "yolo11n.pt",  # Pre-trained YOLO11
        ]
        
        for model_path in default_models:
            try:
                if isinstance(model_path, Path):
                    if not model_path.exists():
                        continue
                    model_path = str(model_path)
                
                print(f"Loading model: {model_path}")
                self.model = YOLO(model_path)
                self.model_path = model_path
                print(f"✅ Successfully loaded model: {model_path}")
                
                # Initialize class counts
                if hasattr(self.model, 'names'):
                    self.detection_stats['class_counts'] = {
                        name: 0 for name in self.model.names.values()
                    }
                
                return True
                
            except Exception as e:
                print(f"Failed to load {model_path}: {e}")
                continue
        
        print("⚠️  No model loaded. Please upload a model.")
        return False
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main monitoring page"""
            return render_template('monitor.html')
        
        @self.app.route('/mobile')
        def mobile():
            """Mobile-optimized monitoring page"""
            return render_template('mobile.html')
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status"""
            return jsonify({
                'model_loaded': self.model is not None,
                'model_path': self.model_path,
                'is_detecting': self.is_detecting,
                'camera_id': self.camera_id,
                'confidence_threshold': self.confidence_threshold,
                'stats': self.detection_stats
            })
        
        @self.app.route('/api/settings', methods=['GET', 'POST'])
        def api_settings():
            """Get/Update settings"""
            if request.method == 'POST':
                data = request.get_json()
                
                if 'confidence_threshold' in data:
                    self.confidence_threshold = float(data['confidence_threshold'])
                
                if 'camera_id' in data:
                    new_camera_id = int(data['camera_id'])
                    if new_camera_id != self.camera_id:
                        self.camera_id = new_camera_id
                        if self.is_detecting:
                            self.stop_detection()
                            self.start_detection()
                
                return jsonify({'status': 'success'})
            
            return jsonify({
                'confidence_threshold': self.confidence_threshold,
                'camera_id': self.camera_id
            })
        
        @self.app.route('/api/detection/start', methods=['POST'])
        def api_start_detection():
            """Start detection"""
            if not self.model:
                return jsonify({'error': 'No model loaded'}), 400
            
            success = self.start_detection()
            if success:
                return jsonify({'status': 'started'})
            else:
                return jsonify({'error': 'Failed to start camera'}), 500
        
        @self.app.route('/api/detection/stop', methods=['POST'])
        def api_stop_detection():
            """Stop detection"""
            self.stop_detection()
            return jsonify({'status': 'stopped'})
        
        @self.app.route('/api/history')
        def api_history():
            """Get detection history"""
            return jsonify(self.detection_history[-50:])  # Last 50 detections
        
        @self.app.route('/api/reset_stats', methods=['POST'])
        def api_reset_stats():
            """Reset detection statistics"""
            self.detection_stats = {
                'total_detections': 0,
                'class_counts': {name: 0 for name in self.model.names.values()} if self.model else {},
                'session_start': datetime.now().isoformat(),
                'last_detection': None,
                'fps': 0
            }
            self.detection_history = []
            return jsonify({'status': 'reset'})
    
    def setup_socket_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            print(f"Client connected: {request.sid}")
            emit('status', {
                'model_loaded': self.model is not None,
                'is_detecting': self.is_detecting,
                'stats': self.detection_stats
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            print(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_frame')
        def handle_frame_request():
            """Handle frame request from client"""
            if self.is_detecting and hasattr(self, 'current_frame'):
                frame_data = self.encode_frame(self.current_frame)
                if frame_data:
                    emit('frame', {'image': frame_data})
    
    def start_detection(self):
        """Start camera detection"""
        if self.is_detecting:
            return True
        
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            if not self.camera.isOpened():
                return False
            
            self.is_detecting = True
            self.detection_thread = threading.Thread(target=self.detection_loop, daemon=True)
            self.detection_thread.start()
            
            print(f"Started detection on camera {self.camera_id}")
            return True
            
        except Exception as e:
            print(f"Error starting detection: {e}")
            return False
    
    def stop_detection(self):
        """Stop camera detection"""
        self.is_detecting = False
        
        if hasattr(self, 'camera') and self.camera:
            self.camera.release()
            self.camera = None
        
        print("Detection stopped")
    
    def detection_loop(self):
        """Main detection loop"""
        fps_counter = 0
        fps_start_time = time.time()
        
        while self.is_detecting:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    break
                
                # Resize frame for better performance
                frame = cv2.resize(frame, (640, 480))
                
                # Run detection
                annotated_frame, detections = self.detect_frame(frame)
                
                # Store current frame for streaming
                self.current_frame = annotated_frame
                
                # Calculate FPS
                fps_counter += 1
                current_time = time.time()
                if current_time - fps_start_time >= 1.0:
                    self.detection_stats['fps'] = fps_counter / (current_time - fps_start_time)
                    fps_counter = 0
                    fps_start_time = current_time
                
                # Process detections
                if detections:
                    self.process_detections(detections)
                
                # Emit updates to connected clients
                self.socketio.emit('stats_update', self.detection_stats)
                
                # Emit frame to clients (throttled)
                if fps_counter % 3 == 0:  # Send every 3rd frame to reduce bandwidth
                    frame_data = self.encode_frame(annotated_frame)
                    if frame_data:
                        self.socketio.emit('frame', {'image': frame_data})
                
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Detection loop error: {e}")
                break
        
        self.is_detecting = False
    
    def detect_frame(self, frame):
        """Detect insects in frame"""
        if not self.model:
            return frame, []
        
        try:
            # Run YOLO detection
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            
            annotated_frame = frame.copy()
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract box info
                        x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        class_name = self.model.names[class_id]
                        
                        # Draw detection
                        color = self.get_class_color(class_id)
                        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Draw label
                        label = f"{class_name}: {confidence:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
                        cv2.rectangle(annotated_frame, (x1, y1-label_size[1]-10), (x1+label_size[0], y1), color, -1)
                        cv2.putText(annotated_frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                        detections.append({
                            'class_name': class_name,
                            'confidence': confidence,
                            'bbox': [x1, y1, x2, y2],
                            'timestamp': datetime.now().isoformat()
                        })
            
            # Draw info panel
            annotated_frame = self.draw_info_panel(annotated_frame)
            
            return annotated_frame, detections
            
        except Exception as e:
            print(f"Detection error: {e}")
            return frame, []
    
    def get_class_color(self, class_id):
        """Get color for class"""
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), 
                 (0, 255, 255), (128, 0, 128), (255, 165, 0), (0, 128, 128), (128, 128, 0)]
        return colors[class_id % len(colors)]
    
    def draw_info_panel(self, frame):
        """Draw information panel on frame"""
        height, width = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (300, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Info text
        cv2.putText(frame, "Insect Detection Monitor", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, f"FPS: {self.detection_stats['fps']:.1f}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Total: {self.detection_stats['total_detections']}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Time: {datetime.now().strftime('%H:%M:%S')}", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        return frame
    
    def process_detections(self, detections):
        """Process and store detections"""
        for detection in detections:
            # Update stats
            self.detection_stats['total_detections'] += 1
            class_name = detection['class_name']
            
            if class_name in self.detection_stats['class_counts']:
                self.detection_stats['class_counts'][class_name] += 1
            
            self.detection_stats['last_detection'] = detection['timestamp']
            
            # Add to history
            self.detection_history.append(detection)
            if len(self.detection_history) > self.max_history:
                self.detection_history.pop(0)
            
            # Emit detection event
            self.socketio.emit('new_detection', detection)
    
    def encode_frame(self, frame):
        """Encode frame to base64 for web streaming"""
        try:
            # Resize for web streaming
            frame = cv2.resize(frame, (640, 480))
            
            # Encode frame
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            frame_data = base64.b64encode(buffer).decode('utf-8')
            return frame_data
        except Exception as e:
            print(f"Frame encoding error: {e}")
            return None
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the web application"""
        print(f"🚀 Starting Web Insect Detection Monitor")
        print(f"📱 Access from computer: http://localhost:{port}")
        print(f"📱 Access from mobile: http://[your-ip-address]:{port}/mobile")
        print(f"⚙️  Settings: http://localhost:{port}")
        print(f"🔄 Auto-loaded YOLO11 model: {self.model_path}")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug)


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Web-based Real-time Insect Detection')
    parser.add_argument('--model', help='Path to YOLO model (optional, will auto-load YOLO11)')
    parser.add_argument('--host', default='0.0.0.0', help='Host IP (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Port number (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    try:
        # Create and run detector
        detector = WebInsectDetector(model_path=args.model)
        detector.run(host=args.host, port=args.port, debug=args.debug)
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
