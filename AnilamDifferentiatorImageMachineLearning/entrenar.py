import tensorflow as tf
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import categorical_crossentropy
from tensorflow.keras.models import Sequential
from tensorflow.keras.callbacks import TensorBoard
from datetime import datetime
import os
import numpy as np

# Cargar los datos de entrenamiento desde el directorio
train_dir = 'normalizadas'

# Obtener las rutas de todas las imágenes en el directorio
image_paths = []
labels = []
class_mapping = {}  # Mapeo de nombres de clase a enteros
class_counter = 0

for class_name in os.listdir(train_dir):
    class_dir = os.path.join(train_dir, class_name)
    if os.path.isdir(class_dir):
        class_mapping[class_name] = class_counter
        for image_name in os.listdir(class_dir):
            image_path = os.path.join(class_dir, image_name)
            image_paths.append(image_path)
            labels.append(class_name)
        class_counter += 1

# Obtener el número de clases
num_classes = len(class_mapping)

# Preparar los datos como tensores
images = []
for image_path in image_paths:
    image = tf.keras.preprocessing.image.load_img(image_path, color_mode='grayscale', target_size=(128, 128))
    image = tf.keras.preprocessing.image.img_to_array(image)
    image = image / 255.0  # Normalizar los valores de píxeles
    images.append(image)
images = np.array(images)

# Convertir las etiquetas de texto a enteros usando el mapeo de clases
labels = [class_mapping[label] for label in labels]

# Convertir las etiquetas a one-hot encoding
labels = tf.keras.utils.to_categorical(labels, num_classes=num_classes)

# Dividir los datos en conjuntos de entrenamiento y validación
from sklearn.model_selection import train_test_split

train_images, val_images, train_labels, val_labels = train_test_split(images, labels, test_size=0.2, random_state=42)

# Definir el modelo CNN
modeloCNN = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 1)),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Conv2D(128, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(256, activation='relu'),
    Dense(num_classes, activation='softmax')  # Capa de salida con neuronas según el número de clases
])

# Compilar el modelo
optimizer = Adam(learning_rate=0.001)
modeloCNN.compile(optimizer=optimizer, loss=categorical_crossentropy, metrics=['accuracy'])

# Definir el callback de TensorBoard
log_dir = "logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = TensorBoard(log_dir=log_dir, histogram_freq=1)

# Entrenar el modelo con el tamaño del lote y el número de épocas personalizados
history = modeloCNN.fit(
    train_images,  # Datos de entrada
    train_labels,  # Etiquetas
    epochs=15,  # Número de épocas
    batch_size=64,  # Tamaño del lote
    validation_data=(val_images, val_labels),  # Datos de validación
    callbacks=[tensorboard_callback]  # Callbacks, si los hay
)

# Guardar el modelo
modeloCNN.save('modelo_cnn.h5')
