from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import MinLengthValidator
from django.db import models

from .validators import MIN_NAME_LENGTH


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório.')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        user = self.create_user(email, password, **extra_fields)
        UserRole.objects.get_or_create(user=user, role=UserRole.Role.ADMINISTRADOR)
        UserRole.objects.get_or_create(user=user, role=UserRole.Role.CLIENTE)
        return user


class User(AbstractBaseUser):
    class Gender(models.TextChoices):
        MASCULINO = 'masculino', 'Masculino'
        FEMININO = 'feminino', 'Feminino'

    name = models.CharField(
        max_length=150,
        validators=[
            MinLengthValidator(
                MIN_NAME_LENGTH,
                message=f'O nome deve ter pelo menos {MIN_NAME_LENGTH} caracteres.',
            ),
        ],
    )
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=20, choices=Gender.choices)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'date_of_birth', 'gender']

    class Meta:
        db_table = 'user'

    def __str__(self):
        return self.name

    @property
    def first_name(self):
        cleaned = (self.name or '').strip()
        if not cleaned:
            return ''
        word = cleaned.split()[0]
        return word[0].upper() + word[1:] if word else ''

    def _cached_role_values(self):
        cached = getattr(self, '_role_values_cache', None)
        if cached is not None:
            return cached

        prefetched = getattr(self, '_prefetched_objects_cache', None) or {}
        if 'user_roles' in prefetched:
            cached = {user_role.role for user_role in self.user_roles.all()}
        else:
            cached = set(self.user_roles.values_list('role', flat=True))

        self._role_values_cache = cached
        return cached

    def has_role(self, role):
        return role in self._cached_role_values()

    @property
    def is_cliente(self):
        return self.has_role(UserRole.Role.CLIENTE)

    @property
    def is_vendedor(self):
        return self.has_role(UserRole.Role.VENDEDOR)

    @property
    def is_administrador(self):
        return self.has_role(UserRole.Role.ADMINISTRADOR)

    def add_role(self, role):
        UserRole.objects.get_or_create(user=self, role=role)
        if hasattr(self, '_role_values_cache'):
            del self._role_values_cache

    def get_roles_display(self):
        role_order = (
            UserRole.Role.ADMINISTRADOR,
            UserRole.Role.VENDEDOR,
            UserRole.Role.CLIENTE,
        )
        roles_by_value = {
            user_role.role: user_role.get_role_display()
            for user_role in self.user_roles.all()
        }
        ordered = [roles_by_value[role] for role in role_order if role in roles_by_value]
        extras = [
            label
            for value, label in roles_by_value.items()
            if value not in role_order
        ]
        return ordered + extras


class ProductFavorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='product_favorites',
    )
    product = models.ForeignKey(
        'vendor.Product',
        on_delete=models.CASCADE,
        related_name='favorites',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'product_favorite'
        ordering = ['-created_at']
        unique_together = [['user', 'product']]

    def __str__(self):
        return f'{self.user.name} → {self.product.name}'


class EstablishmentReview(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pendente'
        APPROVED = 'approved', 'Aprovado'
        REJECTED = 'rejected', 'Rejeitado'

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='establishment_reviews',
    )
    establishment = models.ForeignKey(
        'vendor.Establishment',
        on_delete=models.CASCADE,
        related_name='reviews',
    )
    product = models.ForeignKey(
        'vendor.Product',
        on_delete=models.SET_NULL,
        related_name='reviews',
        null=True,
        blank=True,
    )
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(max_length=1000, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.APPROVED,
    )
    viewed_by_vendor_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'establishment_review'
        ordering = ['-created_at']
        unique_together = [['user', 'establishment']]

    def __str__(self):
        if self.rating:
            return f'{self.user.name} → {self.establishment.name} ({self.rating}★)'
        return f'{self.user.name} → {self.establishment.name} (comentário)'


class UserRole(models.Model):
    class Role(models.TextChoices):
        CLIENTE = 'cliente', 'Cliente'
        VENDEDOR = 'vendedor', 'Vendedor'
        ADMINISTRADOR = 'administrador', 'Administrador'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=20, choices=Role.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_role'
        unique_together = [['user', 'role']]

    def __str__(self):
        return f'{self.user.name} - {self.get_role_display()}'
