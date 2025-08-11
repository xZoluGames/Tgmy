#!/usr/bin/env python3
"""
Gestor de Configuraciones de Seguridad AWS Cognito
Permite configurar MFA, cambiar contraseña, gestionar números y otros ajustes
Compatible con el sistema Tigo Money
"""

import json
import requests
import base64
import getpass
from datetime import datetime
import urllib3
import sys
import re

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class CognitoSecurityManager:
    def __init__(self):
        self.region = "us-east-1"
        self.base_url = f"https://cognito-idp.{self.region}.amazonaws.com/"
        self.credentials = None
        self.access_token = None
        self.username = None
        self.user_attributes = {}
        self.mfa_options = []
        self.pool_mfa_config = {}
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
                
                self.username = token_info.get('username')
                
                return token_info
        except Exception as e:
            print(f"⚠️  Error decodificando token: {e}")
            return {}
    
    def get_user_info(self):
        """Obtiene información completa del usuario actual"""
        print("\n📋 OBTENIENDO INFORMACIÓN DEL USUARIO")
        print("-" * 50)
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.GetUser'
                },
                json={
                    'AccessToken': self.access_token
                },
                verify=False
            )
            
            if response.status_code == 200:
                user_data = response.json()
                
                print("✅ Información del usuario obtenida:")
                print(f"   Username: {user_data.get('Username', 'N/A')}")
                
                # Guardar atributos
                self.user_attributes = {}
                if 'UserAttributes' in user_data:
                    print("\n   📝 Atributos del usuario:")
                    for attr in user_data['UserAttributes']:
                        name = attr.get('Name', '')
                        value = attr.get('Value', '')
                        self.user_attributes[name] = value
                        
                        # Mostrar atributos importantes
                        if name in ['email', 'phone_number', 'email_verified', 'phone_number_verified']:
                            verified = " ✅" if name.endswith('_verified') and value == 'true' else ""
                            print(f"      {name}: {value}{verified}")
                
                # Guardar opciones MFA
                self.mfa_options = user_data.get('MFAOptions', [])
                if self.mfa_options:
                    print("\n   🔐 Opciones MFA configuradas:")
                    for mfa in self.mfa_options:
                        print(f"      Tipo: {mfa.get('DeliveryMedium', 'N/A')}")
                        print(f"      Destino: {mfa.get('AttributeName', 'N/A')}")
                else:
                    print("\n   ℹ️  No hay MFA configurado")
                
                # Mostrar preferencias MFA
                if 'UserMFASettingList' in user_data:
                    print("\n   🔒 Configuración MFA actual:")
                    for setting in user_data['UserMFASettingList']:
                        print(f"      - {setting}")
                
                if 'PreferredMfaSetting' in user_data:
                    print(f"   ⭐ MFA preferido: {user_data['PreferredMfaSetting']}")
                
                return user_data
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error en GetUser: {e}")
            return None
    
    def update_phone_number(self):
        """Actualiza o agrega el número de teléfono del usuario"""
        print("\n📱 GESTIÓN DE NÚMERO DE TELÉFONO")
        print("-" * 50)
        
        current_phone = self.user_attributes.get('phone_number', 'No configurado')
        phone_verified = self.user_attributes.get('phone_number_verified', 'false')
        
        print(f"   Número actual: {current_phone}")
        print(f"   Verificado: {'✅ Sí' if phone_verified == 'true' else '❌ No'}")
        
        print("\n   Opciones:")
        print("   1. Cambiar/Agregar número")
        print("   2. Eliminar número actual")
        print("   3. Verificar número actual")
        print("   4. Cancelar")
        
        choice = input("\n   Seleccione (1-4): ").strip()
        
        if choice == '1':
            return self.set_phone_number()
        elif choice == '2':
            return self.remove_phone_number()
        elif choice == '3':
            return self.verify_attribute('phone_number')
        else:
            print("   Operación cancelada")
            return False
    
    def set_phone_number(self):
        """Establece un nuevo número de teléfono"""
        print("\n📱 ESTABLECER NUEVO NÚMERO")
        print("-" * 50)
        
        print("   Formato requerido: +595XXXXXXXXX")
        new_phone = input("   Nuevo número (con +595): ").strip()
        
        # Validar formato
        if not new_phone.startswith("+595"):
            print("❌ El número debe comenzar con +595")
            return False
        
        # Validar que solo contenga números después del código de país
        phone_digits = new_phone[4:]  # Quitar +595
        if not phone_digits.isdigit() or len(phone_digits) < 9:
            print("❌ Formato de número inválido")
            return False
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.UpdateUserAttributes'
                },
                json={
                    'AccessToken': self.access_token,
                    'UserAttributes': [
                        {
                            'Name': 'phone_number',
                            'Value': new_phone
                        }
                    ]
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Número actualizado exitosamente")
                print("   Se enviará un código de verificación por SMS")
                
                # Actualizar atributos locales
                self.user_attributes['phone_number'] = new_phone
                self.user_attributes['phone_number_verified'] = 'false'
                
                # Solicitar verificación
                verify = input("\n   ¿Desea verificar el número ahora? (s/n): ").strip().lower()
                if verify == 's':
                    return self.verify_attribute('phone_number')
                
                return True
            else:
                print(f"❌ Error al actualizar número: {response.status_code}")
                try:
                    error_data = response.json()
                    error_type = error_data.get('__type', '')
                    
                    if 'InvalidParameterException' in error_type:
                        print("   El formato del número es inválido")
                    elif 'AliasExistsException' in error_type:
                        print("   Este número ya está registrado en otra cuenta")
                    else:
                        print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error actualizando número: {e}")
            return False
    
    def remove_phone_number(self):
        """Elimina el número de teléfono del usuario"""
        print("\n🗑️  ELIMINAR NÚMERO DE TELÉFONO")
        print("-" * 50)
        
        if 'phone_number' not in self.user_attributes:
            print("ℹ️  No hay número configurado")
            return False
        
        print("⚠️  ADVERTENCIA: Esto deshabilitará SMS MFA si está activo")
        confirm = input("   ¿Está seguro? (s/n): ").strip().lower()
        
        if confirm != 's':
            print("   Operación cancelada")
            return False
        
        try:
            # Primero deshabilitar SMS MFA si está activo
            self.set_mfa_preference(sms_enabled=False)
            
            # Eliminar el atributo phone_number (establecerlo vacío)
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.DeleteUserAttributes'
                },
                json={
                    'AccessToken': self.access_token,
                    'UserAttributeNames': ['phone_number']
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Número eliminado exitosamente")
                
                # Actualizar atributos locales
                if 'phone_number' in self.user_attributes:
                    del self.user_attributes['phone_number']
                if 'phone_number_verified' in self.user_attributes:
                    del self.user_attributes['phone_number_verified']
                
                return True
            else:
                print(f"❌ Error al eliminar número: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error eliminando número: {e}")
            return False
    
    def set_mfa_preference(self, sms_enabled=None, totp_enabled=None):
        """Configura las preferencias de MFA del usuario"""
        print("\n🔐 CONFIGURANDO PREFERENCIAS MFA")
        print("-" * 50)
        
        request_data = {
            'AccessToken': self.access_token
        }
        
        # Configurar SMS MFA
        if sms_enabled is not None:
            request_data['SMSMfaSettings'] = {
                'Enabled': sms_enabled,
                'PreferredMfa': sms_enabled
            }
            action = "habilitado" if sms_enabled else "deshabilitado"
            print(f"   SMS MFA será {action}")
        
        # Configurar TOTP MFA (aplicaciones como Google Authenticator)
        if totp_enabled is not None:
            request_data['SoftwareTokenMfaSettings'] = {
                'Enabled': totp_enabled,
                'PreferredMfa': totp_enabled
            }
            action = "habilitado" if totp_enabled else "deshabilitado"
            print(f"   TOTP MFA será {action}")
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.SetUserMFAPreference'
                },
                json=request_data,
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Preferencias MFA actualizadas exitosamente")
                
                # Actualizar credenciales locales
                if "mfa_settings" not in self.credentials:
                    self.credentials["mfa_settings"] = {}
                
                if sms_enabled is not None:
                    self.credentials["mfa_settings"]["sms_enabled"] = sms_enabled
                if totp_enabled is not None:
                    self.credentials["mfa_settings"]["totp_enabled"] = totp_enabled
                self.credentials["mfa_settings"]["updated"] = datetime.now().isoformat()
                
                self.save_credentials()
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                try:
                    error_data = response.json()
                    error_type = error_data.get('__type', '')
                    
                    if 'InvalidParameterException' in error_type:
                        if sms_enabled:
                            print("   No se puede habilitar SMS MFA sin un número verificado")
                        else:
                            print("   Configuración inválida")
                    else:
                        print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en SetUserMFAPreference: {e}")
            return False
    
    def check_pool_mfa_configuration(self):
        """Verifica si el pool de usuarios tiene TOTP habilitado"""
        print("\n🔍 VERIFICANDO CONFIGURACIÓN MFA DEL POOL")
        print("-" * 50)
        
        # Nota: Este endpoint requeriría permisos administrativos
        # Por ahora, intentaremos configurar TOTP y manejar el error si no está habilitado
        
        print("   ℹ️  Verificando soporte para TOTP MFA...")
        
        # Intentar una operación simple con TOTP para verificar si está habilitado
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.AssociateSoftwareToken'
                },
                json={
                    'AccessToken': self.access_token
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("   ✅ TOTP MFA está habilitado en el pool")
                return True
            elif response.status_code == 400:
                error_data = response.json()
                error_type = error_data.get('__type', '')
                
                if 'SoftwareTokenMFANotFoundException' in error_type:
                    print("   ❌ TOTP MFA NO está habilitado en este pool de usuarios")
                    print("   ℹ️  Solo SMS MFA está disponible")
                    return False
                else:
                    print(f"   ⚠️  Estado desconocido: {error_data.get('message', '')}")
                    return None
            else:
                print(f"   ⚠️  No se pudo verificar: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ⚠️  Error verificando: {e}")
            return None
    
    def disable_all_mfa(self):
        """Deshabilita completamente MFA"""
        print("\n⚠️  DESHABILITANDO TODO MFA")
        print("-" * 50)
        print("   Esto reducirá la seguridad de tu cuenta")
        
        confirm = input("   ¿Estás seguro? (s/n): ").strip().lower()
        if confirm != 's':
            print("❌ Operación cancelada")
            return False
        
        return self.set_mfa_preference(sms_enabled=False, totp_enabled=False)
    
    def enable_sms_mfa_only(self):
        """Habilita solo MFA por SMS"""
        print("\n📱 HABILITANDO MFA POR SMS")
        print("-" * 50)
        
        # Verificar que hay un número verificado
        phone = self.user_attributes.get('phone_number')
        phone_verified = self.user_attributes.get('phone_number_verified', 'false')
        
        if not phone:
            print("❌ No hay número de teléfono configurado")
            print("   Configure un número primero (Opción 9)")
            return False
        
        if phone_verified != 'true':
            print("⚠️  El número no está verificado")
            verify = input("   ¿Desea verificarlo ahora? (s/n): ").strip().lower()
            if verify == 's':
                if not self.verify_attribute('phone_number'):
                    return False
        
        return self.set_mfa_preference(sms_enabled=True, totp_enabled=False)
    
    def change_password(self):
        """Cambia la contraseña del usuario"""
        print("\n🔑 CAMBIO DE CONTRASEÑA")
        print("-" * 50)
        
        # Solicitar contraseña actual
        print("   Ingrese la contraseña ACTUAL (sin el prefijo COG):")
        current_password = getpass.getpass("   Contraseña actual: ").strip()
        current_password = "COG" + current_password
        
        # Solicitar nueva contraseña
        print("\n   Ingrese la NUEVA contraseña (sin el prefijo COG):")
        new_password = getpass.getpass("   Nueva contraseña: ").strip()
        new_password_confirm = getpass.getpass("   Confirme nueva contraseña: ").strip()
        
        if new_password != new_password_confirm:
            print("❌ Las contraseñas no coinciden")
            return False
        
        new_password = "COG" + new_password
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.ChangePassword'
                },
                json={
                    'AccessToken': self.access_token,
                    'PreviousPassword': current_password,
                    'ProposedPassword': new_password
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Contraseña cambiada exitosamente")
                print("   Use la nueva contraseña en su próximo inicio de sesión")
                return True
            else:
                print(f"❌ Error al cambiar contraseña: {response.status_code}")
                try:
                    error_data = response.json()
                    message = error_data.get('message', '')
                    
                    if 'NotAuthorizedException' in str(error_data):
                        print("   La contraseña actual es incorrecta")
                    elif 'InvalidPasswordException' in str(error_data):
                        print("   La nueva contraseña no cumple con los requisitos")
                        print("   Debe tener al menos 8 caracteres, mayúsculas, minúsculas y números")
                    else:
                        print(f"   Mensaje: {message}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en ChangePassword: {e}")
            return False
    
    def update_email(self):
        """Actualiza el email del usuario"""
        print("\n📧 ACTUALIZAR EMAIL")
        print("-" * 50)
        
        current_email = self.user_attributes.get('email', 'No configurado')
        print(f"   Email actual: {current_email}")
        
        new_email = input("   Nuevo email: ").strip()
        if not new_email or '@' not in new_email:
            print("❌ Email inválido")
            return False
        
        try:
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.UpdateUserAttributes'
                },
                json={
                    'AccessToken': self.access_token,
                    'UserAttributes': [
                        {
                            'Name': 'email',
                            'Value': new_email
                        }
                    ]
                },
                verify=False
            )
            
            if response.status_code == 200:
                print("✅ Email actualizado exitosamente")
                print("   Se enviará un código de verificación al nuevo email")
                
                # Actualizar atributos locales
                self.user_attributes['email'] = new_email
                self.user_attributes['email_verified'] = 'false'
                
                # Solicitar verificación
                verify = input("\n   ¿Desea verificar el email ahora? (s/n): ").strip().lower()
                if verify == 's':
                    return self.verify_attribute('email')
                
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
            print(f"❌ Error en UpdateUserAttributes: {e}")
            return False
    
    def verify_attribute(self, attribute_name):
        """Inicia la verificación de un atributo (email o phone_number)"""
        print(f"\n✉️  VERIFICACIÓN DE {attribute_name.upper()}")
        print("-" * 50)
        
        # Verificar que el atributo existe
        if attribute_name not in self.user_attributes:
            print(f"❌ No hay {attribute_name} configurado")
            return False
        
        try:
            # Solicitar código de verificación
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.GetUserAttributeVerificationCode'
                },
                json={
                    'AccessToken': self.access_token,
                    'AttributeName': attribute_name
                },
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                delivery = result.get('CodeDeliveryDetails', {})
                
                print(f"✅ Código de verificación enviado")
                print(f"   Destino: {delivery.get('Destination', 'N/A')}")
                print(f"   Medio: {delivery.get('DeliveryMedium', 'N/A')}")
                
                # Solicitar código al usuario
                code = input("\n   Ingrese el código de verificación: ").strip()
                
                if code:
                    # Verificar el código
                    verify_response = requests.post(
                        self.base_url,
                        headers={
                            **self.headers,
                            'X-Amz-Target': 'AWSCognitoIdentityProviderService.VerifyUserAttribute'
                        },
                        json={
                            'AccessToken': self.access_token,
                            'AttributeName': attribute_name,
                            'Code': code
                        },
                        verify=False
                    )
                    
                    if verify_response.status_code == 200:
                        print(f"✅ {attribute_name} verificado exitosamente")
                        
                        # Actualizar atributos locales
                        self.user_attributes[f"{attribute_name}_verified"] = 'true'
                        
                        return True
                    else:
                        print("❌ Código incorrecto o expirado")
                        return False
            else:
                print(f"❌ Error al solicitar código: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Mensaje: {error_data.get('message', response.text)}")
                except:
                    print(f"   Respuesta: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            return False
    
    def setup_totp_mfa(self):
        """Configura MFA con aplicación autenticadora (TOTP)"""
        print("\n📱 CONFIGURAR MFA CON APLICACIÓN AUTENTICADORA")
        print("-" * 50)
        
        # Verificar primero si TOTP está habilitado en el pool
        totp_available = self.check_pool_mfa_configuration()
        
        if totp_available == False:
            print("\n❌ TOTP MFA no está disponible en este sistema")
            print("   Solo puede usar SMS MFA")
            print("\n   Opciones alternativas:")
            print("   1. Use SMS MFA (Opción 3 en el menú principal)")
            print("   2. Contacte al administrador para habilitar TOTP en el pool")
            return False
        elif totp_available == None:
            print("\n⚠️  No se pudo verificar la disponibilidad de TOTP")
            confirm = input("   ¿Desea intentar configurarlo de todos modos? (s/n): ").strip().lower()
            if confirm != 's':
                return False
        
        print("   Compatible con Google Authenticator, Authy, Microsoft Authenticator, etc.")
        
        try:
            # Asociar token de software
            response = requests.post(
                self.base_url,
                headers={
                    **self.headers,
                    'X-Amz-Target': 'AWSCognitoIdentityProviderService.AssociateSoftwareToken'
                },
                json={
                    'AccessToken': self.access_token
                },
                verify=False
            )
            
            if response.status_code == 200:
                result = response.json()
                secret_code = result.get('SecretCode', '')
                
                if secret_code:
                    print("\n✅ Código secreto generado")
                    print("\n📱 INSTRUCCIONES:")
                    print("1. Abra su aplicación autenticadora")
                    print("2. Agregue una nueva cuenta")
                    print("3. Escanee el código QR o ingrese manualmente:")
                    print(f"\n   🔑 Código secreto: {secret_code}")
                    print(f"   📧 Cuenta: {self.username or 'TigoMoney'}")
                    print("   🏢 Emisor: AWS Cognito")
                    
                    # Solicitar código de verificación
                    print("\n4. Ingrese el código de 6 dígitos de su aplicación:")
                    totp_code = input("   Código: ").strip()
                    
                    if totp_code and len(totp_code) == 6:
                        # Verificar el token de software
                        verify_response = requests.post(
                            self.base_url,
                            headers={
                                **self.headers,
                                'X-Amz-Target': 'AWSCognitoIdentityProviderService.VerifySoftwareToken'
                            },
                            json={
                                'AccessToken': self.access_token,
                                'UserCode': totp_code
                            },
                            verify=False
                        )
                        
                        if verify_response.status_code == 200:
                            print("✅ Aplicación autenticadora configurada exitosamente")
                            
                            # Habilitar TOTP MFA
                            self.set_mfa_preference(totp_enabled=True)
                            return True
                        else:
                            print("❌ Código incorrecto")
                            return False
                    else:
                        print("❌ Código inválido")
                        return False
                else:
                    print("❌ No se pudo generar el código secreto")
                    return False
            elif response.status_code == 400:
                error_data = response.json()
                error_type = error_data.get('__type', '')
                
                if 'SoftwareTokenMFANotFoundException' in error_type:
                    print("❌ TOTP MFA no está habilitado en este pool de usuarios")
                    print("   Solo SMS MFA está disponible")
                else:
                    print(f"❌ Error: {error_data.get('message', response.text)}")
                return False
            else:
                print(f"❌ Error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error configurando TOTP: {e}")
            return False
    
    def list_mfa_options(self):
        """Lista todas las opciones MFA disponibles y su estado"""
        print("\n🔐 ESTADO DE OPCIONES MFA")
        print("-" * 50)
        
        print("\n1. SMS MFA:")
        print("   - Estado: ", end="")
        
        phone = self.user_attributes.get('phone_number', None)
        phone_verified = self.user_attributes.get('phone_number_verified', 'false')
        
        if not phone:
            print("❌ No disponible (sin número)")
        elif phone_verified != 'true':
            print("⚠️  Disponible pero no verificado")
        else:
            print("✅ Disponible y verificado")
        
        print(f"   - Número: {phone if phone else 'No configurado'}")
        print(f"   - Verificado: {'✅ Sí' if phone_verified == 'true' else '❌ No'}")
        
        # Verificar si SMS MFA está activo
        sms_active = False
        for mfa in self.mfa_options:
            if mfa.get('DeliveryMedium') == 'SMS':
                sms_active = True
                break
        print(f"   - MFA Activo: {'✅ Sí' if sms_active else '❌ No'}")
        
        print("\n2. TOTP MFA (Aplicación Autenticadora):")
        
        # Verificar disponibilidad de TOTP
        totp_status = self.check_pool_mfa_configuration()
        if totp_status == False:
            print("   - Estado: ❌ No habilitado en el pool")
            print("   - Esta opción no está disponible en este sistema")
        elif totp_status == True:
            print("   - Estado: ✅ Disponible")
            print("   - Compatible con: Google Authenticator, Authy, etc.")
        else:
            print("   - Estado: ⚠️  Desconocido")
        
        print("\n3. Sin MFA:")
        print("   - ⚠️  NO RECOMENDADO")
        print("   - Reduce significativamente la seguridad")
        print("   - Solo contraseña para acceder")
        
        # Mostrar configuración actual
        if self.credentials and "mfa_settings" in self.credentials:
            mfa_settings = self.credentials["mfa_settings"]
            print("\n📊 Configuración guardada localmente:")
            print(f"   - SMS habilitado: {mfa_settings.get('sms_enabled', 'N/A')}")
            print(f"   - TOTP habilitado: {mfa_settings.get('totp_enabled', 'N/A')}")
            print(f"   - Última actualización: {mfa_settings.get('updated', 'N/A')}")
    
    def save_credentials(self):
        """Guarda las credenciales actualizadas"""
        try:
            self.credentials["timestamp"] = datetime.now().isoformat()
            
            with open("credenciales.json", "w", encoding="utf-8") as f:
                json.dump(self.credentials, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ Error al guardar credenciales: {e}")
            return False
    
    def export_security_config(self):
        """Exporta la configuración de seguridad actual"""
        print("\n💾 EXPORTANDO CONFIGURACIÓN DE SEGURIDAD")
        print("-" * 50)
        
        config = {
            "timestamp": datetime.now().isoformat(),
            "username": self.username,
            "attributes": self.user_attributes,
            "mfa_options": self.mfa_options,
            "security_settings": {
                "phone_number": self.user_attributes.get('phone_number', None),
                "phone_verified": self.user_attributes.get('phone_number_verified', 'false'),
                "email": self.user_attributes.get('email', None),
                "email_verified": self.user_attributes.get('email_verified', 'false'),
                "mfa_configured": len(self.mfa_options) > 0
            }
        }
        
        filename = f"security_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Configuración exportada a: {filename}")
            return True
        except Exception as e:
            print(f"❌ Error al exportar: {e}")
            return False
    
    def main_menu(self):
        """Menú principal del gestor de seguridad"""
        while True:
            print("\n" + "=" * 60)
            print("   🔐 GESTOR DE SEGURIDAD - TIGO MONEY")
            print("=" * 60)
            print("\n📋 Opciones disponibles:")
            print("   1. 📋 Ver información del usuario y configuración actual")
            print("   2. 🚫 Deshabilitar TODO MFA (reduce seguridad)")
            print("   3. 📱 Habilitar solo MFA por SMS")
            print("   4. 📲 Configurar MFA con aplicación autenticadora")
            print("   5. 🔑 Cambiar contraseña")
            print("   6. 📧 Actualizar email")
            print("   7. ✉️  Verificar email actual")
            print("   8. 📞 Verificar número de teléfono")
            print("   9. 📱 Gestionar número de teléfono (cambiar/eliminar)")
            print("  10. 📊 Ver estado de opciones MFA")
            print("  11. 💾 Exportar configuración de seguridad")
            print("  12. 🚪 Salir")
            print()
            
            choice = input("Seleccione una opción (1-12): ").strip()
            
            if choice == '1':
                self.get_user_info()
                
            elif choice == '2':
                self.disable_all_mfa()
                
            elif choice == '3':
                self.enable_sms_mfa_only()
                
            elif choice == '4':
                self.setup_totp_mfa()
                
            elif choice == '5':
                self.change_password()
                
            elif choice == '6':
                self.update_email()
                
            elif choice == '7':
                self.verify_attribute('email')
                
            elif choice == '8':
                self.verify_attribute('phone_number')
                
            elif choice == '9':
                self.update_phone_number()
                
            elif choice == '10':
                self.list_mfa_options()
                
            elif choice == '11':
                self.export_security_config()
                
            elif choice == '12':
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida")
            
            if choice in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']:
                input("\nPresione Enter para continuar...")

def main():
    print("=" * 50)
    print("   GESTOR DE SEGURIDAD - TIGO MONEY")
    print("=" * 50)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    manager = CognitoSecurityManager()
    
    # Cargar credenciales
    if not manager.load_credentials():
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    print("\n⚠️  ADVERTENCIA DE SEGURIDAD")
    print("-" * 50)
    print("Este módulo permite modificar configuraciones críticas de seguridad.")
    print("Use con precaución y bajo su propia responsabilidad.")
    
    # Obtener información inicial
    manager.get_user_info()
    
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