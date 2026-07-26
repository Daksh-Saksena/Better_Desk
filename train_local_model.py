import os
import yaml
import shutil
import torch
from ultralytics import YOLO

def main():
    print("="*60)
    print("CONFIGURING LOCAL DATASET PATHS")
    print("="*60)
    
    base_dir = os.path.abspath('roboflow_ds')
    yaml_path = os.path.join(base_dir, 'data.yaml')
    
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
        
    data['train'] = os.path.join(base_dir, 'train', 'images')
    data['val'] = os.path.join(base_dir, 'valid', 'images')
    data['test'] = os.path.join(base_dir, 'test', 'images')
    
    with open(yaml_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
        
    print(f"Updated data.yaml with absolute paths:\n  Train: {data['train']}\n  Val:   {data['val']}")
    
    print("\n" + "="*60)
    print("STARTING LOCAL OFFLINE MODEL TRAINING ON APPLE SILICON GPU")
    print("="*60)
    
    model = YOLO('yolo11n.pt')
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    print(f"Hardware Acceleration Device: {device.upper()}")
    
    # Train for 20 epochs at 320x320 resolution for fast, accurate results on M-series Mac
    project_dir = os.path.abspath(os.path.join('runs', 'local_battery'))
    results = model.train(
        data=yaml_path,
        epochs=20,
        imgsz=320,
        batch=32,
        device=device,
        project=project_dir,
        name='train',
        exist_ok=True,
        workers=2
    )
    
    best_path = os.path.join(project_dir, 'train', 'weights', 'best.pt')
    alt_path = os.path.join(os.path.expanduser('~'), 'Desktop', 'propsoch', 'runs', 'detect', 'runs', 'local_battery', 'train', 'weights', 'best.pt')
    
    found_path = best_path if os.path.exists(best_path) else (alt_path if os.path.exists(alt_path) else None)
    
    if found_path:
        shutil.copy(found_path, 'battery_model.pt')
        print("\n" + "="*60)
        print(f"SUCCESS! Model trained and exported from {found_path} to: battery_model.pt")
        print("BetterDesk will now automatically use this offline model at 60 FPS!")
        print("="*60)
    else:
        print("\nWARNING: Could not find best.pt after training.")

if __name__ == "__main__":
    main()
