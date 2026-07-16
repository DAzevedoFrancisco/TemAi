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


@override_settings(
    SECURE_SSL_REDIRECT=False,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class EstablishmentCreateLocationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='vendedor-loja@example.com',
            password='SenhaSegura123!',
            name='Vendedor Loja',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        assign_vendedor_role(self.user)
        self.client.force_login(self.user)
        self.url = reverse('vendor:establishment_create')
        self.valid_payload = {
            'name': 'Loja Beira Centro',
            'address': 'Avenida Samora Machel, Beira',
            'phone': '841234567',
            'opening_hours': '08:00 - 18:00',
            'latitude': '-19.843600',
            'longitude': '34.838900',
            'user_latitude': '-19.843600',
            'user_longitude': '34.838900',
        }

    def test_create_requires_user_gps(self):
        payload = dict(self.valid_payload)
        payload.pop('user_latitude')
        payload.pop('user_longitude')

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Establishment.objects.filter(name='Loja Beira Centro').exists())
        self.assertContains(response, 'É obrigatório autorizar a localização GPS')

    def test_create_rejects_user_outside_beira(self):
        payload = dict(self.valid_payload)
        payload['user_latitude'] = '-25.969200'
        payload['user_longitude'] = '32.573200'

        response = self.client.post(self.url, payload)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Establishment.objects.filter(name='Loja Beira Centro').exists())
        self.assertContains(response, 'fora da cidade da Beira')

    def test_create_succeeds_with_user_in_beira(self):
        response = self.client.post(self.url, self.valid_payload)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Establishment.objects.filter(name='Loja Beira Centro', owner=self.user).exists())


@override_settings(
    SECURE_SSL_REDIRECT=False,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class EstablishmentDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='dono-loja@example.com',
            password='SenhaSegura123!',
            name='Dono Loja',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.owner)
        assign_vendedor_role(self.owner)
        self.other = User.objects.create_user(
            email='outro-vendedor@example.com',
            password='SenhaSegura123!',
            name='Outro Vendedor',
            date_of_birth=date(1991, 1, 1),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(self.other)
        assign_vendedor_role(self.other)
        self.category, _ = Category.objects.get_or_create(
            slug='alimentacao',
            defaults={'name': 'Alimentação'},
        )
        self.establishment = Establishment.objects.create(
            owner=self.owner,
            name='Loja Para Apagar',
            address='Rua Teste 2, Beira',
            phone='841111222',
            opening_hours='09:00 - 17:00',
            latitude=-19.8436,
            longitude=34.8389,
        )
        Product.objects.create(
            establishment=self.establishment,
            category=self.category,
            name='Produto Cascata',
            description='Será removido com o estabelecimento',
            is_available=True,
        )
        self.url = reverse('vendor:establishment_delete', kwargs={'pk': self.establishment.pk})

    def test_owner_can_delete_establishment_and_products(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('vendor:establishment_list'))
        self.assertFalse(Establishment.objects.filter(pk=self.establishment.pk).exists())
        self.assertFalse(Product.objects.filter(name='Produto Cascata').exists())

    def test_other_vendor_cannot_delete_establishment(self):
        self.client.force_login(self.other)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(Establishment.objects.filter(pk=self.establishment.pk).exists())

    def test_get_is_not_allowed(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertTrue(Establishment.objects.filter(pk=self.establishment.pk).exists())


@override_settings(
    SECURE_SSL_REDIRECT=False,
    DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},
)
class ReviewDeleteTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = User.objects.create_user(
            email='dono-reviews@example.com',
            password='SenhaSegura123!',
            name='Dono Reviews',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.owner)
        assign_vendedor_role(self.owner)
        self.other = User.objects.create_user(
            email='outro-reviews@example.com',
            password='SenhaSegura123!',
            name='Outro Reviews',
            date_of_birth=date(1991, 1, 1),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(self.other)
        assign_vendedor_role(self.other)
        self.client_user = User.objects.create_user(
            email='cliente-reviews@example.com',
            password='SenhaSegura123!',
            name='Cliente Reviews',
            date_of_birth=date(1992, 1, 1),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(self.client_user)
        self.establishment = Establishment.objects.create(
            owner=self.owner,
            name='Loja Com Comentarios',
            address='Rua Teste 3, Beira',
            phone='842222333',
            opening_hours='09:00 - 17:00',
            latitude=-19.8436,
            longitude=34.8389,
        )
        from apps.main.models import EstablishmentReview
        self.review = EstablishmentReview.objects.create(
            user=self.client_user,
            establishment=self.establishment,
            rating=4,
            comment='Bom atendimento',
            status=EstablishmentReview.Status.APPROVED,
        )
        self.url = reverse('vendor:review_delete', kwargs={'pk': self.review.pk})

    def test_owner_can_delete_review(self):
        from apps.main.models import EstablishmentReview
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertFalse(EstablishmentReview.objects.filter(pk=self.review.pk).exists())

    def test_other_vendor_cannot_delete_review(self):
        from apps.main.models import EstablishmentReview
        self.client.force_login(self.other)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertTrue(EstablishmentReview.objects.filter(pk=self.review.pk).exists())
