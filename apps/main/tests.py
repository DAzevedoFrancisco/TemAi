from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from apps.main.search import (
    haversine_km,
    normalize_establishment_coordinates,
    normalize_user_coordinates,
    parse_search_coordinates,
)
from apps.main.models import User, UserRole
from apps.main.services import assign_admin_role, assign_cliente_role, assign_vendedor_role, demote_from_admin, promote_to_admin
from apps.main.validators import (
    MIN_CLIENT_AGE,
    MIN_VENDOR_AGE,
    calculate_age,
    can_become_seller,
    user_meets_min_age,
    validate_date_of_birth,
)


class UserRoleTests(TestCase):
    def test_create_user_encrypts_password(self):
        user = User.objects.create_user(
            email='teste@example.com',
            password='senha123',
            name='Teste',
            date_of_birth='2000-01-01',
            gender=User.Gender.MASCULINO,
        )
        self.assertNotEqual(user.password, 'senha123')
        self.assertTrue(user.check_password('senha123'))

    def test_first_name_returns_first_word_only(self):
        user = User.objects.create_user(
            email='joao@example.com',
            password='senha123',
            name='João Pedro Silva',
            date_of_birth='2000-01-01',
            gender=User.Gender.MASCULINO,
        )
        self.assertEqual(user.first_name, 'João')

    def test_first_name_with_single_name(self):
        user = User.objects.create_user(
            email='maria@example.com',
            password='senha123',
            name='Maria',
            date_of_birth='2000-01-01',
            gender=User.Gender.FEMININO,
        )
        self.assertEqual(user.first_name, 'Maria')

    def test_first_name_capitalizes_first_letter(self):
        user = User.objects.create_user(
            email='ana@example.com',
            password='senha123',
            name='ana carla',
            date_of_birth='2000-01-01',
            gender=User.Gender.FEMININO,
        )
        self.assertEqual(user.first_name, 'Ana')

    def test_register_assigns_cliente_role(self):
        user = User.objects.create_user(
            email='cliente@example.com',
            password='senha123',
            name='Cliente',
            date_of_birth='2000-01-01',
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(user)
        self.assertTrue(user.is_cliente)
        self.assertFalse(user.is_vendedor)

    def test_assign_admin_role_removes_other_roles(self):
        user = User.objects.create_user(
            email='admin@example.com',
            password='senha123',
            name='Admin Teste',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        assign_vendedor_role(user)
        assign_admin_role(user)

        self.assertTrue(user.is_administrador)
        self.assertFalse(user.is_cliente)
        self.assertFalse(user.is_vendedor)
        self.assertEqual(user.user_roles.count(), 1)

    def test_create_superuser_assigns_admin_role(self):
        user = User.objects.create_superuser(
            email='super@example.com',
            password='senha123',
            name='Super Admin',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        self.assertTrue(user.is_administrador)

    def test_is_administrador_requires_admin_role(self):
        user = User.objects.create_user(
            email='legacy@example.com',
            password='senha123',
            name='Legacy Super',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )

        self.assertFalse(user.is_administrador)

        assign_admin_role(user)
        self.assertTrue(user.is_administrador)

    def test_promote_to_admin_assigns_admin_role_only(self):
        user = User.objects.create_user(
            email='promote@example.com',
            password='senha123',
            name='Promote Teste',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)

        promote_to_admin(user)

        user.refresh_from_db()
        self.assertTrue(user.is_administrador)
        self.assertFalse(user.is_cliente)

    def test_demote_from_admin_restores_cliente_role(self):
        user = User.objects.create_user(
            email='demote@example.com',
            password='senha123',
            name='Demote Teste',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        assign_admin_role(user)

        demote_from_admin(user)

        user.refresh_from_db()
        self.assertFalse(user.is_administrador)
        self.assertTrue(user.is_cliente)


class SearchCoordinateTests(TestCase):
    def test_normalize_user_coordinates_accepts_beira_point(self):
        lat, lng = normalize_user_coordinates(-19.8436, 34.8389)
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)

    def test_normalize_user_coordinates_fixes_swapped_values(self):
        lat, lng = normalize_user_coordinates(34.8389, -19.8436)
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)

    def test_normalize_user_coordinates_accepts_point_outside_beira(self):
        lat, lng = normalize_user_coordinates(-19.116, 33.483)
        self.assertAlmostEqual(lat, -19.116)
        self.assertAlmostEqual(lng, 33.483)

    def test_normalize_user_coordinates_fixes_swapped_chota_point(self):
        lat, lng = normalize_user_coordinates(34.8881, -19.8169)
        self.assertAlmostEqual(lat, -19.8169)
        self.assertAlmostEqual(lng, 34.8881)

    def test_haversine_distance_chota_to_casa_dos_bicos(self):
        chota = (-19.8169, 34.8881)
        casa_dos_bicos = (-19.83490, 34.84038)
        distance = haversine_km(*chota, *casa_dos_bicos)
        self.assertGreater(distance, 4)
        self.assertLess(distance, 7)

    def test_haversine_distance_for_nearby_points(self):
        distance = haversine_km(-19.8436, 34.8389, -19.8500, 34.8500)
        self.assertGreater(distance, 0.5)
        self.assertLess(distance, 3)

    def test_parse_search_coordinates_from_strings(self):
        lat, lng = parse_search_coordinates('-19.8436', '34.8389')
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)

    def test_normalize_establishment_coordinates_fixes_swapped_values(self):
        lat, lng = normalize_establishment_coordinates(34.8389, -19.8436)
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)


class DateOfBirthValidationTests(TestCase):
    def test_rejects_future_date(self):
        tomorrow = date.today() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            validate_date_of_birth(tomorrow, min_age=MIN_CLIENT_AGE)

    def test_rejects_client_under_14(self):
        too_young = date.today() - timedelta(days=365 * 13)
        with self.assertRaises(ValidationError):
            validate_date_of_birth(too_young, min_age=MIN_CLIENT_AGE)

    def test_accepts_client_14_or_older(self):
        dob = date.today() - timedelta(days=365 * 14 + 30)
        self.assertEqual(
            validate_date_of_birth(dob, min_age=MIN_CLIENT_AGE),
            dob,
        )

    def test_register_form_enforces_min_client_age(self):
        form = RegisterForm({
            'name': 'Cliente Jovem',
            'email': 'jovem@example.com',
            'password': 'SenhaSegura123!',
            'date_of_birth': (date.today() - timedelta(days=365 * 10)).isoformat(),
            'gender': User.Gender.MASCULINO,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('date_of_birth', form.errors)

    def test_vendor_requires_18_years(self):
        user = User.objects.create_user(
            email='menor@example.com',
            password='senha123',
            name='Menor Vendedor',
            date_of_birth=date.today() - timedelta(days=365 * 17),
            gender=User.Gender.MASCULINO,
        )
        self.assertFalse(user_meets_min_age(user, MIN_VENDOR_AGE))
        self.assertTrue(user_meets_min_age(user, MIN_CLIENT_AGE))

    def test_calculate_age_accounts_for_birthday(self):
        reference = date(2026, 7, 9)
        self.assertEqual(calculate_age(date(2010, 7, 10), reference), 15)
        self.assertEqual(calculate_age(date(2010, 7, 9), reference), 16)


class BecomeSellerTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_underage_user_sees_blocked_page(self):
        user = User.objects.create_user(
            email='menor@example.com',
            password='senha123',
            name='Menor Vendedor',
            date_of_birth=date.today() - timedelta(days=365 * 17),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        self.client.force_login(user)

        response = self.client.get(reverse('vendor:become_seller'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Requisito de idade não cumprido')
        self.assertContains(response, str(MIN_VENDOR_AGE))
        self.assertFalse(user.is_vendedor)

    def test_underage_user_cannot_confirm_via_post(self):
        user = User.objects.create_user(
            email='bloqueado@example.com',
            password='senha123',
            name='Bloqueado Vendedor',
            date_of_birth=date.today() - timedelta(days=365 * 16),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(user)
        self.client.force_login(user)

        response = self.client.post(reverse('vendor:become_seller'))

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_vendedor)

    def test_adult_user_can_become_seller(self):
        user = User.objects.create_user(
            email='adulto@example.com',
            password='senha123',
            name='Adulto Vendedor',
            date_of_birth=date.today() - timedelta(days=365 * 20),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        self.client.force_login(user)

        self.assertTrue(can_become_seller(user))
        response = self.client.post(reverse('vendor:become_seller'))

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)

    def test_assign_vendedor_role_rejects_underage(self):
        user = User.objects.create_user(
            email='service@example.com',
            password='senha123',
            name='Service Test',
            date_of_birth=date.today() - timedelta(days=365 * 15),
            gender=User.Gender.FEMININO,
        )

        with self.assertRaises(ValidationError):
            assign_vendedor_role(user)


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='conta@example.com',
            password='SenhaSegura123!',
            name='Utilizador Conta',
            date_of_birth=date(2000, 5, 15),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        self.url = reverse('account_settings')

    def test_account_settings_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('auth'))

    def test_account_settings_updates_profile(self):
        self.client.login(username='conta@example.com', password='SenhaSegura123!')
        response = self.client.post(self.url, {
            'form_type': 'profile',
            'name': 'Nome Actualizado',
            'email': 'novo@example.com',
            'date_of_birth': '1999-03-20',
            'gender': User.Gender.FEMININO,
        })

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Nome Actualizado')
        self.assertEqual(self.user.email, 'novo@example.com')
        self.assertEqual(self.user.date_of_birth.isoformat(), '1999-03-20')
        self.assertEqual(self.user.gender, User.Gender.FEMININO)

    def test_account_settings_rejects_duplicate_email(self):
        User.objects.create_user(
            email='outro@example.com',
            password='SenhaSegura123!',
            name='Outro Utilizador',
            date_of_birth=date(1998, 1, 1),
            gender=User.Gender.FEMININO,
        )
        self.client.login(username='conta@example.com', password='SenhaSegura123!')
        response = self.client.post(self.url, {
            'form_type': 'profile',
            'name': 'Utilizador Conta',
            'email': 'outro@example.com',
            'date_of_birth': '2000-05-15',
            'gender': User.Gender.MASCULINO,
        })

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'conta@example.com')

    def test_account_settings_changes_password(self):
        self.client.login(username='conta@example.com', password='SenhaSegura123!')
        response = self.client.post(self.url, {
            'form_type': 'password',
            'current_password': 'SenhaSegura123!',
            'new_password': 'NovaSenhaSegura456!',
            'confirm_password': 'NovaSenhaSegura456!',
        })

        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NovaSenhaSegura456!'))

    def test_account_settings_rejects_wrong_current_password(self):
        self.client.login(username='conta@example.com', password='SenhaSegura123!')
        response = self.client.post(self.url, {
            'form_type': 'password',
            'current_password': 'senha-errada',
            'new_password': 'NovaSenhaSegura456!',
            'confirm_password': 'NovaSenhaSegura456!',
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.user.check_password('SenhaSegura123!'))


class VendorProfileNavigationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='vendedor@example.com',
            password='SenhaSegura123!',
            name='Vendedor Teste',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        assign_vendedor_role(self.user)

    def _activate_vendor_profile(self):
        session = self.client.session
        session['active_profile'] = 'vendedor'
        session.save()

    def test_account_settings_hides_client_links_in_vendor_profile(self):
        self.client.login(username='vendedor@example.com', password='SenhaSegura123!')
        self._activate_vendor_profile()

        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Voltar ao painel vendedor')
        self.assertContains(response, 'Voltar ao painel')
        self.assertNotContains(response, 'Favoritos')
        self.assertNotContains(response, 'Painel vendedor</a>')

    def test_favorites_redirects_when_vendor_profile_active(self):
        self.client.login(username='vendedor@example.com', password='SenhaSegura123!')
        self._activate_vendor_profile()

        response = self.client.get(reverse('favorites'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('vendor:dashboard'))
