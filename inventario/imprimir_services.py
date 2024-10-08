# Crear un archivo llamado imprimir_services.py
file_path = '/services.py'  # Cambia 'your_app' por el nombre correcto de tu aplicación

try:
    with open(file_path, 'r', encoding='utf-8') as file:
        contenido = file.read()
        print(contenido)
except FileNotFoundError:
    print(f"El archivo {file_path} no se encontró.")
except Exception as e:
    print(f"Ocurrió un error al leer el archivo: {e}")

from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Imprime el contenido del archivo services.py'

    def handle(self, *args, **kwargs):
        file_path = '/services.py'  # Cambia 'your_app' por el nombre correcto de tu aplicación

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                contenido = file.read()
                self.stdout.write(contenido)
        except FileNotFoundError:
            self.stderr.write(f"El archivo {file_path} no se encontró.")
        except Exception as e:
            self.stderr.write(f"Ocurrió un error al leer el archivo: {e}")
