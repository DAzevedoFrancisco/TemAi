from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from apps.main.forms import RegisterForm
from apps.main.login_throttle import (
    LOGIN_ATTEMPT_LIMIT,
    clear_login_attempts,
    failed_login_error_message,
    is_login_locked,
    register_failed_login,
)
from apps.main.search import (
    build_search_map_markers,
    get_establishment_coordinates,
    normalize_establishment_coordinates,
)
from apps.main.models import User, UserRole
from apps.main.services import (
    assign_admin_role,
    assign_cliente_role,
    assign_vendedor_role,
    demote_from_admin,
    ensure_system_admin,
    has_system_admin,
    promote_to_admin,
    register_user_with_default_role,
)
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

    def test_first_registered_user_is_cliente_by_default(self):
        user = register_user_with_default_role(
            email='primeiro@example.com',
            password='senha123',
            name='Primeiro Cliente',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        self.assertTrue(user.is_cliente)
        self.assertFalse(user.is_administrador)

    def test_auto_promote_can_make_first_user_admin_when_enabled(self):
        with override_settings(AUTO_PROMOTE_FIRST_USER=True):
            user = register_user_with_default_role(
                email='primeiro-admin@example.com',
                password='senha123',
                name='Primeiro Admin',
                date_of_birth='1990-01-01',
                gender=User.Gender.MASCULINO,
            )
        self.assertTrue(user.is_administrador)
        self.assertTrue(user.is_cliente)

    def test_second_registered_user_becomes_cliente(self):
        register_user_with_default_role(
            email='primeiro@example.com',
            password='senha123',
            name='Primeiro Cliente',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        user = register_user_with_default_role(
            email='segundo@example.com',
            password='senha123',
            name='Segundo Cliente',
            date_of_birth='2000-01-01',
            gender=User.Gender.FEMININO,
        )
        self.assertTrue(user.is_cliente)
        self.assertFalse(user.is_administrador)

    def test_ensure_system_admin_promotes_oldest_existing_user(self):
        user = User.objects.create_user(
            email='antigo@example.com',
            password='senha123',
            name='Utilizador Antigo',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        self.assertFalse(has_system_admin())

        with override_settings(AUTO_PROMOTE_FIRST_USER=True):
            promoted = ensure_system_admin()
        user.refresh_from_db()

        self.assertEqual(promoted.pk, user.pk)
        self.assertTrue(user.is_administrador)

    def test_registration_promotes_oldest_when_auto_promote_enabled(self):
        oldest = User.objects.create_user(
            email='antigo@example.com',
            password='senha123',
            name='Utilizador Antigo',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(oldest)

        with override_settings(AUTO_PROMOTE_FIRST_USER=True):
            new_user = register_user_with_default_role(
                email='novo@example.com',
                password='senha123',
                name='Novo Cliente',
                date_of_birth='2000-01-01',
                gender=User.Gender.FEMININO,
            )
        oldest.refresh_from_db()

        self.assertTrue(oldest.is_administrador)
        self.assertTrue(new_user.is_cliente)
        self.assertFalse(new_user.is_administrador)

    def test_assign_admin_role_keeps_other_roles(self):
        user = User.objects.create_user(
            email='admin@example.com',
            password='senha123',
            name='Admin Teste',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        assign_vendedor_role(user)
        assign_admin_role(user)

        self.assertTrue(user.is_administrador)
        self.assertTrue(user.is_cliente)
        self.assertTrue(user.is_vendedor)
        self.assertEqual(user.user_roles.count(), 3)

    def test_create_superuser_assigns_admin_role(self):
        user = User.objects.create_superuser(
            email='super@example.com',
            password='senha123',
            name='Super Admin',
            date_of_birth='1990-01-01',
            gender=User.Gender.MASCULINO,
        )
        self.assertTrue(user.is_administrador)
        self.assertTrue(user.is_cliente)

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

    def test_promote_to_admin_keeps_cliente_role(self):
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
        self.assertTrue(user.is_cliente)

    def test_demote_from_admin_keeps_existing_roles(self):
        user = User.objects.create_user(
            email='demote@example.com',
            password='senha123',
            name='Demote Teste',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        assign_vendedor_role(user)
        assign_admin_role(user)

        demote_from_admin(user)

        user.refresh_from_db()
        self.assertFalse(user.is_administrador)
        self.assertTrue(user.is_cliente)
        self.assertTrue(user.is_vendedor)


class SearchCoordinateTests(TestCase):
    def test_normalize_establishment_coordinates_fixes_swapped_values(self):
        lat, lng = normalize_establishment_coordinates(34.8389, -19.8436)
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)

    def test_get_establishment_coordinates_uses_normalized_values(self):
        from apps.vendor.models import Establishment

        establishment = Establishment(
            latitude=34.8389,
            longitude=-19.8436,
        )
        lat, lng = get_establishment_coordinates(establishment)
        self.assertAlmostEqual(lat, -19.8436)
        self.assertAlmostEqual(lng, 34.8389)

    def test_build_search_map_markers_groups_by_store(self):
        from apps.vendor.models import Category, Establishment, Product

        category = Category.objects.create(name='Geral', slug='geral')
        store = Establishment.objects.create(
            name='Loja Teste',
            address='Rua A',
            phone='840000000',
            opening_hours='08:00 - 18:00',
            latitude=-19.8436,
            longitude=34.8389,
            is_active=True,
            owner=User.objects.create_user(
                email='mapa@example.com',
                password='senha123',
                name='Dono Mapa',
                date_of_birth='1990-01-01',
                gender=User.Gender.MASCULINO,
            ),
        )
        p1 = Product.objects.create(
            establishment=store,
            category=category,
            name='Produto 1',
            description='Descricao 1',
            is_active=True,
            is_available=True,
        )
        p2 = Product.objects.create(
            establishment=store,
            category=category,
            name='Produto 2',
            description='Descricao 2',
            is_active=True,
            is_available=True,
        )

        markers = build_search_map_markers([p1, p2], query='produto')
        self.assertEqual(len(markers), 1)
        self.assertEqual(markers[0]['name'], 'Loja Teste')
        self.assertEqual(len(markers[0]['products']), 2)
        self.assertIn('q=produto', markers[0]['products'][0]['url'])


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
        response = self.client.post(
            reverse('vendor:become_seller'),
            {
                'lat': '-19.843600',
                'lng': '34.838900',
            },
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_vendedor)

    def test_become_seller_requires_location(self):
        user = User.objects.create_user(
            email='semgps@example.com',
            password='senha123',
            name='Sem GPS',
            date_of_birth=date.today() - timedelta(days=365 * 22),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(user)
        self.client.force_login(user)

        response = self.client.post(reverse('vendor:become_seller'))

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_vendedor)

    def test_become_seller_rejects_outside_beira(self):
        user = User.objects.create_user(
            email='maputo@example.com',
            password='senha123',
            name='Fora Beira',
            date_of_birth=date.today() - timedelta(days=365 * 25),
            gender=User.Gender.FEMININO,
        )
        assign_cliente_role(user)
        self.client.force_login(user)

        response = self.client.post(
            reverse('vendor:become_seller'),
            {
                'lat': '-25.969200',
                'lng': '32.573200',
            },
        )

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertFalse(user.is_vendedor)

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


@override_settings(SECURE_SSL_REDIRECT=False)
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
        self.client.force_login(self.user)
        self._activate_vendor_profile()

        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Voltar ao painel vendedor')
        self.assertContains(response, 'Voltar ao painel')
        self.assertNotContains(response, 'Favoritos')
        self.assertNotContains(response, '>Sobre</span>')
        self.assertNotContains(response, 'Painel vendedor</a>')

    def test_favorites_redirects_when_vendor_profile_active(self):
        self.client.force_login(self.user)
        self._activate_vendor_profile()

        response = self.client.get(reverse('favorites'))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('vendor:dashboard'))


def _create_establishment(owner, *, name='Loja Teste', is_active=True):
    from apps.vendor.models import Establishment

    return Establishment.objects.create(
        owner=owner,
        name=name,
        address='Rua Teste 1, Beira',
        phone='841234567',
        opening_hours='08:00 - 18:00',
        latitude=-19.8436,
        longitude=34.8389,
        is_active=is_active,
    )


class AdminRoleEstablishmentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='vendor-admin@example.com',
            password='SenhaSegura123!',
            name='Vendor Admin',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        assign_vendedor_role(self.user)
        self.active_shop = _create_establishment(self.user, name='Loja Activa')
        self.blocked_shop = _create_establishment(self.user, name='Loja Bloqueada', is_active=False)

    def test_promote_to_admin_keeps_active_establishments(self):
        promote_to_admin(self.user)

        self.active_shop.refresh_from_db()
        self.blocked_shop.refresh_from_db()

        self.assertTrue(self.active_shop.is_active)
        self.assertFalse(self.active_shop.suspended_for_admin_role)
        self.assertFalse(self.blocked_shop.is_active)
        self.assertFalse(self.blocked_shop.suspended_for_admin_role)

    def test_demote_from_admin_restores_legacy_suspended_establishments(self):
        self.active_shop.is_active = False
        self.active_shop.suspended_for_admin_role = True
        self.active_shop.save(update_fields=['is_active', 'suspended_for_admin_role'])
        promote_to_admin(self.user)
        demote_from_admin(self.user)

        self.active_shop.refresh_from_db()
        self.blocked_shop.refresh_from_db()

        self.assertTrue(self.active_shop.is_active)
        self.assertFalse(self.active_shop.suspended_for_admin_role)
        self.assertFalse(self.blocked_shop.is_active)
        self.assertFalse(self.blocked_shop.suspended_for_admin_role)


@override_settings(SECURE_SSL_REDIRECT=False)
class AdminClientCatalogTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='SenhaSegura123!',
            name='Admin Teste',
            date_of_birth=date(1990, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(self.user)
        assign_admin_role(self.user)

    def test_search_allows_admin_in_client_profile(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['active_profile'] = 'cliente'
        session.save()

        response = self.client.get(reverse('search_results'), {'q': 'arroz'})

        self.assertEqual(response.status_code, 200)

    def test_favorites_allows_admin_in_client_profile(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['active_profile'] = 'cliente'
        session.save()

        response = self.client.get(reverse('favorites'))

        self.assertEqual(response.status_code, 200)

    def test_account_settings_shows_admin_panel_link(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Administração')
        self.assertContains(response, 'Favoritos')
        self.assertContains(response, 'Sobre')
        self.assertNotContains(response, 'Voltar ao painel de administração')

    def test_account_settings_hides_client_links_in_admin_profile(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['active_profile'] = 'administrador'
        session.save()

        response = self.client.get(reverse('account_settings'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Voltar ao painel de administração')
        self.assertContains(response, 'Voltar à administração')
        self.assertNotContains(response, 'Favoritos')
        self.assertNotContains(response, '>Sobre</span>')


class LoginThrottleServiceTests(SimpleTestCase):
    def setUp(self):
        clear_login_attempts('login@example.com')

    def tearDown(self):
        clear_login_attempts('login@example.com')

    def test_locks_after_limit(self):
        for index in range(LOGIN_ATTEMPT_LIMIT):
            attempts, locked = register_failed_login('login@example.com')
            if index < LOGIN_ATTEMPT_LIMIT - 1:
                self.assertFalse(locked)
            else:
                self.assertTrue(locked)
                self.assertEqual(attempts, LOGIN_ATTEMPT_LIMIT)

        self.assertTrue(is_login_locked('login@example.com'))

    def test_success_clears_attempts(self):
        register_failed_login('login@example.com')
        register_failed_login('login@example.com')
        clear_login_attempts('login@example.com')

        attempts, locked = register_failed_login('login@example.com')
        self.assertEqual(attempts, 1)
        self.assertFalse(locked)
        self.assertIn('Restam 2 tentativas', failed_login_error_message('login@example.com', attempts))


@override_settings(SECURE_SSL_REDIRECT=False)
class LoginThrottleTests(TestCase):
    def setUp(self):
        self.client = Client()
        clear_login_attempts('login@example.com')
        register_user_with_default_role(
            email='segundo@example.com',
            password='SenhaSegura123!',
            name='Utilizador Login',
            date_of_birth=date(2000, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        User.objects.create_user(
            email='login@example.com',
            password='SenhaSegura123!',
            name='Utilizador Login',
            date_of_birth=date(2000, 1, 1),
            gender=User.Gender.MASCULINO,
        )
        assign_cliente_role(User.objects.get(email='login@example.com'))
        self.login_url = reverse('auth')
        self.api_login_url = reverse('api_login')
        self.payload = {
            'email': 'login@example.com',
            'password': 'errada',
        }

    def tearDown(self):
        clear_login_attempts('login@example.com')

    def _post_login(self):
        return self.client.post(self.login_url, {
            'form_type': 'login',
            'email': self.payload['email'],
            'password': self.payload['password'],
        })

    def test_web_login_shows_remaining_attempts(self):
        response = self._post_login()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Restam 2 tentativas')

    def test_web_login_locks_after_three_failed_attempts(self):
        for _ in range(2):
            response = self._post_login()
            self.assertEqual(response.status_code, 200)

        response = self._post_login()

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Excedeu o limite de 3 tentativas')
        self.assertContains(response, 'id="login-submit" disabled')
        self.assertContains(response, 'login-lockout-notice')

    def test_web_login_clears_attempts_after_success(self):
        for _ in range(2):
            self._post_login()

        response = self.client.post(self.login_url, {
            'form_type': 'login',
            'email': 'login@example.com',
            'password': 'SenhaSegura123!',
        })

        self.assertEqual(response.status_code, 302)

        self.client.get(reverse('logout'))

        response = self._post_login()
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Restam 2 tentativas')

    def test_api_login_locks_after_three_failed_attempts(self):
        for index in range(2):
            response = self.client.post(
                self.api_login_url,
                data=self.payload,
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 401, msg=f'attempt {index + 1}')

        response = self.client.post(
            self.api_login_url,
            data=self.payload,
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 429)
        self.assertIn('Excedeu o limite de 3 tentativas', response.json()['detail'])
