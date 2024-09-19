import pymysql
import numpy as np
import pandas as pd
from collections import Counter
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

conn = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')
with conn:
    cur = conn.cursor()
    cur.execute("SELECT pur_id, GROUP_CONCAT(book_name SEPARATOR ', ') FROM `pur_hist` WHERE status = 3 GROUP BY pur_id")
    data = cur.fetchall()
    df = pd.DataFrame(data,columns = ['pur_id','book_name'])
    df['book_name'] = df['book_name'].apply(lambda x: x.split(', '))
    te = TransactionEncoder()
    te_ary = te.fit(df['book_name']).transform(df['book_name'])
df_onehot = pd.DataFrame(te_ary, columns=te.columns_)
frequent_itemsets = apriori(df_onehot, min_support=0.03, use_colnames=True)
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=0.5)
print(frequent_itemsets.sort_values(by='support', ascending=False).head(10))
