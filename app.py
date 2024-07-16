from flask import Flask, render_template, request, redirect, url_for, Response
import pymysql
import datetime

app = Flask(__name__)
data_user = (2,"email","password","name","gender","birth","address",0)
cart = []
number_of_book = []
book_search = ""
book_filter = "ทั้งหมด"
order_number = 0

##mainpage
@app.route("/")
def mainpage():
    conn = connect_mysql()
    print(data_user)
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT id,data_book.book_name,publisher,book_type,book_category,author,description,store,data_book.image_url,data_book.price FROM pur_hist JOIN data_book ON pur_hist.book_id = data_book.id GROUP BY book_id ORDER BY COUNT(*) DESC")
    return render_template('index.html',data = (data_user,)+(cur.fetchall(),))

##storebook
@app.route("/bookdata")
def showData():
    conn = connect_mysql()
    if (data_user[0] == 1):
        with conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM data_book ORDER BY id")
        return render_template('bookdata.html',data= cur.fetchall())
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
            with conn.cursor() as cursor:
                sql = "INSERT INTO `data_book`(`id`, `book_name`, `publisher`, `book_type`, `book_category`, `author`, `description`, `store`, `image_url`,`price`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql,(book_id,book_name,publisher,book_type,category,author,description,store,image_url,price))
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
@app.route("/search/<string:filter>/<string:searchinput>", methods = ['GET'])
def searchbook( filter,searchinput,):
    searchinput = searchinput.replace("+-=","/")
    print(searchinput)
    try:
        conn = connect_mysql() 
        with conn:
            global book_search,book_filter
            book_filter = filter
            book_search = searchinput
            if book_search == "-":
                book_search = ""
            book_name = "%"+book_search+"%"
            print(book_name)
            cur = conn.cursor()
            if(book_filter == "ทั้งหมด"):
                cur.execute("SELECT * FROM `data_book` WHERE `book_name` LIKE %s", book_name)
            else:
                cur.execute("SELECT * FROM `data_book` WHERE `book_name` LIKE %s &&  `book_type` = %s ", (book_name, book_filter))
            rows = (data_user,)+cur.fetchall()
        return render_template('search.html',data=rows, len = len(rows))
    except IndexError:
        rows()
        return render_template('search.html',data=rows)

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
                global data_user 
                data_user = rows[0]
                print(data_user)
            return redirect(url_for('mainpage'))
    except IndexError:
        return redirect("/login")
        
##register
@app.route("/register")
def register():
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
        with conn.cursor() as cursor:
            sql = "INSERT INTO `users`(`email`, `password`, `fname`, `gender`, `birth`, `address`, `tel_no`) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql,(email,password,fullname,gender,birthday,address,tel_no))
            conn.commit()
        return redirect(url_for('mainpage'))

@app.route("/userinfo")
def userdata():
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
        with conn.cursor() as cursor:
            sql = "UPDATE users SET email=%s,password=%s,fname=%s,gender=%s,birth=%s,address=%s,tel_no=%s WHERE customer_id = %s"
            cursor.execute(sql,(email,password,name,gender,birthday,address,tel_no,user_id))
            conn.commit()
            global data_user
            data_user = [user_id,email,password,name,gender,birthday,address,tel_no]
        return userdata()

##Add to cart
@app.route("/addcart/<string:id_data>", methods = ['POST'])
def addcart(id_data):
    wanted = request.form['wanted']
    url = request.form['url']
    print(url)
    global cart
    if id_data in cart:
        number_of_book[cart.index(id_data)] = int(number_of_book[cart.index(id_data)]) +int(wanted)
    else:
        cart.append(id_data)
        number_of_book.append(wanted)
    global book_search
    if url == "mainpage":
        return redirect("/")
    return searchbook(book_filter, book_search)

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
            cur.execute("SELECT * FROM `data_book` WHERE id = %s",(cart[i]))
            data = cur.fetchall()
            data = data[0]+(number_of_book[i],data[0][9]*int(number_of_book[i]),)
            rows += (data,)
            total_price += (rows[i][11])*int(number_of_book[i])
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
## NOT DONE
@app.route("/confirm_list", methods = ["GET"])
def confirm_list():
    global cart,number_of_book
    conn = connect_mysql() 
    date =  datetime.datetime.now()
    print(cart,number_of_book)
    sql = "INSERT INTO pur_hist (book_id, cus_id, amount, status, pur_id, date, book_name, img_book_url, price) VALUES (%s,%s,%s,0,%s,%s,%s,%s,%s)"
    with conn:
        cur = conn.cursor()
        cur.execute("SELECT pur_id FROM pur_hist ORDER BY pur_id DESC LIMIT 1")
        pur_id = cur.fetchone()[0]+1
        for i in range(len(cart)):
            cur.execute("SELECT id, book_name, image_url, price FROM data_book WHERE id = %s",cart[i])
            data_book = cur.fetchone()
            print(data_book[0])
            cur.execute(sql,(data_book[0], data_user[0], number_of_book[i], pur_id,date, data_book[1], data_book[2], data_book[3]))
            conn.commit()
        url = "/purchase/"+str(pur_id)
        number_of_book = []
        data_book = []
    return redirect(url)

##purchase_history
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
        cur.execute("SELECT status, book_id FROM pur_hist WHERE pur_id = %s", pur_id)
        data = cur.fetchall()
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
    return mainpage()

@app.route('/purchase_data')
def purchase_data():
    conn = connect_mysql()
    if(data_user[0] > 0):
        with conn:
            cur = conn.cursor()
            if(data_user[0] == 1):
                cur.execute("SELECT pur_id FROM pur_hist WHERE status = 3 LIMIT 5")
            elif(data_user[0] > 1):
                cur.execute("SELECT pur_id FROM pur_hist WHERE cus_id = %s AND status = 3",data_user[0])
            pur_id = (sorted(set(cur.fetchall())))
            rows = ()
            for i in pur_id:
                if(data_user[0] ==1):
                    cur.execute("SELECT book_id,cus_id,amount,pur_id,date,status FROM pur_hist WHERE pur_id = %s",i[0])
                elif(data_user[0] > 1):
                    cur.execute("SELECT pur_id,book_name,img_book_url,amount,amount*price,status FROM pur_hist WHERE pur_id = %s",i[0])
                pur_data = cur.fetchall()
                cur.execute("SELECT sum(amount*price) FROM pur_hist WHERE pur_id = %s",i[0])
                pur_data = (pur_data,cur.fetchone())
                if(pur_data[0][0][5] > 0):
                    cur.execute("SELECT * FROM con_pur WHERE pur_id = %s",i[0])
                    pur_data += cur.fetchall()
                rows += (pur_data,)
                print(rows)
            if(data_user[0] ==1):
                return render_template('purchase_data.html',data = rows)
            elif(data_user[0] > 1):
                return render_template('history.html',data = rows) 
    else:
        redirect("/")

@app.route('/status')
def status_data():
    conn = connect_mysql() 
    if(data_user[0] > 0):
        with conn:
            cur = conn.cursor()
            if(data_user[0] == 1):
                cur.execute("SELECT pur_id FROM pur_hist WHERE status != 3 ORDER BY status")
            elif(data_user[0] > 1):
                cur.execute("SELECT pur_id FROM pur_hist WHERE cus_id = %s AND status != 3",data_user[0])
            pur_id = (set(cur.fetchall()))
            rows = ()
            for i in pur_id:
                if(data_user[0] ==1):
                    print("say hi admin")
                    cur.execute("SELECT book_id,cus_id,amount,pur_id,date,status FROM pur_hist WHERE pur_id = %s",i[0])
                elif(data_user[0] > 1):
                    cur.execute("SELECT pur_id,book_name,img_book_url,amount,amount*price,status FROM pur_hist WHERE pur_id = %s",i[0])
                pur_data = cur.fetchall()
                cur.execute("SELECT sum(amount*price) FROM pur_hist WHERE pur_id = %s",i[0])
                pur_data = (pur_data,cur.fetchone())
                if(pur_data[0][0][5] > 0):
                    cur.execute("SELECT * FROM con_pur WHERE pur_id = %s",i[0])
                    pur_data += cur.fetchall()
                    print(pur_data)
                rows += (pur_data,)
            if(data_user[0] ==1):
                return render_template('purchase_data.html',data = rows)
            elif(data_user[0] > 1):
                return render_template('history.html',data = rows) 
    else:
        redirect("/")

@app.route('/update_status/<string:pur_id>', methods = ['POST'])
def update_status(pur_id):    
    status = request.form['status']
    conn = connect_mysql()
    with conn:
        cur = conn.cursor()
        cur.execute("UPDATE `pur_hist` SET status = %s WHERE pur_id = %s",(status,pur_id))
        conn.commit()
    return redirect('/purchase_data')

##operation can use any place 

#connect mysql server
def connect_mysql():
    conn = pymysql.connect(host = "bz4wmwysknkncbytijkz-mysql.services.clever-cloud.com",user = "uqktonelhlb44lsb",password = "BflVVXRFGugcEPV42Eas",database = "bz4wmwysknkncbytijkz",charset='utf8mb4')
    return conn

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


if __name__ == "__main__":
    app.run(debug=True)
