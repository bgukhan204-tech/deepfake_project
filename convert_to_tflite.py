import tensorflow as tf
import os
import numpy as np

def convert():
    h5_model_path = "deepfake_model.h5"
    if not os.path.exists(h5_model_path):
        # Check subfolder
        h5_model_path = "model/deepfake_model.h5"
        
    tflite_model_path = "model/deepfake_model.tflite"

    if os.path.exists(h5_model_path):
        print(f"Loading {h5_model_path}... (This may take a moment)")
        model = tf.keras.models.load_model(h5_model_path, compile=False)
        
        print("Converting to TFLite (Optimized)...")
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        
        # QUANTIZATION: This is the secret to 1/4th file size and huge RAM savings!
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        
        print("Processing conversion (Wait about 60 seconds)...")
        tflite_model = converter.convert()
        
        os.makedirs("model", exist_ok=True)
        with open(tflite_model_path, "wb") as f:
            f.write(tflite_model)
        
        print("\n" + "="*40)
        print("SUCCESS! TFLite model created.")
        print(f"Location: {tflite_model_path}")
        print(f"H5 Size: {os.path.getsize(h5_model_path) / 1024 / 1024:.2f} MB")
        print(f"TFLite Size: {os.path.getsize(tflite_model_path) / 1024 / 1024:.2f} MB")
        print("="*40)
        print("\nNEXT STEP: You can now push this small file to GitHub!")
    else:
        print(f"ERROR: {h5_model_path} not found. Please place it in the project folder.")

if __name__ == "__main__":
    convert()
