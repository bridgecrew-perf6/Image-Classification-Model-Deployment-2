# -*- coding: utf-8 -*-
"""Submission Akhir - Image Classification Model Deployment.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1FwSq_BjRnG0kdxwKtyhI2Nm9B7wkCR-H

# Azhar Rizki Zulma

Dataset: https://www.kaggle.com/iarunava/cell-images-for-detecting-malaria

## **Data Preparation**
### Import Library
"""

# Commented out IPython magic to ensure Python compatibility.
import os, zipfile, shutil, PIL
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# %matplotlib inline

from tensorflow import keras
from google.colab import files
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dropout, Flatten, Dense
from tensorflow.keras.utils import plot_model
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import RMSprop

"""### Menginstall Kaggle"""

!pip install -q kaggle

"""### Upload Kredensial (Token API)"""

uploaded = files.upload()

"""### Konfigurasi untuk menerima datasets dari Kaggle"""

!chmod 600 /content/kaggle.json

"""### Download Dataset"""

! KAGGLE_CONFIG_DIR=/content/ kaggle datasets download -d iarunava/cell-images-for-detecting-malaria

"""### Mengekstrak Dataset"""

local_zip = '/content/cell-images-for-detecting-malaria.zip'
zip_ref = zipfile.ZipFile(local_zip, 'r')
zip_ref.extractall('/content')
zip_ref.close()

"""### Mendeklarasikan Direktori Dasar"""

BASE_DIR = '/content/cell_images/'

"""### Membuat fungsi list_files untuk mengidentifikasi jumlah file"""

def list_files(startpath):
  num_files = 0
  for root, dirs, files in os.walk(startpath):
    level = root.replace(startpath, '').count(os.sep)
    indent = ' ' * 2 * (level)
    num_files += len(files)
    print('{}{}/ {}'.format(indent, os.path.basename(root), (str(len(files)) + ' images' if len(files) > 0 else '')))
  
  return num_files

"""### Memanggil fungsi list_files dengan parameter variabel direktori dasar yang telah dibuat sebelumnya"""

list_files(BASE_DIR)

"""### Membuat fungsi read_files untuk membaca setiap files"""

def read_files(startpath):
  image_files = []
  for dirname, dirnames, filenames in os.walk(startpath):
    for filename in filenames:
      image_files.append(os.path.join(dirname, filename))
  
  return image_files

"""### Menghapus file yang tidak digunakan"""

os.remove("/content/cell_images/Parasitized/Thumbs.db")
os.remove("/content/cell_images/Uninfected/Thumbs.db")
os.remove("/content/cell_images/cell_images/Parasitized/Thumbs.db")
os.remove("/content/cell_images/cell_images/Uninfected/Thumbs.db")

"""### Memastikan ukuran image yang beragam dengan fungsi PIL"""

full_dirs = read_files(BASE_DIR + "cell_images")
image_sizes = []
for file in full_dirs:
  image = PIL.Image.open(file)
  width, height = image.size
  image_sizes.append(f'{width}x{height}')

unique_sizes = set(image_sizes)

print(f'Size all images: {len(image_sizes)}')
print(f'Size unique images: {len(unique_sizes)}')
print(f'First 10 unique images: \n{list(unique_sizes)[:10]}')

"""Terdapat 27558 gambar dan 1627 diantaranya memiliki ukuran yang beragam

## **Data Preprocessing dan Data Splitting**

### Melakukan Augmentasi Gambar
"""

datagen = ImageDataGenerator(
  rescale=1./255,
  validation_split=0.2,
  zoom_range=0.2,
  shear_range=0.2,
  rotation_range=0.2
)

"""### Data Image Generator"""

training_generator = datagen.flow_from_directory(
  BASE_DIR + "cell_images",
  subset='training',
  target_size=(120,120),
  seed=42,
  batch_size=64,
  interpolation='nearest',
  class_mode='binary',
  classes=['Parasitized','Uninfected']
)

validation_generator = datagen.flow_from_directory(
  BASE_DIR + "cell_images",
  subset='validation',
  target_size=(120,120),
  seed=42,
  batch_size=64,
  interpolation='nearest',
  class_mode='binary',
  classes=['Parasitized','Uninfected']
)

"""## **Modelling & Training**"""

model = Sequential([
    Conv2D(64, (3,3), activation='relu', input_shape=(120, 120, 3)),
    MaxPooling2D(2, 2),
    Conv2D(64, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Dropout(0.6),
    Conv2D(128, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Conv2D(256, (3,3), activation='relu'),
    MaxPooling2D(2,2),
    Dropout(0.4),
    Flatten(),
    Dense(512, activation='relu'),
    Dropout(0.2),
    Dense(1, activation='sigmoid')
])

model.summary()

plot_model(
    model,
    show_shapes=True,
    show_layer_names=True,
)

class myCallback(tf.keras.callbacks.Callback):
  def on_epoch_end(self, epoch, logs={}):
    if((logs.get('accuracy') > 0.92) and (logs.get('val_accuracy') > 0.92)):
      self.model.stop_training = True
      print("\nThe accuracy of the training set and the validation set has reached > 92%!")
callbacks = myCallback()

LR = 1e-4
model.compile(loss='binary_crossentropy',
              optimizer=RMSprop(learning_rate=LR),
              metrics=['accuracy'])

result = model.fit(
    training_generator,
    validation_data=validation_generator,
    epochs=25,
    steps_per_epoch=150,
    validation_steps=35,
    callbacks=[callbacks],
    verbose=1
)

"""## **Plot Accuracy & Loss**"""

loss = result.history['loss']
val_loss = result.history['val_loss']
acc = result.history['accuracy']
val_acc = result.history['val_accuracy']

plt.figure(figsize=(15, 5))

plt.subplot(1, 2, 1)
plt.title('Loss')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.plot(loss, label='Training set')
plt.plot(val_loss, label='Validation set', linestyle='--')
plt.legend()
plt.grid(linestyle='--', linewidth=1, alpha=0.5)

plt.subplot(1, 2, 2)
plt.title('Accuracy')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.plot(acc, label='Training set')
plt.plot(val_acc, label='Validation set', linestyle='--')
plt.legend()
plt.grid(linestyle='--', linewidth=1, alpha=0.5)

plt.show()

"""## **Convert to TFLite**"""

converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

with tf.io.gfile.GFile('model__v1.tflite', 'wb') as f:
  f.write(tflite_model)