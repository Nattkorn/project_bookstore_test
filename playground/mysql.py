import pymysql

def connect_mysql():
    conn = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')
    return conn


conn = connect_mysql()
with conn:
    cur = conn.cursor()
    cur.execute('ALTER TABLE users MODIFY COLUMN customer_id INT AUTO_INCREMENT PRIMARY KEY;')
    conn.commit()

