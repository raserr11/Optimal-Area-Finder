import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
import requests
import time
import folium
from pyproj import Proj, transform

def traduc_coord(df):
    # Definir el sistema de coordenadas UTM (zona 30N en este caso)
    proj_utm = Proj(proj='utm', zone=30, ellps='WGS84')  # Cambia la zona UTM si es necesario
    proj_wgs84 = Proj(proj='latlong', datum='WGS84')  # Sistema de coordenadas WGS84 (latitud y longitud)

    # Función para convertir de UTM a latitud y longitud
    def convertir_utm_a_latlon(utm_x, utm_y):
        lon, lat = transform(proj_utm, proj_wgs84, utm_x, utm_y)
        return lon, lat

    # Supongamos que tienes las columnas 'coord_x' y 'coord_y' en tu DataFrame
    df['longitud'], df['latitud'] = zip(*df.apply(lambda row: convertir_utm_a_latlon(row['longitud'], row['latitud']), axis=1))


# Función polinómica para calcular el crecimiento basado en las horas de sol
def polinom_luz(h, min_luz, max_luz):
    g_max = 100
    a = 1.25
    h_opt1 = min_luz
    h_opt2 = max_luz
    g_h = g_max - (a * (h - h_opt1) * (h - h_opt2))

    if g_h > 100:
        return 100
    elif g_h < 0:
        return 0
    else:
        return round(g_h, 2)

# Función polinómica para calcular el crecimiento basado en la temperatura
def polinom_temp(t, min_temp, max_temp):
    g_max = 100
    a = 1.05
    t_opt1 = min_temp
    t_opt2 = max_temp
    g_t = g_max - (a * (t - t_opt1) * (t - t_opt2))

    if g_t > 100:
        return 100
    elif g_t < 0:
        return 0
    else:
        return round(g_t, 2)

# Función polinómica para calcular el crecimiento basado en la humedad
def polinom_humed(hr, min_humed, max_humed):
    g_max = 100
    a = 0.15
    hr_opt1 = min_humed
    hr_opt2 = max_humed
    g_hr = g_max - (a * (hr - hr_opt1) * (hr - hr_opt2))

    if g_hr > 100:
        return 100
    elif g_hr < 0:
        return 0
    else:
        return round(g_hr, 2)

# Función para calcular el crecimiento diario basado en los parámetros ponderados
def crec_dia(luz, temp, humed, prop_dia):
    w_luz = 0.5  # Peso de la luz
    w_temp = 0.3  # Peso de la temperatura
    w_humed = 0.2  # Peso de la humedad

    base = (w_luz * luz) + (w_temp * temp) + (w_humed * humed)
    crecimiento_diario = (base * prop_dia) / 100

    return crecimiento_diario

# Función para calcular el crecimiento total de la planta en el periodo de cosecha
def total_crec(df, prop_dia, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX):
    lista_crec = np.array([])

    for _, row in df.iterrows():
        luz = polinom_luz(row['sol'], L_MIN, L_MAX)
        temp = polinom_temp(row['tmed'], T_MIN, T_MAX)
        humed = polinom_humed(row['hrMedia'], H_MIN, H_MAX)

        crec_diario = crec_dia(luz, temp, humed, prop_dia)
        lista_crec = np.append(lista_crec, crec_diario)

    total_crecimiento = lista_crec.sum()
    return total_crecimiento

# Función para obtener los datos de entrada del usuario y calcular PROP_DIA
def data_take():
    plant_name = input('Introduce el nombre de la planta:')
    crop_date1 = input('Fecha Siembra (YYYY-MM-DD):')
    crop_date2 = input('Fecha Cosecha (YYYY-MM-DD):')

    # Convertir fechas para calcular el número de días
    fecha1 = pd.to_datetime(crop_date1)
    fecha2 = pd.to_datetime(crop_date2)
    num_dias = (fecha2 - fecha1).days

    # Cálculo de la proporción diaria basado en los días de cosecha
    prop_dia = 100 / num_dias

    luz_min = float(input('Luz Mínima (horas):'))
    luz_max = float(input('Luz Máxima (horas):'))

    temp_min = float(input('Temperatura Mínima:'))
    temp_max = float(input('Temperatura Máxima:'))

    humed_min = float(input('Humedad Mínima:'))
    humed_max = float(input('Humedad Máxima:'))

    return plant_name, crop_date1, crop_date2, luz_min, luz_max, temp_min, temp_max, humed_min, humed_max, prop_dia

# Función para preparar los datos del JSON
import pandas as pd

def data_prep(data, DATE1, DATE2):
    # Crear el DataFrame con las columnas necesarias
    df = pd.DataFrame(data)[['fecha', 'sol', 'tmed', 'hrMedia']]
    columnas_mod = ['sol', 'tmed', 'hrMedia']

    # Reemplazar comas por puntos y eliminar espacios en blanco
    df[columnas_mod] = df[columnas_mod].replace(',', '.', regex=True).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # Convertir las columnas a float
    df[columnas_mod] = df[columnas_mod].astype(float)
    
    # Convertir la columna de 'fecha' a tipo datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Rellenar valores nulos hacia adelante y hacia atrás
    df[columnas_mod] = df[columnas_mod].ffill()
    df[columnas_mod] = df[columnas_mod].bfill()
    
    # Convertir las fechas de entrada en tipo datetime si no lo son
    DATE1 = pd.to_datetime(DATE1, format="%d-%m-%Y")
    DATE2 = pd.to_datetime(DATE2, format="%d-%m-%Y")

    if DATE1 < DATE2:
        # Filtrar el DataFrame según el intervalo de fechas
        df = df[(df['fecha'] >= DATE1) & (df['fecha'] <= DATE2)]
    else:
        df1 = df[df['fecha'] >= DATE1]
        df2 = df[df['fecha'] <= DATE1]

        df = pd.concat([df1, df2], axis=0, ignore_index=True) 


    return df


def color_gradient(value):
    # value debe estar entre 0 y 1
    red = int(255 * (1 - value))  # Inverso para que el valor mínimo sea rojo
    green = int(255 * value)      # El valor máximo será verde
    return f'rgb({red}, {green}, 0)'

def normalize_scores(pts_dict, score):

    min_score = min(pts_dict.values())
    max_score = max(pts_dict.values())

    normalized = (score - min_score) / (max_score - min_score)

    return normalized

# Función para calcular el crecimiento total por estación
def calc_pts(json_data, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, PROP_DIA, DATE1, DATE2):

    with open(json_data, 'r') as f:
        full_data = json.load(f)

    info_dict = {}

    for code, data in full_data.items():
        df = data_prep(data, DATE1, DATE2)
        pts = total_crec(df, PROP_DIA, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX)
        info_dict[code] = round(pts, 3)

    return info_dict

def calc_full(json_data, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, PROP_DIA, DATE1, DATE2):

    pts_dict = calc_pts(json_data, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, PROP_DIA, DATE1, DATE2)

    full_dict = {}

    for k, v in pts_dict.items():
        color_dict = {}        
        norm_score = normalize_scores(pts_dict, v)
        color = color_gradient(norm_score)
        color_dict['score'] = v 
        color_dict['color'] = color

        full_dict[k] = color_dict

    return full_dict

# functions.py

import os
import json
import pandas as pd
import folium

# Función para tomar datos de plantas predefinidas
def get_predefined_plant_data(plants_json_path, plant):
    with open(plants_json_path, 'r') as file:
        plants_data = json.load(file)
    plant_info = plants_data.get(plant)
    L_MIN, L_MAX = plant_info['sun']
    T_MIN, T_MAX = plant_info['temp']
    H_MIN, H_MAX = plant_info['humidity']
    DATE1, DATE2 = plant_info['sowing'], plant_info['harvest']
    return L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2

# Función para tomar datos de entrada manual
def get_manual_plant_data(request):
    L_MIN = float(request.POST.get('L_MIN'))
    L_MAX = float(request.POST.get('L_MAX'))
    T_MIN = float(request.POST.get('T_MIN'))
    T_MAX = float(request.POST.get('T_MAX'))
    H_MIN = float(request.POST.get('H_MIN'))
    H_MAX = float(request.POST.get('H_MAX'))
    DATE1 = request.POST.get('DATE1')
    DATE2 = request.POST.get('DATE2')
    return L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2

# Función principal para realizar el cálculo y generar el mapa
def calculate_and_generate_map(full_data_json_path, stations_json_path, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2):
    # Procesar las fechas y calcular PROP_DIA
    DATE11 = f"{DATE1}-2023"
    DATE22 = f"{DATE2}-2023"
    fecha1 = pd.to_datetime(DATE11, format="%d-%m-%Y")
    fecha2 = pd.to_datetime(DATE22, format="%d-%m-%Y")
    num_dias = (fecha2 - fecha1).days
    PROP_DIA = 100 / num_dias

    # Ejecutar el cálculo de las estaciones
    stations_results = calc_full(full_data_json_path, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, PROP_DIA, DATE11, DATE22)
    
    # Generar el mapa
    valid_stations_df = pd.read_json(stations_json_path)
    mapa_positron = folium.Map(
        location=[40.416775, -3.703790],
        zoom_start=6,
        tiles="CartoDB positron"
    )

    for index, row in valid_stations_df.iterrows():
        station_code = row['code']
        if station_code in stations_results:
            color = stations_results[station_code]['color']
            folium.CircleMarker(
                location=[row['latitud'], row['longitud']],
                radius=10,
                color=color,
                fill=True,
                fill_color=color,
                popup=row['nombre']
            ).add_to(mapa_positron)

    # Guardar el mapa
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'optim_area')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    mapa_path = os.path.join(static_dir, 'mapa.html')
    mapa_positron.save(mapa_path)

    return stations_results, '/static/optim_area/mapa.html'

