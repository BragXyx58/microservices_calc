import pyodbc

def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=db,1433;"
        "DATABASE=CalculatorDB;"
        "UID=sa;"
        "PWD=Qies$12!;"
    )