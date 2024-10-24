# Vista para la página de entrada de datos
import json
import os
from django.shortcuts import render
from .functions import calc_full  # Importamos tu función calc_full
import folium
import pandas as pd

# Create your views here.

def home(request):
    return render(request, 'optim_area/home.html')


from django.shortcuts import render, redirect
import json
import os

def input_data(request):
    # Cargar los datos del archivo JSON de plantas
    plants_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'plants_data.json')
    with open(plants_json_path, 'r') as file:
        plants_data = json.load(file)
    
    if request.method == 'POST':
        # Ver si los datos son predefinidos o manuales
        if 'plant' in request.POST:  # Predefinido
            selected_plant = request.POST['plant']
            return redirect('result_view', plant=selected_plant)
        
        elif 'sun_min' in request.POST:  # Manual
            sun_min = request.POST['sun_min']
            sun_max = request.POST['sun_max']
            temp_min = request.POST['temp_min']
            temp_max = request.POST['temp_max']
            humidity_min = request.POST['humidity_min']
            humidity_max = request.POST['humidity_max']
            sowing_date = request.POST['sowing_date']
            harvest_date = request.POST['harvest_date']

            # Redirigir a la vista de resultados con los datos manuales
            return redirect('result_view_manual', sun_min=sun_min, sun_max=sun_max, temp_min=temp_min,
                            temp_max=temp_max, humidity_min=humidity_min, humidity_max=humidity_max,
                            sowing_date=sowing_date, harvest_date=harvest_date)

    # Si no se ha enviado el formulario, mostrarlo
    context = {
        'plants': plants_data
    }
    return render(request, 'optim_area/input_data.html', context)


def result_view(request, plant):
    # Ruta a los archivos JSON necesarios
    plants_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'plants_data.json')
    full_data_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'full_data2.json')
    stations_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'valid_stations_ds2.json')

    # Cargar los datos de plantas
    with open(plants_json_path, 'r') as file:
        plants_data = json.load(file)

    # Obtener los datos de la planta seleccionada
    plant_info = plants_data.get(plant)

    # Extraer los parámetros de la planta predefinida
    L_MIN, L_MAX = (plant_info['sun'])
    T_MIN, T_MAX = plant_info['temp']
    H_MIN, H_MAX = plant_info['humidity']
    DATE1, DATE2 = plant_info['sowing'], plant_info['harvest']

    # Añadir el año 2023 a las fechas
    DATE1 = f"{DATE1}/2023"
    DATE2 = f"{DATE2}/2023"

    # Validar las fechas y convertirlas a formato de fecha
    fecha1 = pd.to_datetime(DATE1, format="%d/%m/%Y")
    fecha2 = pd.to_datetime(DATE2, format="%d/%m/%Y")
    num_dias = (fecha2 - fecha1).days
    PROP_DIA = 100 / num_dias

    # Ejecutar la función calc_full() para obtener el diccionario con las estaciones y colores
    stations_results = calc_full(full_data_json_path, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, PROP_DIA, DATE1, DATE2)

    # Cargar los datos de ubicación de las estaciones
    valid_stations_df = pd.read_json(stations_json_path)

    # Crear el mapa con Folium (puedes usar las coordenadas y el zoom según prefieras)
    mapa_positron = folium.Map(
        location=[40.416775, -3.703790],  # Centrado en España
        zoom_start=6,
        tiles="CartoDB positron"
    )

    # Iterar sobre las estaciones y agregar marcadores al mapa
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

    # Guardar el mapa en el directorio estático
    static_dir = os.path.join(os.path.dirname(__file__), 'static', 'optim_area')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    
    mapa_path = os.path.join(static_dir, 'mapa.html')
    mapa_positron.save(mapa_path)

    # Pasar los resultados al template para mostrar el mapa y los datos de la planta
    context = {
        'selected_plant': plant,
        'sun_range': (L_MIN, L_MAX),
        'temp_range': (T_MIN, T_MAX),
        'humidity_range': (H_MIN, H_MAX),
        'sowing_date': DATE1,
        'harvest_date': DATE2,
        'stations_results': stations_results,
        'mapa_url': '/static/optim_area/mapa.html'  # Ruta pública del mapa
    }

    return render(request, 'optim_area/result.html', context)






