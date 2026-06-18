from google.cloud import bigquery
import pandas as pd

# configuracion
PROJECT_ID = 'proyecto_gcp'
DATASET_ID = 'examen_tecnico'
TABLE_ID = 'transactions_anomalies_clean'

# carga csv limpio
df = pd.read_csv('./archivos/transactions_anomalias_clean.csv')

# cliente bigquery
client = bigquery.Client(project=PROJECT_ID)

# evitando que coloque tipos incorrectos
schema = [
    bigquery.SchemaField('tx_id','INT64'),
    bigquery.SchemaField('card_id','STRING'),
    bigquery.SchemaField('amount','FLOAT64'),
    bigquery.SchemaField('tx_date','DATE'),
]

# configuración de la carga
job_config = bigquery.LoadJobConfig(
    schema = schema,
    write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE,
)

# ejecución
table_ref = f'{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}'
job = client.load_table_from_dataframe(df,table_ref,job_config=job_config)
job.result()

print(f'Cargadas {job.output_rows} filas en {table_ref}')