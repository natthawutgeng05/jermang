#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup and Installation Script for Insect Detection System
สคริปต์ติดตั้งและเซตอัพระบบตรวจจับแมลง
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is suitable"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    
    # Check for Python 3.13 compatibility issues
    if version.major == 3 and version.minor >= 13:
        print(f"Python version: {version.major}.{version.minor}.{version.micro} ✓")
        print("Note: Using Python 3.13+, some packages may need newer versions")
    else:
        print(f"Python version: {version.major}.{version.minor}.{version.micro} ✓")
    
    return True

def install_requirements():
    """Install required packages in stages"""
    print("Installing required packages...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        print("Error: requirements.txt not found")
        return False
    
    try:
        # Stage 1: Upgrade pip and basic tools
        print("Stage 1: Upgrading pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Stage 2: Install GUI framework first
        print("Stage 2: Installing PySide6...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PySide6>=6.8.0", "--user"])
        
        # Stage 3: Install core packages
        print("Stage 3: Installing core packages...")
        core_packages = [
            "numpy>=1.24.0",
            "opencv-python>=4.8.0", 
            "Pillow>=10.0.0",
            "PyYAML>=6.0.0",
            "tqdm>=4.66.0",
            "requests>=2.31.0"
        ]
        
        for package in core_packages:
            print(f"  Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
        
        # Stage 4: Install ML packages (may take longer)
        print("Stage 4: Installing machine learning packages...")
        ml_packages = [
            "torch>=2.0.0",
            "torchvision>=0.15.0", 
            "ultralytics>=8.0.0",
            "scikit-learn>=1.3.0"
        ]
        
        for package in ml_packages:
            print(f"  Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"], timeout=300)
            except subprocess.TimeoutExpired:
                print(f"  Warning: {package} installation timed out, but may still be installing...")
        
        # Stage 5: Install optional packages
        print("Stage 5: Installing optional packages...")
        optional_packages = [
            "pandas>=2.0.0",
            "matplotlib>=3.7.0",
            "seaborn>=0.12.0",
            "imageio>=2.31.0",
            "scikit-image>=0.21.0",
            "Flask>=2.3.0",
            "Flask-CORS>=4.0.0"
        ]
        
        for package in optional_packages:
            try:
                print(f"  Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--user"])
            except subprocess.CalledProcessError:
                print(f"  Warning: Failed to install {package}, but continuing...")
        
        print("Requirements installed successfully ✓")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        print("You can try installing manually with:")
        print("  pip install --user -r requirements.txt")
        return False

def check_gpu_support():
    """Check if GPU is available"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(0) if gpu_count > 0 else "Unknown"
            print(f"GPU available: {gpu_name} (CUDA {torch.version.cuda}) ✓")
            return True
        else:
            print("GPU not available, using CPU")
            return False
    except ImportError:
        print("PyTorch not installed yet")
        return False

def create_directories():
    """Create necessary directories"""
    base_dir = Path(__file__).parent
    
    directories = [
        "dataset/images",
        "dataset/annotations", 
        "training/models",
        "detection/output"
    ]
    
    print("Creating directories...")
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  {dir_path} ✓")

def download_yolo_models():
    """Download pre-trained YOLO models"""
    print("Downloading YOLO models...")
    
    try:
        from ultralytics import YOLO
        
        # Download different model sizes
        models = ['yolov8n.pt', 'yolov8s.pt', 'yolov8m.pt']
        
        for model_name in models:
            print(f"  Downloading {model_name}...")
            model = YOLO(model_name)  # This will download the model
            print(f"  {model_name} ✓")
        
        return True
    except Exception as e:
        print(f"Error downloading models: {e}")
        return False

def test_installation():
    """Test if installation is successful"""
    print("Testing installation...")
    
    try:
        # Test imports
        import cv2
        import numpy as np
        import torch
        from ultralytics import YOLO
        import flask
        from PIL import Image
        import pandas as pd
        import matplotlib.pyplot as plt
        
        print("All packages imported successfully ✓")
        
        # Test YOLO model loading
        model = YOLO('yolov8n.pt')
        print("YOLO model loaded successfully ✓")
        
        # Test OpenCV
        print(f"OpenCV version: {cv2.__version__} ✓")
        
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🐛 INSECT DETECTION SYSTEM SETUP COMPLETE 🐛")
    print("="*60)
    print()
    print("📋 Next Steps:")
    print()
    print("1. Start the Annotation Tool:")
    print("   cd annotation_tool")
    print("   python app.py")
    print("   Then open: http://localhost:5000")
    print()
    print("2. Upload and annotate your insect images")
    print()
    print("3. Train your model:")
    print("   cd training")
    print("   python train_yolo.py")
    print()
    print("4. Run detection:")
    print("   # From camera:")
    print("   cd detection")
    print("   python detect_camera.py --model ../training/models/insect_detector_best.pt")
    print()
    print("   # From images:")
    print("   python detect_image.py --model ../training/models/insect_detector_best.pt --input your_image.jpg")
    print()
    print("📁 Directory Structure:")
    print("   dataset/images/      - Put your raw images here")
    print("   dataset/annotations/ - Annotation files (auto-generated)")
    print("   training/models/     - Trained models will be saved here")
    print("   detection/output/    - Detection results")
    print()
    print("💡 Tips:")
    print("   - Annotate at least 100+ images per insect class for good results")
    print("   - Use diverse images (different angles, lighting, backgrounds)")
    print("   - The more data you annotate, the better the model will perform")
    print()
    print("🚀 Happy insect detecting!")
    print("="*60)

def main():
    """Main setup function"""
    print("🐛 Insect Detection System Setup")
    print("="*50)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install requirements
    if not install_requirements():
        return False
    
    # Check GPU support
    check_gpu_support()
    
    # Create directories
    create_directories()
    
    # Download YOLO models
    if not download_yolo_models():
        print("Warning: Failed to download YOLO models, but you can continue")
    
    # Test installation
    if not test_installation():
        print("Warning: Some tests failed, but you can try to continue")
    
    # Print usage instructions
    print_usage_instructions()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nSetup completed successfully! 🎉")
            sys.exit(0)
        else:
            print("\nSetup failed! ❌")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
