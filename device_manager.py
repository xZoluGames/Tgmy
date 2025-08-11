#!/usr/bin/env python3
"""
Gestor de Dispositivos AWS Cognito
Compatible con el sistema Tigo Money
"""

import json
import requests
import base64
import secrets
from datetime import datetime
import urllib3
import sys

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CognitoDeviceManager:
    def __init__(self):
        self.region = "us-east-1"
        self.base_url = f"https://cognito-idp.{self.region}.amazonaws.com/"
        self.credentials = None
        self.access_token = None
        self.device_key = None
        self.username = None
        self.headers = {}
        
    def load_credentials(self):
        """Carga las credenciales desde credenciales.json"""
        try:
            with open("credenciales.json", "r", encoding="utf-8") as f:
                self.credentials = json.load(f)
                
                self.access_token = self.credentials.get("AccessToken")
                if not self.access_token:
                    print("❌ No se encontró AccessToken en credenciales.json")
                    return False
                
                # Configurar headers
                self.headers = {
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/x-amz-json-1.1',
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService'
                }
                
                # Decodificar token para obtener información
                self.decode_token()
                
                print("✅ Credenciales cargadas exitosamente")
                return True
                
        except FileNotFoundError:
            print("❌ No se encontró el archivo credenciales.json")
            print("   Por favor, ejecute primero el script de autenticación")
            return False
        except json.JSONDecodeError:
            print("❌ Error al leer credenciales.json")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def decode_token(self):
        """Decodifica el access token para obtener información"""
        try:
            parts = self.access_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Agregar padding si es necesario
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                token_info = json.loads(decoded)
                
                self.device_key = token_info.get('device_key')
                self.username = token_info.get('username')
                
                return token_info
        except Exception as e:
            print(f"⚠️  Error decodificando token: {e}")
            return {}
    
    def save_device_info(self, device_info):
        """Guarda información del dispositivo en credenciales.json"""
        try:
            if "device_info" not in self.credentials:
                self.credentials["device_info"] = {}
            
            self.credentials["device_info"].update(device_info)
            self.credentials["timestamp"] = datetime.now().isoformat()
            
            with open("credenciales.json", "w", encoding="utf-8") as f:
                json.dump(self.credentials, f, indent=2, ensure_ascii=False)
            
            print("💾 Información del dispositivo guardada en credenciales.json")
            return True
        except Exception as e:
            print(f"❌ Error al guardar información: {e}")
            return False
    
    def print_device_info(self):
        """Muestra información del dispositivo actual"""
        print("\n📱 INFORMACIÓN DEL DISPOSITIVO ACTUAL")
        print("=" * 50)
        
        if self.device_key:
            print(f"Device Key: {self.device_key}")
            device_id = self.device_key.split('_')[1] if '_' in self.device_key else 'N/A'
            print(f"Device ID: {device_id}")
        else:
            print("Device Key: No disponible")
        
        print(f"Username: {self.username or 'N/A'}")
        print(f"Región: {self.region}")
        
        # Mostrar info guardada si existe
        if self.credentials and "device_info" in self.credentials:
            print("\n📋 Información guardada:")
            for key, value in self.credentials["device_info"].items():
                print(f"   {key}: {value}")
    
    def get_device(self):
        """Obtiene información detallada del dispositivo actual"""
        print("\n🔍 OBTENIENDO INFORMACIÓN DEL DISPOSITIVO")
        print("-" * 50)
        
        if not self.device_key:
            print("❌ No hay device_key en el token")
            return None
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.GetDevice'
                },
                json={
                    'AccessToken': self.access_token,
                    'DeviceKey': self.device_key
                },
                verify=False
            )
            
            if response.status_code == 200:
                device_data = response.json()
                device = device_data.get('Device', {})
                
                print("✅ Información del dispositivo obtenida:")
                print(f"   Device Key: {device.get('DeviceKey', 'N/A')}")
                print(f"   Status: {device.get('DeviceStatus', 'N/A')}")
                print(f"   Creado: {device.get('DeviceCreateDate', 'N/A')}")
                print(f"   Última modificación: {device.get('DeviceLastModifiedDate', 'N/A')}")
                print(f"   Último acceso: {device.get('DeviceLastAuthenticatedDate', 'N/A')}")
                
                # Mostrar atributos
                if 'DeviceAttributes' in device:
                    print("   Atributos:")
                    for attr in device['DeviceAttributes']:
                        name = attr.get('Name', '')
                        value = attr.get('Value', '')
                        print(f"      {name}: {value}")
                
                # Guardar información
                device_info = {
                    "device_key": device.get('DeviceKey'),
                    "device_status": device.get('DeviceStatus'),
                    "device_created": device.get('DeviceCreateDate'),
                    "last_accessed": device.get('DeviceLastAuthenticatedDate')
                }
                self.save_device_info(device_info)
                
                return device_data
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error en GetDevice: {e}")
            return None
    
    def list_devices(self):
        """Lista todos los dispositivos del usuario"""
        print("\n📋 LISTANDO TODOS LOS DISPOSITIVOS")
        print("-" * 50)
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.ListDevices'
                },
                json={
                    'AccessToken': self.access_token,
                    'Limit': 10
                },
                verify=False
            )
            
            if response.status_code == 200:
                devices_data = response.json()
                devices = devices_data.get('Devices', [])
                
                if not devices:
                    print("📱 No se encontraron dispositivos registrados")
                    return []
                
                print(f"✅ Encontrados {len(devices)} dispositivo(s):")
                
                for i, device in enumerate(devices, 1):
                    print(f"\n   📱 Dispositivo #{i}:")
                    print(f"      Key: {device.get('DeviceKey', 'N/A')}")
                    print(f"      Status: {device.get('DeviceStatus', 'N/A')}")
                    print(f"      Creado: {device.get('DeviceCreateDate', 'N/A')}")
                    print(f"      Último acceso: {device.get('DeviceLastAuthenticatedDate', 'N/A')}")
                    
                    # Marcar el dispositivo actual
                    if device.get('DeviceKey') == self.device_key:
                        print("      👈 ESTE ES TU DISPOSITIVO ACTUAL")
                
                return devices
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error en ListDevices: {e}")
            return []
    
    def confirm_device(self, device_name=None):
        """Confirma el dispositivo actual"""
        print("\n🔐 CONFIRMANDO DISPOSITIVO")
        print("-" * 50)
        
        if not self.device_key:
            print("❌ No hay device_key disponible")
            return None
        
        if not device_name:
            device_name = f"TigoMoney-Device-{secrets.token_hex(4)}"
        
        print(f"   Nombre del dispositivo: {device_name}")
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.ConfirmDevice'
                },
                json={
                    'AccessToken': self.access_token,
                    'DeviceKey': self.device_key,
                    'DeviceName': device_name
                },
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Dispositivo confirmado exitosamente!")
                
                if 'UserConfirmationNecessary' in result:
                    if result['UserConfirmationNecessary']:
                        print("📧 Se requiere confirmación adicional del usuario")
                    else:
                        print("✅ No se requiere confirmación adicional")
                
                # Guardar información
                device_info = {
                    "device_confirmed": True,
                    "device_name": device_name,
                    "confirmation_date": datetime.now().isoformat()
                }
                self.save_device_info(device_info)
                
                return result
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error en ConfirmDevice: {e}")
            return None
    
    def update_device_status(self, remember=True):
        """Actualiza el estado del dispositivo (recordar/no recordar)"""
        print(f"\n📝 ACTUALIZANDO ESTADO DEL DISPOSITIVO")
        print("-" * 50)
        
        if not self.device_key:
            print("❌ No hay device_key disponible")
            return False
        
        status = "remembered" if remember else "not_remembered"
        action = "recordar" if remember else "no recordar"
        print(f"   Configurando dispositivo para: {action}")
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.UpdateDeviceStatus'
                },
                json={
                    'AccessToken': self.access_token,
                    'DeviceKey': self.device_key,
                    'DeviceRememberedStatus': status
                },
                verify=False
            )
            
            if response.status_code == 200:
                print(f"✅ Dispositivo configurado para {action}")
                
                # Guardar información
                device_info = {
                    "device_remembered": remember,
                    "status_updated": datetime.now().isoformat()
                }
                self.save_device_info(device_info)
                
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en UpdateDeviceStatus: {e}")
            return False
    
    def forget_device(self, device_key=None):
        """Elimina (olvida) un dispositivo"""
        print(f"\n🗑️  ELIMINANDO DISPOSITIVO")
        print("-" * 50)
        
        target_device = device_key or self.device_key
        if not target_device:
            print("❌ No hay device_key disponible")
            return False
        
        print(f"   Device Key: {target_device}")
        
        # Advertencia si es el dispositivo actual
        if target_device == self.device_key:
            print("\n⚠️  ADVERTENCIA: Vas a eliminar tu dispositivo ACTUAL")
            print("   Esto requerirá autenticación completa en el próximo inicio de sesión")
            confirm = input("   ¿Estás seguro? (s/n): ").strip().lower()
            if confirm != 's':
                print("❌ Operación cancelada")
                return False
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.ForgetDevice'
                },
                json={
                    'AccessToken': self.access_token,
                    'DeviceKey': target_device
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Dispositivo eliminado exitosamente")
                
                # Si era el dispositivo actual, limpiar info local
                if target_device == self.device_key:
                    if "device_info" in self.credentials:
                        del self.credentials["device_info"]
                        self.save_device_info({})
                
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en ForgetDevice: {e}")
            return False
    
    def main_menu(self):
        """Menú principal del gestor de dispositivos"""
        while True:
            print("\n" + "=" * 60)
            print("   🔧 GESTOR DE DISPOSITIVOS - TIGO MONEY")
            print("=" * 60)
            print("\n📋 Opciones disponibles:")
            print("   1. 📱 Ver información del dispositivo actual")
            print("   2. 📋 Listar todos los dispositivos")
            print("   3. 🔐 Confirmar dispositivo actual")
            print("   4. 💾 Marcar dispositivo como 'recordado'")
            print("   5. 🔄 Marcar dispositivo como 'no recordado'")
            print("   6. 🗑️  Eliminar dispositivo actual")
            print("   7. 🗑️  Eliminar otro dispositivo")
            print("   8. 📖 ¿Qué es un dispositivo en Cognito?")
            print("   9. 🚪 Salir")
            print()
            
            choice = input("Seleccione una opción (1-9): ").strip()
            
            if choice == '1':
                self.print_device_info()
                self.get_device()
                
            elif choice == '2':
                self.list_devices()
                
            elif choice == '3':
                name = input("Nombre del dispositivo (Enter para automático): ").strip()
                self.confirm_device(name if name else None)
                
            elif choice == '4':
                self.update_device_status(remember=True)
                
            elif choice == '5':
                self.update_device_status(remember=False)
                
            elif choice == '6':
                self.forget_device()
                
            elif choice == '7':
                devices = self.list_devices()
                if devices:
                    key = input("\nIngrese el Device Key a eliminar: ").strip()
                    if key:
                        self.forget_device(key)
                
            elif choice == '8':
                self.explain_devices()
                
            elif choice == '9':
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida")
            
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8']:
                input("\nPresione Enter para continuar...")
    
    def explain_devices(self):
        """Explica el concepto de dispositivos en Cognito"""
        print("\n📚 DISPOSITIVOS EN AWS COGNITO")
        print("=" * 60)
        print("""
🔐 ¿QUÉ ES UN DISPOSITIVO EN COGNITO?

Un "dispositivo" en AWS Cognito representa un punto de acceso único
desde el cual un usuario se autentica. Puede ser:
- Un navegador web específico
- Una aplicación móvil
- Un dispositivo físico (teléfono, tablet, PC)

🎯 BENEFICIOS DE LOS DISPOSITIVOS:

1. SALTAR MFA: Si marcas un dispositivo como "recordado",
   puedes evitar el código SMS en futuros inicios de sesión.

2. SEGURIDAD: Puedes ver y eliminar dispositivos no reconocidos
   desde los cuales alguien accedió a tu cuenta.

3. CONTROL: Gestiona desde dónde puedes acceder a tu cuenta.

📱 ESTADOS DEL DISPOSITIVO:

- NO CONFIRMADO: Dispositivo nuevo, sin confirmar
- CONFIRMADO: Dispositivo verificado y activo
- RECORDADO: Dispositivo de confianza (puede saltar MFA)
- NO RECORDADO: Requiere autenticación completa

🔑 DEVICE KEY:
Es el identificador único del dispositivo. Se genera
automáticamente cuando inicias sesión desde un nuevo dispositivo.

💡 RECOMENDACIONES:

- Confirma y marca como "recordado" solo dispositivos personales
- Revisa periódicamente la lista de dispositivos
- Elimina dispositivos que no reconozcas o no uses
- En dispositivos públicos, NO los marques como recordados
        """)

def main():
    print("=" * 50)
    print("   GESTOR DE DISPOSITIVOS - TIGO MONEY")
    print("=" * 50)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    manager = CognitoDeviceManager()
    
    # Cargar credenciales
    if not manager.load_credentials():
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    # Ejecutar menú principal
    manager.main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresione Enter para salir...")