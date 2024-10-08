# Generated by Django 4.2.16 on 2024-10-01 23:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0018_alter_facturacliente_punto_venta'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facturacliente',
            name='numero',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='facturacliente',
            unique_together={('numero', 'tipo', 'punto_venta')},
        ),
    ]
