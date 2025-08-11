#!/usr/bin/env python3
"""
Script para autenticación en AWS Cognito con SMS MFA
Autor: Script automatizado
"""

import json
import requests
import getpass
import base64
import time
from datetime import datetime, timezone
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CognitoAuthenticator:
    def __init__(self):
        self.base_url = "https://proxy.cognito.tigomoney.io/"
        self.client_id = "7b5aujqnnu2pf9ji7jdhan12d1"
        self.user_pool_id = "us-east-1_G5gLRkNXN"
        self.device_id = "49b1eaa9-ecc1-4441-93ff-0d7ba6c31246"
        self.session = None
        
    def generate_user_context_data(self, username):
        """Genera el UserContextData codificado en base64"""
        timestamp = str(int(time.time() * 1000))
        
        context_data = {
            "contextData": {
                "DeviceId": f"{self.device_id}:{datetime.now(timezone.utc).isoformat()}",
                "DeviceName": "Windows",
                "ClientTimezone": "-03:00",
                "ApplicationName": "wallet_app_frontend",
                "ApplicationVersion": "8.0.16(80160002)",
                "DeviceLanguage": "es-ES",
                "DeviceOSReleaseVersion": "Chrome/139.0.0.0",
                "ScreenHeightPixels": "1440",
                "ScreenWidthPixels": "2560"
            },
            "username": username,
            "userPoolId": self.user_pool_id,
            "timestamp": timestamp
        }
        
        # Simplificado - en producción necesitarías generar la firma correctamente
        encoded_data = {
            "payload": json.dumps(context_data),
            "signature": "LABynWql5xidCZo0ByEH3sMOJUdh3TqVAlpgFe8dZF8=",
            "version": "FLUTTER20230306"
        }
        
        return base64.b64encode(json.dumps(encoded_data).encode()).decode()

    def initiate_auth(self, username, password):
        """Inicia el proceso de autenticación"""
        print("\n🔐 Iniciando autenticación...")
        
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Origin": "https://moneyapp.tigo.com.py",
            "Referer": "https://moneyapp.tigo.com.py/",
        }
        
        data = {
            "AuthFlow": "USER_PASSWORD_AUTH",
            "ClientId": self.client_id,
            "AuthParameters": {
                "USERNAME": username,
                "PASSWORD": password
            },
            "ClientMetadata": {},
            "UserContextData": {
                "EncodedData": self.generate_user_context_data(username)
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "ChallengeName" in result and result["ChallengeName"] == "SMS_MFA":
                    print("✅ Autenticación inicial exitosa")
                    print(f"📱 Se ha enviado un código SMS a: {result['ChallengeParameters'].get('CODE_DELIVERY_DESTINATION', 'tu número')}")
                    self.session = result["Session"]
                    return True
                else:
                    print("❌ Respuesta inesperada del servidor")
                    print(json.dumps(result, indent=2))
                    return False
            else:
                print(f"❌ Error en la solicitud: {response.status_code}")
                print(response.text)
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def respond_to_auth_challenge(self, username, sms_code):
        """Responde al desafío de autenticación con el código SMS"""
        print("\n🔐 Verificando código SMS...")
        
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.RespondToAuthChallenge",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
            "Origin": "https://moneyapp.tigo.com.py",
            "Referer": "https://moneyapp.tigo.com.py/",
        }
        
        data = {
            "ClientId": self.client_id,
            "ChallengeName": "SMS_MFA",
            "Session": self.session,
            "ChallengeResponses": {
                "USERNAME": username,
                "SMS_MFA_CODE": sms_code
            },
            "UserContextData": {
                "EncodedData": self.generate_user_context_data(username)
            },
            "ClientMetadata": {}
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if "AuthenticationResult" in result:
                    print("✅ Autenticación completada exitosamente")
                    return result["AuthenticationResult"]
                else:
                    print("❌ Error en la autenticación")
                    print(json.dumps(result, indent=2))
                    return None
            else:
                print(f"❌ Error en la solicitud: {response.status_code}")
                print(response.text)
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def save_credentials(self, auth_result):
        """Guarda las credenciales en un archivo JSON"""
        credentials = {
            "AccessToken": auth_result.get("AccessToken"),
            "IdToken": auth_result.get("IdToken"),
            "RefreshToken": auth_result.get("RefreshToken"),
            "ExpiresIn": auth_result.get("ExpiresIn"),
            "TokenType": auth_result.get("TokenType"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Guardar información del dispositivo si viene en la respuesta
        if "NewDeviceMetadata" in auth_result:
            device_meta = auth_result["NewDeviceMetadata"]
            credentials["device_info"] = {
                "device_key": device_meta.get("DeviceKey"),
                "device_group_key": device_meta.get("DeviceGroupKey"),
                "new_device": True
            }
        
        try:
            with open("credenciales.json", "w", encoding="utf-8") as f:
                json.dump(credentials, f, indent=2, ensure_ascii=False)
            print("✅ Credenciales guardadas en 'credenciales.json'")
            return True
        except Exception as e:
            print(f"❌ Error al guardar credenciales: {e}")
            return False

def main():
    print("=" * 50)
    print("   AWS Cognito - Sistema de Autenticación")
    print("=" * 50)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    authenticator = CognitoAuthenticator()
    
    # Solicitar credenciales
    print("\n📝 Ingrese sus credenciales:")
    username = input("Usuario (incluya +595): ").strip()
    
    # Validar formato del número
    if not username.startswith("+595"):
        print("⚠️ El número debe comenzar con +595")
        username = "+595" + username.lstrip("+")
        print(f"📞 Número ajustado a: {username}")
    
    # Solicitar contraseña y agregar prefijo COG
    password_input = getpass.getpass("Contraseña: ").strip()
    password = "COG" + password_input
    print("✅ Prefijo 'COG' agregado a la contraseña")
    
    # Iniciar autenticación
    if authenticator.initiate_auth(username, password):
        # Solicitar código SMS
        print("\n" + "=" * 50)
        sms_code = input("📱 Ingrese el código SMS recibido: ").strip()
        
        # Verificar código SMS
        auth_result = authenticator.respond_to_auth_challenge(username, sms_code)
        
        if auth_result:
            # Guardar credenciales
            if authenticator.save_credentials(auth_result):
                print("\n" + "=" * 50)
                print("🎉 ¡Proceso completado exitosamente!")
                print("=" * 50)
                
                # Mostrar información de los tokens
                print("\n📋 Resumen de tokens obtenidos:")
                print(f"  • Access Token: ...{auth_result['AccessToken'][-20:]}")
                print(f"  • ID Token: ...{auth_result['IdToken'][-20:]}")
                print(f"  • Refresh Token: ...{auth_result['RefreshToken'][-20:]}")
                print(f"  • Expira en: {auth_result.get('ExpiresIn', 'N/A')} segundos")
            else:
                print("\n⚠️ Los tokens se obtuvieron pero no se pudieron guardar")
        else:
            print("\n❌ No se pudo completar la autenticación")
    else:
        print("\n❌ No se pudo iniciar el proceso de autenticación")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Proceso cancelado por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()