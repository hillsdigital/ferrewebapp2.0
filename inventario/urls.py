from django.urls import path
from .views import (
    ClienteDetailView,
    FacturaEmitidaListView,
    FacturaVentaDetailView,
    FacturaVentaView,
    HomePageView,
    MetodoPagoCreateView,
    MetodoPagoListView,
    ProveedorCreateView,
    ProveedorUpdateView,
    ProveedorListView,
    ProductoCreateView,
    ProductoUpdateView,
    ProductoListView,
    OrdenCompraListView,
    OrdenCompraCreateView,
    OrdenCompraUpdateView,
    OrdenCompraDeleteView,
    FacturaListView,
    StockCreateView,
    StockUpdateView,
    StockListView,
    flujo_de_caja,
    get_precio_compra,
    get_proveedores,
    registrar_cobro,
)
from inventario import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('proveedores/', ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedor/create/', ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedor/<int:pk>/update/', ProveedorUpdateView.as_view(), name='proveedor_update'),
#    productos
    path('productos/', ProductoListView.as_view(), name='producto_list'),
    path('producto/create/', ProductoCreateView.as_view(), name='producto_create'),
    path('producto/<int:pk>/update/', ProductoUpdateView.as_view(), name='producto_update'),
       path('cargar/', views.cargar_archivo, name='cargar_archivo'),


    path('ordenes-compra/', OrdenCompraListView.as_view(), name='orden_compra_list'),
    path('orden-compra/create/', OrdenCompraCreateView.as_view(), name='orden_compra_create'),
    path('orden-compra/<int:pk>/update/', OrdenCompraUpdateView.as_view(), name='orden_compra_update'),
    path('orden-compra/<int:pk>/delete/', OrdenCompraDeleteView.as_view(), name='orden_compra_delete'),
    
    # Facturas de proveedores
    path('facturas-proveedores/', FacturaListView.as_view(), name='factura_list'),
    path('factura-proveedor/<int:orden_compra_id>/create/', views.factura_create, name='factura_create'),
    path('factura-proveedor/<int:factura_id>/productos/create/', views.factura_producto_create, name='factura_producto_create'),
    path('factura-proveedor/<int:factura_id>/', views.factura_detail, name='factura_detail'),
    path('factura-proveedor/<int:factura_id>/update/', views.factura_update, name='factura_update'),
    
    # Facturas de ventas
    path('ventas/', views.venta_list, name='venta_list'),
    path('ventas/create/', views.crear_venta, name='venta_create'),
    path('venta/<int:id>/', views.venta_detail, name='venta_detail'),
    path('ventas/<int:pk>/facturar/', FacturaVentaView.as_view(), name='factura_venta'),
    path('facturas-ventas/', FacturaEmitidaListView.as_view(), name='factura_emitida_venta_list'),
    path('ventas/<int:venta_id>/registrar_cobro/', registrar_cobro, name='registrar_cobro'),
    path('facturas-ventas/<int:pk>/', FacturaVentaDetailView.as_view(), name='factura_venta_detail'),

    # Otros
    path('stocks/', StockListView.as_view(), name='stock_list'),
    path('stock/create/', StockCreateView.as_view(), name='stock_create'),
    path('stock/<int:pk>/update/', StockUpdateView.as_view(), name='stock_update'),

    path('clientes/', views.cliente_list, name='cliente_list'),
    path('clientes/create/', views.cliente_create, name='cliente_create'),
    path('clientes/<int:pk>/update/', views.cliente_update, name='cliente_update'),
    path('clientes/<int:pk>/delete/', views.cliente_delete, name='cliente_delete'),
    path('clientes/<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),
    
    path('ajax/get_proveedores/', get_proveedores, name='get_proveedores'),
    path('ajax/get_precio_compra/', get_precio_compra, name='get_precio_compra'),
    
     path('metodo_pago/create/', MetodoPagoCreateView.as_view(), name='metodo_pago_create'),
    path('metodo_pago/list/', MetodoPagoListView.as_view(), name='metodo_pago_list'),
    path('reporte_financiero/', views.reporte_financiero_view, name='reporte_financiero'),
    path('flujo-de-caja/', flujo_de_caja, name='flujo_de_caja'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
