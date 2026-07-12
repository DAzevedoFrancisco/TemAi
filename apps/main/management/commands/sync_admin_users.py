from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.main.models import UserRole

User = get_user_model()


class Command(BaseCommand):
    help = (
        'Normaliza contas de administrador: remove perfis extra de contas '
        'com o papel administrador no painel /gestao/.'
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

        with transaction.atomic():
            panel_admins = (
                User.objects
                .filter(user_roles__role=UserRole.Role.ADMINISTRADOR)
                .prefetch_related('user_roles')
                .distinct()
            )
            for user in panel_admins:
                extra_roles = user.user_roles.exclude(role=UserRole.Role.ADMINISTRADOR)
                if not extra_roles.exists():
                    continue

                if dry_run:
                    self.stdout.write(
                        f'[dry-run] Remover perfis extra de {user.email}.'
                    )
                else:
                    extra_roles.delete()
                updated_users += 1

            if dry_run:
                transaction.set_rollback(True)

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'Dry-run concluído. {updated_users} alteração(ões) seriam aplicadas.'
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f'Sincronização concluída. {updated_users} alteração(ões) aplicadas.'
        ))
