# Generated by Django 4.2.16 on 2024-10-01 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0011_remove_facturacliente_punto_venta_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='facturacliente',
            name='punto_venta',
            field=models.CharField(default='0001', max_length=5),
        ),
        migrations.AlterField(
            model_name='facturacliente',
            name='numero',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
