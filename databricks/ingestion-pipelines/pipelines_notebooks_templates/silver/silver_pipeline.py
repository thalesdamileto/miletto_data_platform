# Databricks notebook source
# DBTITLE 1,Imports
# Imports
import os
import sys
import json
from pyspark.sql.functions import col, lit, row_number
from pyspark.sql.window import Window
from delta.tables import DeltaTable
from datetime import datetime

# Get Repo Root
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = f"/Workspace{notebook_path.split('/pipelines_notebooks_templates')[0]}"
sys.path.append(f"{repo_root}/pipelines_notebooks_templates/helpers")

from general_helpers import TYPE_MAPPING, get_data_contract, get_watermark, update_watermark
from quality_helpers import execute_quality_procedures

# COMMAND ----------

# DBTITLE 1, Initialize parameters
# Source table
dbutils.widgets.text("source_table", "bronze.dbo.iss_data")
source_table = dbutils.widgets.get("source_table")

# Destination table
dbutils.widgets.text("destination_table", "silver.dbo.iss_data")
destination_table = dbutils.widgets.get("destination_table")

# Read Data Contract
dbutils.widgets.text("data_contract_id", "1")
data_contract_id = dbutils.widgets.get("data_contract_id")
data_contract = get_data_contract(repo_root, data_contract_id)

# Data Contract Atributes
pk_column = data_contract["parameters"]["pk_columns"].split(",")
watermark_column = data_contract["parameters"]["watermark_column"]
ordering_column = data_contract["parameters"]["ordering_column"]
quality_procedures = data_contract["parameters"]["quality_procedures"]

# COMMAND ----------

# DBTITLE 1, READING DATA
def apply_contract(contract: dict, bronze_table):

    source = contract["parameters"]["source"]
    mappings = contract["parameters"]["column_mapping"]

    table = f'{source["catalog"]}.{source["schema"]}.{source["table"]}'

    select_exprs = []

    for m in mappings:

        src = m["source_column"]
        dst = m["destination_column"]
        spark_type = TYPE_MAPPING[m["type"]]

        # Default procedure for cast is True
        do_cast = m.get("cast", True)

        if do_cast:
            expr = col(src).cast(spark_type).alias(dst)
        else:
            expr = col(src).alias(dst)

        select_exprs.append(expr)

    return bronze_table.select(*select_exprs)

# Apply watermark filter
watermark_value = get_watermark(spark, contract_id=data_contract_id)
if watermark_value:
    print(f"watermark value: {watermark_value}")
    bronze_table = spark.read.table(source_table).filter(col(watermark_column) > watermark_value)
else:
    print(f"No watermark filter applied")
    bronze_table = spark.read.table(source_table)
# Apply contract
silver_df = apply_contract(data_contract, bronze_table)

# COMMAND ----------

# DBTITLE 1, CHECKING IF THERE IS NEW DATA
if not silver_df.head(1):
    dbutils.notebook.exit("No new data")

# COMMAND ----------

# DBTITLE 1, DATA QUALITY ACTIONS
# Dedup Rows
window = Window.partitionBy(pk_column).orderBy(col(ordering_column).desc())
silver_df = silver_df.withColumn("row_number", row_number().over(window)).filter(col("row_number") == 1).drop("row_number")

# Drop null rows for not nullable rows
not_nullable_cols = [m["destination_column"] for m in data_contract["parameters"]["column_mapping"] if not m["nullable"]]
silver_df = silver_df.na.drop(subset=not_nullable_cols, how="all")

# Other Quality Procedures
silver_df = execute_quality_procedures(spark, silver_df, quality_procedures)

# COMMAND ----------

# DBTITLE 1, Write Section
# Check destination schema existence
schema_name = data_contract["parameters"]["destination"]["schema"]
catalog_name = data_contract["parameters"]["destination"]["catalog"]
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}")

# Build merge condition
condition_list = []
for column in pk_column:
    statement = f"target.{column} = source.{column}"
    condition_list.append(statement)
merge_condition = " AND ".join(condition_list)

# Ingest Data
from datetime import datetime
write_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
silver_df = silver_df.withColumn("write_date", lit(write_date))

if not spark.catalog.tableExists(destination_table):
    (
        silver_df
        .write
        .format("delta")
        .mode("overwrite")
        .saveAsTable(destination_table)
    )
else:
    DeltaTable.forName(spark, destination_table) \
        .alias("target") \
        .merge(
            silver_df.alias("source"),
            merge_condition
        ) \
        .whenMatchedUpdateAll() \
        .whenNotMatchedInsertAll() \
        .execute()          

# Update watermark
new_watermark = silver_df.select(watermark_column).agg({"*": "max"}).collect()[0][0]
update_watermark(spark, destination_table=destination_table, contract_id=data_contract_id, watermark_column=watermark_column, new_watermark_value=new_watermark)

print(f"Data ingested successfully. new watermark: {new_watermark}")
    
