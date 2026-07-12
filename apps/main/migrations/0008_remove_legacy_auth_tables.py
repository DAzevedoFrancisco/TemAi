from django.db import migrations


def promote_legacy_superusers(apps, schema_editor):
    User = apps.get_model('main', 'User')
    UserRole = apps.get_model('main', 'UserRole')

    for user in User.objects.filter(is_superuser=True):
        UserRole.objects.get_or_create(user=user, role='administrador')


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_optional_review_fields'),
    ]

    operations = [
        migrations.RunPython(promote_legacy_superusers, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='user',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='user',
            name='user_permissions',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_superuser',
        ),
        migrations.RemoveField(
            model_name='user',
            name='is_staff',
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS django_admin_log',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS auth_group_permissions',
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql='DROP TABLE IF EXISTS auth_group',
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
