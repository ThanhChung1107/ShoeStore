# discounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('apply-discount/', views.apply_discount_ajax, name='apply_discount'),
    path('remove-discount/', views.remove_discount_ajax, name='remove_discount'),
]