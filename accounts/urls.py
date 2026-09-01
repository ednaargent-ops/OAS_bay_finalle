from django.urls import path

from . import views

urlpatterns = [
    path('team/', views.technician_list, name='technician_list'),
    path('team/new/', views.technician_create, name='technician_create'),
    path('team/<int:pk>/update/', views.technician_update, name='technician_update'),
]
