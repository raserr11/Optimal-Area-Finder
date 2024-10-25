# Vista para la página de entrada de datos
import json
import os
from django.shortcuts import render
from .functions import get_predefined_plant_data, get_manual_plant_data, calculate_and_generate_map
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


# views.py



def result_view(request, plant=None):
    plants_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'plants_data.json')
    full_data_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'full_data2.json')
    stations_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'valid_stations_ds2.json')

    # Determinar si usar datos predefinidos o manuales
    if plant:
        L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2 = get_predefined_plant_data(plants_json_path, plant)
    else:
        L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2 = get_manual_plant_data(request)

    # Llamar a la función para calcular y generar el mapa
    stations_results, mapa_url = calculate_and_generate_map(
        full_data_json_path, stations_json_path, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2
    )

    # Pasar los resultados al template
    context = {
        'selected_plant': plant,
        'sun_range': (L_MIN, L_MAX),
        'temp_range': (T_MIN, T_MAX),
        'humidity_range': (H_MIN, H_MAX),
        'sowing_date': DATE1,
        'harvest_date': DATE2,
        'stations_results': stations_results,
        'mapa_url': mapa_url
    }
    return render(request, 'optim_area/result.html', context)







