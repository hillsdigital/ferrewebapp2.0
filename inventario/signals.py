from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import FacturaProducto, Stock, VentaProducto




from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Función para actualizar el stock después de guardar una línea de factura de proveedor


# Crear o actualizar el stock después de guardar una FacturaProducto
@receiver(post_save, sender=FacturaProducto)
def update_stock_on_factura_save(sender, instance, **kwargs):
    producto = instance.producto
    proveedor = instance.factura.orden_compra.proveedor
    cantidad = instance.cantidad
    precio_unitario = instance.precio_unitario

    # Buscar un registro existente de stock
    stock, created = Stock.objects.get_or_create(
        producto=producto,
        proveedor=proveedor,
        defaults={'cantidad': 0, 'precio_compra': precio_unitario}
    )

    # Actualizar la cantidad y el precio de compra en el stock
    stock.cantidad += cantidad  # Aumentar la cantidad
    stock.precio_compra = precio_unitario  # Actualizar el precio de compra
    stock.save()

# Disminuir el stock después de eliminar una FacturaProducto
@receiver(post_delete, sender=FacturaProducto)
def update_stock_on_factura_delete(sender, instance, **kwargs):
    producto = instance.producto
    proveedor = instance.factura.orden_compra.proveedor
    cantidad = instance.cantidad

    # Buscar el registro existente de stock
    try:
        stock = Stock.objects.get(producto=producto, proveedor=proveedor)
        stock.cantidad -= cantidad  # Disminuir la cantidad
        if stock.cantidad < 0:
            stock.cantidad = 0  # No permitir valores negativos

        stock.save()
    except Stock.DoesNotExist:
        # Manejar el caso donde el stock no existe
        pass




# ventas/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Factura, FacturaCliente

@receiver(post_save, sender=Factura)
def factura_post_save(sender, instance, created, **kwargs):
    if created:
        instance.enviar_afip()

@receiver(post_save, sender=FacturaCliente)
def factura_cliente_post_save(sender, instance, created, **kwargs):
    if created:
        instance.enviar_afip()
