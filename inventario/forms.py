from django import forms
from .models import CobroVenta, MetodoPago, OrdenCompra, OrdenCompraProducto, Proveedor, Producto, Factura, FacturaProducto, Stock, StockDetalle
from .models import Cliente, Venta, VentaProducto, FacturaCliente
from django.forms import inlineformset_factory
from decimal import Decimal, ROUND_HALF_UP



class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'cuit', 'email', 'cbu', 'nombre_contacto', 'celular', 'alias_cuenta_bancaria']  # Incluimos el alias de la cuenta


class CargarArchivoForm(forms.Form):
    archivo = forms.FileField()

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['codigo', 'nombre', 'descripcion', 'foto']
from django import forms
from .models import OrdenCompra, OrdenCompraProducto, Producto

import datetime  # Importa el módulo para manejar fechas

class OrdenCompraForm(forms.ModelForm):
    class Meta:
        model = OrdenCompra
        fields = ['fecha', 'proveedor']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Iniciar la fecha con la fecha actual
        self.fields['fecha'].initial = datetime.date.today()


class OrdenCompraProductoForm(forms.ModelForm):
    class Meta:
        model = OrdenCompraProducto
        fields = ['producto', 'cantidad']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuramos el queryset para mostrar los nombres de los productos
        self.fields['producto'].queryset = Producto.objects.all()
        # Utilizamos label_from_instance para mostrar el nombre del producto
        self.fields['producto'].label_from_instance = lambda obj: obj.nombre
        # Aplicamos Select2 al campo de producto
        self.fields['producto'].widget.attrs.update({'class': 'select2'})

# Inlineformset para gestionar productos dentro de la orden de compra
OrdenCompraProductoFormSet = forms.inlineformset_factory(
    OrdenCompra,
    OrdenCompraProducto,
    form=OrdenCompraProductoForm,
    extra=1,
    can_delete=True
)

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['numero', 'fecha', 'tipo']  # Incluye el número y tipo
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'tipo': forms.Select(),  # Widget de selección para tipo de factura
            'numero': forms.TextInput(attrs={'readonly': False})  # Permitir que el número sea editable
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Iniciar la fecha con la fecha actual
        self.fields['fecha'].initial = datetime.date.today()

        
class FacturaProductoForm(forms.ModelForm):
    producto_nombre = forms.CharField(
        label='Producto',
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    precio_sin_iva = forms.DecimalField(
        label='Subtotal Sin IVA',
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        decimal_places=2,
        max_digits=10
    )
    precio_con_iva = forms.DecimalField(
        label='Subtotal Con IVA',
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        decimal_places=2,
        max_digits=10
    )
    total_iva = forms.DecimalField(
        label='Total IVA',
        widget=forms.TextInput(attrs={'readonly': 'readonly'}),
        decimal_places=2,
        max_digits=10
    )
    iva = forms.ChoiceField(
        label='IVA (%)',
        choices=[(21, '21%'), (10.5, '10.5%'), (0, 'Sin IVA')],
        widget=forms.Select()
    )

    class Meta:
        model = FacturaProducto
        fields = ['producto', 'cantidad', 'precio_unitario', 'iva']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1'}),
            'precio_unitario': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        producto = kwargs.pop('producto', None)
        factura = kwargs.pop('factura', None)
        super().__init__(*args, **kwargs)

        if producto and factura:
            self.fields['producto'].widget = forms.HiddenInput()
            self.fields['producto_nombre'].initial = producto.nombre
            self.fields['producto'].initial = producto
            cantidad = self.initial.get('cantidad', 1)

            # Cálculo dependiendo del tipo de factura
            if factura.tipo == 'A':
                subtotal_sin_iva = producto.precio_unitario * cantidad
                subtotal_con_iva = subtotal_sin_iva * (1 + float(self.fields['iva'].initial) / 100)
                total_iva = subtotal_con_iva - subtotal_sin_iva
                self.fields['precio_sin_iva'].initial = subtotal_sin_iva
                self.fields['precio_con_iva'].initial = subtotal_con_iva
                self.fields['total_iva'].initial = total_iva

            elif factura.tipo == 'B':
                subtotal_con_iva = producto.precio_unitario * cantidad
                subtotal_sin_iva = subtotal_con_iva / (1 + float(self.fields['iva'].initial) / 100)
                self.fields['precio_con_iva'].initial = subtotal_con_iva
                self.fields['precio_sin_iva'].initial = subtotal_sin_iva

            elif factura.tipo == 'S':
                self.fields['iva'].initial = 0
                self.fields['iva'].widget = forms.HiddenInput()  # Ocultar el campo IVA
                self.fields['precio_sin_iva'].widget = forms.HiddenInput()
                self.fields['precio_con_iva'].widget = forms.HiddenInput()
                self.fields['total_iva'].widget = forms.HiddenInput()


FacturaProductoFormSet = forms.inlineformset_factory(
    Factura,
    FacturaProducto,
    form=FacturaProductoForm,
    extra=0,
    can_delete=True
)

class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['producto', 'cantidad']

class StockDetalleForm(forms.ModelForm):
    class Meta:
        model = StockDetalle
        fields = ['stock', 'proveedor', 'precio_compra']




class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nombre', 'direccion', 'telefono', 'email', 'cuit']

class VentaForm(forms.ModelForm):
    metodo_pago_principal = forms.ModelChoiceField(
        queryset=MetodoPago.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'metodo-pago-select'})
    )

    class Meta:
        model = Venta
        fields = ['cliente', 'fecha', 'metodo_pago_principal']
        widgets = {     
            'fecha': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Iniciar la fecha con la fecha actual
        self.fields['fecha'].initial = datetime.date.today()

    def clean_cliente(self):
        cliente = self.cleaned_data.get('cliente')
        metodo_pago_principal = self.cleaned_data.get('metodo_pago_principal')

        if metodo_pago_principal and metodo_pago_principal.nombre.lower() == 'a cuenta' and not cliente:
            raise forms.ValidationError("El cliente es obligatorio para ventas a cuenta.")
        return cliente



class VentaProductoForm(forms.ModelForm):
    proveedor = forms.ModelChoiceField(
        queryset=Proveedor.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'proveedor-select'})
    )
    cantidad = forms.IntegerField(required=True)
    precio_unitario = forms.DecimalField(
        required=False,
        disabled=True,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'readonly': 'readonly'})
    )

    class Meta:
        model = VentaProducto
        fields = ['producto', 'cantidad', 'proveedor', 'precio_unitario']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['producto'].queryset = Producto.objects.filter(stock__cantidad__gt=0).distinct()
        self.fields['producto'].label_from_instance = self.get_producto_label

    def get_producto_label(self, obj):
        stock = obj.stock_set.first()
        cantidad = stock.cantidad if stock else '0'
        return f'{obj.nombre} - {cantidad} unidades'

    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        proveedor = cleaned_data.get('proveedor')
        cantidad_solicitada = cleaned_data.get('cantidad')

        if producto and proveedor:
            try:
                # Obtener el detalle de stock para el producto y proveedor seleccionado
                stock_detalle = StockDetalle.objects.get(
                    stock__producto=producto,
                    proveedor=proveedor
                )
                cantidad_disponible = stock_detalle.cantidad
                
                # Verificar si la cantidad solicitada excede la cantidad disponible
                if cantidad_solicitada > cantidad_disponible:
                    self.add_error('cantidad', f'No puedes vender más de {cantidad_disponible} unidades de este producto para el proveedor seleccionado.')

                # Calcular y asignar el precio de venta
                precio_compra = stock_detalle.precio_compra
                precio_venta = precio_compra * Decimal('1.30')
                cleaned_data['precio_unitario'] = precio_venta.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
            except StockDetalle.DoesNotExist:
                cleaned_data['precio_unitario'] = Decimal('0.00')
                self.add_error('proveedor', 'El proveedor seleccionado no tiene un precio de compra registrado para el producto.')
        return cleaned_data


VentaProductoFormset = inlineformset_factory(
    Venta,
    VentaProducto,
    form=VentaProductoForm,
    extra=1,
    can_delete=True
)

from django import forms
from .models import FacturaCliente

class FacturaClienteForm(forms.ModelForm):
    class Meta:
        model = FacturaCliente
        fields = ['tipo', 'numero', 'punto_venta']
        widgets = {
            'tipo': forms.Select(choices=FacturaCliente.TIPO_FACTURA_CHOICES),
            'numero': forms.TextInput(attrs={'readonly': 'readonly'}),  # Hacer 'numero' de solo lectura
            'punto_venta': forms.TextInput(attrs={'readonly': 'readonly'}),  # Opcional: hacer 'punto_venta' de solo lectura
        }

    def save(self, commit=True):
        factura = super().save(commit=False)
        factura.calcular_totales()  # Asegúrate de que este método esté definido en tu modelo.
        if commit:
            factura.save()
        return factura


from django import forms
from .models import CobroVenta

class CobroForm(forms.ModelForm):
    class Meta:
        model = CobroVenta
        fields = ['metodo_pago', 'monto']

    def __init__(self, *args, **kwargs):
        self.venta = kwargs.pop('venta', None)
        super().__init__(*args, **kwargs)
        if self.venta:
            # Cambia la etiqueta del monto para incluir el saldo pendiente
            self.fields['monto'].label = f'Monto (Saldo pendiente: {self.venta.saldo_pendiente()})'
            # Asigna el saldo pendiente como valor inicial del campo monto
            self.fields['monto'].initial = self.venta.saldo_pendiente()

class MetodoPagoForm(forms.ModelForm):
    class Meta:
        model = MetodoPago
        fields = ['nombre']
class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['producto', 'cantidad']

class StockDetalleForm(forms.ModelForm):
    class Meta:
        model = StockDetalle
        fields = ['proveedor', 'precio_compra']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configuración adicional si es necesaria
