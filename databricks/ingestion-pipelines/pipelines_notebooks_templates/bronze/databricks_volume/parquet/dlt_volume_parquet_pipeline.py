# Import modules
from pyspark import pipelines as dp

# COMMAND ----------

# Initiating parameters from pipeline configuration
source_path = spark.conf.get("source_path")
target_schema = spark.conf.get("target_schema")
target_table = spark.conf.get("target_table")
description = spark.conf.get("description")

# COMMAND ----------

# Table attributes
target_catalog = "bronze"
full_table_name = f"`{target_catalog}`.`{target_schema}`.`{target_table}`"

# Paths attributes
schema_path = f"/Volumes/workspace/default/schemas/{target_catalog}/{target_schema}/{target_table}/"

# COMMAND ----------

@dp.table(
    name=target_table,  # DLT já sabe o schema do pipeline
    comment=f"Bronze delta table: {full_table_name}. Description: {description}"
)
def iss_raw():
    return (
        spark.readStream
            .format("cloudFiles")
            .option("cloudFiles.format", "parquet")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("cloudFiles.schemaLocation", schema_path)
            .load(source_path)
    )