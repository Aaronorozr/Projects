import heapq
import pandas as pd
from unidecode import unidecode
import warnings
import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext

pd.options.mode.chained_assignment = None
warnings.filterwarnings("ignore")

Data_Metro = "GrafoMetro.txt"

def read_Data(file_path):
    df = pd.read_csv(file_path, header=None, skiprows=1, names=["Partida", "Destino", "Distancia"], encoding="utf-8")
    df['Distancia'] = pd.to_numeric(df['Distancia'], errors='coerce')  # Convierte la columna 'Distancia' a flotante
    df.dropna(subset=['Distancia'], inplace=True)  # Elimina las filas donde 'Distancia' es NaN
    return df


class MetroGraph:
    def __init__(self):
        self.nodes = set()
        self.edges = {}

    def add_node(self, station):
        self.nodes.add(station)
        if station not in self.edges:
            self.edges[station] = []

    def add_edge(self, station1, station2, distance):
        self.edges[station1].append((station2, distance))
        self.edges[station2].append((station1, distance))

    def dijkstra(self, start_station, end_station):
        if start_station not in self.nodes or end_station not in self.nodes:
            return None

        distances = {station: float('inf') for station in self.nodes}
        distances[start_station] = 0
        previous_station = {}
        priority_queue = [(0, start_station)]

        while priority_queue:
            current_distance, current_station = heapq.heappop(priority_queue)

            if current_distance > distances[current_station]:
                continue

            for neighbor, weight in self.edges[current_station]:
                distance = current_distance + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_station[neighbor] = current_station
                    heapq.heappush(priority_queue, (distance, neighbor))

        path = []
        current = end_station
        while current in previous_station:
            path.insert(0, current)
            current = previous_station[current]

        if path:
            path.insert(0, start_station)
            return path, distances[end_station]
        else:
            return None


def find_path(metro, nodes, result_label, station_start_cb, station_end_cb):
    start_station = unidecode(station_start_cb.get().strip().lower())
    end_station = unidecode(station_end_cb.get().strip().lower())
    if start_station == end_station:
        result_label.config(text="Estación repetida.")
    elif start_station not in nodes or end_station not in nodes:
        result_label.config(text="Estación inválida.")
    else:
        path, distance = metro.dijkstra(start_station, end_station)
        if path:
            result_label.config(text="Camino más corto: " + " -> ".join(path) + "\nDistancia total: " + str(distance))
        else:
            result_label.config(text="Camino no encontrado.")

# Inicio de la GUI
def start_gui():
    root = tk.Tk()
    root.title("Buscador de Ruta de Metro")
    root.geometry("430x400")

    df = read_Data(Data_Metro)
    df = df.applymap(lambda x: unidecode(x.strip().lower()) if isinstance(x, str) else x)
    nodos_partida = df["Partida"].unique()
    nodos_salida = df["Destino"].unique()
    nodes = pd.concat([pd.Series(nodos_partida), pd.Series(nodos_salida)]).unique()
    metro = MetroGraph()

    for node in nodes:
        metro.add_node(node)

    for i in range(len(df)):
        metro.add_edge(df.iloc[i, 0], df.iloc[i, 1], df.iloc[i, 2])

    # Comboboxes para estaciones
    station_start_cb = ttk.Combobox(root, values=sorted(nodes))
    station_start_cb.grid(row=0, column=1, padx=10, pady=10)
    station_start_cb.set("Seleccionar estación de partida")

    station_end_cb = ttk.Combobox(root, values=sorted(nodes))
    station_end_cb.grid(row=1, column=1, padx=10, pady=10)
    station_end_cb.set("Seleccionar estación de destino")

    # Botón para buscar ruta
    find_path_button = tk.Button(root, text="Buscar Ruta", command=lambda: find_path(metro, nodes, result_label, station_start_cb, station_end_cb))
    find_path_button.grid(row=2, column=1, padx=10, pady=10)

    # Etiqueta para mostrar resultados
    result_label = tk.Label(root, text="", justify=tk.LEFT)
    result_label.grid(row=3, column=1, padx=10, pady=10)
    result_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, height=10, width=50)
    result_text.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    result_text.config(state=tk.DISABLED)

    def find_path():
        start_station = unidecode(station_start_cb.get().strip().lower())
        end_station = unidecode(station_end_cb.get().strip().lower())
        if start_station == end_station:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.INSERT, "Estación repetida.")
            result_text.config(state=tk.DISABLED)
        elif start_station not in nodes or end_station not in nodes:
            result_text.config(state=tk.NORMAL)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.INSERT, "Estación inválida.")
            result_text.config(state=tk.DISABLED)
        else:
            path, distance = metro.dijkstra(start_station, end_station)
            if path:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.INSERT, "Camino más corto: " + " -> ".join(path) + "\nDistancia total: " + str(distance))
                result_text.config(state=tk.DISABLED)
            else:
                result_text.config(state=tk.NORMAL)
                result_text.delete(1.0, tk.END)
                result_text.insert(tk.INSERT, "Camino no encontrado.")
                result_text.config(state=tk.DISABLED)

    # Modificar el botón para llamar a la nueva función find_path
    find_path_button.config(command=find_path)

    # Ejecutar la interfaz gráfica
    root.mainloop()

# Llamar a la función para iniciar la GUI
start_gui()