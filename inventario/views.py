import datetime
from django import forms
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DeleteView, TemplateView
from .models import CobroVenta, FacturaProducto, MetodoPago, OrdenCompraProducto, PagoFactura, Proveedor, Producto, OrdenCompra, Factura, Stock, StockDetalle, VentaProducto
from .forms import CobroForm, FacturaProductoForm, MetodoPagoForm, OrdenCompraProductoFormSet, ProveedorForm, ProductoForm, OrdenCompraForm, FacturaForm, FacturaProductoFormSet, StockDetalleForm, StockForm, VentaProductoForm
import logging
from django.forms import modelformset_factory
from .forms import ClienteForm
from .models import Cliente
from django.shortcuts import render, redirect, get_object_or_404
from .forms import VentaForm, VentaProductoFormset, FacturaClienteForm
from .models import Venta, FacturaCliente
from django.contrib import messages
import pandas as pd
import os
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.files.storage import default_storage
from .forms import CargarArchivoForm, ProductoForm
from .models import Producto
from django.views.generic.detail import DetailView

from django.shortcuts import render
from .models import Factura, Venta
from decimal import Decimal
from django.db.models import Sum

class HomePageView(TemplateView):
    template_name = 'base.html'

class ProveedorCreateView(CreateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'
    success_url = reverse_lazy('proveedor_list')

class ProveedorUpdateView(UpdateView):
    model = Proveedor
    form_class = ProveedorForm
    template_name = 'proveedor_form.html'
    success_url = reverse_lazy('proveedor_list')

class ProveedorListView(ListView):
    model = Proveedor
    template_name = 'proveedor_list.html'
    context_object_name = 'proveedores'


# producto
HEADER_MAP = {
    'CODIGO': ['CODIGO', 'CÓDIGO', 'Código', 'COD'],
    'PRODUCTO': ['PRODUCTO', 'DESCRIPCION', 'DESCRIPCION', 'Producto'],
    'DESCRIPCION': ['DESCRIPCION', 'Descripción', 'DESC'],
}

def normalize_header(header):
    for key, variations in HEADER_MAP.items():
        if header in variations:
            return key
    return header

def process_excel(file_path):
    try:
        df = pd.read_excel(file_path, header=None)
        candidate_row = 2
        df.columns = df.iloc[candidate_row]
        df = df[candidate_row + 1:]
        df.columns = [normalize_header(col) for col in df.columns]
        df.dropna(how='all', inplace=True)
        df.fillna('', inplace=True)
        return None, df
    except Exception as e:
        return f"Ocurrió un error: {str(e)}", None

def almacenar_datos_en_modelo(df):
    for _, row in df.iterrows():
        try:
            codigo = row.get('CODIGO', 'No disponible')
            producto, creado = Producto.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'nombre': row.get('PRODUCTO', ''),
                    'descripcion': row.get('DESCRIPCION', ''),
                }
            )
        except Exception as e:
            print(f"Error al almacenar el producto {row.get('CODIGO', 'No disponible')}: {str(e)}")

def cargar_archivo(request):
    if request.method == 'POST':
        form = CargarArchivoForm(request.POST, request.FILES)
        if form.is_valid():
            archivo = request.FILES['archivo']
            archivo_path = default_storage.save(archivo.name, archivo)
            archivo_full_path = default_storage.path(archivo_path)

            error, df = process_excel(archivo_full_path)

            if error:
                return HttpResponse(error)

            if df.empty:
                return HttpResponse("El DataFrame está vacío después del procesamiento.")

            almacenar_datos_en_modelo(df)

            os.remove(archivo_full_path)

            return HttpResponse("Datos procesados y almacenados exitosamente.")
    else:
        form = CargarArchivoForm()

    return render(request, 'cargar_archivo.html', {'form': form})

def lista_productos(request):
    productos = Producto.objects.all()
    return render(request, 'lista_productos.html', {'productos': productos})

class ProductoCreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')

class ProductoUpdateView(UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'producto_form.html'
    success_url = reverse_lazy('producto_list')

    def form_valid(self, form):
        producto = form.save(commit=False)
        if 'foto' in form.changed_data:  # Verifica si se ha cambiado la foto
            old_foto = self.get_object().foto
            if old_foto:
                if os.path.isfile(old_foto.path):
                    os.remove(old_foto.path)  # Elimina la foto anterior del sistema de archivos
        producto.save()
        return super().form_valid(form)

class ProductoListView(ListView):
    model = Producto
    template_name = 'producto_list.html'
    context_object_name = 'productos'

class OrdenCompraListView(ListView):
    model = OrdenCompra
    template_name = 'orden_compra_list.html'
    context_object_name = 'ordenes_compra'

    def get_queryset(self):
        return OrdenCompra.objects.all().order_by('-fecha')  # Ordena por la fecha más reciente primero


class OrdenCompraCreateView(CreateView):
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'orden_compra_form.html'
    success_url = reverse_lazy('orden_compra_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['productos_formset'] = OrdenCompraProductoFormSet(self.request.POST, prefix='productos')
        else:
            context['productos_formset'] = OrdenCompraProductoFormSet(prefix='productos')
        context['productos'] = Producto.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        context = self.get_context_data()
        productos_formset = context['productos_formset']

        if productos_formset.is_valid():
            productos_formset.instance = self.object
            productos_formset.save()
        
        return response


class OrdenCompraUpdateView(UpdateView):
    model = OrdenCompra
    form_class = OrdenCompraForm
    template_name = 'orden_compra_form.html'
    success_url = reverse_lazy('orden_compra_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        orden_compra = self.object
        if self.request.POST:
            context['productos_formset'] = OrdenCompraProductoFormSet(self.request.POST, instance=orden_compra, prefix='productos')
        else:
            context['productos_formset'] = OrdenCompraProductoFormSet(instance=orden_compra, prefix='productos')
        context['productos'] = Producto.objects.all()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        productos_formset = context['productos_formset']
        if productos_formset.is_valid():
            response = super().form_valid(form)
            productos_formset.instance = self.object
            productos_formset.save()
            return response
        return self.form_invalid(form)


class OrdenCompraDeleteView(DeleteView):
    model = OrdenCompra
    template_name = 'orden_compra_confirm_delete.html'
    success_url = reverse_lazy('orden_compra_list')


from django.http import JsonResponse
from .models import Factura

def obtener_proximo_numero_factura(request):
    tipo = request.GET.get('tipo')
    punto_venta = '0001'  # Puedes hacerlo dinámico si es necesario

    # Obtener la última factura de este tipo y punto de venta
    ultima_factura = Factura.objects.filter(punto_venta=punto_venta, tipo=tipo).order_by('-id').first()

    if ultima_factura:
        ultimo_numero = int(ultima_factura.numero.split('-')[-1]) + 1
    else:
        ultimo_numero = 1

    numero_factura = f"{punto_venta}-{tipo}-{ultimo_numero:08d}"
    return JsonResponse({'numero_factura': numero_factura})


def factura_create(request, orden_compra_id):
    orden_compra = get_object_or_404(OrdenCompra, id=orden_compra_id)
    
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        if form.is_valid():
            factura = form.save(commit=False)
            factura.orden_compra = orden_compra
            factura.save()
            return redirect('factura_producto_create', factura_id=factura.id)  # Redirige a la creación de productos para esta factura
    else:
        form = FacturaForm()
    
    return render(request, 'factura_form.html', {'form': form, 'orden_compra': orden_compra})

def factura_producto_create(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    orden_compra = factura.orden_compra

    if request.method == 'POST':
        orden_compra_productos = OrdenCompraProducto.objects.filter(orden_compra=orden_compra)

        for oc_producto in orden_compra_productos:
            producto = oc_producto.producto
            try:
                cantidad = int(request.POST.get(f'cantidad_{producto.id}', 0))
                precio_unitario = float(request.POST.get(f'precio_unitario_{producto.id}', 0))
                iva = float(request.POST.get(f'iva_{producto.id}', 21))  # Tomar el valor de IVA del formulario
            except ValueError:
                continue  # Ignorar si hay un error en los datos

            if cantidad > 0 and precio_unitario > 0:
                # Crear el producto de la factura
                factura_producto = FacturaProducto(
                    factura=factura,
                    producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio_unitario,
                    iva=iva
                )
                factura_producto.save()

                # Actualizar o crear el stock
                stock, created = Stock.objects.get_or_create(
                    producto=producto,
                    defaults={'cantidad': 0}
                )
                stock.cantidad += cantidad
                stock.save()

                # Actualiza o crea el StockDetalle
                stock_detalle, created = StockDetalle.objects.get_or_create(
                    stock=stock,
                    proveedor=orden_compra.proveedor,
                    defaults={'precio_compra': precio_unitario, 'cantidad': 0}  # Asegúrate de inicializar 'cantidad'
                )
                
                # Actualizar cantidad y precio en StockDetalle
                stock_detalle.cantidad += cantidad  # Sumar la cantidad
                stock_detalle.precio_compra = precio_unitario  # Actualiza el precio
                stock_detalle.save()

        return redirect('factura_detail', factura_id=factura.id)

    else:
        orden_compra_productos = OrdenCompraProducto.objects.filter(orden_compra=orden_compra)

    return render(request, 'factura_productos_form.html', {
        'factura': factura,
        'orden_compra_productos': orden_compra_productos
    })


def factura_detail(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    productos = FacturaProducto.objects.filter(factura=factura)
    
    total = sum(p.calcular_total() for p in productos)

    return render(request, 'factura_detail.html', {
        'factura': factura,
        'productos': productos,
        'total': total
    })
# Usamos formset para manejar los productos de la factura
FacturaProductoFormSet = modelformset_factory(FacturaProducto, form=FacturaProductoForm, extra=0, can_delete=True)

# Vista para actualizar una factura existente
def factura_update(request, factura_id):
    factura = get_object_or_404(Factura, id=factura_id)
    formset = FacturaProductoFormSet(queryset=FacturaProducto.objects.filter(factura=factura))

    if request.method == 'POST':
        formset = FacturaProductoFormSet(request.POST, request.FILES, queryset=FacturaProducto.objects.filter(factura=factura))
        
        if formset.is_valid():
            # Obtener el conjunto de instancias antes de los cambios
            old_instances = list(FacturaProducto.objects.filter(factura=factura))

            # Guardar los cambios en los productos de la factura
            instances = formset.save(commit=False)
            for instance in instances:
                # Ajustar el stock antes de guardar cambios
                old_instance = next((x for x in old_instances if x.id == instance.id), None)
                
                if old_instance:
                    # Calcular la diferencia en cantidad y ajustar el stock
                    diferencia_cantidad = instance.cantidad - old_instance.cantidad
                    stock_item = Stock.objects.get(producto=instance.producto, proveedor=factura.orden_compra.proveedor)
                    stock_item.cantidad += diferencia_cantidad
                    stock_item.save()
                else:
                    # Nuevo producto agregado a la factura
                    stock_item = Stock.objects.get_or_create(producto=instance.producto, proveedor=factura.orden_compra.proveedor, defaults={'cantidad': 0, 'precio_compra': instance.precio_unitario})[0]
                    stock_item.cantidad += instance.cantidad
                    stock_item.save()

                instance.save()

            # Eliminar productos que fueron eliminados en el formset
            for old_instance in old_instances:
                if old_instance not in instances:
                    stock_item = Stock.objects.get(producto=old_instance.producto, proveedor=factura.orden_compra.proveedor)
                    stock_item.cantidad -= old_instance.cantidad
                    if stock_item.cantidad < 0:
                        stock_item.cantidad = 0
                    stock_item.save()
                    old_instance.delete()

            return redirect('factura_detail', factura_id=factura.id)
    else:
        formset = FacturaProductoFormSet(queryset=FacturaProducto.objects.filter(factura=factura))

    context = {
        'formset': formset,
        'factura': factura
    }
    return render(request, 'factura_productos_form.html', context)


class FacturaListView(ListView):
    model = Factura
    template_name = 'factura_list.html'
    context_object_name = 'facturas'

    def get_queryset(self):
        facturas = Factura.objects.select_related('orden_compra__proveedor').prefetch_related('facturaproducto_set__producto')

        # Calcular el total general para cada factura
        for factura in facturas:
            total_general = 0
            for producto in factura.facturaproducto_set.all():
                producto.total = producto.calcular_total()  # Usa el método calcular_total del modelo
                total_general += producto.total
            factura.total_general = total_general
        
        return facturas
class StockCreateView(CreateView):
    model = Stock
    form_class = StockForm
    template_name = 'stock_form.html'
    success_url = reverse_lazy('stock_list')

class StockUpdateView(UpdateView):
    model = Stock
    form_class = StockForm
    template_name = 'stock_form.html'
    success_url = reverse_lazy('stock_list')

class StockListView(ListView):
    model = Stock
    template_name = 'stock_list.html'
    context_object_name = 'stocks'

    def get_queryset(self):
        # Obtén todos los stocks y los detalles de stock relacionados
        stocks = Stock.objects.prefetch_related('stockdetalle_set')
        return stocks


def cliente_list(request):
    clientes = Cliente.objects.all()
    return render(request, 'cliente_list.html', {'clientes': clientes})

def cliente_create(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('cliente_list')
    else:
        form = ClienteForm()
    return render(request, 'cliente_form.html', {'form': form})

class ClienteDetailView(DetailView):
    model = Cliente
    template_name = 'cliente_detail.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = self.object

        # Añadimos los datos adicionales al contexto
        context['productos_comprados'] = cliente.productos_comprados()
        context['ventas_pendientes'] = cliente.ventas_pendientes()
        context['facturas_emitidas'] = cliente.facturas_emitidas()
        context['pagos_realizados'] = cliente.pagos_realizados()
        return context


def cliente_update(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('cliente_list')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'cliente_form.html', {'form': form})

def cliente_delete(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('cliente_list')
    return render(request, 'cliente_confirm_delete.html', {'cliente': cliente})

def venta_list(request):
    ventas = Venta.objects.all().order_by('-fecha')  # Ordena por fecha descendente
    return render(request, 'venta_list.html', {'ventas': ventas})



import logging

logger = logging.getLogger(__name__)
from django.http import JsonResponse



def get_proveedores(request):
    producto_id = request.GET.get('producto_id')
    proveedores = []
    
    if producto_id:
        # Filtrar detalles de stock según el producto
        stock_detalles = StockDetalle.objects.filter(
            stock__producto_id=producto_id
        ).select_related('proveedor')
        
        for detalle in stock_detalles:
            proveedores.append({
                'id': detalle.proveedor.id,
                'nombre': detalle.proveedor.nombre,
                'precio_compra': detalle.precio_compra,
                'cantidad': detalle.cantidad
            })
    return JsonResponse(proveedores, safe=False)



from django.http import JsonResponse
from .models import StockDetalle

def get_precio_compra(request):
    proveedor_id = request.GET.get('proveedor_id')
    producto_id = request.GET.get('producto_id')
    response_data = {'precio_compra': None}

    if proveedor_id and producto_id:
        try:
            stock_detalle = StockDetalle.objects.get(
                proveedor_id=proveedor_id,
                stock__producto_id=producto_id
            )
            response_data['precio_compra'] = stock_detalle.precio_compra
        except StockDetalle.DoesNotExist:
            response_data['precio_compra'] = None

    return JsonResponse(response_data)
from django.forms import formset_factory

def seleccionar_producto_proveedor(request):
    stocks = Stock.objects.all()
    return render(request, 'tu_template.html', {'stocks': stocks})

from django.db import transaction

def crear_venta(request):
    VentaProductoFormset = formset_factory(VentaProductoForm, extra=1)

    if request.method == 'POST':
        venta_form = VentaForm(request.POST)
        productos_formset = VentaProductoFormset(request.POST)

        if venta_form.is_valid() and productos_formset.is_valid():
            venta = venta_form.save(commit=False)
            metodo_pago = venta_form.cleaned_data.get('metodo_pago_principal')

            if metodo_pago and metodo_pago.nombre.lower() == 'a cuenta':
                venta.es_a_cuenta = True
            else:
                venta.es_a_cuenta = False

            errors = False

            try:
                with transaction.atomic():
                    venta.save()

                    for form in productos_formset:
                        if form.cleaned_data:
                            producto = form.cleaned_data.get('producto')
                            cantidad = form.cleaned_data.get('cantidad')
                            proveedor = form.cleaned_data.get('proveedor')
                            precio_unitario = form.cleaned_data.get('precio_unitario')

                            # Obtener stock global y stock del proveedor
                            stock_detalle = StockDetalle.objects.get(
                                stock__producto=producto,
                                proveedor=proveedor
                            )
                            stock = stock_detalle.stock

                            # Verificar si hay suficiente cantidad en el stock del proveedor
                            if stock_detalle.cantidad >= cantidad:
                                # Descontar del stock del proveedor
                                stock_detalle.cantidad -= cantidad
                                stock_detalle.save()

                                # Descontar del stock global
                                if stock.cantidad >= cantidad:
                                    stock.cantidad -= cantidad
                                    stock.save()
                                else:
                                    errors = True
                                    form.add_error(None, 'No hay suficiente stock global disponible para el producto.')
                            else:
                                errors = True
                                form.add_error(None, 'No hay suficiente stock disponible para este proveedor.')

                            # Si no hay errores, crear el registro de la venta
                            if not errors:
                                VentaProducto.objects.create(
                                    venta=venta,
                                    producto=producto,
                                    cantidad=cantidad,
                                    proveedor=proveedor,
                                    precio_unitario=precio_unitario
                                )
                            else:
                                raise ValueError("Stock insuficiente.")

            except Exception as e:
                # Si ocurre un error, eliminar la venta y revertir transacciones
                venta.delete()
                return render(request, 'crear_venta.html', {
                    'venta_form': venta_form,
                    'productos_formset': productos_formset,
                    'error': str(e)
                })

            if not errors:
                # Calcular el total de la venta
                venta.calcular_total()

                # Si es a cuenta, actualizar el saldo del cliente
                if venta.es_a_cuenta:
                    cliente = venta.cliente
                    cliente.actualizar_saldo(venta.total)

                return redirect('venta_list')

        else:
            print("VentaForm errores:", venta_form.errors)
            print("ProductosFormset errores:", productos_formset.errors)
    else:
        venta_form = VentaForm()
        productos_formset = VentaProductoFormset()

    return render(request, 'crear_venta.html', {
        'venta_form': venta_form,
        'productos_formset': productos_formset,
    })



def venta_detail(request, id):
    venta = get_object_or_404(Venta, id=id)
    productos = VentaProducto.objects.filter(venta=venta)
    
    # Verificar si la venta tiene cliente
    if venta.cliente:
        saldo_cliente = venta.cliente.saldo  # Obtener el saldo del cliente
    else:
        saldo_cliente = None  # No hay saldo si no hay cliente

    return render(request, 'venta_detail.html', {
        'venta': venta,
        'productos': productos,
        'saldo_cliente': saldo_cliente  # Pasar el saldo del cliente al template
    })
def obtener_numero_factura(request):
    tipo = request.GET.get('tipo')
    punto_venta = '0001'  # O el valor que corresponda
    nueva_factura = FacturaCliente(tipo=tipo, punto_venta=punto_venta)
    nuevo_numero = nueva_factura.generar_numero_factura()

    return JsonResponse({'numero': nuevo_numero})
class FacturaVentaView(UpdateView):
    model = Venta
    form_class = FacturaClienteForm
    template_name = 'factura_venta_form.html'
    success_url = reverse_lazy('venta_list')

    def get(self, request, *args, **kwargs):
        venta = self.get_object()

        if not venta.cliente:
            messages.error(request, "No se puede emitir factura para una venta sin cliente.")
            return redirect('venta_list')

        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        venta = self.get_object()

        if not hasattr(venta, 'facturacliente'):
            factura_cliente = FacturaCliente.objects.create(
                venta=venta,
                tipo='A',  # Establece el tipo de factura por defecto, cambia a 'B' si es necesario
                punto_venta='0001'  # Valor por defecto para el punto de venta
            )
        else:
            factura_cliente = venta.facturacliente

        factura_cliente.calcular_totales()
        
        kwargs['instance'] = factura_cliente
        return kwargs

    def form_valid(self, form):
        response = super().form_valid(form)
        factura_cliente = form.instance
        factura_cliente.calcular_totales()
        factura_cliente.save()
        return response



    
class FacturaEmitidaListView(ListView):
    model = FacturaCliente
    template_name = 'factura_emitida_list.html'
    context_object_name = 'facturas_emitidas'

class FacturaVentaDetailView(DetailView):
    model = FacturaCliente  # Modelo FacturaCliente
    template_name = 'factura_venta_detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        factura = self.get_object()
        
        # Accede a los productos de la venta asociada a la factura
        productos = factura.venta.ventaproducto_set.all()
        
        # Añadir los productos al contexto
        context['productos'] = productos
        
        # Añadir información de la factura y sus totales
        context['subtotal'] = factura.subtotal
        context['iva'] = factura.iva
        context['total'] = factura.total
        context['precio_sin_iva'] = factura.precio_sin_iva
        context['precio_con_iva'] = factura.precio_con_iva
        context['total_iva'] = factura.total_iva
        
        return context



class StockUpdateView(UpdateView):
    model = Stock
    form_class = StockForm
    template_name = 'stock_form.html'
    success_url = reverse_lazy('stock_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        StockDetalleFormSet = inlineformset_factory(Stock, StockDetalle, form=StockDetalleForm, extra=0)  # extra=0 para no agregar formularios en blanco
        if self.request.POST:
            data['stock_detalle_forms'] = StockDetalleFormSet(self.request.POST, instance=self.object)
        else:
            data['stock_detalle_forms'] = StockDetalleFormSet(instance=self.object)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        stock_detalle_forms = context['stock_detalle_forms']
        if stock_detalle_forms.is_valid():
            response = super().form_valid(form)
            stock_detalle_forms.instance = self.object
            stock_detalle_forms.save()
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))
        

class MetodoPagoCreateView(CreateView):
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodo_pago_form.html'
    success_url = reverse_lazy('metodo_pago_list')  # Redirige a una lista de métodos de pago después de la creación

    def form_valid(self, form):
        return super().form_valid(form)        
class MetodoPagoListView(ListView):
    model = MetodoPago
    template_name = 'metodo_pago_list.html'
    context_object_name = 'metodos_pago'    





def registrar_cobro(request, venta_id):
    venta = Venta.objects.get(id=venta_id)
    saldo_pendiente = venta.saldo_pendiente()

    if request.method == 'POST':
        cobro_form = CobroForm(request.POST, venta=venta)
        if cobro_form.is_valid():
            monto = cobro_form.cleaned_data['monto']
            metodo_pago = cobro_form.cleaned_data['metodo_pago']

            if monto > saldo_pendiente:
                cobro_form.add_error('monto', 'El monto no puede ser mayor que el saldo pendiente.')
            else:
                venta.registrar_pago(monto, metodo_pago)
                return redirect('venta_list')  # Redirigir a la lista de ventas
    else:
        # Inicializa el formulario con el saldo pendiente como sugerencia
        cobro_form = CobroForm(venta=venta)

    return render(request, 'registrar_cobro.html', {
        'cobro_form': cobro_form,
        'monto_total': venta.total,
        'saldo_pendiente': saldo_pendiente,
        'mostrar_boton': saldo_pendiente > 0,  # Mostrar botón solo si hay saldo pendiente
    })

from django.db.models import Sum, F, ExpressionWrapper, DecimalField

class ReporteFinanciero:
    @staticmethod
    def generar_reporte(fecha_inicio, fecha_fin):
        # 1. Ventas dentro del período
        ventas = Venta.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        total_ventas = ventas.aggregate(total=Sum('facturacliente__total'))['total'] or 0
        iva_ventas = ventas.aggregate(total_iva=Sum('facturacliente__total_iva'))['total_iva'] or 0

        # 2. Pagos recibidos dentro del período
        cobros = CobroVenta.objects.filter(fecha_cobro__range=[fecha_inicio, fecha_fin])
        total_cobros = cobros.aggregate(total=Sum('monto'))['total'] or 0

        # 3. Facturas emitidas dentro del período
        facturas = FacturaCliente.objects.filter(fecha_emision__range=[fecha_inicio, fecha_fin])
        total_facturas = facturas.aggregate(total=Sum('total'))['total'] or 0
        iva_facturas = facturas.aggregate(total_iva=Sum('total_iva'))['total_iva'] or 0

        # 4. Compras realizadas dentro del período
        compras = OrdenCompra.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        productos_comprados = FacturaProducto.objects.filter(factura__orden_compra__in=compras)
        total_compras = productos_comprados.aggregate(total=Sum(ExpressionWrapper(F('cantidad') * F('precio_con_iva'), output_field=DecimalField())))['total'] or 0

        # 5. Facturas de compras emitidas dentro del período
        facturas_compras = Factura.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
        iva_compras = FacturaProducto.objects.filter(factura__in=facturas_compras).aggregate(total_iva=Sum('total_iva'))['total_iva'] or 0

        # 6. Pagos a proveedores dentro del período
        pagos_proveedores = PagoFactura.objects.filter(fecha_pago__range=[fecha_inicio, fecha_fin])
        total_pagos_proveedores = pagos_proveedores.aggregate(total=Sum('monto'))['total'] or 0

        # 7. Generación del reporte financiero
        reporte = {
            'total_ventas': total_ventas,
            'iva_ventas': iva_ventas,
            'total_cobros': total_cobros,
            'total_facturas': total_facturas,
            'iva_facturas': iva_facturas,
            'total_compras': total_compras,
            'iva_compras': iva_compras,
            'total_pagos_proveedores': total_pagos_proveedores,
            'saldo_final': total_ventas - total_compras - total_pagos_proveedores + total_cobros,
        }

        return reporte


# Ejemplo de uso
fecha_inicio = datetime.date(2024, 1, 1)
fecha_fin = datetime.date(2024, 9, 18)
reporte = ReporteFinanciero.generar_reporte(fecha_inicio, fecha_fin)

for key, value in reporte.items():
    print(f'{key}: {value}')

def reporte_financiero_view(request):
    fecha_inicio = datetime.date(2024, 1, 1)
    fecha_fin = datetime.date(2024, 9, 18)
    reporte = ReporteFinanciero.generar_reporte(fecha_inicio, fecha_fin)

    return render(request, 'reporte_financiero.html', {'reporte': reporte})


def flujo_de_caja(request):
    # Cobros de Ventas
    cobros_ventas = CobroVenta.objects.aggregate(total_cobros=Sum('monto'))['total_cobros'] or 0

    # Pagos de Compras
    pagos_facturas = PagoFactura.objects.aggregate(total_pagos=Sum('monto'))['total_pagos'] or 0

    # Totales
    total_efectivo = cobros_ventas - pagos_facturas

    contexto = {
        'cobros_ventas': cobros_ventas,
        'pagos_facturas': pagos_facturas,
        'total_efectivo': total_efectivo,
    }

    return render(request, 'flujo_caja.html', contexto)
