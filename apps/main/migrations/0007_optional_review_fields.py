from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0006_user_gender_admin_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='establishmentreview',
            name='rating',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='establishmentreview',
            name='comment',
            field=models.TextField(blank=True, max_length=1000),
        ),
    ]
