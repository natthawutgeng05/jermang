#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real-time Insect Detection from Camera
ระบบตรวจจับแมลงแบบ Real-time จากกล้อง
"""

import cv2
import numpy as np
import time
import argparse
from pathlib import Path
import sys

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics not installed. Please run: pip install ultralytics")
    sys.exit(1)

class InsectDetector:
    def __init__(self, model_path, confidence_threshold=0.5, device='cpu'):
        """
        Initialize insect detector
        
        Args:
            model_path (str): Path to trained YOLO model
            confidence_threshold (float): Minimum confidence for detection
            device (str): Device to run inference on ('cpu' or 'cuda')
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Load model
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        print(f"Loading model: {self.model_path}")
        self.model = YOLO(str(self.model_path))
        
        # Load class names
        self.class_names = self.model.names
        print(f"Loaded {len(self.class_names)} classes: {list(self.class_names.values())}")
        
        # Define colors for each class
        self.colors = self._generate_colors(len(self.class_names))
        
        # Statistics
        self.detection_count = {name: 0 for name in self.class_names.values()}
        self.fps_counter = 0
        self.fps_start_time = time.time()
        
    def _generate_colors(self, num_classes):
        """Generate distinct colors for each class"""
        colors = []
        for i in range(num_classes):
            hue = i * 180 // num_classes
            color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
            colors.append(tuple(map(int, color)))
        return colors
    
    def detect_frame(self, frame):
        """
        Detect insects in a single frame
        
        Args:
            frame: Input frame from camera
            
        Returns:
            Annotated frame with detections
        """
        # Run inference
        results = self.model(frame, conf=self.confidence_threshold, device=self.device)
        
        # Process results
        annotated_frame = frame.copy()
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Get box coordinates
                    x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    # Get class name and color
                    class_name = self.class_names[class_id]
                    color = self.colors[class_id]
                    
                    # Update detection count
                    self.detection_count[class_name] += 1
                    
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
                    
                    detections.append({
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': (x1, y1, x2, y2)
                    })
        
        return annotated_frame, detections
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.fps_counter += 1
        current_time = time.time()
        elapsed_time = current_time - self.fps_start_time
        
        if elapsed_time >= 1.0:  # Update FPS every second
            fps = self.fps_counter / elapsed_time
            self.fps_counter = 0
            self.fps_start_time = current_time
            return fps
        return None
    
    def draw_info_panel(self, frame, fps=None):
        """Draw information panel on frame"""
        height, width = frame.shape[:2]
        panel_height = 150
        panel_width = 300
        
        # Create semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (panel_width, panel_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        y_offset = 30
        
        # Title
        cv2.putText(frame, "Insect Detection", (20, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        y_offset += 25
        
        # FPS
        if fps is not None:
            cv2.putText(frame, f"FPS: {fps:.1f}", (20, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 20
        
        # Detection counts (show top 3)
        sorted_counts = sorted(self.detection_count.items(), 
                             key=lambda x: x[1], reverse=True)[:3]
        
        cv2.putText(frame, "Detections:", (20, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        y_offset += 15
        
        for class_name, count in sorted_counts:
            if count > 0:
                cv2.putText(frame, f"  {class_name}: {count}", (20, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                y_offset += 15
        
        return frame
    
    def run_camera_detection(self, camera_id=0, save_video=False, output_path="output_detection.mp4"):
        """
        Run real-time detection from camera
        
        Args:
            camera_id (int): Camera device ID
            save_video (bool): Whether to save output video
            output_path (str): Path to save output video
        """
        # Initialize camera
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera {camera_id}")
        
        # Get camera properties
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        print(f"Camera initialized: {frame_width}x{frame_height} @ {fps} FPS")
        
        # Initialize video writer if saving
        video_writer = None
        if save_video:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_writer = cv2.VideoWriter(output_path, fourcc, fps, 
                                         (frame_width, frame_height))
            print(f"Saving video to: {output_path}")
        
        print("Starting detection... Press 'q' to quit, 's' to save current frame")
        
        frame_count = 0
        current_fps = 0
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    print("Failed to read frame from camera")
                    break
                
                # Detect insects
                annotated_frame, detections = self.detect_frame(frame)
                
                # Calculate FPS
                fps_value = self.calculate_fps()
                if fps_value is not None:
                    current_fps = fps_value
                
                # Draw information panel
                annotated_frame = self.draw_info_panel(annotated_frame, current_fps)
                
                # Save video frame
                if video_writer is not None:
                    video_writer.write(annotated_frame)
                
                # Display frame
                cv2.imshow('Insect Detection', annotated_frame)
                
                # Print detections to console
                if detections:
                    print(f"Frame {frame_count}: Found {len(detections)} insects")
                    for det in detections:
                        print(f"  - {det['class_name']}: {det['confidence']:.2f}")
                
                frame_count += 1
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    save_path = f"detection_frame_{frame_count}.jpg"
                    cv2.imwrite(save_path, annotated_frame)
                    print(f"Frame saved to: {save_path}")
                elif key == ord('r'):
                    # Reset detection counts
                    self.detection_count = {name: 0 for name in self.class_names.values()}
                    print("Detection counts reset")
                
        except KeyboardInterrupt:
            print("\nDetection stopped by user")
        
        finally:
            # Cleanup
            cap.release()
            if video_writer is not None:
                video_writer.release()
            cv2.destroyAllWindows()
            
            # Print final statistics
            print("\nFinal Detection Statistics:")
            for class_name, count in self.detection_count.items():
                if count > 0:
                    print(f"  {class_name}: {count} detections")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Real-time insect detection from camera')
    parser.add_argument('--model', required=True, help='Path to trained YOLO model')
    parser.add_argument('--camera', type=int, default=0, help='Camera device ID (default: 0)')
    parser.add_argument('--confidence', type=float, default=0.5, 
                       help='Confidence threshold (default: 0.5)')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu', 
                       help='Device to run inference on (default: cpu)')
    parser.add_argument('--save_video', action='store_true', 
                       help='Save output video')
    parser.add_argument('--output', default='output_detection.mp4', 
                       help='Output video path (default: output_detection.mp4)')
    
    args = parser.parse_args()
    
    try:
        # Initialize detector
        detector = InsectDetector(
            model_path=args.model,
            confidence_threshold=args.confidence,
            device=args.device
        )
        
        # Run detection
        detector.run_camera_detection(
            camera_id=args.camera,
            save_video=args.save_video,
            output_path=args.output
        )
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
