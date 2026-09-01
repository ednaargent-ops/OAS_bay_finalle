from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job-cards/', views.job_card_list, name='job_card_list'),
    path('payments/', views.payment_list, name='payment_list'),
    path('customers/<int:customer_pk>/job-cards/new/', views.job_card_create, name='job_card_create'),
    path('job-cards/<int:pk>/', views.job_card_detail, name='job_card_detail'),
    path('job-cards/<int:pk>/add-service/', views.job_card_add_service, name='job_card_add_service'),
    path('job-cards/service-lines/<int:pk>/remove/', views.job_card_remove_service, name='job_card_remove_service'),
    path('job-cards/<int:pk>/add-part/', views.job_card_add_part, name='job_card_add_part'),
    path('job-cards/part-lines/<int:pk>/remove/', views.job_card_remove_part, name='job_card_remove_part'),
    path('job-cards/<int:pk>/add-payment/', views.job_card_add_payment, name='job_card_add_payment'),
    path('job-cards/<int:pk>/status/', views.job_card_update_status, name='job_card_update_status'),
    path('payments/<int:pk>/receipt/', views.receipt, name='receipt'),
]
