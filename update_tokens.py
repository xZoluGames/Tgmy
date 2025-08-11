#!/usr/bin/env python3
"""
Script para actualizar tokens usando RefreshToken
Compatible con el sistema Tigo Money
"""

import json
import requests
import sys
from datetime import datetime
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TokenRefresher:
    def __init__(self):
        self.proxy_url = "https://proxy.cognito.tigomoney.io/"
        self.client_id = "7b5aujqnnu2pf9ji7jdhan12d1"
        self.credentials = None
        self.device_key = None
        
    def load_credentials(self):
        """Carga las credenciales desde el archivo"""
        try:
            with open("credenciales.json", "r", encoding="utf-8") as f:
                self.credentials = json.load(f)
                
                # Extraer device_key del AccessToken si existe
                self.extract_device_key()
                
                print("✅ Credenciales cargadas exitosamente")
                return True
        except FileNotFoundError:
            print("❌ No se encontró el archivo credenciales.json")
            print("   Por favor, ejecute primero el script de autenticación")
            return False
        except json.JSONDecodeError as e:
            print(f"❌ Error al leer credenciales.json: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def extract_device_key(self):
        """Extrae el device_key del AccessToken"""
        try:
            import base64
            
            access_token = self.credentials.get("AccessToken", "")
            if not access_token:
                return
            
            # Decodificar el token (JWT)
            parts = access_token.split('.')
            if len(parts) >= 2:
                payload = parts[1]
                # Agregar padding si es necesario
                payload += '=' * (4 - len(payload) % 4)
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                
                self.device_key = token_data.get('device_key')
                if self.device_key:
                    print(f"📱 Device Key encontrado: {self.device_key}")
        except Exception as e:
            print(f"⚠️  No se pudo extraer device_key: {e}")
    
    def save_credentials(self):
        """Guarda las credenciales actualizadas"""
        try:
            self.credentials["timestamp"] = datetime.now().isoformat()
            
            with open("credenciales.json", "w", encoding="utf-8") as f:
                json.dump(self.credentials, f, indent=2, ensure_ascii=False)
            
            print("✅ Credenciales guardadas exitosamente")
            return True
        except Exception as e:
            print(f"❌ Error al guardar credenciales: {e}")
            return False
    
    def refresh_tokens(self):
        """Actualiza los tokens usando el RefreshToken"""
        print("\n🔄 Actualizando tokens...")
        
        if not self.credentials.get("RefreshToken"):
            print("❌ No se encontró RefreshToken en credenciales.json")
            return False
        
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Cache-Control": "no-store",
            "Origin": "https://moneyapp.tigo.com.py",
            "Referer": "https://moneyapp.tigo.com.py/"
        }
        
        auth_params = {
            "REFRESH_TOKEN": self.credentials["RefreshToken"]
        }
        
        # Agregar device_key si existe
        if self.device_key:
            auth_params["DEVICE_KEY"] = self.device_key
        
        payload = {
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": auth_params
        }
        
        try:
            response = requests.post(
                self.proxy_url,
                headers=headers,
                json=payload,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "AuthenticationResult" in result:
                    auth_result = result["AuthenticationResult"]
                    
                    # Actualizar tokens
                    self.credentials["AccessToken"] = auth_result["AccessToken"]
                    self.credentials["IdToken"] = auth_result["IdToken"]
                    
                    # El RefreshToken puede no venir en la respuesta
                    if "RefreshToken" in auth_result:
                        self.credentials["RefreshToken"] = auth_result["RefreshToken"]
                        print("   ♻️  RefreshToken actualizado")
                    
                    # Actualizar otros campos si vienen
                    if "ExpiresIn" in auth_result:
                        self.credentials["ExpiresIn"] = auth_result["ExpiresIn"]
                    
                    if "TokenType" in auth_result:
                        self.credentials["TokenType"] = auth_result["TokenType"]
                    
                    print("✅ Tokens actualizados exitosamente")
                    
                    # Mostrar información de expiración
                    expires_in = auth_result.get("ExpiresIn", 1800)
                    print(f"⏱️  Los tokens expiran en: {expires_in} segundos ({expires_in//60} minutos)")
                    
                    return True
                else:
                    print("❌ Respuesta inesperada del servidor")
                    print(json.dumps(result, indent=2))
                    return False
            else:
                print(f"❌ Error del servidor: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', 'Sin mensaje')}")
                    print(f"   Tipo: {error_data.get('__type', 'Desconocido')}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def show_token_info(self):
        """Muestra información sobre los tokens actuales"""
        print("\n📋 INFORMACIÓN DE TOKENS ACTUALES")
        print("=" * 50)
        
        if self.credentials.get("AccessToken"):
            print(f"✅ AccessToken: ...{self.credentials['AccessToken'][-20:]}")
        else:
            print("❌ AccessToken: No disponible")
        
        if self.credentials.get("IdToken"):
            print(f"✅ IdToken: ...{self.credentials['IdToken'][-20:]}")
        else:
            print("❌ IdToken: No disponible")
        
        if self.credentials.get("RefreshToken"):
            print(f"✅ RefreshToken: ...{self.credentials['RefreshToken'][-20:]}")
        else:
            print("❌ RefreshToken: No disponible")
        
        if self.device_key:
            print(f"📱 Device Key: {self.device_key}")
        
        if self.credentials.get("timestamp"):
            print(f"🕐 Última actualización: {self.credentials['timestamp']}")
        
        if self.credentials.get("ExpiresIn"):
            expires = self.credentials['ExpiresIn']
            print(f"⏱️  Tiempo de expiración: {expires} segundos ({expires//60} minutos)")

def main():
    print("=" * 50)
    print("   ACTUALIZADOR DE TOKENS - TIGO MONEY")
    print("=" * 50)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    refresher = TokenRefresher()
    
    # Cargar credenciales
    if not refresher.load_credentials():
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    # Mostrar información actual
    refresher.show_token_info()
    
    # Preguntar si desea actualizar
    print("\n" + "=" * 50)
    choice = input("¿Desea actualizar los tokens ahora? (s/n): ").strip().lower()
    
    if choice == 's':
        # Actualizar tokens
        if refresher.refresh_tokens():
            # Guardar credenciales actualizadas
            if refresher.save_credentials():
                print("\n" + "=" * 50)
                print("🎉 ¡Proceso completado exitosamente!")
                refresher.show_token_info()
            else:
                print("\n⚠️  Los tokens se actualizaron pero no se pudieron guardar")
        else:
            print("\n❌ No se pudieron actualizar los tokens")
            print("   Posibles causas:")
            print("   - El RefreshToken ha expirado")
            print("   - Problemas de conexión")
            print("   - Credenciales inválidas")
            print("\n💡 Sugerencia: Ejecute el script de autenticación nuevamente")
    else:
        print("\n⚠️  Actualización cancelada por el usuario")
    
    input("\nPresione Enter para salir...")

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