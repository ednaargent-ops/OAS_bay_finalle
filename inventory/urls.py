from django.urls import path

from . import views

urlpatterns = [
    path('inventory/parts/', views.spare_part_list, name='spare_part_list'),
    path('inventory/parts/restock/', views.spare_part_restock, name='spare_part_restock'),
    path('inventory/parts/<int:pk>/edit/', views.spare_part_edit, name='spare_part_edit'),
    path('inventory/parts/<int:pk>/delete/', views.spare_part_delete, name='spare_part_delete'),
    path('inventory/services/', views.service_list, name='service_list'),
    path('inventory/services/new/', views.service_create, name='service_create'),
    path('inventory/services/<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('inventory/services/<int:pk>/delete/', views.service_delete, name='service_delete'),
]
