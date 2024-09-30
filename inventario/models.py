import datetime
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
import os


class Proveedor(models.Model):
    nombre = models.CharField(max_length=255)
    cuit = models.CharField(max_length=16)  # Campo para CUIT
    email = models.EmailField(max_length=255)  # Campo para email
    cbu = models.CharField(max_length=22, blank=True, null=True)  # Campo para CBU
    nombre_contacto = models.CharField(max_length=255, blank=True, null=True)  # Alias o nombre de contacto
    celular = models.CharField(max_length=15, blank=True, null=True)  # Número de celular
    alias_cuenta_bancaria = models.CharField(max_length=100, blank=True, null=True)  # Alias de la cuenta bancaria

    def __str__(self):
        return self.nombre
    
class Producto(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField()
    codigo = models.CharField(max_length=50, unique=True)
    foto = models.ImageField(upload_to='productos/', blank=True, null=True)  # Campo para la foto

    def __str__(self):
        return self.nombre

    def delete(self, *args, **kwargs):
        if self.foto:
            if os.path.isfile(self.foto.path):
                os.remove(self.foto.path)  # Eliminar la foto del sistema de archivos al eliminar el producto
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.nombre

class OrdenCompra(models.Model):
    fecha = models.DateField()
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    
    def __str__(self):
        return f'Orden {self.id} - {self.fecha}'

class OrdenCompraProducto(models.Model):
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()

class Factura(models.Model):
    TIPO_FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
        ('S', 'Sin Factura'),  # Nueva opción sin tratamiento de IVA
    ]
    
    numero = models.CharField(max_length=255)
    fecha = models.DateField()
    orden_compra = models.ForeignKey(OrdenCompra, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=1, choices=TIPO_FACTURA_CHOICES)
    
    def __str__(self):
        return f'Factura {self.numero} - {self.tipo} - {self.fecha}'


class FacturaProducto(models.Model):
    IVA_CHOICES = [
        (21, '21%'),
        (10.5, '10.5%'),
        (0, 'Sin IVA'),
    ]

    factura = models.ForeignKey(Factura, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=5, decimal_places=2, choices=IVA_CHOICES, default=21)  # IVA seleccionado
    precio_sin_iva = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_con_iva = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_iva = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Si el tipo de factura es 'A', calculamos con IVA
        if self.factura.tipo == 'A':
            self.precio_sin_iva = self.precio_unitario
            self.precio_con_iva = self.precio_unitario * (1 + self.iva / 100)
            self.total_iva = self.precio_con_iva - self.precio_sin_iva

        # Si es 'B', el precio con IVA ya está incluido
        elif self.factura.tipo == 'B':
            self.precio_con_iva = self.precio_unitario
            self.precio_sin_iva = self.precio_unitario / (1 + self.iva / 100)

        # Si es 'Sin Factura', no hay tratamiento de IVA
        elif self.factura.tipo == 'S':
            self.iva = 0
            self.precio_sin_iva = self.precio_unitario
            self.precio_con_iva = self.precio_unitario
            self.total_iva = 0
        
        super().save(*args, **kwargs)

    def calcular_total(self):
        """Devuelve el total del producto (cantidad * precio_con_iva)"""
        return self.cantidad * self.precio_con_iva



from django.db import models
class Stock(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    ultima_actualizacion = models.DateTimeField(auto_now=True)  # Fecha de actualización automática

    def __str__(self):
        return f'{self.producto.nombre} - {self.cantidad} unidades'

class StockDetalle(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()  # Cantidad de productos de este proveedor
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    ultima_actualizacion = models.DateTimeField(auto_now=True)  # Fecha de actualización automática

    def __str__(self):
        return f'{self.stock.producto.nombre} - {self.proveedor.nombre} - {self.cantidad} unidades - ${self.precio_compra}'

    class Meta:
        unique_together = ('stock', 'proveedor')  # Asegura que no haya duplicados



class Cliente(models.Model):
    nombre = models.CharField(max_length=255)
    direccion = models.TextField()
    telefono = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return self.nombre

    def actualizar_saldo(self, monto):
        """Ajusta el saldo del cliente aumentando el monto dado."""
        self.saldo += Decimal(monto)
        self.save()

    def registrar_pago(self, monto):
        """Registra un pago realizado por el cliente, descontando el monto dado."""
        if monto <= 0:
            raise ValueError("El monto del pago debe ser positivo.")
        self.saldo -= Decimal(monto)
        self.save()

    def actualizar_saldo_facturado(self, venta, monto_facturado):
            """
            Ajusta el saldo del cliente cuando se emite una factura para una venta específica,
            agregando el monto facturado (con impuestos) y actualizando la venta correspondiente.
            """
            if venta.es_a_cuenta:
                # Para ventas a cuenta, ajustamos el saldo del cliente
                saldo_actual_venta = venta.total
                diferencia = Decimal(monto_facturado) - saldo_actual_venta

                # Actualiza el saldo del cliente con la diferencia
                self.saldo += diferencia
                self.save()

                # Actualiza el total de la venta con el monto facturado
                venta.total = monto_facturado
                venta.save()
            else:
                # Para ventas no a cuenta, solo actualizamos el saldo de la venta
                venta.total = monto_facturado
                venta.save()

    def calcular_saldo_pendiente(self):
        """Calcula el saldo pendiente del cliente en función de las ventas no saldadas."""
        ventas_no_saldadas = Venta.objects.filter(cliente=self, pagada=False)
        saldo_pendiente = sum(venta.saldo_pendiente() for venta in ventas_no_saldadas)
        return saldo_pendiente

    def productos_comprados(self):
        """Devuelve un queryset con todos los productos comprados por el cliente"""
        ventas = Venta.objects.filter(cliente=self)
        productos = VentaProducto.objects.filter(venta__in=ventas).values('producto__nombre').annotate(total_cantidad=Sum('cantidad'))
        return productos

    def ventas_pendientes(self):
        """Devuelve un queryset con todas las ventas pendientes de pago del cliente"""
        ventas_pendientes = Venta.objects.filter(cliente=self, pagada=False)
        return ventas_pendientes

    def facturas_emitidas(self):
        """Devuelve un queryset con todas las facturas emitidas para el cliente"""
        facturas = FacturaCliente.objects.filter(venta__cliente=self)
        return facturas

    def pagos_realizados(self):
        """Devuelve un queryset con todos los pagos realizados a facturas del cliente"""
        pagos = PagoFactura.objects.filter(factura__venta__cliente=self)
        return pagos

class Venta(models.Model):
    cliente = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.CASCADE)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    metodo_pago_principal = models.ForeignKey('MetodoPago', null=True, blank=True, on_delete=models.SET_NULL)
    pagada = models.BooleanField(default=False)  # Indica si la venta está completamente pagada
    es_a_cuenta = models.BooleanField(default=False)  # Indica si la venta es a cuenta

    def __str__(self):
        return f'Venta {self.id} - {self.cliente.nombre} - {self.fecha}'

    def calcular_total(self):
        """Calcula el total de la venta sumando el precio por la cantidad de productos."""
        productos = self.ventaproducto_set.all()
        self.total = sum(item.cantidad * item.precio_unitario for item in productos)
        self.save()

    def registrar_pago(self, monto, metodo_pago):
        """Registra un pago para la venta y actualiza su estado y saldo pendiente."""
        if monto <= 0:
            raise ValueError("El monto del pago debe ser positivo.")
        
        saldo_pendiente = self.saldo_pendiente()

        if monto > saldo_pendiente:
            raise ValueError("El monto del pago no puede ser mayor que el saldo pendiente de la venta.")

        # Crear el registro de cobro
        CobroVenta.objects.create(
            venta=self,
            fecha_cobro=datetime.date.today(),  # O la fecha que desees
            metodo_pago=metodo_pago,
            monto=monto
        )

        # Actualizar el estado de la venta
        if monto >= saldo_pendiente:
            self.pagada = True

        self.save()

        # Actualizar el saldo del cliente solo si la venta es a cuenta
        if self.es_a_cuenta:
            self.cliente.registrar_pago(monto)

    def saldo_pendiente(self):
        """Calcula el saldo pendiente en función del total de la venta y los pagos registrados."""
        total_cobros = sum(cobro.monto for cobro in self.cobroventa_set.all())
        return self.total - total_cobros
        
class VentaProducto(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # IVA segregado

    def calcular_precio_con_iva(self):
        return self.precio_unitario + (self.precio_unitario * Decimal('0.21'))  # 21% IVA

    def __str__(self):
        return f'{self.producto.nombre} - {self.cantidad} unidades - {self.precio_unitario}'

class FacturaCliente(models.Model):
    TIPO_FACTURA_CHOICES = [
        ('A', 'Factura A'),
        ('B', 'Factura B'),
    ]
    
    venta = models.OneToOneField('Venta', on_delete=models.CASCADE)
    numero = models.CharField(max_length=255)
    fecha_emision = models.DateField(auto_now_add=True)
    tipo = models.CharField(max_length=1, choices=TIPO_FACTURA_CHOICES)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_sin_iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_con_iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f'Factura {self.numero} - {self.tipo} - {self.fecha_emision}'

    def calcular_totales(self):
        items = self.venta.ventaproducto_set.all()

        if self.tipo == 'A':
            # Factura A: Calcula IVA y subtotal
            self.precio_sin_iva = sum(item.cantidad * item.precio_unitario for item in items)
            self.total_iva = self.precio_sin_iva * Decimal('0.21')  # IVA del 21%
            self.precio_con_iva = self.precio_sin_iva + self.total_iva
            self.subtotal = self.precio_sin_iva
        elif self.tipo == 'B':
            # Factura B: Precio incluye el IVA, no se separa IVA
            self.precio_con_iva = sum(item.cantidad * (item.precio_unitario * Decimal('1.21')) for item in items)
            self.precio_sin_iva = 0  # No se muestra en Factura B
            self.total_iva = 0  # No se muestra en Factura B
            self.subtotal = self.precio_con_iva

        # Asignar total
        self.iva = self.total_iva
        self.total = self.precio_con_iva
        self.save()

        # Actualizar el saldo del cliente después de calcular la factura
        self.venta.cliente.actualizar_saldo_facturado(self.venta, self.total)
    def generar_mensaje_whatsapp(self):
        """Genera un mensaje de WhatsApp con los datos de la factura"""
        return f"Hola {self.venta.cliente.nombre}, te envío la factura {self.numero} por un total de {self.total}. Fecha de emisión: {self.fecha_emision}."

    def generar_mensaje_gmail(self):
        """Genera un mensaje para enviar por correo electrónico"""
        return f"Hola {self.venta.cliente.nombre},\n\nTe envío la factura #{self.numero} emitida el {self.fecha_emision} por un total de {self.total}.\n\nSaludos."




class MetodoPago(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

class PagoFactura(models.Model):
    factura = models.ForeignKey(FacturaCliente, on_delete=models.CASCADE)
    fecha_pago = models.DateField()
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.CASCADE)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Pago de {self.monto} a {self.factura.numero} - {self.metodo_pago.nombre} - {self.fecha_pago}'

class CobroVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    fecha_cobro = models.DateField()
    metodo_pago = models.ForeignKey('MetodoPago', on_delete=models.SET_NULL, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Cobro {self.id} - Venta {self.venta.id} - Monto {self.monto}'