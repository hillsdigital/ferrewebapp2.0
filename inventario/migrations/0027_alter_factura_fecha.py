# Generated by Django 4.2.16 on 2024-10-15 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0026_remove_facturaproducto_retencion_ingresos_brutos_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='factura',
            name='fecha',
            field=models.DateTimeField(),
        ),
    ]
