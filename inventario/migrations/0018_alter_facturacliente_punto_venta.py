# Generated by Django 4.2.16 on 2024-10-01 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0017_facturacliente_punto_venta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facturacliente',
            name='punto_venta',
            field=models.CharField(default='0001', max_length=5),
        ),
    ]
