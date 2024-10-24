from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('input-data/', views.input_data, name='input_data'),
    path('result/<str:plant>/', views.result_view, name='result_view'),  # Nueva vista para resultados
]
