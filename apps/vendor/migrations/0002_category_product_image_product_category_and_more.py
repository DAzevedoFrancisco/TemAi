from django.db import migrations, models
import apps.vendor.models
import django.db.models.deletion


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('vendor', 'Category')
    categories = [
        ('Alimentação', 'alimentacao'),
        ('Bebidas', 'bebidas'),
        ('Vestuário', 'vestuario'),
        ('Eletrónica', 'eletronica'),
        ('Serviços', 'servicos'),
        ('Saúde e Beleza', 'saude-beleza'),
        ('Casa e Decoração', 'casa-decoracao'),
        ('Outros', 'outros'),
    ]
    for name, slug in categories:
        Category.objects.get_or_create(name=name, defaults={'slug': slug})


def assign_default_category(apps, schema_editor):
    Product = apps.get_model('vendor', 'Product')
    Category = apps.get_model('vendor', 'Category')
    default_category = Category.objects.first()
    if default_category:
        Product.objects.filter(category__isnull=True).update(category=default_category)


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'db_table': 'category',
                'ordering': ['name'],
            },
        ),
        migrations.RunPython(create_default_categories, migrations.RunPython.noop),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='products',
                to='vendor.category',
            ),
        ),
        migrations.RunPython(assign_default_category, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='products',
                to='vendor.category',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=apps.vendor.models.product_image_path,
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(),
        ),
        migrations.RemoveField(
            model_name='product',
            name='price',
        ),
    ]
