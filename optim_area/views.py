import json
import os
from django.shortcuts import render, redirect
from .functions import get_predefined_plant_data, calculate_and_generate_map
import folium
import pandas as pd

def home(request):
    return render(request, 'optim_area/home.html')

def input_data(request):
    # Cargar los datos del archivo JSON de plantas
    plants_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'plants_data.json')
    with open(plants_json_path, 'r') as file:
        plants_data = json.load(file)
    
    if request.method == 'POST':
        if 'plant' in request.POST:  # Predefinido
            selected_plant = request.POST['plant']
            return redirect('result_view', plant=selected_plant)
        
        elif 'sun_min' in request.POST:  # Manual
            plant_name = request.POST['plant_name']
            manual_plant_data = {
                "sun": [int(request.POST['sun_min']), int(request.POST['sun_max'])],
                "temp": [int(request.POST['temp_min']), int(request.POST['temp_max'])],
                "humidity": [int(request.POST['humidity_min']), int(request.POST['humidity_max'])],
                "sowing": request.POST['sowing_date'],
                "harvest": request.POST['harvest_date']
            }
            # Guardar manual_plant_data en la sesión
            request.session['manual_plant_data'] = manual_plant_data
            return redirect('result_view', plant=plant_name)

    context = {
        'plants': plants_data
    }
    return render(request, 'optim_area/input_data.html', context)

def result_view(request, plant=None):
    plants_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'plants_data.json')
    full_data_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'full_data2.json')
    stations_json_path = os.path.join(os.path.dirname(__file__), 'predefined', 'valid_stations_ds2.json')

    predef_plants = ['tomato', 'lettuce', 'cucumber', 'pepper', 'zucchini', 'carrot', 'broccoli', 'spinach', 'pumpkin', 'radish', 'eggplant', 'beetroot', 'onion', 'garlic', 'sweet_potato', 'corn']
    
    if plant and plant in predef_plants:
        L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2 = get_predefined_plant_data(plants_json_path, plant)
    else:
        # Usar datos de la planta manual de la sesión
        manual_data = request.session.get('manual_plant_data')
        if not manual_data:
            return redirect('input_data')
        
        L_MIN, L_MAX = manual_data['sun']
        T_MIN, T_MAX = manual_data['temp']
        H_MIN, H_MAX = manual_data['humidity']
        DATE1 = manual_data['sowing']
        DATE2 = manual_data['harvest']

    stations_results, mapa_url = calculate_and_generate_map(
        full_data_json_path, stations_json_path, L_MIN, L_MAX, T_MIN, T_MAX, H_MIN, H_MAX, DATE1, DATE2
    )

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








