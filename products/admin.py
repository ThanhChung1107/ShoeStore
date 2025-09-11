from django.contrib import admin
from .models import Product,Size, ProductSize
from django.utils import timezone
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

from django.contrib import admin
from .models import ProductReview, ReviewImage

class ReviewImageInline(admin.TabularInline):
    model = ReviewImage
    extra = 1
    readonly_fields = ['uploaded_at']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'created_at', 'has_shop_reply']
    list_filter = ['rating', 'created_at', 'product']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ReviewImageInline]
    
    fieldsets = (
        ('Thông tin đánh giá', {
            'fields': ('product', 'user', 'rating', 'comment', 'created_at', 'updated_at')
        }),
        ('Phản hồi từ shop', {
            'fields': ('shop_reply', 'replied_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_shop_reply(self, obj):
        return bool(obj.shop_reply)
    has_shop_reply.boolean = True
    has_shop_reply.short_description = 'Đã phản hồi'
    
    def save_model(self, request, obj, form, change):
        # Tự động cập nhật thời gian phản hồi khi shop reply
        if 'shop_reply' in form.changed_data and obj.shop_reply:
            obj.replied_at = timezone.now()
        super().save_model(request, obj, form, change)

@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'uploaded_at']
    list_filter = ['uploaded_at']
    readonly_fields = ['uploaded_at']