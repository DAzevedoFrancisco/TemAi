from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.main.models import UserRole
from apps.main.services import assign_cliente_role

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Garante que administradores têm pelo menos o perfil de cliente. '
        'Já não remove cliente/vendedor — um utilizador pode ter os três perfis.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostra as alterações sem gravar na base de dados.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated_users = 0

        panel_admins = (
            User.objects
            .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
            .prefetch_related('user_roles')
            .distinct()
        )
        for user in panel_admins:
            if user.is_cliente or user.is_vendedor:
                continue

            if dry_run:
                self.stdout.write(
                    f'[dry-run] Atribuir perfil cliente a {user.email}.'
                )
            else:
                assign_cliente_role(user)
            updated_users += 1

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'Dry-run concluído. {updated_users} alteração(ões) seriam aplicadas.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Sincronização concluída. {updated_users} alteração(ões) aplicadas.'
        ))
