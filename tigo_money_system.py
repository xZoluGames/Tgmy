#!/usr/bin/env python3
"""
Sistema Completo Tigo Money - Menú Principal
Integra todos los módulos del sistema
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

class TigoMoneySystem:
    def __init__(self):
        self.credentials_file = "credenciales.json"
        self.has_credentials = False
        self.credentials_info = {}
        
    def check_credentials(self):
        """Verifica si existen credenciales válidas"""
        try:
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, "r", encoding="utf-8") as f:
                    self.credentials_info = json.load(f)
                    
                # Verificar tokens esenciales
                if self.credentials_info.get("AccessToken") and self.credentials_info.get("IdToken"):
                    self.has_credentials = True
                    return True
            return False
        except:
            return False
    
    def show_credentials_status(self):
        """Muestra el estado actual de las credenciales"""
        print("\n📊 ESTADO DEL SISTEMA")
        print("=" * 50)
        
        if self.has_credentials:
            print("✅ Credenciales disponibles")
            
            # Mostrar información básica
            if self.credentials_info.get("timestamp"):
                print(f"   Última actualización: {self.credentials_info['timestamp']}")
            
            if self.credentials_info.get("ExpiresIn"):
                expires = self.credentials_info["ExpiresIn"]
                print(f"   Tokens expiran en: {expires} segundos ({expires//60} minutos)")
            
            # Verificar device_info
            if self.credentials_info.get("device_info"):
                print("   📱 Información de dispositivo disponible")
            
            # Extraer número de teléfono del IdToken si es posible
            try:
                import base64
                id_token = self.credentials_info.get("IdToken", "")
                if id_token:
                    parts = id_token.split('.')
                    if len(parts) >= 2:
                        payload = parts[1]
                        payload += '=' * (4 - len(payload) % 4)
                        decoded = base64.urlsafe_b64decode(payload)
                        token_data = json.loads(decoded)
                        phone = token_data.get("phone_number", "")
                        if phone:
                            print(f"   📞 Número asociado: {phone}")
            except:
                pass
        else:
            print("❌ No hay credenciales disponibles")
            print("   Ejecute primero la opción 1 (Autenticación)")
    
    def run_authentication(self):
        """Ejecuta el script de autenticación"""
        print("\n🔐 Ejecutando módulo de autenticación...")
        print("-" * 50)
        try:
            import subprocess
            # Intentar ejecutar el script de autenticación
            result = subprocess.run([sys.executable, "cognito_auth.py"], capture_output=False)
            if result.returncode == 0:
                print("\n✅ Autenticación completada")
                self.check_credentials()  # Recargar credenciales
            else:
                print("\n⚠️  La autenticación no se completó correctamente")
        except FileNotFoundError:
            print("❌ No se encontró el archivo cognito_auth.py")
            print("   Asegúrese de que todos los scripts estén en la misma carpeta")
        except Exception as e:
            print(f"❌ Error ejecutando autenticación: {e}")
    
    def run_operations(self):
        """Ejecuta el script de operaciones"""
        if not self.has_credentials:
            print("\n⚠️  Necesita autenticarse primero (Opción 1)")
            return
        
        print("\n💼 Ejecutando módulo de operaciones...")
        print("-" * 50)
        try:
            import subprocess
            result = subprocess.run([sys.executable, "tigo_operations.py"], capture_output=False)
            if result.returncode == 0:
                print("\n✅ Módulo de operaciones finalizado")
        except FileNotFoundError:
            print("❌ No se encontró el archivo tigo_operations.py")
        except Exception as e:
            print(f"❌ Error ejecutando operaciones: {e}")
    
    def run_token_refresh(self):
        """Ejecuta el script de actualización de tokens"""
        if not self.has_credentials:
            print("\n⚠️  Necesita autenticarse primero (Opción 1)")
            return
        
        print("\n🔄 Ejecutando módulo de actualización de tokens...")
        print("-" * 50)
        try:
            import subprocess
            result = subprocess.run([sys.executable, "update_tokens.py"], capture_output=False)
            if result.returncode == 0:
                print("\n✅ Actualización de tokens completada")
                self.check_credentials()  # Recargar credenciales
        except FileNotFoundError:
            print("❌ No se encontró el archivo update_tokens.py")
        except Exception as e:
            print(f"❌ Error actualizando tokens: {e}")
    
    def run_device_manager(self):
        """Ejecuta el script de gestión de dispositivos"""
        if not self.has_credentials:
            print("\n⚠️  Necesita autenticarse primero (Opción 1)")
            return
        
        print("\n📱 Ejecutando módulo de gestión de dispositivos...")
        print("-" * 50)
        try:
            import subprocess
            result = subprocess.run([sys.executable, "device_manager.py"], capture_output=False)
            if result.returncode == 0:
                print("\n✅ Gestión de dispositivos finalizada")
                self.check_credentials()  # Recargar credenciales
        except FileNotFoundError:
            print("❌ No se encontró el archivo device_manager.py")
        except Exception as e:
            print(f"❌ Error en gestión de dispositivos: {e}")
    
    def run_security_config(self):
        """Ejecuta el script de configuración de seguridad"""
        if not self.has_credentials:
            print("\n⚠️  Necesita autenticarse primero (Opción 1)")
            return
        
        print("\n🔐 Ejecutando módulo de configuración de seguridad...")
        print("-" * 50)
        try:
            import subprocess
            result = subprocess.run([sys.executable, "security_config.py"], capture_output=False)
            if result.returncode == 0:
                print("\n✅ Configuración de seguridad finalizada")
                self.check_credentials()  # Recargar credenciales
        except FileNotFoundError:
            print("❌ No se encontró el archivo security_config.py")
        except Exception as e:
            print(f"❌ Error en configuración de seguridad: {e}")
    
    def check_folders(self):
        """Verifica y crea las carpetas necesarias"""
        folders = ["NumbersInfo", "PendingOperations"]
        print("\n📁 Verificando estructura de carpetas...")
        
        for folder in folders:
            folder_path = Path(folder)
            if not folder_path.exists():
                folder_path.mkdir(exist_ok=True)
                print(f"   ✅ Carpeta '{folder}' creada")
            else:
                print(f"   ✅ Carpeta '{folder}' existe")
    
    def show_help(self):
        """Muestra ayuda del sistema"""
        print("\n📖 AYUDA DEL SISTEMA TIGO MONEY")
        print("=" * 60)
        print("""
🔧 MÓDULOS DEL SISTEMA:

1. AUTENTICACIÓN (cognito_auth.py)
   - Inicio de sesión con usuario y contraseña
   - Verificación por SMS (MFA)
   - Genera archivo credenciales.json

2. OPERACIONES (tigo_operations.py)
   - Consulta información de números
   - Gestiona operaciones pendientes
   - Modo automático para aceptar operaciones

3. ACTUALIZAR TOKENS (update_tokens.py)
   - Renueva los tokens antes de que expiren
   - Usa el RefreshToken para obtener nuevos tokens
   - Mantiene la sesión activa sin reautenticación

4. GESTIÓN DE DISPOSITIVOS (device_manager.py)
   - Lista dispositivos registrados
   - Confirma dispositivos de confianza
   - Permite saltar MFA en dispositivos recordados

5. CONFIGURACIÓN DE SEGURIDAD (security_config.py)
   - Habilitar/Deshabilitar MFA
   - Cambiar tipo de MFA (SMS/TOTP)
   - Cambiar contraseña
   - Actualizar y verificar email
   - Configurar autenticación con aplicaciones

📋 FLUJO RECOMENDADO:

1. Primera vez:
   - Ejecutar Autenticación (Opción 1)
   - Configurar seguridad si desea (Opción 5)
   - Ejecutar Operaciones (Opción 2)

2. Uso regular:
   - Si los tokens expiraron: Actualizar Tokens (Opción 3)
   - Ejecutar Operaciones (Opción 2)

3. Mantenimiento:
   - Revisar dispositivos periódicamente (Opción 4)
   - Actualizar configuración de seguridad (Opción 5)
   - Actualizar tokens antes de que expiren (Opción 3)

📁 ESTRUCTURA DE ARCHIVOS:

- credenciales.json: Tokens y configuración
- NumbersInfo/: Información de números consultados
- PendingOperations/: Historial de operaciones procesadas
- security_config_*.json: Exportaciones de configuración

⚠️  SEGURIDAD:
- No comparta el archivo credenciales.json
- Los tokens tienen tiempo de expiración limitado
- Revise periódicamente los dispositivos registrados
- Configure MFA para mayor seguridad
        """)
    
    def main_menu(self):
        """Menú principal del sistema"""
        while True:
            # Verificar credenciales
            self.check_credentials()
            
            # Limpiar pantalla (opcional)
            # os.system('cls' if os.name == 'nt' else 'clear')
            
            print("\n" + "=" * 60)
            print("   🚀 SISTEMA TIGO MONEY - MENÚ PRINCIPAL")
            print("=" * 60)
            
            # Mostrar estado
            self.show_credentials_status()
            
            print("\n📋 OPCIONES DISPONIBLES:")
            print("   1. 🔐 Autenticación (Login)")
            print("   2. 💼 Operaciones (Consultas y Transacciones)")
            print("   3. 🔄 Actualizar Tokens")
            print("   4. 📱 Gestión de Dispositivos")
            print("   5. 🔒 Configuración de Seguridad y MFA")
            print("   6. 📁 Verificar Carpetas del Sistema")
            print("   7. 📖 Ayuda")
            print("   8. 🚪 Salir")
            print()
            
            choice = input("Seleccione una opción (1-8): ").strip()
            
            if choice == '1':
                self.run_authentication()
                
            elif choice == '2':
                self.run_operations()
                
            elif choice == '3':
                self.run_token_refresh()
                
            elif choice == '4':
                self.run_device_manager()
                
            elif choice == '5':
                self.run_security_config()
                
            elif choice == '6':
                self.check_folders()
                
            elif choice == '7':
                self.show_help()
                
            elif choice == '8':
                print("\n👋 ¡Hasta luego!")
                print("   Gracias por usar el Sistema Tigo Money")
                break
                
            else:
                print("❌ Opción inválida")
            
            if choice in ['1', '2', '3', '4', '5', '6', '7']:
                input("\nPresione Enter para continuar...")

def check_requirements():
    """Verifica que todos los scripts necesarios existan"""
    required_files = [
        "cognito_auth.py",
        "tigo_operations.py",
        "update_tokens.py",
        "device_manager.py",
        "security_config.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("⚠️  ADVERTENCIA: Faltan algunos archivos del sistema")
        print("   Archivos faltantes:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n   El sistema funcionará con limitaciones")
        input("   Presione Enter para continuar...")
        return False
    
    return True

def main():
    print("=" * 60)
    print("   🚀 SISTEMA TIGO MONEY v1.1")
    print("=" * 60)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    # Verificar archivos requeridos
    check_requirements()
    
    # Crear instancia del sistema
    system = TigoMoneySystem()
    
    # Verificar carpetas
    system.check_folders()
    
    # Ejecutar menú principal
    system.main_menu()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Sistema cerrado por el usuario")
        print("👋 ¡Hasta luego!")
    except Exception as e:
        print(f"\n❌ Error crítico del sistema: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresione Enter para salir...")