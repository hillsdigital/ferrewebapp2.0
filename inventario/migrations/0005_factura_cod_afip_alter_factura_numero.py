# Generated by Django 4.2.16 on 2024-10-01 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0004_proveedor_alias_cuenta_bancaria_proveedor_celular_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='factura',
            name='cod_afip',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AlterField(
            model_name='factura',
            name='numero',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
