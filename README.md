# Examen Técnico — Data Engineer Semi Senior

Solución completa al examen técnico de Financiera OH. Cubre análisis SQL, integración de datos, calidad de datos y desafío avanzado con IA generativa.

---

## Estructura del proyecto

```
exNovaCamp/
├── archivos/
│   ├── customers.csv
│   ├── cards.csv
│   ├── transactions.csv
│   ├── cards_processor_a.csv
│   ├── cards_processor_b.csv
│   ├── equivalence_table_extended.csv
│   ├── financial_rules.csv
│   ├── transactions_anomalies.csv
│   ├── business_rules_text.csv
│   ├── data_quality_report.json          ← generado por data_quality.py
│   ├── transactions_anomalies_clean.csv  ← generado por data_quality.py
│   ├── desafio_avanzado_B.docx           ← análisis business_rules_text
│   └── pipeline_documentacion.docx       ← documentación completa del pipeline
├── explorer.py          ← Parte 1 y Parte 2 (SQL con DuckDB)
├── data_quality.py      ← Parte 3 (Data Quality Report)
├── load_bq.py           ← Opcional: carga a BigQuery
├── generar_word.py      ← Genera desafio_avanzado_B.docx
└── generar_pipeline_doc.py ← Genera pipeline_documentacion.docx
```

---

## Requisitos

```bash
pip install duckdb pandas openpyxl python-docx
```

---

## Parte 1 — Ejercicios SQL

Archivo: `explorer.py`

Las queries usan **DuckDB** con SQL estándar compatible con BigQuery. Se ejecutan directamente sobre los archivos CSV.

| # | Consulta | Técnica | Resultado |
|---|---|---|---|
| 1.1 | Clientes por segmento | `COUNT + GROUP BY` | Bronze: 5, Gold: 2, Silver: 3 |
| 1.2 | Transacciones y monto por tipo de tarjeta | `INNER JOIN + SUM` | Mastercard $3,853 / Visa $3,549 |
| 1.3 | Clientes con tarjeta Blocked | `INNER JOIN + WHERE` | 3 clientes |
| 1.4 | Monto promedio por cliente (>3 tx) | `Doble JOIN + AVG + HAVING` | 3 clientes cumplen el criterio |
| 1.5 | Transacciones sobre percentil 90 | `Subquery + PERCENTILE_CONT` | 3 transacciones (>$471) |
| 1.6 | Transacciones con tarjetas inexistentes | `LEFT JOIN + IS NULL` | 0 filas — datos íntegros |

```bash
python3 explorer.py
```

---

## Parte 1 — Preguntas Conceptuales

**Pregunta 7 — Tabla transacciones enriquecidas**

Esquema propuesto para capa BI:

| Columna | Tipo | Descripción |
|---|---|---|
| tx_id | INT64 | Identificador único de transacción |
| tx_date | DATE | Fecha de transacción (base para partición) |
| customer_id | INT64 | FK del cliente |
| full_name | STRING | Nombre del cliente |
| segment | STRING | Segmento del cliente (Bronze/Silver/Gold) |
| card_id | INT64 | FK de la tarjeta |
| card_type | STRING | Tipo de tarjeta |
| card_status | STRING | Estado de la tarjeta |
| amount | FLOAT64 | Monto de la transacción |
| register_date | DATE | Fecha de registro del cliente |

**Pregunta 8 — Particiones vs Clustering**

- **Partición por `tx_date`**: las queries siempre acotan por rango de fechas — BigQuery escanea solo las particiones relevantes.
- **Clustering por `segment` y `card_type`**: dimensiones de análisis frecuentes en BI — reduce el escaneo dentro de cada partición.

**Pregunta 9 — Escalabilidad 10x**

1. Partición diaria por `tx_date`
2. Clustering por `segment` + `card_type`
3. Expiración automática de particiones antiguas
4. Materialized Views para KPIs recurrentes
5. Disciplina en queries — evitar `SELECT *`

---

## Parte 2 — Pipeline cards_financial_master

Archivo: `explorer.py` (sección 2.1)

Pipeline construido con **4 CTEs encadenados**:

```
unified → standardized → enriched → cards_financial_master
```

| CTE | Operación |
|---|---|
| `unified` | `UNION ALL` de `cards_processor_a` y `cards_processor_b` con columna `processor` |
| `standardized` | Doble `LEFT JOIN` contra `equivalence_table_extended` para normalizar tipo y estado |
| `enriched` | `LEFT JOIN` contra `financial_rules` para traer tasas, comisiones y seguros |
| `cards_financial_master` | Cálculo de `monthly_total_cost = interest_rate * 1000 + commission + insurance_fee` + columnas de auditoría |

**Fórmula:**
```
monthly_total_cost = interest_rate × 1000 + commission + insurance_fee
```

**En BigQuery productivo:**
```sql
CREATE OR REPLACE TABLE dataset.cards_financial_master
PARTITION BY load_date
CLUSTER BY processor, customer_id, card_type, status
AS ( ... )
```

---

## Parte 3 — Data Quality Report

Archivo: `data_quality.py`

```bash
python3 data_quality.py
```

**Validaciones aplicadas sobre `transactions_anomalies.csv`:**

| Validación | Resultado |
|---|---|
| Valores nulos | `tx_date`: 9, `amount`: 5, `card_id`: 4 |
| Duplicados | 0 |
| Fechas futuras | 5 transacciones |
| `card_id` inexistentes en procesadores | 7 filas (X9999 + nulls) |
| Campos no documentados | `extra_column` |
| Montos negativos | 9 transacciones |

**Resultado de limpieza:** 1 fila limpia de 20 originales (dataset de prueba con anomalías intencionales).

**Archivos generados:**
- `archivos/data_quality_report.json` — reporte completo de problemas
- `archivos/transactions_anomalies_clean.csv` — dataset limpio

**Carga a BigQuery (opcional):**
```bash
python3 load_bq.py
```

---

## Desafío Avanzado

### A) Auditoría de SQL generado con IA

Se usó IA generativa como asistente para proponer queries y estructurar el pipeline. Errores detectados en auditoría manual:

- Nombre incorrecto de archivo (`equivalence_table` vs `equivalence_table_extended`)
- `.show()` faltante en query de Parte 1.2
- Typo en `PERCENTILE_CCNT` y estructura de sintaxis incorrecta
- `set {}` en lugar de `list []` para schema de BigQuery

### B) Análisis de business_rules_text.csv

Ver: `archivos/desafio_avanzado_B.docx`

| Regla | Implementable | Problema |
|---|---|---|
| 1 — GOLD_A → GOLD_ESTÁNDAR | Parcial | `GOLD_ESTÁNDAR` no existe en equivalence_table — usar `GOLD` |
| 2 — SILVER_B antes de 2020 → LEGACY_SILVER | No | Falta columna `issue_date` en `cards_processor_b` |
| 3 — BRONZE >20 tx → comisión reducida | Parcial | "comisión reducida" no está cuantificada en `financial_rules` |
| 4 — Cliente Gold con ≥2 tarjetas activas → beneficio premium | Parcial | "beneficio premium" no está cuantificado |

### C) Documentación del pipeline

Ver: `archivos/pipeline_documentacion.docx`

Documento Word completo con arquitectura, fuentes de datos, decisiones técnicas, resultados y recomendaciones.

### D) IA para debugging — cuándo sí y cuándo no

**Usar IA:**
- Optimización de queries, análisis de errores, generación de boilerplate, documentación automática

**No usar IA:**
- Datos con información personal real (nombres, DNI, tarjetas) — riesgo legal y ético
- Credenciales o API keys en el prompt — riesgo de seguridad
- Decisiones de arquitectura en producción sin revisión humana
- Confiar en SQL generado sin auditarlo — puede tener lógica incorrecta

**Buena práctica:** anonimizar datos antes de compartirlos con IA, como lo hace este dataset (Cliente 1, Cliente 2...).

---

## Ejecución completa

```bash
# Parte 1 y Parte 2
python3 explorer.py

# Parte 3
python3 data_quality.py

# Documentos Word
python3 generar_word.py
python3 generar_pipeline_doc.py
```
