import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, Input
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam

print(f"TensorFlow Version: {tf.__version__}")

IMG_SIZE = (224, 224)
BATCH_SIZE = 64
DATASET_DIR = "dataset"

if not os.path.exists("model"):
    os.makedirs("model")

print("Setting up Data Generators with Data Augmentation...")

train_datagen = ImageDataGenerator(
    rescale=1.0/255.0,
    rotation_range=10,
    width_shift_range=0.08,
    height_shift_range=0.08,
    horizontal_flip=True,
    validation_split=0.2
)

train_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='training',
    shuffle=True
)

val_generator = train_datagen.flow_from_directory(
    DATASET_DIR,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='binary',
    subset='validation',
    shuffle=False
)

print(f"Class Indices: {train_generator.class_indices}")

print("Building High-Accuracy MobileNetV2 Transfer Learning Architecture...")

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet'
)

# Freeze base model layers initially
base_model.trainable = False

inputs = Input(shape=(224, 224, 3))
x = base_model(inputs, training=False)
x = GlobalAveragePooling2D()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
outputs = Dense(1, activation='sigmoid')(x)

model = Model(inputs, outputs)

model.compile(
    optimizer=Adam(learning_rate=1e-3),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

print("Phase 1: Training Top Classification Head...")
history1 = model.fit(
    train_generator,
    steps_per_epoch=100, # Faster steps per epoch
    validation_data=val_generator,
    validation_steps=30,
    epochs=3
)

print("Phase 2: Fine-Tuning Top Layers of MobileNetV2...")
base_model.trainable = True

# Freeze bottom 100 layers, fine-tune top layers
for layer in base_model.layers[:100]:
    layer.trainable = False

model.compile(
    optimizer=Adam(learning_rate=1e-5),
    loss='binary_crossentropy',
    metrics=['accuracy']
)

history2 = model.fit(
    train_generator,
    steps_per_epoch=100,
    validation_data=val_generator,
    validation_steps=30,
    epochs=3
)

# Save H5 Model
h5_path = "model/deepfake_model.h5"
model.save(h5_path)
print(f"High-Accuracy Model saved to {h5_path}")

# Convert to TFLite
print("Converting to Optimized TFLite Model...")
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

tflite_path = "model/deepfake_model.tflite"
with open(tflite_path, "wb") as f:
    f.write(tflite_model)

size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
print(f"SUCCESS! Optimized TFLite model saved at {tflite_path} ({size_mb:.2f} MB)")
