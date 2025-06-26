import os
import json
import shutil
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
import numpy as np

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = '../dataset/images'
ANNOTATION_FOLDER = '../dataset/annotations'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ANNOTATION_FOLDER, exist_ok=True)

# Default insect classes
DEFAULT_CLASSES = [
    'butterfly',  # ผีเสื้อ
    'bee',        # ผึ้ง
    'ant',        # มด
    'dragonfly',  # แมลงปอ
    'beetle',     # ด้วง
    'mosquito',   # ยุง
    'fly',        # แมลงวัน
    'spider',     # แมงมุม
    'grasshopper', # ตั๊กแตน
    'moth'        # ผีเสื้อกลางคืน
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_classes():
    """Load class names from file or use defaults"""
    classes_file = '../dataset/classes.txt'
    if os.path.exists(classes_file):
        with open(classes_file, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f.readlines()]
    else:
        # Create default classes file
        with open(classes_file, 'w', encoding='utf-8') as f:
            for cls in DEFAULT_CLASSES:
                f.write(f"{cls}\n")
        return DEFAULT_CLASSES

def save_classes(classes):
    """Save class names to file"""
    classes_file = '../dataset/classes.txt'
    with open(classes_file, 'w', encoding='utf-8') as f:
        for cls in classes:
            f.write(f"{cls}\n")

def load_annotation(image_name):
    """Load existing annotation for an image"""
    annotation_file = os.path.join(ANNOTATION_FOLDER, image_name.rsplit('.', 1)[0] + '.txt')
    if os.path.exists(annotation_file):
        annotations = []
        with open(annotation_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) == 5:
                    class_id, x_center, y_center, width, height = map(float, parts)
                    annotations.append({
                        'class_id': int(class_id),
                        'x_center': x_center,
                        'y_center': y_center,
                        'width': width,
                        'height': height
                    })
        return annotations
    return []

def save_annotation(image_name, annotations):
    """Save annotations in YOLO format"""
    annotation_file = os.path.join(ANNOTATION_FOLDER, image_name.rsplit('.', 1)[0] + '.txt')
    with open(annotation_file, 'w') as f:
        for ann in annotations:
            f.write(f"{ann['class_id']} {ann['x_center']} {ann['y_center']} {ann['width']} {ann['height']}\n")

@app.route('/')
def index():
    """Main annotation interface"""
    images = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    classes = load_classes()
    return render_template('index.html', images=images, classes=classes)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload new images for annotation"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded_files = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            uploaded_files.append(filename)
    
    return jsonify({'uploaded_files': uploaded_files})

@app.route('/images/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/get_image_info/<image_name>')
def get_image_info(image_name):
    """Get image dimensions and existing annotations"""
    image_path = os.path.join(UPLOAD_FOLDER, image_name)
    if not os.path.exists(image_path):
        return jsonify({'error': 'Image not found'}), 404
    
    # Get image dimensions
    with Image.open(image_path) as img:
        width, height = img.size
    
    # Load existing annotations
    annotations = load_annotation(image_name)
    classes = load_classes()
    
    return jsonify({
        'width': width,
        'height': height,
        'annotations': annotations,
        'classes': classes
    })

@app.route('/save_annotation', methods=['POST'])
def save_annotation_route():
    """Save annotations for an image"""
    data = request.get_json()
    image_name = data.get('image_name')
    annotations = data.get('annotations', [])
    
    if not image_name:
        return jsonify({'error': 'Image name is required'}), 400
    
    save_annotation(image_name, annotations)
    return jsonify({'success': True})

@app.route('/get_classes')
def get_classes():
    """Get list of available classes"""
    return jsonify({'classes': load_classes()})

@app.route('/add_class', methods=['POST'])
def add_class():
    """Add a new class"""
    data = request.get_json()
    new_class = data.get('class_name', '').strip()
    
    if not new_class:
        return jsonify({'error': 'Class name is required'}), 400
    
    classes = load_classes()
    if new_class not in classes:
        classes.append(new_class)
        save_classes(classes)
        return jsonify({'success': True, 'classes': classes})
    else:
        return jsonify({'error': 'Class already exists'}), 400

@app.route('/delete_class', methods=['POST'])
def delete_class():
    """Delete a class"""
    data = request.get_json()
    class_name = data.get('class_name', '').strip()
    
    classes = load_classes()
    if class_name in classes:
        classes.remove(class_name)
        save_classes(classes)
        return jsonify({'success': True, 'classes': classes})
    else:
        return jsonify({'error': 'Class not found'}), 400

@app.route('/export_dataset')
def export_dataset():
    """Export dataset statistics"""
    images = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)]
    classes = load_classes()
    
    stats = {
        'total_images': len(images),
        'total_classes': len(classes),
        'classes': classes,
        'annotated_images': 0,
        'total_annotations': 0,
        'class_distribution': {cls: 0 for cls in classes}
    }
    
    for image in images:
        annotations = load_annotation(image)
        if annotations:
            stats['annotated_images'] += 1
            stats['total_annotations'] += len(annotations)
            for ann in annotations:
                if 0 <= ann['class_id'] < len(classes):
                    class_name = classes[ann['class_id']]
                    stats['class_distribution'][class_name] += 1
    
    return jsonify(stats)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
