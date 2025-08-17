from django.db import models
from categorys.models import Category
from brands.models import Brand

class Size(models.Model):
    value = models.CharField(max_length=5, verbose_name="Size giày")

    def __str__(self):
        return self.value

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Tên sản phẩm")
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.ForeignKey(Size, on_delete=models.CASCADE)
    stock = models.PositiveIntegerField(default=0, verbose_name="Số lượng tồn kho")

    class Meta:
        unique_together = ('product', 'size')  # Mỗi product + size chỉ có 1 bản ghi

    def __str__(self):
        return f"{self.product.name} - {self.size.value} ({self.stock})"
