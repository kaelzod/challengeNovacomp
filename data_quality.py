import pandas as pd
import json
from datetime import date

# 1. cargando datasets
anomalias = pd.read_csv('./archivos/transactions_anomalies.csv')
cards_a = pd.read_csv('./archivos/cards_processor_a.csv')
cards_b = pd.read_csv('./archivos/cards_processor_b.csv')

reporte = {}

# 2. Nulls por columna
reporte['nulls'] = {
    col: int(count) for col, count in anomalias.isnull().sum().items() if count > 0
}

# 3. duplicados
reporte['duplicados'] = int(anomalias.duplicated().sum())
reporte['duplicados_tx_id'] = int(anomalias.duplicated(subset=['tx_id']).sum())

# 4. fechas
anomalias['tx_date'] = pd.to_datetime(anomalias['tx_date'], errors='coerce')
hoy = pd.Timestamp(date.today())
fechas_futuras = anomalias[anomalias['tx_date'] > hoy]
reporte['fechas_futuras'] = int(len(fechas_futuras))
reporte['tx_ids_fecha_futura'] = fechas_futuras['tx_id'].tolist()

# 5. existen A o B
ids_validos = set(cards_a['card_id_a']).union(set(cards_b['card_id_b']))
card_ids_invalidos = anomalias[~anomalias['card_id'].isin(ids_validos)]
reporte['card_ids_invalidos'] = int(len(card_ids_invalidos))
reporte['card_ids_invalidos_valores'] = card_ids_invalidos['card_id'].dropna().unique().tolist()

# 6. campos no documentados
columnas_esperadas = {'tx_id','card_id','amount','tx_date'}
columnas_actuales = set(anomalias.columns)
campos_no_documentados = columnas_actuales - columnas_esperadas
reporte['campos_no_documentados'] = list(campos_no_documentados)

# 7. montos negativos
montos_negativos = anomalias[anomalias['amount'] < 0]
reporte['montos_negativos'] = int(len(montos_negativos))
reporte['tx_ids_monto_negativo'] = montos_negativos['tx_id'].tolist()

# reporte
with open('./archivos/data_quality_report.json','w') as f:
    json.dump(reporte, f, indent=4, default=str)
print('Reporte generado')

# limpieza
clean = anomalias.copy()
clean = clean.dropna(subset=['card_id','amount','tx_date']) #quita nulos
clean = clean[clean['tx_date'] <= hoy] # quita fechas
clean = clean[clean['card_id'].isin(ids_validos)] # quita card_ids invalidos
clean = clean[clean['amount']>0] # quitar montos negativos
clean = clean.drop(columns=['extra_column']) # quita campo no documentado
clean.to_csv('./archivos/transactions_anomalias_clean.csv', index=False)
print(f'Archivo limpio exportado: {len(clean)} filas de {len(anomalias)} originales')