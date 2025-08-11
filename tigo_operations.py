#!/usr/bin/env python3
"""
Script para gestión de operaciones Tigo Money
Utiliza el IdToken de credenciales.json para autorización
"""

import json
import requests
import time
import os
from datetime import datetime
from pathlib import Path
import signal
import sys
import urllib3

# Deshabilitar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TigoMoneyOperations:
    def __init__(self):
        self.base_url = "https://py.tigomoney.io"
        self.api_key = "rqt5y3XnRI6FM17kKuENR53J2DUTTOM35djPZl6I"
        self.id_token = None
        self.headers = {}
        self.running = True
        
        # Configurar carpetas
        self.numbers_info_dir = Path("NumbersInfo")
        self.pending_ops_dir = Path("PendingOperations")
        self.numbers_info_dir.mkdir(exist_ok=True)
        self.pending_ops_dir.mkdir(exist_ok=True)
        
        # Cargar credenciales
        self.load_credentials()
        
    def load_credentials(self):
        """Carga el IdToken desde credenciales.json"""
        try:
            with open("credenciales.json", "r", encoding="utf-8") as f:
                credentials = json.load(f)
                self.id_token = credentials.get("IdToken")
                
                if not self.id_token:
                    print("❌ No se encontró IdToken en credenciales.json")
                    sys.exit(1)
                    
                # Configurar headers comunes
                self.headers = {
                    "authorization": self.id_token,
                    "x-api-key": self.api_key,
                    "content-type": "application/json",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
                    "origin": "https://moneyapp.tigo.com.py",
                    "referer": "https://moneyapp.tigo.com.py/",
                    "accept": "*/*",
                    "accept-language": "es-ES,es;q=0.9"
                }
                
                print("✅ Credenciales cargadas exitosamente")
                
        except FileNotFoundError:
            print("❌ No se encontró el archivo credenciales.json")
            print("   Por favor, ejecute primero el script de autenticación")
            sys.exit(1)
        except json.JSONDecodeError:
            print("❌ Error al leer credenciales.json")
            sys.exit(1)
    
    def validate_number(self, number):
        """Valida que el número tenga 10 dígitos y solo contenga números"""
        if not number.isdigit():
            return False
        if len(number) != 10:
            return False
        return True
    
    def get_account_info(self, number):
        """Obtiene información de la cuenta para un número dado"""
        url = f"{self.base_url}/accounts/msisdn/{number}/accountinfo"
        
        print(f"\n🔍 Obteniendo información del número {number}...")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                # Guardar en archivo
                file_path = self.numbers_info_dir / f"{number}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Información obtenida y guardada en {file_path}")
                
                # Mostrar resumen
                if "name" in data and "fullName" in data["name"]:
                    print(f"   Nombre: {data['name']['fullName']}")
                if "status" in data:
                    print(f"   Estado: {data['status']}")
                if "subStatus" in data:
                    print(f"   Sub-Estado: {data['subStatus']}")
                    
                return data
            else:
                print(f"❌ Error al obtener información: {response.status_code}")
                if response.text:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def get_pending_operations(self, number):
        """Obtiene las operaciones pendientes para un número dado"""
        url = f"{self.base_url}/accounts/msisdn/{number}/pendingoperations"
        
        print(f"\n🔍 Consultando operaciones pendientes para {number}...")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                
                if not data or data == []:
                    print("ℹ️ No hay operaciones pendientes")
                    return []
                
                print(f"✅ Se encontraron {len(data)} operación(es) pendiente(s)")
                
                # Mostrar detalles de las operaciones
                for i, op in enumerate(data, 1):
                    print(f"\n   Operación {i}:")
                    print(f"   - Tipo: {op.get('type', 'N/A')}")
                    print(f"   - Monto: {op.get('currency', '')} {op.get('amount', 'N/A')}")
                    print(f"   - Descripción: {op.get('descriptionText', 'N/A')}")
                    print(f"   - Referencia: {op.get('pendingReference', 'N/A')}")
                    print(f"   - Fecha solicitud: {op.get('requestDate', 'N/A')}")
                    print(f"   - Fecha expiración: {op.get('expirationDate', 'N/A')}")
                    
                    # Buscar notificationText en metadata
                    metadata = op.get('metadata', [])
                    for meta in metadata:
                        if meta.get('key') == 'notificationText':
                            print(f"   - Notificación: {meta.get('value', '')}")
                
                return data
            else:
                print(f"❌ Error al obtener operaciones: {response.status_code}")
                if response.text:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def accept_pending_operation(self, pending_reference, number):
        """Acepta una operación pendiente"""
        url = f"{self.base_url}/accounts/pendingoperations/{pending_reference}"
        
        print(f"\n✅ Aceptando operación con referencia {pending_reference}...")
        
        data = {
            "op": "REPLACE",
            "path": "status",
            "value": "confirm"
        }
        
        try:
            response = requests.patch(url, headers=self.headers, json=data, timeout=30, verify=False)
            
            if response.status_code in [200, 201]:
                result = response.json()
                print(f"✅ Operación aceptada exitosamente")
                print(f"   - Referencia de transacción: {result.get('transactionReference', 'N/A')}")
                print(f"   - Estado: {result.get('status', 'N/A')}")
                return result
            else:
                print(f"❌ Error al aceptar operación: {response.status_code}")
                if response.text:
                    print(f"   Respuesta: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error de conexión: {e}")
            return None
    
    def save_pending_operation_result(self, number, pending_ops, accept_result):
        """Guarda el resultado de una operación pendiente aceptada"""
        file_path = self.pending_ops_dir / f"{number}.json"
        
        # Cargar datos existentes si el archivo existe
        existing_data = []
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
            except:
                existing_data = []
        
        # Crear nuevo registro
        new_record = {
            "timestamp": datetime.now().isoformat(),
            "pending_operations": pending_ops,
            "accept_result": accept_result
        }
        
        existing_data.append(new_record)
        
        # Guardar datos actualizados
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Resultado guardado en {file_path}")
    
    def option_get_info(self):
        """Opción 1: Obtener información del número"""
        number = input("\n📱 Ingrese el número (10 dígitos): ").strip()
        
        if not self.validate_number(number):
            print("❌ El número debe tener exactamente 10 dígitos numéricos")
            return
        
        self.get_account_info(number)
    
    def option_pending_operations(self):
        """Opción 2: Obtener y gestionar operaciones pendientes"""
        number = input("\n📱 Ingrese el número (10 dígitos): ").strip()
        
        if not self.validate_number(number):
            print("❌ El número debe tener exactamente 10 dígitos numéricos")
            return
        
        pending_ops = self.get_pending_operations(number)
        
        if pending_ops and pending_ops != []:
            print("\n" + "=" * 50)
            choice = input("¿Desea aceptar la(s) operación(es) pendiente(s)? (s/n): ").strip().lower()
            
            if choice == 's':
                for op in pending_ops:
                    pending_ref = op.get('pendingReference')
                    if pending_ref:
                        result = self.accept_pending_operation(pending_ref, number)
                        if result:
                            self.save_pending_operation_result(number, pending_ops, result)
                        else:
                            print("❌ No se pudo aceptar la operación, regresando al menú...")
                            return
            else:
                print("ℹ️ Operación cancelada por el usuario")
    
    def signal_handler(self, sig, frame):
        """Manejador para Ctrl+C"""
        print("\n\n⚠️ Modo automático cancelado por el usuario")
        self.running = False
    
    def option_automatic_mode(self):
        """Opción 3: Modo automático"""
        number = input("\n📱 Ingrese el número (10 dígitos): ").strip()
        
        if not self.validate_number(number):
            print("❌ El número debe tener exactamente 10 dígitos numéricos")
            return
        
        # Obtener información inicial
        info = self.get_account_info(number)
        if not info:
            print("❌ No se pudo obtener información del número")
            return
        
        print("\n" + "=" * 50)
        print("🤖 MODO AUTOMÁTICO ACTIVADO")
        print("   Consultando operaciones pendientes cada 5 segundos...")
        print("   Presione Ctrl+C para detener")
        print("=" * 50)
        
        # Configurar manejador de señal
        signal.signal(signal.SIGINT, self.signal_handler)
        self.running = True
        
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        while self.running:
            try:
                # Obtener operaciones pendientes
                pending_ops = self.get_pending_operations(number)
                
                if pending_ops is None:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"\n❌ Se alcanzó el límite de {max_consecutive_errors} errores consecutivos")
                        print("   Deteniendo modo automático...")
                        break
                else:
                    consecutive_errors = 0  # Resetear contador de errores
                    
                    if pending_ops and pending_ops != []:
                        print(f"\n🎯 ¡Operación pendiente detectada! Aceptando automáticamente...")
                        
                        for op in pending_ops:
                            pending_ref = op.get('pendingReference')
                            if pending_ref:
                                result = self.accept_pending_operation(pending_ref, number)
                                if result:
                                    self.save_pending_operation_result(number, pending_ops, result)
                                    print("✅ Operación procesada y guardada exitosamente")
                    else:
                        print(f"⏳ [{datetime.now().strftime('%H:%M:%S')}] Sin operaciones pendientes...")
                
                # Esperar 5 segundos antes de la siguiente consulta
                if self.running:
                    time.sleep(5)
                    
            except Exception as e:
                print(f"\n❌ Error inesperado: {e}")
                break
        
        print("\n" + "=" * 50)
        input("Presione Enter para volver al menú principal...")
    
    def main_menu(self):
        """Menú principal del programa"""
        while True:
            print("\n" + "=" * 50)
            print("   TIGO MONEY - SISTEMA DE OPERACIONES")
            print("=" * 50)
            print("\n📋 Opciones disponibles:")
            print("   1. Obtener Información del número")
            print("   2. Obtener Operaciones Pendientes")
            print("   3. Modo Automático")
            print("   4. Salir")
            print()
            
            choice = input("Seleccione una opción (1-4): ").strip()
            
            if choice == "1":
                self.option_get_info()
                input("\nPresione Enter para continuar...")
                
            elif choice == "2":
                self.option_pending_operations()
                input("\nPresione Enter para continuar...")
                
            elif choice == "3":
                self.option_automatic_mode()
                
            elif choice == "4":
                print("\n👋 ¡Hasta luego!")
                break
                
            else:
                print("❌ Opción inválida. Por favor seleccione 1, 2, 3 o 4")

def main():
    print("=" * 50)
    print("   TIGO MONEY - SISTEMA DE OPERACIONES")
    print("=" * 50)
    print("⚠️  Verificación SSL deshabilitada para compatibilidad")
    
    try:
        app = TigoMoneyOperations()
        app.main_menu()
    except KeyboardInterrupt:
        print("\n\n⚠️ Programa terminado por el usuario")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()