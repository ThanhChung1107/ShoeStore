from django.contrib import admin
from .models import Product
# Register your models here.
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'get_sizes')
    list_filter = ('category', 'brand', 'sizes')
    search_fields = ('name', 'description')
    list_editable = ('price', 'stock')
    readonly_fields = ('created_at', 'updated_at')
    filter_horizontal = ('sizes',)  # Cho phép chọn nhiều size với giao diện đẹp

    def get_sizes(self, obj):
        return ", ".join([size.size for size in obj.sizes.all()])
    get_sizes.short_description = 'Sizes'