from django.urls import path
from . import views

urlpatterns = [
    path('',views.product,name='product'),
    path('filter-products/', views.filter_products, name='filter_products'),
    path('product/<int:product_id>/', views.product_details, name='product_detail'),    
    path('product_search/',views.product_search,name='product_search'),
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('product/<int:product_id>/reviews/', views.product_reviews, name='product_reviews'),
    path('product/<int:product_id>/add-review/', views.add_review, name='add_review'),
    path('get-search-history/', views.get_search_history, name='get_search_history'),
    path('delete-search-history/', views.delete_search_history, name='delete_search_history'),
    path('clear-search-history/', views.clear_search_history, name='clear_search_history'),
    path('track-view/<int:product_id>/', views.track_product_view, name='track_product_view'),
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
]
