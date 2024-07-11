import tkinter as tk
import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline

# Preprocesamiento de texto
def preprocess_text(text):
    text = text.lower()  # Convertir a minúsculas
    text = re.sub(r'[^\w\s]', '', text)  # Eliminar caracteres especiales
    return text

# Función para cargar datos desde archivo TXT
def cargar_datos_txt(archivo, emocion):
    with open(archivo, "r", encoding="utf-8") as f:
        textos = f.readlines()
    return pd.DataFrame({"texto": textos, "emocion": emocion})

# Rutas de los archivos (ajusta según tu ubicación)
ruta_tristeza = "tristeza.txt"  # Reemplaza con la ruta correcta
ruta_alegria = "alegria.txt"  # Reemplaza con la ruta correcta
ruta_miedo = "miedo.txt"  # Reemplaza con la ruta correcta
ruta_ira = "enojo.txt"  # Reemplaza con la ruta correcta

# Cargar datos de tristeza
df_tristeza = cargar_datos_txt(ruta_tristeza, "tristeza")

# Cargar datos de alegría
df_alegria = cargar_datos_txt(ruta_alegria, "alegria")

# Cargar datos de miedo
df_miedo = cargar_datos_txt(ruta_miedo, "miedo")

# Cargar datos de ira
df_ira = cargar_datos_txt(ruta_ira, "enojo")

# Combinar los DataFrames
df = pd.concat([df_tristeza, df_alegria, df_miedo, df_ira])

# Vectorización TF-IDF
tfidf_vectorizer = TfidfVectorizer()
X = tfidf_vectorizer.fit_transform(df["texto"])

# Clasificador SVM
svm_classifier = SVC(kernel="linear")

# Pipeline
model = Pipeline([
    ("tfidf", tfidf_vectorizer),
    ("clf", svm_classifier)
])

# Entrenar el modelo
model.fit(df["texto"], df["emocion"])

# Función para analizar el texto ingresado
def analizar_texto():
    nuevo_texto = entrada_texto.get("1.0", tk.END).strip()
    if nuevo_texto:
        emocion_predicha = model.predict([preprocess_text(nuevo_texto)])
        resultado.set(f"Emoción predicha: {emocion_predicha[0]}")

# Crear la interfaz gráfica
ventana = tk.Tk()
ventana.title("Detección de Emociones")
ventana.geometry("400x400")

# Widgets de la interfaz
etiqueta_texto = tk.Label(ventana, text="Ingresa un texto:")
etiqueta_texto.pack(pady=10)

entrada_texto = tk.Text(ventana, height=10, width=40)
entrada_texto.pack(pady=10)

boton_analizar = tk.Button(ventana, text="Analizar", command=analizar_texto)
boton_analizar.pack(pady=10)

resultado = tk.StringVar()
etiqueta_resultado = tk.Label(ventana, textvariable=resultado, font=("Helvetica", 14))
etiqueta_resultado.pack(pady=10)

# Iniciar el loop de la interfaz
ventana.mainloop()
