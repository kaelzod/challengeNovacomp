import duckdb

print("CUSTOMERS")
duckdb.sql("SELECT * FROM './archivos/customers.csv' LIMIT 5").show()

print("CARDS")
duckdb.sql("SELECT * FROM './archivos/cards.csv' LIMIT 5").show()

print("transaccions")
duckdb.sql("SELECT * FROM './archivos/transactions.csv' LIMIT 5").show()


print("1.1. NUMERO DE CLIENTES AGRUPADO POR SEGMENT")
duckdb.sql("""SELECT segment, count(customer_id) as total_clientes
           FROM './archivos/customers.csv'
           GROUP BY segment
           ORDER BY segment
""").show()

print("1.2. TOTAL DE TRANSACCION POR TIPO DE TARJETA")
duckdb.sql("""SELECT CA.CARD_TYPE, COUNT(TR.TX_ID) AS total_transacciones, SUM(TR.AMOUNT) as monto_total
           FROM './archivos/cards.csv' CA
           INNER JOIN './archivos/transactions.csv' TR on ( CA.card_id = TR.card_id )
           GROUP BY CA.CARD_TYPE
           ORDER BY 3 DESC
""").show()

print("1.3. CLIENTES QUE TIENEN AL MENOS 1 TARJETA EN ESTADO BLOCKED")
duckdb.sql("""SELECT CU.FULL_NAME, CU.SEGMENT, CA.CARD_TYPE, CA.STATUS
           FROM './archivos/customers.csv' CU
           INNER JOIN './archivos/cards.csv' CA ON ( CU.CUSTOMER_ID = CA.CUSTOMER_ID )
           WHERE CA.STATUS = 'Blocked'
""").show()

print("1.4. PROMEDIO TRANSADO POR CADA CLIENTE")
duckdb.sql("""SELECT CU.FULL_NAME, AVG(TR.AMOUNT) AS MONTO_PROMEDIO
           FROM './archivos/customers.csv' CU
           INNER JOIN './archivos/cards.csv'        CA ON ( CU.CUSTOMER_ID = CA.CUSTOMER_ID )
           INNER JOIN './archivos/transactions.csv' TR ON ( CA.CARD_ID     = TR.CARD_ID     )
           GROUP BY CU.FULL_NAME
           HAVING (COUNT(TR.TX_ID)>3)
""").show()

print("1.5. TRANSACCIONES CUYO MONTO ESTÁ POR ENCIMA DEL PERCENTIL 90")
duckdb.sql("""SELECT TX_ID, AMOUNT
           FROM './archivos/transactions.csv'
           WHERE AMOUNT > (
               SELECT PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY AMOUNT)
               FROM './archivos/transactions.csv'
           )
           ORDER BY AMOUNT DESC
""").show()

print("1.6. TRANSACCIONES ASOCIADAS A TARJETAS INEXISTENTES")
duckdb.sql("""SELECT TX.TX_ID, TX.CARD_ID, TX.AMOUNT
           FROM './archivos/transactions.csv' TX
           LEFT JOIN './archivos/cards.csv' CA ON (TX.CARD_ID = CA.CARD_ID)
           WHERE CA.CARD_ID IS NULL
""").show()



print("2.1. CARDS_FINANCIAL_MASTER")
duckdb.sql("""
-- En BigQuery: CREATE OR REPLACE TABLE dataset.cards_financial_master
-- PARTITION BY load_date CLUSTER BY processor, customer_id, card_type, status AS (
WITH unified AS (
    SELECT
        card_id_a       AS card_id,
        customer_id,
        card_type_a     AS card_type_raw,
        status_a        AS status_raw,
        'A'             AS processor
    FROM './archivos/cards_processor_a.csv'

    UNION ALL

    SELECT
        card_id_b       AS card_id,
        customer_id,
        card_type_b     AS card_type_raw,
        status_b        AS status_raw,
        'B'             AS processor
    FROM './archivos/cards_processor_b.csv'
),

standardized AS (
    SELECT
        u.card_id,
        u.customer_id,
        u.card_type_raw,
        u.status_raw,
        eq_type.value_standard  AS card_type,
        eq_stat.value_standard  AS status,
        u.processor
    FROM unified u
    LEFT JOIN './archivos/equivalence_table_extended.csv' eq_type
        ON  eq_type.attribute = 'card_type'
        AND (
            (u.processor = 'A' AND eq_type.value_processor_a = u.card_type_raw) OR
            (u.processor = 'B' AND eq_type.value_processor_b = u.card_type_raw)
        )
    LEFT JOIN './archivos/equivalence_table_extended.csv' eq_stat
        ON  eq_stat.attribute = 'status'
        AND (
            (u.processor = 'A' AND eq_stat.value_processor_a = u.status_raw) OR
            (u.processor = 'B' AND eq_stat.value_processor_b = u.status_raw)
        )
),

enriched AS (
    SELECT
        s.card_id,
        s.customer_id,
        s.card_type,
        s.status,
        s.processor,
        f.interest_rate,
        f.commission,
        f.insurance_fee
    FROM standardized s
    LEFT JOIN './archivos/financial_rules.csv' f
        ON  s.processor     = f.processor
        AND s.card_type_raw = f.card_type_raw
),

cards_financial_master AS (
    SELECT
        card_id,
        customer_id,
        card_type,
        status,
        processor,
        interest_rate,
        commission,
        insurance_fee,
        (interest_rate * 1000 + commission + insurance_fee) AS monthly_total_cost,
        current_date   AS load_date,
        now()          AS load_timestamp
    FROM enriched
)

SELECT * FROM cards_financial_master
""").show()