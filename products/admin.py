from django.contrib import admin
from .models import Product,Size, ProductSize
# Register your models here.
class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1  # Số dòng thêm mới mặc định
    min_num = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price')
    list_filter = ('category', 'brand')
    search_fields = ('name', 'description')
    inlines = [ProductSizeInline]