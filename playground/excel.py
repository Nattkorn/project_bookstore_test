import pymysql
import pandas as pd

connection = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')

tables = ['data_book', 'users', 'pur_hist']

with pd.ExcelWriter('bookstore_data.xlsx', engine='openpyxl') as writer:
    for table in tables:
        query = f'SELECT * FROM {table}'
        df = pd.read_sql(query, connection)
        df.to_excel(writer, sheet_name=table, index=False)

print('Data exported to output.xlsx')

# ปิดการเชื่อมต่อ
connection.close()