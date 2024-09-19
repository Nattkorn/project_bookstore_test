import pymysql

def connect_mysql():
    conn = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')
    return conn

conn = connect_mysql()
with conn:
    cur = conn.cursor()
    cur.execute('SELECT id, promotion FROM data_book')
    promotion = cur.fetchall()
    print(promotion)