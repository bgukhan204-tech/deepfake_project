import os
import cv2
import numpy as np

try:
    import tensorflow as tf
    from tensorflow.keras.optimizers import Adam
    from model.unet_segmentation import build_unet_model
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None

def generate_synthetic_training_data(num_samples=100, img_size=(224, 224)):
    """
    Generates synthetic image-mask pairs to train/fine-tune the U-Net model.
    Creates pristine images with simulated local morphing/manipulation masks.
    """
    X = []
    Y = []
    h, w = img_size
    
    for i in range(num_samples):
        # Base image: random noise + gradient patterns
        base = np.random.randint(50, 200, (h, w, 3), dtype=np.uint8)
        mask = np.zeros((h, w, 1), dtype=np.float32)
        
        # 50% of samples have simulated manipulations
        if i % 2 == 0:
            # Draw synthetic manipulated patches
            cx = np.random.randint(40, w - 40)
            cy = np.random.randint(40, h - 40)
            rw = np.random.randint(20, 50)
            rh = np.random.randint(20, 50)
            
            # Apply local gaussian noise & distortion to base
            patch = base[cy:cy+rh, cx:cx+rw].copy()
            noisy_patch = cv2.GaussianBlur(patch, (9, 9), 3.0)
            noisy_patch = np.clip(noisy_patch.astype(np.float32) * 1.2, 0, 255).astype(np.uint8)
            
            base[cy:cy+rh, cx:cx+rw] = noisy_patch
            mask[cy:cy+rh, cx:cx+rw, 0] = 1.0
            
        X.append(base.astype(np.float32) / 255.0)
        Y.append(mask)
        
    return np.array(X), np.array(Y)


def train_and_export_unet():
    if not HAS_TF:
        print("[ERROR] TensorFlow is required for U-Net training.")
        return

    print("Building U-Net Model Architecture...")
    unet = build_unet_model(input_shape=(224, 224, 3))
    unet.compile(optimizer=Adam(learning_rate=1e-3), loss='binary_crossentropy', metrics=['accuracy'])
    
    print("Generating Synthetic Manipulation Data for Fine-tuning...")
    X_train, Y_train = generate_synthetic_training_data(num_samples=120)
    
    print("Training U-Net Model...")
    unet.fit(X_train, Y_train, epochs=3, batch_size=16, verbose=1)
    
    os.makedirs("model", exist_ok=True)
    h5_path = "model/unet_segmentation.h5"
    unet.save(h5_path)
    print(f"[OK] U-Net model saved to {h5_path}")
    
    try:
        print("Converting to TFLite model...")
        converter = tf.lite.TFLiteConverter.from_keras_model(unet)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_model = converter.convert()
        
        tflite_path = "model/unet_segmentation.tflite"
        with open(tflite_path, "wb") as f:
            f.write(tflite_model)
        print(f"[OK] Quantized TFLite U-Net saved to {tflite_path}")
    except Exception as e:
        print(f"[WARNING] TFLite conversion skipped: {e}")

if __name__ == "__main__":
    train_and_export_unet()
