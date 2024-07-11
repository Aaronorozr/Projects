import os
from PIL import Image

def normalize_images(input_folder, output_folder, target_size=(128, 128), rotation_range=30):
    # Lista de animales seleccionados
    selected_animals = ['caballo', 'elefante', 'gato']
    
    # Crear la carpeta de salida si no existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Contador de imágenes procesadas en total
    total_processed_images = 0
    
    # Procesar todas las imágenes de cada clase desde 'input_folder'
    for animal_folder in os.listdir(input_folder):
        if animal_folder in selected_animals:
            # Ruta completa de la carpeta de entrada para el animal actual
            animal_input_folder = os.path.join(input_folder, animal_folder)
            
            # Ruta completa de la carpeta de salida para el animal actual
            animal_output_folder = os.path.join(output_folder, animal_folder)
            
            # Crear la carpeta de salida para el animal actual si no existe
            if not os.path.exists(animal_output_folder):
                os.makedirs(animal_output_folder)
            
            # Procesar todas las imágenes del animal actual
            for filename in os.listdir(animal_input_folder):
                input_path = os.path.join(animal_input_folder, filename)
                output_path = os.path.join(animal_output_folder, filename)  # Conservar el nombre original
                
                try:
                    # Abrir la imagen
                    img = Image.open(input_path)
                    
                    # Obtener dimensiones originales
                    width, height = img.size
                    
                    # Calcular el tamaño del recorte para hacerla cuadrada
                    if width > height:
                        left = (width - height) / 2
                        top = 0
                        right = (width + height) / 2
                        bottom = height
                    else:
                        left = 0
                        top = (height - width) / 2
                        right = width
                        bottom = (height + width) / 2
                    
                    # Recortar la imagen para hacerla cuadrada
                    img = img.crop((left, top, right, bottom))
                    
                    # Redimensionar la imagen al tamaño deseado
                    img = img.resize(target_size)
                    
                    # Convertir la imagen al modo de escala de grises
                    img = img.convert('L')
                    
                    # Guardar la imagen en la carpeta de salida en formato JPEG
                    img.save(output_path, "JPEG")
                    
                    # Incrementar el contador de imágenes procesadas
                    total_processed_images += 1
                except Exception as e:
                    print(f"Error al procesar la imagen {input_path}: {e}")
    
    print(f"Total de imágenes procesadas: {total_processed_images}")

# Ejemplo de uso
input_folder = 'animales'
output_folder = 'normalizadas'

# Procesar todas las imágenes de cada clase desde 'animales'
normalize_images(input_folder, output_folder)
