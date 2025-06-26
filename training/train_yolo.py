#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO Training Script for Insect Detection
ระบบการ Train โมเดล YOLO สำหรับตรวจจับแมลง
"""

import os
import sys
import yaml
import shutil
from pathlib import Path
from ultralytics import YOLO
from sklearn.model_selection import train_test_split
import cv2
import numpy as np
from tqdm import tqdm

class InsectYOLOTrainer:
    def __init__(self, data_dir="../dataset", output_dir="./models"):
        """
        Initialize the YOLO trainer
        
        Args:
            data_dir (str): Path to dataset directory
            output_dir (str): Path to save trained models
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.images_dir = self.data_dir / "images"
        self.annotations_dir = self.data_dir / "annotations"
        self.classes_file = self.data_dir / "classes.txt"
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Load classes
        self.classes = self.load_classes()
        print(f"Found {len(self.classes)} classes: {self.classes}")
        
    def load_classes(self):
        """Load class names from classes.txt"""
        if not self.classes_file.exists():
            raise FileNotFoundError(f"Classes file not found: {self.classes_file}")
        
        with open(self.classes_file, 'r', encoding='utf-8') as f:
            classes = [line.strip() for line in f.readlines() if line.strip()]
        
        return classes
    
    def get_annotated_images(self):
        """Get list of images that have corresponding annotation files"""
        annotated_images = []
        
        if not self.images_dir.exists():
            print(f"Images directory not found: {self.images_dir}")
            return annotated_images
        
        for image_file in self.images_dir.glob("*"):
            if image_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp']:
                annotation_file = self.annotations_dir / f"{image_file.stem}.txt"
                if annotation_file.exists():
                    annotated_images.append(image_file.name)
        
        return annotated_images
    
    def create_dataset_splits(self, test_size=0.2, val_size=0.1):
        """
        Create train/val/test splits and organize data for YOLO training
        
        Args:
            test_size (float): Proportion of data for testing
            val_size (float): Proportion of data for validation
        """
        annotated_images = self.get_annotated_images()
        
        if len(annotated_images) == 0:
            raise ValueError("No annotated images found! Please annotate some images first.")
        
        print(f"Found {len(annotated_images)} annotated images")
        
        # Handle small datasets
        if len(annotated_images) < 10:
            print("⚠️  Warning: Very small dataset detected!")
            print("   For better results, annotate at least 20-50 images per class")
            
            if len(annotated_images) <= 3:
                # Use all images for training when very few samples
                train_images = annotated_images
                val_images = []
                test_images = []
                print("   Using all images for training (no validation/test split)")
            else:
                # Simple split for small datasets
                split_idx = max(1, len(annotated_images) - 1)
                train_images = annotated_images[:split_idx]
                val_images = annotated_images[split_idx:]
                test_images = []
        else:
            # Standard split for larger datasets
            train_images, temp_images = train_test_split(
                annotated_images, test_size=(test_size + val_size), random_state=42
            )
            
            if temp_images:
                val_images, test_images = train_test_split(
                    temp_images, test_size=(test_size / (test_size + val_size)), random_state=42
                )
            else:
                val_images, test_images = [], []
        
        print(f"Dataset splits:")
        print(f"  Train: {len(train_images)} images")
        print(f"  Validation: {len(val_images)} images")
        print(f"  Test: {len(test_images)} images")
        
        # Create YOLO dataset structure
        dataset_dir = self.output_dir / "dataset"
        dataset_dir.mkdir(exist_ok=True)
        
        splits = {
            'train': train_images,
            'val': val_images if val_images else train_images,  # Use train images for val if no val set
            'test': test_images
        }
        
        for split_name, image_list in splits.items():
            if not image_list and split_name != 'test':  # Always create train and val, skip empty test
                continue
                
            split_dir = dataset_dir / split_name
            (split_dir / "images").mkdir(parents=True, exist_ok=True)
            (split_dir / "labels").mkdir(parents=True, exist_ok=True)
            
            for image_name in tqdm(image_list, desc=f"Creating {split_name} split"):
                # Copy image
                src_image = self.images_dir / image_name
                dst_image = split_dir / "images" / image_name
                shutil.copy2(src_image, dst_image)
                
                # Copy annotation
                annotation_name = f"{Path(image_name).stem}.txt"
                src_annotation = self.annotations_dir / annotation_name
                dst_annotation = split_dir / "labels" / annotation_name
                shutil.copy2(src_annotation, dst_annotation)
        
        return dataset_dir
    
    def create_data_yaml(self, dataset_dir):
        """Create data.yaml file for YOLO training"""
        data_yaml = {
            'path': str(dataset_dir.absolute()),
            'train': 'train/images',
            'val': 'val/images',
            'test': 'test/images',
            'nc': len(self.classes),
            'names': self.classes
        }
        
        yaml_path = self.output_dir / "data.yaml"
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data_yaml, f, default_flow_style=False, allow_unicode=True)
        
        print(f"Created data.yaml: {yaml_path}")
        return yaml_path
    
    def validate_annotations(self):
        """Validate annotation files for correct format"""
        print("Validating annotations...")
        
        valid_count = 0
        invalid_files = []
        
        for annotation_file in self.annotations_dir.glob("*.txt"):
            try:
                with open(annotation_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        
                        parts = line.split()
                        if len(parts) != 5:
                            raise ValueError(f"Line {line_num}: Expected 5 values, got {len(parts)}")
                        
                        class_id = int(parts[0])
                        if not (0 <= class_id < len(self.classes)):
                            raise ValueError(f"Line {line_num}: Invalid class_id {class_id}")
                        
                        # Check if coordinates are in valid range [0, 1]
                        for i, coord in enumerate(parts[1:], 1):
                            coord_val = float(coord)
                            if not (0 <= coord_val <= 1):
                                raise ValueError(f"Line {line_num}: Coordinate {i} out of range: {coord_val}")
                
                valid_count += 1
                
            except Exception as e:
                invalid_files.append((annotation_file.name, str(e)))
        
        print(f"Validation complete: {valid_count} valid files")
        
        if invalid_files:
            print(f"Found {len(invalid_files)} invalid annotation files:")
            for filename, error in invalid_files[:5]:  # Show first 5 errors
                print(f"  {filename}: {error}")
            if len(invalid_files) > 5:
                print(f"  ... and {len(invalid_files) - 5} more")
        
        return len(invalid_files) == 0
    
    def train_model(self, model_size='n', epochs=100, imgsz=640, batch_size=16, model_version='yolo11'):
        """
        Train YOLO model
        
        Args:
            model_size (str): Model size ('n', 's', 'm', 'l', 'x')
            epochs (int): Number of training epochs
            imgsz (int): Image size for training
            batch_size (int): Batch size for training
            model_version (str): YOLO version ('yolo11', 'yolov10', 'yolov8')
        """
        print("Starting YOLO training...")
        
        # Validate annotations first
        if not self.validate_annotations():
            print("Please fix annotation errors before training")
            return None
        
        # Create dataset splits
        dataset_dir = self.create_dataset_splits()
        
        # Create data.yaml
        data_yaml_path = self.create_data_yaml(dataset_dir)
        
        # Initialize YOLO model
        if model_version == 'yolo11':
            model_name = f"yolo11{model_size}.pt"
        elif model_version == 'yolov10':
            model_name = f"yolov10{model_size}.pt"
        else:  # default to yolov8
            model_name = f"yolov8{model_size}.pt"
            
        model = YOLO(model_name)
        
        print(f"🚀 Training with {model_name} (YOLO version: {model_version})")
        print(f"📊 Dataset: {data_yaml_path}")
        print(f"⚙️  Settings: {epochs} epochs, {imgsz}x{imgsz} images, batch size {batch_size}")
        
        # Start training
        results = model.train(
            data=str(data_yaml_path),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            name='insect_detection',
            project=str(self.output_dir),
            exist_ok=True,
            save=True,
            save_period=10,  # Save checkpoint every 10 epochs
            patience=20,     # Early stopping patience
            verbose=True
        )
        
        # Save final model
        best_model_path = self.output_dir / "insect_detection" / "weights" / "best.pt"
        final_model_path = self.output_dir / "insect_detector_best.pt"
        
        if best_model_path.exists():
            shutil.copy2(best_model_path, final_model_path)
            print(f"Best model saved to: {final_model_path}")
        
        return results
    
    def evaluate_model(self, model_path=None):
        """Evaluate trained model"""
        if model_path is None:
            model_path = self.output_dir / "insect_detector_best.pt"
        
        if not Path(model_path).exists():
            print(f"Model not found: {model_path}")
            return None
        
        model = YOLO(model_path)
        data_yaml_path = self.output_dir / "data.yaml"
        
        if data_yaml_path.exists():
            results = model.val(data=str(data_yaml_path))
            return results
        else:
            print("data.yaml not found. Please train the model first.")
            return None


def main():
    """Main training function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train YOLO model for insect detection')
    parser.add_argument('--data_dir', default='../dataset', help='Path to dataset directory')
    parser.add_argument('--output_dir', default='./models', help='Path to save models')
    parser.add_argument('--model_size', choices=['n', 's', 'm', 'l', 'x'], default='n', 
                       help='Model size (n=nano, s=small, m=medium, l=large, x=extra-large)')
    parser.add_argument('--model_version', choices=['yolo11', 'yolov10', 'yolov8'], default='yolo11',
                       help='YOLO model version (yolo11=default, yolov10, yolov8)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--imgsz', type=int, default=640, help='Image size for training')
    parser.add_argument('--batch_size', type=int, default=16, help='Batch size for training')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate existing model')
    
    args = parser.parse_args()
    
    try:
        trainer = InsectYOLOTrainer(args.data_dir, args.output_dir)
        
        if args.evaluate:
            print("Evaluating model...")
            results = trainer.evaluate_model()
            if results:
                print("Evaluation completed successfully")
        else:
            print("🚀 Starting YOLO11 training...")
            results = trainer.train_model(
                model_size=args.model_size,
                epochs=args.epochs,
                imgsz=args.imgsz,
                batch_size=args.batch_size,
                model_version=args.model_version
            )
            
            if results:
                print("Training completed successfully!")
                print("You can now use the trained model for detection.")
            else:
                print("Training failed!")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
