from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.main.services import assign_admin_role, assign_cliente_role, register_user_with_default_role
from apps.vendor.models import Category, Establishment, Product

User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False, AUTO_PROMOTE_FIRST_USER=True)
class AdminPanelGuardTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = register_user_with_default_role(
            email='admin@example.com',
            password='SenhaSegura123!',
            name='Admin Principal',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        self.other = User.objects.create_user(
            email='outro@example.com',
            password='SenhaSegura123!',
            name='Outro Utilizador',
            date_of_birth=date(1995, 1, 1),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(self.other)
        self.client.force_login(self.admin)

    def test_cannot_block_own_account(self):
        response = self.client.post(
            reverse('admin_panel:user_toggle_active', kwargs={'pk': self.admin.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cannot_block_last_active_admin(self):
        assign_admin_role(self.other)
        # Leave only `other` as active admin
        self.admin.is_active = False
        self.admin.save(update_fields=['is_active'])
        self.client.force_login(self.other)

        response = self.client.post(
            reverse('admin_panel:user_toggle_active', kwargs={'pk': self.other.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.other.refresh_from_db()
        self.assertTrue(self.other.is_active)

    def test_can_block_non_last_admin(self):
        assign_admin_role(self.other)
        response = self.client.post(
            reverse('admin_panel:user_toggle_active', kwargs={'pk': self.other.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.other.refresh_from_db()
        self.assertFalse(self.other.is_active)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
        self.assertTrue(self.admin.is_administrador)

    def test_cannot_demote_last_active_admin(self):
        response = self.client.post(
            reverse('admin_panel:demote_admin', kwargs={'pk': self.admin.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_administrador)

    def test_can_self_demote_when_another_admin_exists(self):
        assign_admin_role(self.other)
        response = self.client.post(
            reverse('admin_panel:demote_admin', kwargs={'pk': self.admin.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('home'))
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_administrador)
        self.assertTrue(self.admin.is_cliente)
        self.other.refresh_from_db()
        self.assertTrue(self.other.is_administrador)

    def test_promote_admin_keeps_existing_roles(self):
        response = self.client.post(
            reverse('admin_panel:promote_admin'),
            {'email': self.other.email},
        )
        self.assertEqual(response.status_code, 302)
        self.other.refresh_from_db()
        self.assertTrue(self.other.is_administrador)
        self.assertTrue(self.other.is_cliente)


@override_settings(SECURE_SSL_REDIRECT=False)
class UnavailableProductCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        owner = User.objects.create_user(
            email='loja@example.com',
            password='SenhaSegura123!',
            name='Dono Loja',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(owner)
        category, _ = Category.objects.get_or_create(
            slug='alimentacao',
            defaults={'name': 'Alimentação'},
        )
        establishment = Establishment.objects.create(
            owner=owner,
            name='Loja Teste',
            address='Rua A, Beira',
            phone='841234567',
            opening_hours='09:00-18:00',
            latitude=-19.8436,
            longitude=34.8389,
        )
        self.available = Product.objects.create(
            establishment=establishment,
            category=category,
            name='Produto Disponivel',
            description='Visivel',
            is_available=True,
        )
        self.unavailable = Product.objects.create(
            establishment=establishment,
            category=category,
            name='Produto Indisponivel',
            description='Oculto',
            is_available=False,
        )

    def test_search_hides_unavailable_products(self):
        response = self.client.get(reverse('search_results'), {'q': 'Produto'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.available.name)
        self.assertNotContains(response, self.unavailable.name)

    def test_product_detail_404_for_unavailable(self):
        response = self.client.get(
            reverse('product_detail', kwargs={'pk': self.unavailable.pk}),
        )
        self.assertEqual(response.status_code, 404)
