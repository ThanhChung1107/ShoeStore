from django.contrib import admin
from .models import Discount, AutomaticDiscount

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'value', 'min_order_value', 'start_date', 'end_date', 'is_active']
    list_filter = ['discount_type', 'is_active']
    filter_horizontal = ['products', 'categories']

@admin.register(AutomaticDiscount)
class AutomaticDiscountAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_type', 'value', 'min_order_value', 'start_date', 'end_date', 'is_active']
    list_filter = ['discount_type', 'is_active']
