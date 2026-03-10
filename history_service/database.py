import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=sql_server;"
        "DATABASE=CalculatorDB;"
        "UID=sa;"
        "PWD=Qies$12!"
    )