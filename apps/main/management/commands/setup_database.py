from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

import pymysql


class Command(BaseCommand):
    help = 'Cria a base de dados MySQL "mob" e aplica as migrações.'

    def handle(self, *args, **options):
        db_settings = settings.DATABASES['default']
        database_name = db_settings['NAME']

        self.stdout.write(f'A ligar ao MySQL em {db_settings["HOST"]}:{db_settings["PORT"]}...')

        pymysql_conn = pymysql.connect(
            host=db_settings['HOST'],
            user=db_settings['USER'],
            password=db_settings['PASSWORD'],
            port=int(db_settings['PORT']),
            charset='utf8mb4',
        )

        try:
            with pymysql_conn.cursor() as cursor:
                cursor.execute(
                    f'CREATE DATABASE IF NOT EXISTS `{database_name}` '
                    'CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci'
                )
            pymysql_conn.commit()
            self.stdout.write(self.style.SUCCESS(f'Base de dados "{database_name}" pronta.'))
        finally:
            pymysql_conn.close()

        call_command('migrate')
        self.stdout.write(self.style.SUCCESS('Migrações aplicadas com sucesso.'))
