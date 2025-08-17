from django.db import models
from categorys.models import Category
from brands.models import Brand
# Create your models here.
class ShoeSize(models.Model):
    SIZE_CHOICES = [
        ('36', '36'), ('37', '37'), ('38', '38'),
        ('39', '39'), ('40', '40'), ('41', '41'), ('42', '42')
    ]
    size = models.CharField(max_length=3, choices=SIZE_CHOICES, unique=True)

    def __str__(self):
        return self.size
class Product(models.Model):
   
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name="Danh mục")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Giá bán")
    stock = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")
    description = models.TextField(blank=True, null=True, verbose_name="Mô tả")
    image = models.ImageField(upload_to="products/", blank=True, null=True, verbose_name="Hình ảnh")
    sizes = models.ManyToManyField(ShoeSize, blank=True,verbose_name="kích cỡ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Thương hiệu"
    )
    class Meta:
        verbose_name = "Sản phẩm"
        verbose_name_plural = "Sản phẩm"

    def __str__(self):
        return f"{self.name} - {self.get_size_display()}"