#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YOLO Model Comparison Script
สคริปต์เปรียบเทียบ YOLOv8, YOLOv10, และ YOLO11
"""

import os
import sys
import time
import json
from pathlib import Path
from ultralytics import YOLO
import torch

class YOLOModelComparison:
    def __init__(self, data_yaml_path="../training/models/data.yaml"):
        """
        Initialize YOLO model comparison
        
        Args:
            data_yaml_path (str): Path to data.yaml file
        """
        self.data_yaml_path = Path(data_yaml_path)
        self.results = {}
        self.models_to_test = {
            'yolov8n': 'yolov8n.pt',
            'yolov10n': 'yolov10n.pt', 
            'yolo11n': 'yolo11n.pt'
        }
        
        if not self.data_yaml_path.exists():
            raise FileNotFoundError(f"Data yaml not found: {self.data_yaml_path}")
    
    def download_models(self):
        """Download all models for comparison"""
        print("📥 Downloading YOLO models for comparison...")
        
        for model_name, model_file in self.models_to_test.items():
            print(f"  Downloading {model_name}...")
            try:
                model = YOLO(model_file)
                print(f"  ✅ {model_name} downloaded successfully")
            except Exception as e:
                print(f"  ❌ Failed to download {model_name}: {e}")
                self.models_to_test.pop(model_name, None)
    
    def get_model_info(self, model):
        """Get model information"""
        try:
            info = {
                'parameters': sum(p.numel() for p in model.model.parameters()),
                'model_size_mb': Path(model.ckpt_path).stat().st_size / (1024*1024) if hasattr(model, 'ckpt_path') else 0,
                'input_size': getattr(model.model, 'imgsz', 640)
            }
            return info
        except Exception as e:
            print(f"Warning: Could not get model info: {e}")
            return {}
    
    def benchmark_inference_speed(self, model, num_runs=10):
        """Benchmark inference speed"""
        print(f"    ⏱️  Benchmarking inference speed...")
        
        # Create dummy input
        dummy_input = torch.randn(1, 3, 640, 640)
        
        # Warmup
        for _ in range(3):
            _ = model(dummy_input, verbose=False)
        
        # Benchmark
        times = []
        for _ in range(num_runs):
            start_time = time.time()
            _ = model(dummy_input, verbose=False)
            end_time = time.time()
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        fps = 1.0 / avg_time
        
        return {
            'avg_inference_time_ms': avg_time * 1000,
            'fps': fps,
            'min_time_ms': min(times) * 1000,
            'max_time_ms': max(times) * 1000
        }
    
    def quick_training_test(self, model_name, model_file, epochs=5):
        """Quick training test to compare learning capabilities"""
        print(f"  🏋️  Quick training test for {model_name}...")
        
        try:
            model = YOLO(model_file)
            
            # Get model info
            model_info = self.get_model_info(model)
            
            # Benchmark inference speed
            speed_info = self.benchmark_inference_speed(model)
            
            # Quick training (very few epochs)
            print(f"    📚 Running {epochs} epochs training...")
            start_time = time.time()
            
            results = model.train(
                data=str(self.data_yaml_path),
                epochs=epochs,
                imgsz=640,
                batch=4,  # Small batch for quick test
                name=f'{model_name}_test',
                project='./comparison',
                exist_ok=True,
                save=False,  # Don't save checkpoints
                verbose=False,
                patience=0,  # Disable early stopping
                plots=False  # Disable plots
            )
            
            training_time = time.time() - start_time
            
            # Get final metrics
            metrics = {
                'training_time_minutes': training_time / 60,
                'final_map50': float(results.results_dict.get('metrics/mAP50(B)', 0)),
                'final_map50_95': float(results.results_dict.get('metrics/mAP50-95(B)', 0)),
                'final_precision': float(results.results_dict.get('metrics/precision(B)', 0)),
                'final_recall': float(results.results_dict.get('metrics/recall(B)', 0)),
                'epochs_completed': epochs
            }
            
            # Combine all results
            result = {
                **model_info,
                **speed_info,
                **metrics
            }
            
            print(f"    ✅ {model_name} completed - mAP50: {metrics['final_map50']:.3f}")
            return result
            
        except Exception as e:
            print(f"    ❌ {model_name} failed: {e}")
            return {'error': str(e)}
    
    def run_comparison(self, epochs=5):
        """Run full model comparison"""
        print("🔬 Starting YOLO Model Comparison")
        print("=" * 50)
        
        # Download models
        self.download_models()
        
        # Test each model
        for model_name, model_file in self.models_to_test.items():
            print(f"\n📊 Testing {model_name}...")
            self.results[model_name] = self.quick_training_test(model_name, model_file, epochs)
        
        # Save results
        self.save_results()
        
        # Print summary
        self.print_summary()
    
    def save_results(self):
        """Save comparison results to JSON"""
        output_dir = Path("./comparison")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_file = output_dir / f"yolo_comparison_{timestamp}.json"
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {results_file}")
    
    def print_summary(self):
        """Print comparison summary"""
        print("\n" + "=" * 60)
        print("📈 YOLO MODEL COMPARISON SUMMARY")
        print("=" * 60)
        
        # Table headers
        print(f"{'Model':<12} {'Params':<10} {'Size(MB)':<10} {'FPS':<8} {'mAP50':<8} {'Time(min)':<10}")
        print("-" * 60)
        
        for model_name, result in self.results.items():
            if 'error' in result:
                print(f"{model_name:<12} {'ERROR':<10} {'N/A':<10} {'N/A':<8} {'N/A':<8} {'N/A':<10}")
                continue
            
            params = result.get('parameters', 0) / 1e6  # Convert to millions
            size_mb = result.get('model_size_mb', 0)
            fps = result.get('fps', 0)
            map50 = result.get('final_map50', 0)
            time_min = result.get('training_time_minutes', 0)
            
            print(f"{model_name:<12} {params:<10.1f}M {size_mb:<10.1f} {fps:<8.1f} {map50:<8.3f} {time_min:<10.1f}")
        
        # Recommendations
        print("\n🎯 RECOMMENDATIONS:")
        best_speed = max(self.results.items(), key=lambda x: x[1].get('fps', 0) if 'error' not in x[1] else 0)
        best_accuracy = max(self.results.items(), key=lambda x: x[1].get('final_map50', 0) if 'error' not in x[1] else 0)
        
        print(f"  🚀 Fastest: {best_speed[0]} ({best_speed[1].get('fps', 0):.1f} FPS)")
        print(f"  🎯 Most accurate: {best_accuracy[0]} (mAP50: {best_accuracy[1].get('final_map50', 0):.3f})")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Compare YOLO models performance')
    parser.add_argument('--epochs', type=int, default=5, help='Number of epochs for quick training test')
    parser.add_argument('--data', default='../training/models/data.yaml', help='Path to data.yaml file')
    
    args = parser.parse_args()
    
    try:
        comparator = YOLOModelComparison(args.data)
        comparator.run_comparison(args.epochs)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
