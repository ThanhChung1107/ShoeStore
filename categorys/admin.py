from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import  Category

# Register your models here.
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'product_count')
    list_filter = ('status',)
    search_fields = ('name',)
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Số sản phẩm'