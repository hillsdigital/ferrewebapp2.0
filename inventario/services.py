import base64
import datetime
import os
import xml.etree.ElementTree as ET
import requests
from decimal import Decimal
from django.conf import settings
from OpenSSL import crypto
from zeep import Client
from zeep.transports import Transport
from inventario.models import FacturaCliente, FacturaProducto  # Asegúrate de que los modelos estén importados
import logging

# Configuración de AFIP
CUIT = settings.CUIT
CERT_PATH = os.path.join(settings.BASE_DIR, 'certs', 'certificado.crt')
KEY_PATH = os.path.join(settings.BASE_DIR, 'certs', 'clave_privada.key')

WSAA_URL_HOMOLOGACION = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
WSAA_URL_PRODUCCION = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
WSFEV1_URL_HOMOLOGACION = "https://wshomologacion.afip.gov.ar/wsfev1/service.asmx?WSDL"
WSFEV1_URL_PRODUCCION = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"

logger = logging.getLogger(__name__)

class AFIPServiceBase:
    def __init__(self, ambiente='homologacion'):
        self.ambiente = ambiente
        if self.ambiente == 'homologacion':
            self.wsaa_url = WSAA_URL_HOMOLOGACION
            self.wsfev1_url = WSFEV1_URL_HOMOLOGACION
        else:
            self.wsaa_url = WSAA_URL_PRODUCCION
            self.wsfev1_url = WSFEV1_URL_PRODUCCION
        self.token = None
        self.sign = None

    def generar_tra(self):
        unique_id = int(datetime.datetime.now().timestamp())
        generation_time = (datetime.datetime.now() - datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")
        expiration_time = (datetime.datetime.now() + datetime.timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")

        tra = f"""<?xml version="1.0" encoding="UTF-8"?>
        <loginTicketRequest version="1.0">
            <header>
                <uniqueId>{unique_id}</uniqueId>
                <generationTime>{generation_time}</generationTime>
                <expirationTime>{expiration_time}</expirationTime>
            </header>
            <service>wsfe</service>
        </loginTicketRequest>"""
        return tra.encode("utf-8")

    def firmar_tra(self, tra):
        with open(KEY_PATH, 'rb') as key_file:
            key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())
        with open(CERT_PATH, 'rb') as cert_file:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_file.read())

        p7 = crypto.PKCS7_sign(cert, key, None, tra, crypto.PKCS7_BINARY | crypto.PKCS7_DETACHED)
        p7_data = crypto.dump_pkcs7(p7)
        cms = base64.b64encode(p7_data).decode('utf-8')
        return cms

    def obtener_token_sign(self):
        tra = self.generar_tra()
        tra_firmado = self.firmar_tra(tra)
        login_cms = f"""<loginCms>{tra_firmado}</loginCms>"""

        headers = {'Content-Type': 'application/soap+xml; charset=utf-8'}
        response = requests.post(self.wsaa_url, data=login_cms, headers=headers)

        if response.status_code != 200:
            logger.error(f"Error en WSAA: {response.status_code} - {response.text}")
            raise Exception(f"Error en WSAA: {response.status_code}")

        xml_response = ET.fromstring(response.content)
        namespaces = {'ns': 'http://ar.gov.afip.dif.wsaa/'}
        token = xml_response.find('.//{http://ar.gov.afip.dif.wsaa/}token').text
        sign = xml_response.find('.//{http://ar.gov.afip.dif.wsaa/}sign').text

        self.token = token
        self.sign = sign

        return token, sign

    def get_client_wsfev1(self):
        if not self.token or not self.sign:
            self.obtener_token_sign()

        transport = Transport(timeout=30)
        client = Client(wsdl=self.wsfev1_url, transport=transport)
        return client


class AFIPService(AFIPServiceBase):
    def enviar_factura(self, factura_id):
        try:
            factura = FacturaCliente.objects.get(id=factura_id)
        except FacturaCliente.DoesNotExist:
            logger.error(f"FacturaCliente con id {factura_id} no existe.")
            raise Exception("Factura no encontrada.")

        # Calcular totales si no están calculados
        if not factura.total:
            factura.calcular_totales()

        fe_comp_cons_req = self.preparar_datos_factura(factura)

        client = self.get_client_wsfev1()
        try:
            response = client.service.FECAESolicitar(
                Auth={
                    'Token': self.token,
                    'Sign': self.sign,
                    'Cuit': int(CUIT)
                },
                FeCAEReq=fe_comp_cons_req
            )
        except Exception as e:
            logger.error(f"Error al llamar a FECAESolicitar: {e}")
            raise Exception(f"Error al llamar a AFIP: {e}")

        self.procesar_respuesta_factura(factura, response)

    def preparar_datos_factura(self, factura):
        productos = FacturaProducto.objects.filter(factura=factura)

        iva_dict = {}
        for producto in productos:
            iva_id = self.obtener_id_iva(producto.iva)
            if iva_id not in iva_dict:
                iva_dict[iva_id] = {
                    'Id': iva_id,
                    'BaseImp': 0.0,
                    'Importe': 0.0
                }
            iva_dict[iva_id]['BaseImp'] += float(producto.precio_sin_iva * producto.cantidad)
            iva_dict[iva_id]['Importe'] += float(producto.total_iva * producto.cantidad)

        iva_list = list(iva_dict.values())

        detalles = []
        for producto in productos:
            detalles.append({
                'Concepto': 1,  # 1: Productos, 2: Servicios, etc.
                'DocTipo': 80,  # CUIT
                'DocNro': int(factura.venta.cliente.cuit),
                'CbteDesde': int(factura.numero.split('-')[-1]),
                'CbteHasta': int(factura.numero.split('-')[-1]),
                'CbteFch': factura.fecha_emision.strftime('%Y%m%d'),
                'ImpTotal': float(factura.total),
                'ImpTotConc': 0.0,
                'ImpNeto': float(factura.subtotal),
                'ImpOpEx': 0.0,
                'ImpIVA': float(factura.iva),
                'ImpTrib': 0.0,
                'MonId': 'PES',
                'MonCotiz': 1.0,
                'Iva': iva_list,
                'Opcionales': []
            })

        fe_comp_cons_req = {
            'FeCAEReq': {
                'FeCabReq': {
                    'CantReg': 1,
                    'PtoVta': int(factura.punto_venta),
                    'CbteTipo': self.obtener_tipo_cbte(factura.tipo)
                },
                'FeDetReq': {
                    'FECAEDetRequest': detalles
                }
            }
        }

        # Imprimir los datos que se están preparando
        print("Datos de la factura que se están preparando para enviar a AFIP:", fe_comp_cons_req)

        return fe_comp_cons_req

    def obtener_id_iva(self, iva):
        if iva == Decimal('21.00'):
            return 5  # 21% Responsable Inscripto
        elif iva == Decimal('10.50'):
            return 4  # 10.5% Responsable Inscripto
        elif iva == Decimal('0.00'):
            return 3  # Sin IVA
        else:
            return 3  # Default a Sin IVA

    def obtener_tipo_cbte(self, tipo):
        if tipo == 'A':
            return 1
        elif tipo == 'B':
            return 6
        else:
            return 0  # Sin comprobante

    def procesar_respuesta_factura(self, factura, response):
        try:
            fe_det_resp = response.FECAESolicitarResult.FeDetResp.FECAEDetResponse[0]
            if fe_det_resp.CAE:
                cae = fe_det_resp.CAE
                cae_vto = fe_det_resp.CAEFchVto

                factura.cae = cae
                factura.cae_vto = datetime.datetime.strptime(cae_vto, '%Y%m%d').date()
                factura.save()

                logger.info(f"Factura {factura.numero} enviada exitosamente a AFIP. CAE: {cae}")
            else:
                if hasattr(response.FECAESolicitarResult, 'Errors') and response.FECAESolicitarResult.Errors.Err:
                    errores = response.FECAESolicitarResult.Errors.Err
                    mensaje_error = errores[0].Msg if errores else "Error desconocido al solicitar CAE."
                    logger.error(f"AFIP Error: {mensaje_error}")
                    raise Exception(f"AFIP Error: {mensaje_error}")
                else:
                    logger.error("No se recibió CAE ni errores de AFIP.")
                    raise Exception("No se recibió CAE ni errores de AFIP.")
        except Exception as e:
            logger.error(f"Error al procesar la respuesta de AFIP: {e}")
            raise Exception(f"Error al procesar la respuesta de AFIP: {e}")
