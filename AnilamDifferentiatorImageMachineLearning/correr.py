import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf

# Cargar el modelo previamente entrenado
modeloCNN = tf.keras.models.load_model('modelo_cnn.h5')

def cargar_imagen():
    filename = filedialog.askopenfilename()
    img = Image.open(filename).resize((128, 128))
    img_color = img.convert('RGB')  # Convertir a imagen en color
    img_grayscale = img.convert('L')  # Convertir a escala de grises
    img = np.array(img_grayscale) / 255.0  # Normalizar los valores de píxeles
    return img, img_color, filename

def predecir_imagen():
    img, img_color, filename = cargar_imagen()
    img_tk = ImageTk.PhotoImage(img_color)
    imagen_label.config(image=img_tk)
    imagen_label.image = img_tk  # Mantener una referencia para evitar que se elimine la imagen de la memoria

    img = img.reshape(1, 128, 128, 1)  # Añadir dimensión de lote y canal
    prediction = modeloCNN.predict(img)
    clases = ['Caballo', 'Elefante', 'Gato']  # El orden debe coincidir con el orden de clases en tu modelo
    resultado_label.config(text=f'Predicción: {clases[np.argmax(prediction)]} \nImagen: {filename}')

# Configuración de la ventana
root = tk.Tk()
root.title("Clasificador de Imágenes")

# Botón para cargar imagen
cargar_button = tk.Button(root, text="Cargar Imagen", command=predecir_imagen)
cargar_button.pack(pady=10)

# Etiqueta para mostrar la imagen
imagen_label = tk.Label(root)
imagen_label.pack()

# Etiqueta para mostrar el resultado
resultado_label = tk.Label(root, text="")
resultado_label.pack()

root.mainloop()
