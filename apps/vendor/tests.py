import tempfile
from datetime import date
from io import BytesIO
from unittest.mock import patch

from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.main.models import User
from apps.main.services import assign_cliente_role, assign_vendedor_role
from apps.vendor.models import Category, Establishment, Product


def _image_upload(name='produto.jpg'):
    image = Image.new('RGB', (32, 32), color='blue')
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    buffer.seek(0)
    return SimpleUploadedFile(name, buffer.read(), content_type='image/jpeg')


@override_settings(
    SECURE_SSL_REDIRECT=False,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class ProductCreateTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.mkdtemp()
        self.storage_override = override_settings(
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            },
            MEDIA_ROOT=self.media_dir,
        )
        self.storage_override.enable()

        self.client = Client()
        self.user = User.objects.create_user(
            email='vendedor-produto@example.com',
            password='SenhaSegura123!',
            name='Vendedor Produto',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        assign_vendedor_role(self.user)
        self.category, _ = Category.objects.get_or_create(
            slug='alimentacao',
            defaults={'name': 'Alimentação'},
        )
        self.establishment = Establishment.objects.create(
            owner=self.user,
            name='Mercado Central',
            address='Rua Teste 1, Beira',
            phone='841234567',
            opening_hours='08:00 - 18:00',
            latitude=-19.8436,
            longitude=34.8389,
        )

    def tearDown(self):
        self.storage_override.disable()

    def test_product_create_saves_image_successfully(self):
        self.client.force_login(self.user)
        url = reverse('vendor:product_create', kwargs={'est_pk': self.establishment.pk})

        response = self.client.post(url, {
            'name': 'Arroz',
            'description': 'Arroz branco de 1kg',
            'category': self.category.pk,
            'is_available': 'on',
            'image': _image_upload(),
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('vendor:product_list', kwargs={'pk': self.establishment.pk}))
        product = Product.objects.get(name='Arroz')
        self.assertEqual(product.establishment_id, self.establishment.pk)
        self.assertTrue(product.image.name)

    def test_product_name_is_title_cased_on_create(self):
        self.client.force_login(self.user)
        url = reverse('vendor:product_create', kwargs={'est_pk': self.establishment.pk})

        response = self.client.post(url, {
            'name': 'arroz branco especial',
            'description': 'Pacote de 1kg',
            'category': self.category.pk,
            'is_available': 'on',
            'image': _image_upload(),
        })

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(establishment=self.establishment, description='Pacote de 1kg')
        self.assertEqual(product.name, 'Arroz Branco Especial')

    def test_product_create_shows_error_when_image_upload_fails(self):
        self.client.force_login(self.user)
        url = reverse('vendor:product_create', kwargs={'est_pk': self.establishment.pk})

        with patch.object(default_storage, 'save', side_effect=Exception('upload failed')):
            response = self.client.post(url, {
                'name': 'Feijão',
                'description': 'Feijão vermelho',
                'category': self.category.pk,
                'is_available': 'on',
                'image': _image_upload('feijao.jpg'),
            })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Product.objects.filter(name='Feijão').exists())
        self.assertContains(response, 'Não foi possível guardar a imagem do produto')
