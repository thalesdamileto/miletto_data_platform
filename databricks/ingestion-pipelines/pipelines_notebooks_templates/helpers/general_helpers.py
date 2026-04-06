import json
import os
from pyspark.sql.functions import *
from pyspark.sql.types import *
from datetime import datetime

true = True
false = False

WATERMARK_TABLE = "workspace.default.pipelines_watermark"

TYPE_MAPPING = {
    "string": StringType(),
    "boolean": BooleanType(),

    "byte": ByteType(),
    "short": ShortType(),
    "int": IntegerType(),
    "bigint": LongType(),

    "float": FloatType(),
    "double": DoubleType(),

    "date": DateType(),
    "timestamp": TimestampType(),

    "binary": BinaryType()
}

def get_data_contract(repo_root:str, contract_id: str) -> dict:
    contract_file = f"{repo_root}/pipelines_metadata/silver/contracts.json"

    with open(contract_file, "r") as f:
        data = json.load(f)

    for contract in data["contract_list"]:
        if contract["contract_id"] == contract_id:
            return contract

    raise ValueError(f"Contract_id {contract_id} não encontrado")

def get_watermark(spark, contract_id:str , watermark_table: str = WATERMARK_TABLE) -> str:
    watermark_df = spark.read.table(watermark_table)
    try:
        watermark = watermark_df.select(col("watermark_value")).filter(col("contract_id") == contract_id).collect()[0][0]
        return watermark
    
    except Exception as error:
        print(f"Watermark not found for contract_id {contract_id}, assuming first run with full table processing. {error}")
        return None

def update_watermark(spark, destination_table:str, contract_id:str, watermark_column:str, new_watermark_value:datetime, watermark_table: str = WATERMARK_TABLE):
    try:
        spark.sql(f"""
            MERGE INTO {watermark_table} AS t
            USING (
                SELECT '{destination_table}' AS destination_table, 
                '{contract_id}' AS contract_id, 
                '{watermark_column}' AS watermark_column,
                '{new_watermark_value}' AS watermark_value
            ) AS s
            ON t.contract_id = s.contract_id
            WHEN MATCHED THEN UPDATE SET 
                destination_table = s.destination_table,
                watermark_column = s.watermark_column,
                watermark_value = s.watermark_value
            WHEN NOT MATCHED THEN INSERT 
                (destination_table, contract_id, watermark_column, watermark_value) 
                VALUES (s.destination_table, s.contract_id, s.watermark_column, s.watermark_value)
        """)   
    except Exception as error:
        print(f"Error updating watermark for contract_id {contract_id}. {error}")
