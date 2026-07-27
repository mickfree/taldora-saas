## Endpoints Públicos de la API (v1)

### 1. Consulta de Tipo de Cambio USD / PEN
Obtiene el tipo de cambio oficial del día (compra y venta) para Soles peruanos (PEN) frente al Dólar estadounidense (USD).

* **URL:** `/api/v1/tipo-cambio/`
* **Método:** `GET`
* **Autenticación:** Requerida (Bearer Token / Header / Query Param)
* **Parámetros Query:**
  * `fecha` *(opcional)*: Fecha a consultar (por defecto: `Hoy`).

#### Ejemplo de Petición:
```bash
http://localhost:8000/api/v1/tipo-cambio/
```

#### Respuesta Exitosa (`200 OK`):
```json
{
  "success": true,
  "compra": 3.752,
  "venta": 3.758,
  "fecha": "2026-07-26",
  "fuente": "BCRP (26.Jul.26)"
}
```

---

### 2. Consulta de RUC SUNAT
Obtiene la información fiscal y datos completos de un contribuyente a partir de su número de RUC de 11 dígitos.

* **URL:** `/api/v1/ruc/`
* **Método:** `GET`
* **Autenticación:** Requerida (Bearer Token / Header / Query Param)
* **Parámetros Query:**
  * `numero` o `ruc` *(obligatorio)*: Número de RUC válido de 11 dígitos (Ej. `20100047218`).

#### Ejemplo de Petición:
```bash
http://127.0.0.1:8000/api/v1/ruc/?numero=20100047218 
```

#### Respuesta Exitosa (`200 OK`):
```json
{
  "success": true,
  "data": {
    "ruc": "20100047218",
    "razon_social": "PETROLEOS DEL PERU PETROPERU SA",
    "estado": "ACTIVO",
    "condicion": "HABIDO",
    "direccion": "AV. ENRIQUE CANAVAL Y MOREYRA NRO. 150",
    "departamento": "LIMA",
    "provincia": "LIMA",
    "distrito": "SAN ISIDRO",
    "ubigeo": "150131",
    "es_agente_retencion": false
  }
}
```

---

## Respuestas de Error Comunes

| Código HTTP | Significado | Estructura JSON de Ejemplo |
| :--- | :--- | :--- |
| `401 Unauthorized` | Token ausente, inválido o inactivo. | `{"success": false, "error": "Token de API inválido o inactivo."}` |
| `400 Bad Request` | Parámetros incompletos o RUC no válido (módulo 11). | `{"success": false, "error": "Debe proporcionar el parámetro 'numero'..."}` |
| `429 Too Many Requests` | Cuota de consumo del plan mensual excedida. | `{"success": false, "error": "Límite de peticiones de tu plan excedido..."}` |
| `503 Service Unavailable` | Servicio proveedor o scraper no disponible. | `{"success": false, "error": "Tipo de cambio temporalmente no disponible."}` |



