from django.db import migrations


def title_case_name(value):
    parts = ' '.join((value or '').split()).split()
    return ' '.join(part[:1].upper() + part[1:].lower() for part in parts)


def capitalize_existing_product_names(apps, schema_editor):
    Product = apps.get_model('vendor', 'Product')
    for product in Product.objects.all().iterator():
        new_name = title_case_name(product.name)
        if new_name != product.name:
            product.name = new_name
            product.save(update_fields=['name'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0005_establishment_suspended_for_admin_role'),
    ]

    operations = [
        migrations.RunPython(capitalize_existing_product_names, noop_reverse),
    ]
