from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models

from apps.main.validators import MIN_NAME_LENGTH, title_case_name, validate_mozambique_phone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'category'
        ordering = ['name']
        verbose_name_plural = 'categorias'

    def __str__(self):
        return self.name


class Establishment(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='establishments',
    )
    name = models.CharField(
        max_length=200,
        validators=[
            MinLengthValidator(
                MIN_NAME_LENGTH,
                message=f'O nome deve ter pelo menos {MIN_NAME_LENGTH} caracteres.',
            ),
        ],
    )
    address = models.TextField()
    phone = models.CharField(
        max_length=30,
        validators=[validate_mozambique_phone],
    )
    opening_hours = models.CharField(max_length=200)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    suspended_for_admin_role = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'establishment'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


def product_image_path(instance, filename):
    return f'products/{instance.establishment_id}/{filename}'


class Product(models.Model):
    establishment = models.ForeignKey(
        Establishment,
        on_delete=models.CASCADE,
        related_name='products',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to=product_image_path, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'product'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if self.name:
            self.name = title_case_name(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
