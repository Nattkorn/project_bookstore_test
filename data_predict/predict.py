import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import seaborn as sns 

df = pd.read_csv("data_predict/book_data.csv")
gender = {'ชาย':1, 'หญิง':2}
age = {'15-20 ปี':1, '21-29 ปี':2, '30-39 ปี':3, '40-49 ปี':4, '50 ปีขึ้นไป':5}
educate = {'มัธยมต้น':1, 'มัธยมปลาย หรือเทียบเท่า':2, 'ปวช.':3, 'ปวส.':4, 'ปริญญาตรี หรือเทียบเท่า':5, 'ปริญญาโท':6, 'ปริญญาเอก':7}
job = {'รับราชการ':1, 'พนักงานรัฐวิสาหกิจ':2, 'พนักงานบริษัทเอกชน':3, 'ธุรกิจส่วนตัว':4, 'รับจ้างทั่วไป':5, 'นักเรียน':6, 'นักศึกษา':7, 'ค้าขาย':8}
income = {'0 - 15,000 บาท':1, '15,001 - 30,000 บาท':2, '30,001 – 50,000 บาท':3, 'มากกว่า 50,000 บาท':4}
directory_type = {'ความรู้รอบตัว':1, 'บริหาร / การเงิน / การตลาด':2, 'ท่องเที่ยว':3, 'งานอดิเรก / งานฝีมือ':4, 'สุขภาพ / อาหาร / ความงาม':5, 'เทคโนโลยี / คอมพิวเตอร์':6, 'ศิลปะ / ดนตรี':7, 'พืช / การเกษตร':8, 'สารคดี / ประวัติศาสตร์ / ชีวประวัติ':9, 'ปรัชญา / ศาสนา':10, 'โหราศาสตร์ / ความเชื่อ':11, 'กฏหมาย / การเมือง':12, 'จิตวิทยา / พัฒนาตนเอง':13, 'วิชาการ / ความรู้ทั่วไป':14}
fiction_type = {'นวนิยาย':1, 'เรื่องสั้น':2, 'นิยายภาพ':3}
fiction_catagory = {'ความรัก':1, 'สะท้อนสังคม':2, 'ผจญภัย / แฟนตาซี':3, 'ฆาตกรรม / สืบสวน สอบสวน':4, 'ตลกขำขัน':5, 'อิงประวัติศาสตร์':6, 'ศาสนา / การเมือง':7, 'วิทยาศาสตร์ / ไซไฟ':8}

df['gender'] = df['gender'].map(gender)
df['age'] = df['age'].map(age)
df['education'] = df['education'].map(educate)
df['job'] = df['job'].map(job)
df['income'] = df['income'].map(income)
df['directory_type'] = df['directory_type'].map(directory_type)
df['fiction_type'] = df['fiction_type'].map(fiction_type)
df['fiction_catagory'] = df['fiction_catagory'].map(fiction_catagory)
df.fillna({
    'job' : df['job'].mode()[0],
    'directory_type' : df['directory_type'].mode()[0],
    'fiction_type' : df['fiction_type'].mode()[0],
    'fiction_catagory' : df['fiction_catagory'].mode()[0]
}, inplace=True)


X = df[['gender','age','education','job','income']]
scaler = StandardScaler()
scaled_features = scaler.fit_transform(X)
kmeans = KMeans(n_clusters=7) # สมมุติให้มี 3 กลุ่ม
kmeans.fit(scaled_features)
df['cluster_directory'] = kmeans.labels_

group_avg_reading = df.groupby('cluster_directory')['directory_type'].agg(lambda x: x.value_counts().idxmax())
print("ประเภทหนังสือที่เป็นค่าเฉลี่ยในแต่ละกลุ่ม:\n", group_avg_reading)

#test predict
new_data = {'gender': [1], 'age': [2], 'education': [2], 'job': [1], 'income': [1]}
new_df = pd.DataFrame(new_data)
new_scaled_features = scaler.transform(new_df)
predicted_group = kmeans.predict(new_scaled_features)
print(f'\nข้อมูลใหม่อยู่ในกลุ่ม: {predicted_group[0]}')
predicted_book_type = group_avg_reading[predicted_group[0]]
print(f'ทำนายประเภทหนังสือของข้อมูลใหม่: {predicted_book_type}')

from sklearn.metrics import silhouette_score
silhouette_avg = silhouette_score(scaled_features, kmeans.labels_)
print(f'Silhouette Score: {silhouette_avg}')
#Silhouette Score: 0.6306297866829043