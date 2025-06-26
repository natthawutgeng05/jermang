#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Insect Detection from Images
ระบบตรวจจับแมลงจากรูปภาพ
"""

import cv2
import numpy as np
import argparse
from pathlib import Path
import sys
import json

try:
    from ultralytics import YOLO
except ImportError:
    print("Error: ultralytics not installed. Please run: pip install ultralytics")
    sys.exit(1)

class ImageInsectDetector:
    def __init__(self, model_path, confidence_threshold=0.5, device='cpu'):
        """
        Initialize insect detector for images
        
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
        
    def _generate_colors(self, num_classes):
        """Generate distinct colors for each class"""
        colors = []
        for i in range(num_classes):
            hue = i * 180 // num_classes
            color = cv2.cvtColor(np.uint8([[[hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
            colors.append(tuple(map(int, color)))
        return colors
    
    def detect_image(self, image_path, save_result=True, output_dir="output"):
        """
        Detect insects in an image
        
        Args:
            image_path (str): Path to input image
            save_result (bool): Whether to save annotated image
            output_dir (str): Directory to save results
            
        Returns:
            Detection results
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        print(f"Processing image: {image_path}")
        print(f"Image size: {image.shape[1]}x{image.shape[0]}")
        
        # Run inference
        results = self.model(image, conf=self.confidence_threshold, device=self.device)
        
        # Process results
        detections = []
        annotated_image = image.copy()
        
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
                    
                    # Store detection
                    detection = {
                        'class_name': class_name,
                        'class_id': class_id,
                        'confidence': confidence,
                        'bbox': {
                            'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                            'width': x2 - x1, 'height': y2 - y1
                        }
                    }
                    detections.append(detection)
                    
                    # Draw bounding box
                    cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 3)
                    
                    # Draw label
                    label = f"{class_name}: {confidence:.2f}"
                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
                    
                    # Background for label
                    cv2.rectangle(annotated_image, 
                                (x1, y1 - label_size[1] - 15), 
                                (x1 + label_size[0] + 10, y1), 
                                color, -1)
                    
                    # Label text
                    cv2.putText(annotated_image, label, 
                              (x1 + 5, y1 - 8), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.8, 
                              (255, 255, 255), 2)
        
        # Print results
        print(f"Found {len(detections)} insects:")
        class_counts = {}
        for det in detections:
            class_name = det['class_name']
            confidence = det['confidence']
            bbox = det['bbox']
            print(f"  - {class_name}: {confidence:.2f} at ({bbox['x1']}, {bbox['y1']}, {bbox['x2']}, {bbox['y2']})")
            
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        # Print summary
        if class_counts:
            print("\nSummary:")
            for class_name, count in class_counts.items():
                print(f"  {class_name}: {count}")
        
        # Save results if requested
        if save_result:
            output_dir = Path(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            # Save annotated image
            output_image_path = output_dir / f"{image_path.stem}_detected{image_path.suffix}"
            cv2.imwrite(str(output_image_path), annotated_image)
            print(f"Annotated image saved to: {output_image_path}")
            
            # Save detection results as JSON
            output_json_path = output_dir / f"{image_path.stem}_results.json"
            results_data = {
                'image_path': str(image_path),
                'image_size': {'width': image.shape[1], 'height': image.shape[0]},
                'model_path': str(self.model_path),
                'confidence_threshold': self.confidence_threshold,
                'detections': detections,
                'summary': class_counts
            }
            
            with open(output_json_path, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_json_path}")
        
        return {
            'detections': detections,
            'annotated_image': annotated_image,
            'summary': class_counts
        }
    
    def detect_batch(self, input_dir, output_dir="batch_output", image_extensions=None):
        """
        Detect insects in multiple images
        
        Args:
            input_dir (str): Directory containing images
            output_dir (str): Directory to save results
            image_extensions (list): List of image extensions to process
        """
        if image_extensions is None:
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        
        input_dir = Path(input_dir)
        if not input_dir.exists():
            raise FileNotFoundError(f"Input directory not found: {input_dir}")
        
        # Find all images
        image_files = []
        for ext in image_extensions:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"No images found in {input_dir}")
            return
        
        print(f"Found {len(image_files)} images to process")
        
        # Create output directory
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        # Process each image
        all_results = []
        total_detections = {}
        
        for i, image_file in enumerate(image_files, 1):
            print(f"\nProcessing {i}/{len(image_files)}: {image_file.name}")
            
            try:
                result = self.detect_image(image_file, save_result=True, output_dir=output_dir)
                all_results.append({
                    'image_file': str(image_file),
                    'result': result
                })
                
                # Update total counts
                for class_name, count in result['summary'].items():
                    total_detections[class_name] = total_detections.get(class_name, 0) + count
                    
            except Exception as e:
                print(f"Error processing {image_file}: {e}")
        
        # Save batch summary
        batch_summary = {
            'total_images': len(image_files),
            'processed_images': len(all_results),
            'total_detections': sum(total_detections.values()),
            'detections_by_class': total_detections,
            'results': all_results
        }
        
        summary_path = output_dir / "batch_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, indent=2, ensure_ascii=False)
        
        print(f"\nBatch processing complete!")
        print(f"Total detections: {sum(total_detections.values())}")
        print(f"Results saved to: {output_dir}")
        print(f"Summary saved to: {summary_path}")
        
        return batch_summary


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Insect detection from images')
    parser.add_argument('--model', required=True, help='Path to trained YOLO model')
    parser.add_argument('--input', required=True, 
                       help='Path to input image or directory')
    parser.add_argument('--output', default='output', 
                       help='Output directory (default: output)')
    parser.add_argument('--confidence', type=float, default=0.5, 
                       help='Confidence threshold (default: 0.5)')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default='cpu', 
                       help='Device to run inference on (default: cpu)')
    parser.add_argument('--batch', action='store_true', 
                       help='Process all images in input directory')
    parser.add_argument('--no_save', action='store_true', 
                       help='Do not save results')
    
    args = parser.parse_args()
    
    try:
        # Initialize detector
        detector = ImageInsectDetector(
            model_path=args.model,
            confidence_threshold=args.confidence,
            device=args.device
        )
        
        input_path = Path(args.input)
        
        if args.batch or input_path.is_dir():
            # Batch processing
            print("Running batch detection...")
            detector.detect_batch(input_path, args.output)
        else:
            # Single image processing
            print("Running single image detection...")
            detector.detect_image(input_path, 
                                save_result=not args.no_save, 
                                output_dir=args.output)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
