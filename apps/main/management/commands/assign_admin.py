from django.core.management.base import BaseCommand

from apps.main.models import User
from apps.main.services import assign_admin_role


class Command(BaseCommand):
    help = 'Atribui o perfil de administrador a um utilizador existente pelo email.'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Email do utilizador')

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            self.stderr.write(self.style.ERROR(f'Utilizador com email "{email}" não encontrado.'))
            return

        assign_admin_role(user)
        self.stdout.write(self.style.SUCCESS(
            f'Perfil de administrador atribuído a {user.name} ({user.email}). '
            f'Outros perfis foram removidos.'
        ))
