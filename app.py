from flask import Flask, render_template, request, redirect, url_for, Response, send_file, flash, jsonify
import pymysql
import datetime
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
from io import BytesIO
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
import math

app = Flask(__name__)
app.secret_key = 'your_secret_key'
data_user = (0 ,"email","password","name","gender","birth","address",0)
cart = []
number_of_book = []
searchbook = ""
filter = ""
order_number = 0
data_predic = [0,0,0,0,0,0,0,0,0,0,0]

##mainpage
@app.route("/")
def mainpage():
    rows = (data_user,)
    conn = connect_mysql()
    print(data_user)
    if data_user[0] == 1:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT book_id, pur_hist.book_name, SUM(amount), SUM(amount)*pur_hist.price, store FROM pur_hist JOIN data_book ON book_id = id WHERE status = 3 GROUP BY book_id")
            rows += (cur.fetchall(),)
            cur.execute("SELECT type, SUM(amount), SUM(amount*data_book.price) FROM pur_hist JOIN data_book ON book_id = id WHERE status = 3 GROUP BY type")
            rows += (cur.fetchall(),)
        return render_template('main.html',data = rows)
    return render_template('index.html',data = rows+(getmostselling(), getpromotion_book()))

@app.route("/report", methods = ['POST'])
def report():
    rows = (data_user,)
    start = request.form['start']
    end = request.form['end']
    filter =  request.form.get('fillter')
    filter = "%"+filter+"%"
    print(filter)
    print(start)
    print(end)
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        query = f"SELECT book_id, pur_hist.book_name, SUM(amount), SUM(amount)*pur_hist.price, store FROM pur_hist JOIN data_book ON book_id = id WHERE date >= '{start}' AND date <= '{end}' AND status = 3 AND book_type LIKE '{filter}' GROUP BY book_id"
        print(query)
        cur.execute(query)
        rows += (cur.fetchall(),)
        cur.execute("SELECT type, SUM(amount), SUM(amount*data_book.price) FROM pur_hist JOIN data_book ON book_id = id WHERE date >= %s AND date <= %s AND status = 3 GROUP BY type ", (start,end))
        rows += (cur.fetchall(),)
        print(rows)
    return render_template("main.html", data = rows)

##storebook
@app.route("/showData", defaults = {'page':1})
@app.route("/showData/<int:page>")
def showData(page):
    items_per_page = 10
    offset = (page - 1) * items_per_page
    conn = connect_mysql()
    if (data_user[0] == 1):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM data_book ORDER BY id LIMIT %s OFFSET %s", (items_per_page, offset))
            books = cur.fetchall()
            cur.execute("SELECT COUNT(*) FROM data_book")
            total_book = cur.fetchone()[0]
            total_page = math.ceil(total_book/items_per_page)
        return render_template('bookdata.html',data= books, page = page , total_pages = total_page)
    else:
        return redirect("/")

@app.route("/add")
def add_user():
    if (data_user[0] == 1):
        return render_template('addbook.html')
    else:
        return redirect("/")
    
@app.route("/delete/<string:id_data>", methods = ['GET'])
def delete(id_data):
    if (data_user[0] == 1):
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM data_book WHERE id=%s",(id_data))
            conn.commit()
            cur.execute("DELETE FROM pur_hist WHERE book_id=%s AND status = 0",(id_data))
            conn.commit()
        return redirect(url_for('showData'))
    else:
        return redirect("/")

@app.route("/insert", methods = ['POST'])
def insert():
    if (data_user[0] == 1):
        if request.method == "POST":
            conn = connect_mysql()
            book_id = request.form['book_id']
            book_name = request.form['book_name']
            publisher = request.form['publisher']
            book_type = request.form['book_type']
            category = request.form['category']
            author = request.form['author']
            description = request.form['description']
            store = request.form['store']
            image_url = request.form['image_url']
            price = request.form['price']
            
            type_book = request.form['type']
            with conn.cursor() as cursor:
                sql = "INSERT INTO `data_book`(`id`, `book_name`, `publisher`, `book_type`, `book_category`, `author`, `description`, `store`, `image_url`,`price`,`type`,`promotion`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,0)"
                cursor.execute(sql,(book_id,book_name,publisher,book_type,category,author,description,store,image_url,price,type_book))
                conn.commit()
            return redirect(url_for('showData'))
    else:
        return redirect("/")

@app.route("/update", methods = ['POST'])
def update():
    if (data_user[0] == 1):
        if request.method == "POST":
            conn = connect_mysql()
            book_id = request.form['book_id']
            book_name = request.form['book_name']
            publisher = request.form['publisher']
            book_type = request.form['book_type']
            category = request.form['category']
            author = request.form['author']
            description = request.form['description']
            store = request.form['store']
            image_url = request.form['image_url']
            price = request.form['price']
            with conn.cursor() as cursor:
                sql = "UPDATE `data_book` SET `book_name`=%s,`publisher`=%s,`book_type`=%s,`book_category`=%s,`author`=%s,`description`=%s,`store`=%s,`image_url`=%s,`price`=%s WHERE `id`= %s"
                cursor.execute(sql,(book_name,publisher,book_type,category,author,description,store,image_url,price,book_id))
                conn.commit()
            return redirect(url_for('showData'))
    else:
        return redirect("/")

##search
@app.route("/searchbook", methods = ['POST'], defaults = {'page':1})
@app.route("/searchbook/<int:page>")
def searchbook(page):
    items_per_page = 12
    offset = (page - 1) * items_per_page
    global searchbook,filter
    try:
        searchbook = request.form["searchinput"]
        filter = request.form.get('fillter')
    except Exception as e:
        print(searchbook)
        print(filter)
    try:
        firstsearch = searchbook + '%'
        middlesearch = '%' + searchbook + '%'
        filter = '%' + filter + '%'
        conn = connect_mysql()  # Assuming connect_mysql() is the function that returns a connection
        cur = conn.cursor()
        # First search
        cur.execute(
            "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1, CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
            "FROM data_book " 
            "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
            "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
            "WHERE book_type LIKE %s AND (book_name LIKE %s OR book_name LIKE %s ) LIMIT %s OFFSET %s",
            (filter, firstsearch, middlesearch, items_per_page, offset)
        )
        search_results = cur.fetchall()       
        cur.execute(
            "SELECT COUNT(*) "
            "FROM data_book "
            "WHERE book_type LIKE %s AND (book_name LIKE %s OR book_name LIKE %s )",
            (filter, firstsearch, middlesearch)
        )
        total_books = cur.fetchone()[0]
        total_page = math.ceil(total_books/items_per_page)

        # Second query for popular books
        mostsell_books = getmostselling()
        rows = data_user,(searchbook),(filter),search_results,getpromotion_book()
        print(rows)
        
        return render_template('search.html', data=rows, len=len(rows), page = page , total_pages = total_page)
        
    except Exception as e:
        print(e)  # For debugging purposes
        rows = ()
        return render_template('search.html', data=rows)

    finally:
        conn.close()  # Always close the connection

##login
@app.route("/login")
def login():
    if data_user[0]==0:
        return render_template('login.html',data = 0)
    else:        
        return redirect(url_for('mainpage'))

@app.route("/logout")
def logout():
    global data_user
    global cart
    cart = []
    number_of_book = []
    data_user = (0,"email","password","name","gender","birth","address",0)
    return redirect("/")

@app.route("/getlogin", methods = ['POST'])
def getlogin():
    try:
        conn = connect_mysql() 
        if request.method == "POST":
            email = request.form['email']
            password = request.form['password']
            with conn.cursor() as cursor:
                sql = "SELECT `customer_id`, `email`, `password`, `fname`, `gender`, `birth`, `address`, `tel_no` FROM `users` WHERE `email` = %s && `password` = %s"
                cursor.execute(sql,(email, password))
                conn.commit()
                rows = cursor.fetchall()
                if rows == ():
                    print("not have")
                    flash('อีเมลหรือรหัสผ่านไม่ถูกต้องกรุณาลองอีกครั้ง', 'error')
                    return redirect(url_for('login'))
                global data_user 
                data_user = rows[0]
                print(data_user)
            return redirect(url_for('mainpage'))
    except IndexError:
        return redirect("/login")
        
##register
@app.route("/register", methods=['GET', 'POST'])
def register():
        if request.method == 'POST':
            conn = connect_mysql()
            email = request.form['email']
            password = request.form['password']
            fullname = request.form['fullname']
            gender = request.form['gender']
            birthday = request.form['birthday']
            address = request.form['address']
            tel_no = request.form['tel_no']
        
            if not email:
                flash('โปรดใส่อีเมลของท่าน', 'error')
            elif len(email.split('@'))!=2:
                flash('โปรดใส่อีเมลของท่านให้ถูกต้อง', 'error')
            if not password:
                flash('โปรดใส่รหัสของท่าน', 'error')
            if not fullname:
                flash('โปรดใส่ชื่อของท่าน', 'error')
            if not gender:
                flash('โปรดใส่เพศของท่าน', 'error')
            if not birthday:
                flash('โปรดใส่วันเกิดของท่าน', 'error')
            if not address:
                flash('โปรดใส่ที่อยู่ของท่าน', 'error')
            if not tel_no:
                flash('โปรดใส่เบอร์โทรของท่าน.', 'error')
            elif len(tel_no) != 10:
                flash('โปรดใส่เบอร์โทรให้ถูกต้อง', 'error')
            if not email or not password or not fullname or not gender or not birthday or not address or not tel_no or len(tel_no) != 10 or len(email.split('@'))!=2:
                return render_template('register.html', email=email, password=password, fullname=fullname, 
                                gender=gender, birthday=birthday, address=address, tel_no=tel_no)
            try:
                with conn.cursor() as cursor:
                    sql = "INSERT INTO `users`(`email`, `password`, `fname`, `gender`, `birth`, `address`, `tel_no`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    cursor.execute(sql, (email, password, fullname, gender, birthday, address, tel_no))
                    conn.commit()
                
                return redirect(url_for('mainpage'))
            except pymysql.MySQLError as e:
                flash(f"An error occurred: {str(e)}", 'danger')
                return render_template('register.html', email=email, password=password, fullname=fullname, 
                                gender=gender, birthday=birthday, address=address, tel_no=tel_no)
            finally:
                conn.close()
                return redirect(url_for('mainpage'))
        return render_template('register.html')

@app.route("/insert_user", methods = ['POST'])
def insert_user():
    if request.method == "POST":
        conn = connect_mysql()
        email = request.form['email']
        password = request.form['password']
        fullname = request.form['fullname']
        gender = request.form['gender']
        birthday = request.form['birthday']
        address = request.form['address']
        tel_no = request.form['tel_no']
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO `users`(`email`, `password`, `fname`, `gender`, `birth`, `address`, `tel_no`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql,(email,password,fullname,gender,birthday,address,tel_no))
                conn.commit()
        except pymysql.err.OperationalError as e:
            print(f"OperationalError: {e}")
            return redirect(url_for('register'))
        return redirect(url_for('mainpage'))

@app.route("/userinfo")
def userdata():
    global data_user
    conn = connect_mysql()
    print(data_user)
    with conn:
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE customer_id = %s',data_user[0])
        data_user = cur.fetchall()[0]
    print(data_user)
    if data_user[0] == 1:
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users")
            rows = cur.fetchall()
            return render_template('userinfo_admin.html', data = rows)
    return render_template('userinfo.html',data=data_user)

@app.route("/updateuser", methods = ['POST'])
def updatauser():
    conn = connect_mysql() 
    if request.method == "POST":
        user_id = request.form['user_id']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        gender = request.form['gender']
        birthday = request.form['birthday']
        address = request.form['address']
        tel_no = request.form['tel_no']
        if not email:
            flash('โปรดใส่อีเมลของท่าน', 'error')
        elif len(email.split('@'))!=2:
            flash('โปรดใส่อีเมลของท่านให้ถูกต้อง', 'error')
        if not password:
            flash('โปรดใส่รหัสของท่าน', 'error')
        if not name:
            flash('โปรดใส่ชื่อของท่าน', 'error')
        if not gender:
            flash('โปรดใส่เพศของท่าน', 'error')
        if not birthday:
            flash('โปรดใส่วันเกิดของท่าน', 'error')
        if not address:
            flash('โปรดใส่ที่อยู่ของท่าน', 'error')
        if not tel_no:
            flash('โปรดใส่เบอร์โทรศัพท์ของท่าน', 'error')
        elif len(tel_no) != 10:
            flash('โปรดใส่เบอร์โทรให้ถูกต้อง', 'error')
        if not email or not password or not name or not gender or not birthday or not address or not tel_no or len(tel_no) != 10 or len(email.split('@'))!=2:
            return userdata()
        with conn.cursor() as cursor:
            sql = "UPDATE users SET email=%s,password=%s,fname=%s,gender=%s,birth=%s,address=%s,tel_no=%s WHERE customer_id = %s"
            cursor.execute(sql,(email,password,name,gender,birthday,address,tel_no,user_id))
            conn.commit()
            global data_user
        return userdata()

@app.route('/deleteuser/<int:user_id>')
def delete_user(user_id):
    print(f"ลบข้อมูล ID: {user_id}")
    conn = connect_mysql()
    with conn:
        cur =conn.cursor()
        cur.execute("DELETE FROM `users` WHERE customer_id = %s", user_id)
        conn.commit()
    return redirect("/userinfo")

##Add to cart
@app.route("/addcart", methods = ['POST'])
def add_cart():
    try:
        data = request.get_json()[0]
        print(data)
        if data['book_id'] in cart:
            number_of_book[cart.index(data['book_id'])] = int(number_of_book[cart.index(data['book_id'])]) +int(data['amount'])
        else:
            cart.append(data['book_id'])
            number_of_book.append(data['amount'])
        print(number_of_book)
        print(cart)
        return jsonify({'message': 'Data received successfully', 'data': data}), 200
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}),400
##cart
@app.route("/cart", methods = ['GET'])
def showcart():
    conn = connect_mysql() 
    with conn:
        cur = conn.cursor()
        global cart
        total_price = 0
        rows = ()
        for i in range(len(cart)):
            cur.execute("SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1 AND promotion.start < CURDATE() AND promotion.end > CURDATE(), CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
                        "FROM `data_book` "
                        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
                        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
                        "WHERE data_book.id = %s",(cart[i]))
            data = cur.fetchall()
            data = data[0]+(number_of_book[i],data[0][9]*int(number_of_book[i]),)
            rows += (data,)
            total_price += int(rows[i][12])*int(number_of_book[i])
        rows += (total_price,)
    return render_template('cart.html',data=rows,len = len(rows))

##delete in cart
@app.route("/deletecart/<string:id_data>", methods = ['GET'])
def deletecart(id_data):
    print(cart.index(id_data))
    number_of_book.remove(number_of_book[cart.index(id_data)])
    cart.remove(id_data)
    return redirect(url_for('showcart'))

@app.route("/deletecartall", methods = ['GET'])
def deletecartall():
    global number_of_book,cart
    number_of_book = []
    cart = []
    return redirect(url_for('showcart'))

@app.route("/confirm_list", methods = ["GET"])
def confirm_list():
    global cart,number_of_book
    conn = connect_mysql() 
    date =  datetime.datetime.now()
    print(cart,number_of_book)
    sql = "INSERT INTO pur_hist (book_id, cus_id, amount, status, pur_id, date, book_name, img_book_url, price) VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s)"
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT pur_id FROM pur_hist ORDER BY pur_id DESC LIMIT 1")
            pur_id = cur.fetchone()[0]+1
            for i in range(len(cart)):
                cur.execute("SELECT data_book.id, book_name, image_url, IF(data_book.promotion = 1 AND promotion.start < CURDATE() AND promotion.end > CURDATE(), CEIL(data_book.price*(100-sale)/100), data_book.price) "
                        "FROM data_book "
                        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
                        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
                        "WHERE data_book.id = %s",cart[i])
                data_book = cur.fetchone()
                print(data_book[0])
                cur.execute(sql,(data_book[0], data_user[0], number_of_book[i], pur_id,date, data_book[1], data_book[2], data_book[3]))
                conn.commit()
            url = "/purchase/"+str(pur_id)
            number_of_book = []
            cart = []
    except Exception as e:
        print(f"ERROR : {e}")
    return redirect(url)

##purchase
@app.route("/purchase/<string:pur_id>",methods = ['GET'])
def purchase(pur_id):
    global order_number
    order_number = pur_id
    conn = connect_mysql() 
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT status, cus_id FROM pur_hist WHERE pur_id = %s", pur_id)
        status = cur.fetchall()[0]
        print(status)
        print(status[0])
        if(status[1] == data_user[0]):
            if(status[0] == 0): 
                cur.execute("SELECT SUM(amount*price) FROM pur_hist WHERE pur_id = %s",pur_id)
                total_price = cur.fetchall()
                data  = (data_user[0],data_user[3],data_user[6],data_user[7])
                data_purchase = (data,total_price,pur_id,)
            else:
                cur.execute("SELECT SUM(amount*price) FROM pur_hist WHERE pur_id = %s",pur_id)
                total_price = cur.fetchall()
                cur.execute("SELECT pur_id, name, address, tel_no FROM con_pur WHERE pur_id =%s",pur_id)
                data_con = cur.fetchone()
                data_purchase = (data_con,total_price,pur_id,)
            return render_template('confirm_purchase.html',data = data_purchase)
        else:
            return redirect('/')

@app.route("/purchase", methods = ['POST'])
def submit_purchase():
    global order_number
    conn = connect_mysql()
    with conn:
        pur_id = request.form['pur_id']
        name = request.form['name']
        address = request.form['address']   
        tel_no = request.form['tel_no']
        image = request.files['image']
        image_data = image.read()
        cur = conn.cursor()
        if not name:
            flash('โปรดใส่ชื่อของท่าน', 'error')
        if not address:
            flash('โปรดใส่ที่อยู่ของท่าน', 'error')
        if not tel_no:
            flash('โปรดใส่เบอร์โทรของท่าน.', 'error')
        elif len(tel_no)< 10:
            flash('โปรดใส่เบอร์โทรให้ถูกต้อง', 'error')
        elif not image:
            flash('โปรดใส่รูปยืนยันการชำระเงิน', 'error')
        if not name or not address or not tel_no or not image:
            return purchase(pur_id)
        cur.execute("SELECT status, book_id FROM pur_hist WHERE pur_id = %s", pur_id)
        data = cur.fetchall()
        try:
            if (data[0][0] == 0):
                cur.execute("INSERT INTO `con_pur`( `img_confirm`, `pur_id`, `name`, `address`, `tel_no`) VALUES (%s,%s,%s,%s,%s)",(image_data,order_number,name,address,tel_no))
                conn.commit()
                for i in data:
                    cur.execute("UPDATE data_book SET store = store-(SELECT amount FROM pur_hist WHERE pur_id = %s AND book_id = %s) WHERE id = %s",(pur_id,i[1],i[1]))
                    conn.commit()
            else:
                cur.execute("UPDATE `con_pur` SET `pur_id`=%s ,`name`=%s ,`address`=%s ,`tel_no`=%s ,`img_confirm`=%s  WHERE pur_id = %s",(pur_id, name, address, tel_no, image_data, pur_id))
                conn.commit()
            cur.execute("UPDATE pur_hist SET status = 1 WHERE pur_id = %s",order_number)
            conn.commit()
        except Exception as e:
            print(e)
    return mainpage()

@app.route('/purchase_data', defaults={'page': 1})
@app.route('/purchase_data/<int:page>')
def purchase_data(page):
    conn = connect_mysql() 
    if(data_user[0] > 0):
        with conn:
            items_per_page = 10
            offset = (page - 1) * items_per_page
            cur = conn.cursor()  
            if(data_user[0] == 1):
                cur.execute("SELECT * FROM `pur_hist` WHERE status = 3 ORDER BY date DESC, pur_id ASC LIMIT %s OFFSET %s", (items_per_page, offset))
            else:
                cur.execute("SELECT * FROM `pur_hist` WHERE cus_id = %s AND status = 3 ORDER BY status DESC, pur_id ASC", data_user[0])
            data = cur.fetchall()
            grouped_data = {}
            for purchase_data in data:
                key = purchase_data[8]
                if key in grouped_data:
                    grouped_data[key].append(purchase_data)
                else:
                    grouped_data[key] = [purchase_data]
            data = tuple(tuple(values) for values in grouped_data.values())
            data = list(data)
            for i in range(len(data)):
                price = 0
                for purchase_data in data[i]:
                    price += purchase_data[2] * purchase_data[7]
                new_tuple = (data[i],) + (price,)
                if data[i][0][3]>0:
                    cur.execute("SELECT * FROM con_pur WHERE %s", data[i][0][8])
                    new_tuple += (cur.fetchone(),)
                data[i] = new_tuple
            data = tuple(data)
            if(data_user[0] ==1):
                cur.execute("SELECT COUNT(*) FROM `pur_hist` WHERE status = 3")
                total_items = cur.fetchone()[0]
                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(page)
                print(total_pages)
                return render_template("adminhistory.html",data = data, page=page, total_pages=total_pages)
            else:
                cur.execute("SELECT COUNT(*) FROM `pur_hist` WHERE status = 3 AND cus_id =%s",data_user[0])
                total_items = cur.fetchone()[0]
                total_pages = (total_items + items_per_page - 1) // items_per_page
                print(page)
                print(total_pages)
                return render_template("history.html",data = data, page=page, total_pages=total_pages)
    else:
        redirect("/")

@app.route('/status_data', defaults={'page': 1})
@app.route('/status_data/<int:page>')
def status_data(page):
    conn = connect_mysql() 
    if(data_user[0] > 0):
        with conn:
            items_per_page = 5
            offset = ((page - 1) * items_per_page)
            cur = conn.cursor()
            books = ()
            if(data_user[0] == 1):
                cur.execute("SELECT pur_id FROM `pur_hist` WHERE status > 0 AND status != 3 GROUP BY pur_id ORDER BY date LIMIT %s OFFSET %s", (items_per_page, offset))
            else:
                cur.execute("SELECT pur_id FROM `pur_hist` WHERE cus_id = %s AND status != 3 ORDER BY status DESC, pur_id ASC LIMIT %s OFFSET %s", (data_user[0], items_per_page, offset))
            list_purchase = cur.fetchall()
            print(list_purchase)
            print(len(list_purchase))
            for pur_id in list_purchase:
                price = 0
                cur.execute("SELECT * FROM pur_hist WHERE pur_id = %s",pur_id)
                book = (cur.fetchall(),)
                for i in book:
                    price += i[0][2]*i[0][7]
                book += (price,)
                if book[0][0][3] > 0:
                    cur.execute("SELECT * FROM con_pur WHERE pur_id = %s", pur_id)
                    book += cur.fetchall()
                books += (book,)
            
            if(data_user[0] ==1):
                cur.execute("SELECT COUNT(DISTINCT pur_id) FROM pur_hist WHERE status > 0 AND status != 3")
                total_purchase = cur.fetchone()[0]
                total_pages = math.ceil(total_purchase/items_per_page)
                return render_template("purchase_data.html",data = books, page=page, total_pages = total_pages)
            else:
                cur.execute("SELECT COUNT(DISTINCT pur_id) FROM pur_hist WHERE cus_id = %s AND status != 3", data_user[0])
                total_purchase = cur.fetchone()[0]
                total_pages = math.ceil(total_purchase/items_per_page)
                return render_template("status.html",data = books, page=page, total_pages = total_pages)
    else:
        redirect("/")

@app.route('/delete_purchase', methods = ['POST'])
def delete_purchase():
    try:
        data = request.get_json()[0]
        print(data)
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM pur_hist WHERE pur_id = %s', (data['pur_id']))
            conn.commit()
        return jsonify({'message': 'Data received successfully', 'data': data}), 200
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred', 'error': str(e)}),400


@app.route('/update_status/<string:pur_id>', methods = ['POST'])
def update_status(pur_id):    
    status = request.form['status']
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute("UPDATE `pur_hist` SET status = %s WHERE pur_id = %s",(status,pur_id))
        conn.commit()
    return redirect('/status_data')

## alert book out stock
@app.route('/alert')
def alert():
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT id, book_name, store, cus_want FROM `data_book` LEFT OUTER JOIN (SELECT book_id, COUNT(book_id) AS cus_want FROM `pur_hist` WHERE 1 GROUP BY book_id) AS sub_table ON data_book.id = sub_table.book_id WHERE store = 0 OR cus_want >0;")
        books = cur.fetchall()
    return render_template('alert.html',data = books)

##suport decition
@app.route('/support_decision')
def support_decition():
    return render_template('supdes.html')

@app.route('/predict', methods = ['POST'], defaults = {'page':1})
@app.route('/predict/<int:page>')
def predict(page):
    items_per_page = 12
    offset = (page-1)*items_per_page
    global data_predic
    if(data_predic[0] == 0 | data_predic[0] == 'None'):
        data_predic[0] = request.form.get('gender')
        data_predic[1] = request.form.get('age')
        data_predic[2] = request.form.get('education')
        data_predic[3] = request.form.get('job')
        data_predic[4] = request.form.get('income')
        data_predic[5] = request.form.get('type_1')
        data_predic[6] = request.form.get('type_2')
        data_predic[7] = request.form.get('type_3m')
        data_predic[8] = request.form.get('category_3m')
        data_predic[9] = request.form.get('avg_cost')
    print("data_predic",data_predic)
    type_book_answer = predict_readtype(data_predic)
    
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1, CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
            "FROM data_book "
            "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
            "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
            "WHERE type = %s "
            "LIMIT %s OFFSET %s "
            ,(type_book_answer, items_per_page, offset))
        books = cur.fetchall()
        cur.execute(
            "SELECT COUNT(*)"
            "FROM data_book "
            "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
            "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
            "WHERE type = %s "
            ,(type_book_answer))
        total_items = cur.fetchall()[0][0]
        cur.execute(
        "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1, CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
        "FROM data_book "
        "JOIN pur_hist ON data_book.id = pur_hist.book_id "
        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
        "WHERE pur_hist.status = 3 AND data_book.type = %s"
        "GROUP by pur_hist.book_id "
        "ORDER by SUM(pur_hist.amount) DESC LIMIT 8", (type_book_answer))
        mostsell_books = cur.fetchall()
        print(total_items)
        total_pages = math.ceil(total_items/items_per_page)
        rows = (data_user,)+(type_book_answer,)+(books,)+(mostsell_books,)
        return render_template('answer.html', data= rows, page=page, total_pages = total_pages)

#support_manager assosiation rule
@app.route("/support_manager")
def support_manager():
    conn = connect_mysql()
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
        pd.set_option('display.max_colwidth', None)
        answer = frequent_itemsets.sort_values(by='support', ascending=False)
        answer = [tuple(set(item) if isinstance(item, frozenset) else item for item in row)for row in answer.itertuples(index=False, name=None)]
        answer = [(value, tuple(item_set)) for value, item_set in answer]
        single_item = [(support, items) for support, items in answer if len(items) == 1]
        multiple_item = [(support, items) for support, items in answer if len(items) > 1]
        rows = (single_item,multiple_item,)
    return render_template('assosiation.html',data = rows)

#addpromotion
@app.route("/submit_promotion", methods=['POST'])
def submit_promotion():
    data = request.json
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        for i in data:
            if(i['format'] == "เล่มที่ขายดีในหมวดหมู่นั้น"):
                
                cur.execute("SELECT book_type FROM data_book WHERE book_name = %s",(i['book']))
                book_type = cur.fetchone()[0]
                print(book_type)
                cur.execute("INSERT INTO promotion (target, promotion_type, start, end, sale) VALUES (%s, %s, %s, %s, %s)",(book_type, i['format'], i['start'], i['end'], i['sale']))
                conn.commit()
                cur.execute("SELECT book_id FROM pur_hist JOIN data_book ON id = book_id WHERE book_type = %s GROUP by book_id ORDER BY SUM(amount) DESC LIMIT 10", (book_type))
                books = cur.fetchall()
                cur.execute("SELECT id FROM promotion WHERE 1 ORDER BY id DESC LIMIT 1")
                promotion_id = cur.fetchone()[0]
                for i in books:
                    cur.execute("INSERT INTO promotion_detail (book_id, promotion_id) VALUES (%s, %s)",(i[0],promotion_id))
                    conn.commit()
            elif(i['format'] == "ทั้งหมดในเรื่องนี้"):
                book_name = i['book'].split("เล่ม")
                bookname = "%"+book_name[0]+"%"
                cur.execute("INSERT INTO promotion (target, promotion_type, start, end, sale) VALUES (%s, %s, %s, %s, %s)",(i['book'], i['format'], i['start'], i['end'], i['sale']))
                conn.commit()
                cur.execute("SELECT id FROM promotion WHERE 1 ORDER BY id DESC LIMIT 1")
                promotion_id = cur.fetchone()[0]
                cur.execute("SELECT id FROM data_book WHERE book_name LIKE %s", (bookname))
                books = cur.fetchall()
                for i in books:
                    cur.execute("INSERT INTO promotion_detail (book_id, promotion_id) VALUES (%s, %s)",(i[0],promotion_id))
                    conn.commit()
            elif(i['format'] == "เฉพาะเล่มนี้"):
                cur.execute("INSERT INTO promotion (target, promotion_type, start, end, sale) VALUES (%s, %s, %s, %s, %s)",(i['book'], i['format'], i['start'], i['end'], i['sale']))
                conn.commit()
                cur.execute("SELECT id FROM promotion WHERE 1 ORDER BY id DESC LIMIT 1")
                promotion_id = cur.fetchone()[0]
                cur.execute("SELECT id FROM data_book WHERE book_name = %s", (i['book']))
                book_id = cur.fetchone()[0]
                cur.execute("INSERT INTO promotion_detail (book_id, promotion_id) VALUES (%s, %s)",(book_id,promotion_id))
                conn.commit()
    return jsonify({"message": "Data received successfully!"}), 200

@app.route("/promotion")
def promotion():
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM promotion")
        promotions = list(cur.fetchall())
        for i in range(len(promotions)):
            cur. execute("SELECT book_name, price, CEIL(price*(100-sale)/100), data_book.id FROM promotion_detail JOIN data_book ON book_id = data_book.id JOIN promotion ON promotion_id = promotion.id WHERE promotion_id = %s", (promotions[i][5]))
            books_promotion = cur.fetchall()
            promotions[i] += (books_promotion,)
    return render_template("promotion.html", data = promotions)

@app.route("/edit_promotion", methods = ['POST'])
def edit_promotion():
    try:
        data = request.get_json()[0]
        conn = connect_mysql()
        print(data)
        with conn:
            cur = conn.cursor()
            cur.execute('UPDATE promotion SET target = %s, promotion_type = %s, start = %s, end = %s, sale = %s WHERE id = %s',(data['book'], data['format'], data['start'], data['end'], data['sale'], data['id']))
            conn.commit()
        return redirect(promotion())
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 400

@app.route("/delete_book_promotion", methods = ['POST'])
def delete_book_promotion():
    try:
        data = request.get_json()[0]
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute('DELETE FROM promotion_detail WHERE book_id = %s AND promotion_id = %s', (data['book_id'], data['promotion_id']))
            conn.commit()
            cur.execute("UPDATE `data_book` SET `promotion`= 0 WHERE %s", data['book_id'])
        return redirect(promotion())
    except Exception as e:
        return jsonify({'message': 'An error occurred', 'error': str(e)}), 400

@app.route("/addbook_promotion", methods = ['POST'])
def addbook_promotion():
    try:
        data = request.get_json()[0]
        print(data)
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO promotion_detail (book_id,promotion_id) VALUES (%s, %s)', (data['book_id'], data['id']))
            conn.commit()
            print("success")
        return jsonify({'message': 'Data received successfully', 'data': data}), 200
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred', 'error': str(e)}),400

@app.route("/delete_promotion/<string:promotion_id>")
def delete_promotion(promotion_id):
    try:
        print(promotion_id)
        conn = connect_mysql()
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM `promotion` WHERE id = %s", promotion_id)
            conn.commit()
            cur.execute("DELETE FROM `promotion_detail` WHERE promotion_id = %s", promotion_id)
            conn.commit()
        return promotion()
    except Exception as e:
        print(e)
        return jsonify({'message': 'An error occurred', 'error': str(e)}),400
    

##operation can use any place 

@app.route('/download-excel')
def download_excel():
    data_frames = get_mysql_data()
    if data_frames is None:
        return "An error occurred while retrieving data from the database.", 500
    try:
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, df in data_frames.items():
                df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)
        return send_file(output, download_name='data.xlsx', as_attachment=True)
    except Exception as e:
        print(f"Error: {e}")
        return "An error occurred while creating the Excel file.", 500

#connect mysql server
def connect_mysql():
    conn = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')
    return conn


#connect mysql localhost
# def connect_mysql():
#     conn = pymysql.connect(host = "localhost",
#                            user = "root",
#                            password = "",
#                            database = "bookstore_data",
#                            charset='utf8mb4',
#                            connect_timeout=28800)
#     return conn

#get data to excel
def get_mysql_data():
    conn = connect_mysql()
    
    # ดึงข้อมูลจาก 3 ตาราง
    queries = {
        'Table1': "SELECT * FROM data_book",
        'Table2': "SELECT * FROM users",
        'Table3': "SELECT * FROM pur_hist"
    }
    
    data_frames = {}
    for sheet_name, query in queries.items():
        df = pd.read_sql(query, conn)
        data_frames[sheet_name] = df
    
    conn.close()
    print(data_frames)
    return data_frames

##open image in mysql
@app.route("/image/<int:pur_id>")
def image(pur_id):
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT cus_id FROM pur_hist WHERE pur_id = %s",pur_id)
        cus_id = cur.fetchone()[0]
        if((cus_id==data_user[0]) | (data_user[0] == 1)):
            cur.execute("SELECT img_confirm FROM con_pur WHERE pur_id = %s", (pur_id,))
            image_blob = cur.fetchone()[0]
            return Response(image_blob, mimetype='image/png')
        return redirect('/')

##search book
def search(searchbook, filter):
    print(searchbook)
    print(filter)
    try:
        firstsearch = searchbook + '%'
        middlesearch = '%' + searchbook + '%'
        filter = '%' + filter + '%'
        conn = connect_mysql()  # Assuming connect_mysql() is the function that returns a connection
        cur = conn.cursor()
        # First search
        cur.execute(
            "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1, CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
            "FROM data_book " 
            "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
            "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
            "WHERE book_type LIKE %s AND (book_name LIKE %s OR book_name LIKE %s )",
            (filter, firstsearch, middlesearch)
        )
        search_results = cur.fetchall()
        
        cur = conn.cursor()
        cur.execute(
        "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1 AND promotion.start < CURDATE() AND promotion.end > CURDATE(), CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
        "FROM data_book "
        "JOIN pur_hist ON data_book.id = pur_hist.book_id "
        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
        "WHERE pur_hist.status = 3  AND book_type LIKE %s AND (book_name LIKE %s OR book_name LIKE %s"
        "GROUP by pur_hist.book_id "
        "ORDER by SUM(pur_hist.amount) DESC LIMIT 8")
        mostsell_books = cur.fetchall()

        # Second query for popular books
        mostsell_books = getmostselling()

        rows = data_user,(searchbook),(filter),search_results,mostsell_books
        return render_template('search.html', data=rows, len=len(rows))
        
    except Exception as e:
        print(e)  # For debugging purposes
        rows = ()
        return render_template('search.html', data=rows)

    finally:
        conn.close()  # Always close the connection

@app.errorhandler(pymysql.err.OperationalError)
def handle_operational_error(error):
    if error.args[0] == 1226:
        return jsonify({"error": "User has exceeded the max_user_connections limit."}), 503
    elif error.args[0] == 2003:
        return jsonify({"error": "Can't connect to MySQL server (timed out)."}), 504
    return jsonify({"error": "An unknown operational error occurred."}), 500


##best sell
def getmostselling():
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute(
        "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1 AND promotion.start < CURDATE() AND promotion.end > CURDATE(), CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
        "FROM data_book "
        "JOIN pur_hist ON data_book.id = pur_hist.book_id "
        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
        "WHERE pur_hist.status = 3 "
        "GROUP by pur_hist.book_id "
        "ORDER by SUM(pur_hist.amount) DESC LIMIT 12")
        mostsell_books = cur.fetchall()
    return mostsell_books

def getpromotion_book():
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute(   
        "SELECT data_book.id, data_book.book_name, publisher, book_type, book_category, author, description, store, data_book.image_url, IF(data_book.promotion = 1, CEIL(data_book.price*(100-sale)/100), data_book.price), data_book.price "
        "FROM data_book "
        "LEFT OUTER JOIN promotion_detail ON promotion_detail.book_id = data_book.id "
        "LEFT OUTER JOIN promotion ON promotion_detail.promotion_id = promotion.id "
        "WHERE data_book.promotion = 1 AND promotion.start < CURDATE() AND promotion.end > CURDATE() "
        )
        promotion_books = cur.fetchall()
    return promotion_books

def predict_readtype(data_predic):
    df = pd.read_csv("data_predict/book_data.csv")
    df = df.drop(['Timestamp','ท่านมีความยินดีในการตอบแบบสอบถามครั้งนี้หรือไม่','directory_type','fiction_type','fiction_catagory','Purchase_CH','frequency','favorite_autor','favorite_book','buy_in_6m'], axis=1)
    gender = {'ชาย':1, 'หญิง':2}
    age = {'15-20 ปี':1, '21-29 ปี':2, '30-39 ปี':3, '40-49 ปี':3, '50 ปีขึ้นไป':4}
    educate = {'มัธยมต้น':1, 'มัธยมปลาย หรือเทียบเท่า':2, 'ปวช.':3, 'ปวส.':4, 'ปริญญาตรี หรือเทียบเท่า':5, 'ปริญญาโท':6, 'ปริญญาเอก':7}
    job = {'รับราชการ':1, 'พนักงานรัฐวิสาหกิจ':2, 'พนักงานบริษัทเอกชน':3, 'ธุรกิจส่วนตัว':4, 'รับจ้างทั่วไป':5, 'นักเรียน':6, 'นักศึกษา':7, 'ค้าขาย':8}
    income = {'0 - 15,000 บาท':1, '15,001 – 30,000 บาท':2, '30,001 – 50,000 บาท':3, 'มากกว่า 50,000 บาท':4}
    book_type = {'บันเทิงคดี (ตอบข้อ 5 - 6)':1, 'บันเทิงคดี (ตอบข้อ 3-4) (เป็นหนังสือที่มีเนื้อหาให้ความบันเทิงแก่ผู้อ่าน)':1, 'สารคดี (ตอบข้อ 4)':2, 'สารคดี (ตอบข้อ 2) (เป็นหนังสือที่มุ่งให้ความรู้แก่ผู้อ่าน มีเนื้อหาหลากหลาย ครอบคลุมวิชาการสาขาต่าง ๆ)':2}
    types = {'นิยาย เเละวรรณกรรม':1, 'วิทยาการ เเละเทคโนโลยี':2, 'ประวัติศาสตร์ เเละวัฒนธรรม':3, 'การศึกษา เเละการเรียนรู้':4, 'ธุรกิจ เเละการเงิน':5, 'สุขภาพ เเละการดูเเลรักษา':6, 'ศาสนา เเละปรัชญา':7}
    category = {'หนังสือเรียน':1, 'หนังสือการ์ตูน':2, 'นิยาย':3, 'วรรณกรรม':4, 'หนังสือท่องเที่ยว':5, 'ไลฟ์สไตล์':6, 'สุขภาพ เเละความงาม':7, 'คอมพิวเตอร์':8, 'โหราศาสตร์ ดูดวง ฮวงจุ้ย':9, 'หนังสือต่างประเทศ':10, 'หนังสือเตรียมสอบ เเนวข้อสอบ':11}
    cost = {'ไม่เกิน 200 บาท':1, '201 - 500 บาท':2, '501 - 800 บาท':3, '801 - 1,000 บาท':4, '1,001 - 1,500 บาท':5, 'มากกว่า 1,500 บาท':6}
    df['gender'] = df['gender'].map(gender)
    df['age'] = df['age'].map(age)
    df['education'] = df['education'].map(educate)
    df['job'] = df['job'].map(job)
    df['income'] = df['income'].map(income)
    df['book_type'] = df['book_type'].map(book_type)
    df['type_1'] = df['type_1'].map(types)
    df['type_2'] = df['type_2'].map(types)
    df['type_3'] = df['type_3'].map(types)
    df['category_1'] = df['category_1'].map(category)
    df['category_2'] = df['category_2'].map(category)
    df['category_3'] = df['category_3'].map(category)
    df['type_3m'] = df['type_3m'].map(types)
    df['type_6m'] = df['type_6m'].map(types)
    df['category_3m'] = df['category_3m'].map(category)
    df['category_6m'] = df['category_6m'].map(category)
    df['avg_cost'] = df['avg_cost'].map(cost)
    df['cost_per_book'] = df['cost_per_book'].map(cost)
    df.fillna({
    'job' : df['job'].mode()[0],
    'book_type' : df['book_type'].mode()[0],
    'type_1' : df['type_1'].mode()[0],
    'type_2' : df['type_2'].mode()[0],
    'type_3' : df['type_3'].mode()[0],
    'category_1' : df['category_1'].mode()[0],
    'category_2' : df['category_2'].mode()[0],
    'category_3' : df['category_3'].mode()[0],
    'type_3m' : df['type_3m'].mode()[0],
    'type_6m' : df['type_6m'].mode()[0],
    'category_3m' : df['category_3m'].mode()[0],
    'category_6m' : df['category_6m'].mode()[0],
    'avg_cost' : df['avg_cost'].mode()[0],
    'cost_per_book' : df['cost_per_book'].mode()[0]
    }, inplace=True)

    X = df[['gender', 'age', 'education', 'job', 'income']]
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(X)
    kmeans = KMeans(n_clusters=21)
    kmeans.fit(scaled_features)
    df['cluster'] = kmeans.labels_
    most_common_book_type = df.groupby('cluster')['book_type'].agg(lambda x: x.mode()[0])
    df['most_in_cluster'] = df['cluster'].map(most_common_book_type)

    X = df[['gender', 'age', 'education', 'job', 'income', 'type_2', 'type_3', 'type_3m', 'category_6m', 'avg_cost']]
    y = df['most_in_cluster']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    dt = DecisionTreeClassifier(random_state=42)
    dt.fit(X_train, y_train)
    y_pred_dt = dt.predict(X_test)
    sample_data = pd.DataFrame({'gender': [2]
                            ,'age': [3]
                            ,'education': [6],
                            'job': [3],
                            'income': [3],
                            'type_2': [4],
                            'type_3': [1],
                            'type_3m':[1], 
                            'category_6m':[2],
                            'avg_cost': [4]})
    book_type = {1:'บันเทิงคดี',2:'สารคดี'}
    answer = book_type[int(dt.predict(sample_data))]
    return answer

if __name__ == "__main__":
    app.run(debug=True)
