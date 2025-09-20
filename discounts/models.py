from django.db import models
from django.utils import timezone
from products.models import Product, Category
from django.core.validators import MinValueValidator, MaxValueValidator

class Discount(models.Model):
    #kiểu giảm giá
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'phần trăm'),
        ('fixed','cố định')
    ]
    #code giảm giá
    code = models.CharField(max_length=50, unique=True, verbose_name="Mã giảm giá")
    description = models.TextField(blank=True,verbose_name="Mô tả")
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPE_CHOICES,
        default='percentage',
        verbose_name="Loại giảm giá"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="giá trị giảm",
        help_text="Phần trăm hoặc số tiền cố định tùy loại"
    )

    min_order_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Giá trị đơn hàng tối thiểu"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Số tiền giảm tối đa (nếu áp dụng)",
        help_text="Chỉ áp dụng cho giảm giá theo phần trăm"
    )
    start_date = models.DateTimeField(verbose_name="Ngày bắt đầu")
    end_date = models.DateTimeField(verbose_name="Ngày kết thúc")
    max_usage = models.PositiveIntegerField(
        default=1,
        verbose_name="Số lần sử dụng tối đa"
    )
    current_usage = models.PositiveIntegerField(
        default=0,
        verbose_name="Số lần đã sử dụng"
    )
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(
        Product, 
        blank=True,
        verbose_name="Áp dụng cho sản phẩm"
    )
    categories = models.ManyToManyField(
        Category, 
        blank=True,
        verbose_name="Áp dụng cho danh mục"
    )
    class Meta:
        verbose_name = "Mã giảm giá"
        verbose_name_plural = "Mã giảm giá"
    
    def __str__(self):
        return f"{self.code} - {self.get_discount_type_display()}: {self.value}"
    
    def is_valid(self):
        now = timezone.now()
        return (
            self.is_active and
            self.start_date <= now <= self.end_date and
            self.current_usage < self.max_usage
        )
    
    def calculate_discount_amount(self, order_total, products_in_cart):
        """
        Tính toán số tiền được giảm dựa trên tổng đơn hàng và sản phẩm trong giỏ
        """
        if not self.is_valid():
            return 0
        
        # Kiểm tra giá trị đơn hàng tối thiểu
        if order_total < self.min_order_value:
            return 0
        
        # Kiểm tra nếu mã chỉ áp dụng cho sản phẩm/danh mục cụ thể
        if self.products.exists() or self.categories.exists():
            applicable = False
            for product in products_in_cart:
                if (self.products.filter(id=product.id).exists() or 
                    self.categories.filter(id=product.category.id).exists()):
                    applicable = True
                    break
            
            if not applicable:
                return 0
        
        # Tính toán số tiền giảm
        if self.discount_type == 'percentage':
            discount_amount = order_total * (self.value / 100)
            if self.max_discount_amount:
                discount_amount = min(discount_amount, self.max_discount_amount)
        else:  # fixed amount
            discount_amount = min(self.value, order_total)
        
        return discount_amount
    
class AutomaticDiscount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Phần trăm'),
        ('fixed', 'Số tiền cố định'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Tên chương trình")
    description = models.TextField(blank=True, verbose_name="Mô tả")
    discount_type = models.CharField(
        max_length=10, 
        choices=DISCOUNT_TYPE_CHOICES, 
        default='percentage',
        verbose_name="Loại giảm giá"
    )
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Giá trị giảm"
    )
    min_order_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        verbose_name="Áp dụng cho đơn hàng từ"
    )
    max_discount_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name="Số tiền giảm tối đa"
    )
    start_date = models.DateTimeField(verbose_name="Ngày bắt đầu")
    end_date = models.DateTimeField(verbose_name="Ngày kết thúc")
    is_active = models.BooleanField(default=True, verbose_name="Kích hoạt")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Giảm giá tự động"
        verbose_name_plural = "Giảm giá tự động"
    
    def __str__(self):
        return f"{self.name} - Áp dụng cho đơn từ {self.min_order_value}"
    
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date
    
    def calculate_discount_amount(self, order_total):
        """
        Tính toán số tiền được giảm dựa trên tổng đơn hàng
        """
        if not self.is_valid() or order_total < self.min_order_value:
            return 0
        
        if self.discount_type == 'percentage':
            discount_amount = order_total * (self.value / 100)
            if self.max_discount_amount:
                discount_amount = min(discount_amount, self.max_discount_amount)
        else:  # fixed amount
            discount_amount = min(self.value, order_total)
        
        return discount_amount