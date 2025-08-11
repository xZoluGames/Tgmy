# 🚀 Sistema Tigo Money - Suite Completa de Gestión

Sistema integral para la gestión de operaciones Tigo Money con autenticación AWS Cognito, gestión de tokens, operaciones automatizadas y control de dispositivos.

## 📋 Tabla de Contenidos
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Estructura del Sistema](#estructura-del-sistema)
- [Guía de Uso](#guía-de-uso)
- [Módulos del Sistema](#módulos-del-sistema)
- [Solución de Problemas](#solución-de-problemas)
- [Seguridad](#seguridad)

## 🔧 Requisitos

### Software Necesario
- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Librerías Python
```bash
pip install requests urllib3
```

## 📦 Instalación

1. **Descarga todos los scripts en la misma carpeta:**
   - `tigo_money_system.py` - Script maestro (menú principal)
   - `cognito_auth.py` - Autenticación con SMS
   - `tigo_operations.py` - Operaciones y consultas
   - `update_tokens.py` - Actualización de tokens
   - `device_manager.py` - Gestión de dispositivos
   - `security_config.py` - Configuración de seguridad y MFA

2. **Instala las dependencias:**
```bash
pip install requests urllib3
```

3. **Ejecuta el sistema principal:**
```bash
python tigo_money_system.py
```

## 📁 Estructura del Sistema

```
tigo-money-system/
│
├── tigo_money_system.py    # Script maestro con menú principal
├── cognito_auth.py          # Módulo de autenticación
├── tigo_operations.py       # Módulo de operaciones
├── update_tokens.py         # Módulo de actualización de tokens
├── device_manager.py        # Módulo de gestión de dispositivos
├── security_config.py       # Módulo de configuración de seguridad
├── credenciales.json        # Archivo de tokens (se genera automáticamente)
│
├── NumbersInfo/             # Carpeta con información de números consultados
│   └── [numero].json        # Archivos JSON con datos de cada número
│
├── PendingOperations/       # Carpeta con historial de operaciones
│   └── [numero].json        # Archivos JSON con operaciones procesadas
│
└── security_config_*.json   # Exportaciones de configuración de seguridad
```

## 🚀 Guía de Uso

### Primera Vez - Configuración Inicial

1. **Ejecuta el sistema principal:**
```bash
python tigo_money_system.py
```

2. **Selecciona Opción 1 - Autenticación:**
   - Ingresa tu número con +595 (ej: +595983335492)
   - Ingresa tu contraseña (sin el prefijo COG, se agrega automáticamente)
   - Ingresa el código SMS que recibirás
   - Se generará `credenciales.json` con tus tokens

3. **Configura tu dispositivo (Opcional):**
   - Selecciona Opción 4 - Gestión de Dispositivos
   - Confirma tu dispositivo para futuras autenticaciones más rápidas

4. **Comienza a operar:**
   - Selecciona Opción 2 - Operaciones
   - Elige entre las opciones disponibles

### Uso Regular

1. **Si tus tokens expiraron:**
   - Selecciona Opción 3 - Actualizar Tokens
   - Los tokens se renovarán automáticamente

2. **Para operaciones diarias:**
   - Selecciona Opción 2 - Operaciones
   - Usa el modo automático para procesar operaciones continuamente

## 📚 Módulos del Sistema

### 1. 🔐 Autenticación (`cognito_auth.py`)

**Funciones:**
- Login con usuario y contraseña
- Verificación por SMS (MFA)
- Generación de tokens de acceso
- Guardado automático de credenciales

**Uso:**
```bash
python cognito_auth.py
```

### 2. 💼 Operaciones (`tigo_operations.py`)

**Funciones:**
- **Opción 1:** Obtener información de un número
- **Opción 2:** Consultar y aceptar operaciones pendientes
- **Opción 3:** Modo automático (consulta cada 5 segundos)

**Uso:**
```bash
python tigo_operations.py
```

**Características del Modo Automático:**
- Consulta operaciones pendientes cada 5 segundos
- Acepta automáticamente las operaciones encontradas
- Se detiene con Ctrl+C
- Guarda historial de todas las transacciones

### 3. 🔄 Actualización de Tokens (`update_tokens.py`)

**Funciones:**
- Renueva tokens antes de que expiren
- Usa RefreshToken para obtener nuevos AccessToken e IdToken
- Mantiene la sesión activa sin reautenticación

**Uso:**
```bash
python update_tokens.py
```

### 4. 📱 Gestión de Dispositivos (`device_manager.py`)

**Funciones:**
- Listar todos los dispositivos registrados
- Confirmar dispositivo actual
- Marcar dispositivo como "recordado" (salta MFA)
- Eliminar dispositivos no reconocidos

**Uso:**
```bash
python device_manager.py
```

### 5. 🔒 Configuración de Seguridad (`security_config.py`)

**Funciones:**
- **Deshabilitar/Habilitar MFA:** Control total sobre autenticación multifactor
- **Cambiar tipo de MFA:** Alternar entre SMS y aplicación autenticadora (TOTP)
- **Configurar TOTP:** Compatible con Google Authenticator, Authy, etc.
- **Cambiar contraseña:** Actualizar credenciales de acceso
- **Gestionar email:** Actualizar y verificar dirección de correo
- **Verificar atributos:** Confirmar email y número de teléfono
- **Exportar configuración:** Respaldar configuración de seguridad

**Uso:**
```bash
python security_config.py
```

**Opciones de MFA disponibles:**
- **SMS MFA:** Códigos por mensaje de texto
- **TOTP MFA:** Aplicaciones autenticadoras (más seguro)
- **Sin MFA:** No recomendado (reduce seguridad)

## 🔍 Solución de Problemas

### Error: "No se encontró credenciales.json"
**Solución:** Ejecuta primero la autenticación (Opción 1 en el menú principal)

### Error: "Token expirado"
**Solución:** Actualiza los tokens (Opción 3) o reautentica (Opción 1)

### Error: "Error de conexión"
**Posibles causas:**
- Verifica tu conexión a internet
- Los servidores pueden estar temporalmente no disponibles
- Firewall o antivirus bloqueando las conexiones

### Error: "Código SMS incorrecto"
**Solución:** 
- Verifica que ingresaste el código exacto
- Espera unos segundos después de recibir el SMS
- Si el código expiró, reinicia el proceso

### Modo automático no detecta operaciones
**Verificar:**
- El número ingresado es correcto (10 dígitos)
- Las credenciales no han expirado
- Hay operaciones pendientes reales

## 🔐 Seguridad

### Recomendaciones Importantes

1. **Protege tu archivo `credenciales.json`:**
   - No lo compartas con nadie
   - No lo subas a repositorios públicos
   - Considera encriptar el archivo si es posible

2. **Gestiona tus dispositivos:**
   - Revisa periódicamente los dispositivos registrados
   - Elimina dispositivos que no reconozcas
   - Solo marca como "recordados" dispositivos personales

3. **Configura MFA apropiadamente:**
   - **Recomendado:** Usa TOTP (aplicación autenticadora) para máxima seguridad
   - **Alternativa:** SMS MFA si no tienes acceso a aplicaciones autenticadoras
   - **Evitar:** Deshabilitar completamente MFA reduce significativamente la seguridad

4. **Actualiza tokens regularmente:**
   - Los tokens expiran cada 30 minutos
   - Actualízalos antes de que expiren para mantener la sesión

5. **Cambio de contraseña periódico:**
   - Cambia tu contraseña regularmente usando el módulo de seguridad
   - Usa contraseñas fuertes con mayúsculas, minúsculas, números y símbolos

6. **Verificación de atributos:**
   - Mantén tu email y teléfono verificados
   - Actualiza estos datos si cambian

7. **Uso en computadoras públicas:**
   - NO marques el dispositivo como recordado
   - NO deshabilites MFA
   - Elimina el archivo `credenciales.json` al terminar
   - Cierra sesión completamente

### Archivos Sensibles
- `credenciales.json` - Contiene tokens de acceso y configuración MFA
- `NumbersInfo/*.json` - Información personal de cuentas
- `PendingOperations/*.json` - Historial de transacciones
- `security_config_*.json` - Exportaciones de configuración de seguridad

## 📝 Notas Adicionales

### Estructura de credenciales.json
```json
{
  "AccessToken": "eyJ...",
  "IdToken": "eyJ...",
  "RefreshToken": "eyJ...",
  "ExpiresIn": 1800,
  "TokenType": "Bearer",
  "timestamp": "2025-08-10T21:09:31.995861",
  "device_info": {
    "device_key": "us-east-1_...",
    "device_group_key": "...",
    "device_confirmed": true,
    "device_name": "TigoMoney-Device-...",
    "device_remembered": true
  },
  "mfa_settings": {
    "sms_enabled": true,
    "totp_enabled": false,
    "updated": "2025-08-10T21:09:31.995861"
  }
}
```

### Validación de Números
- Los números deben tener exactamente 10 dígitos
- Formato: 0983335492 (sin +595)
- Solo se aceptan números numéricos

### Límites del Sistema
- Máximo 10 dispositivos por cuenta
- Tokens expiran en 30 minutos (1800 segundos)
- RefreshToken válido por 30 días
- Consultas en modo automático: cada 5 segundos

## 🆘 Soporte

Para problemas específicos con el sistema Tigo Money, contacta al soporte oficial de Tigo.

---

**Versión:** 1.1.0  
**Última actualización:** Agosto 2025  
**Compatibilidad:** Python 3.7+