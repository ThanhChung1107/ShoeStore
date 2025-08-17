

# Create your models here.
from django.db import models
from django.utils.text import slugify

class Brand(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Tên thương hiệu"
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name="Đường dẫn SEO"
    )

    class Meta:
        verbose_name = "Thương hiệu"
        verbose_name_plural = "Thương hiệu"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)