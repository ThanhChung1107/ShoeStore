from django.urls import path
from . import views

urlpatterns = [
    path('',views.product,name='product'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('product/<int:product_id>/', views.product_details, name='product_detail'),    

]
