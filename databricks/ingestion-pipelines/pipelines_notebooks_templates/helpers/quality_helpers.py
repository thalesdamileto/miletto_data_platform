from pyspark.sql.functions import *

def lower_case_columns(dataframe, columns):
    column_list = [c.strip() for c in columns.split(',')]
    select_exprs = []
    for c in dataframe.columns:

        if c in column_list:
            select_exprs.append(lower(col(c)).alias(c))
        else:
            select_exprs.append(col(c))

    print(select_exprs)
    return dataframe.select(*select_exprs)

def upper_case_columns(dataframe, columns):
    column_list = [c.strip() for c in columns.split(',')]
    select_exprs = []
    for c in dataframe.columns:

        if c in column_list:
            select_exprs.append(upper(col(c)).alias(c))
        else:
            select_exprs.append(col(c))

    print(select_exprs)
    return dataframe.select(*select_exprs)

def strip_str_columns(dataframe, columns):
    column_list = [c.strip() for c in columns.split(',')]
    select_exprs = []

    for c in dataframe.columns:
        if c in column_list:
            select_exprs.append(trim(col(c)).alias(c))
        else:
            select_exprs.append(col(c))

    print(select_exprs)
    return dataframe.select(*select_exprs)

procedures_map = {
    "upper_case_columns": upper_case_columns,
    "lower_case_columns": lower_case_columns,
    "strip_str_columns": strip_str_columns
}

def execute_quality_procedures(spark, dataframe, quality_procedures):
    df = dataframe
    
    for procedure_name, column in quality_procedures.items():
        procedure_function = procedures_map.get(procedure_name)
        
        if procedure_function:
            df = procedure_function(df, column)
    
    return df
