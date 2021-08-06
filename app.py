import hmac
import sqlite3

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS
from flask_mail import Mail, Message
import re
import cloudinary
import cloudinary.uploader

# email validation
regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

# create class for user log in details
class User(object):
    def __init__(self, id, username, password, email):
        self.id = id
        self.username = username
        self.password = password
        self.email = email


# create class(object) for products
class Product(object):
    def __init__(self, product_id, product_name, product_type, price, quantity, product_image):
        self.product_id = product_id
        self.product_name = product_name
        self.product_type = product_type
        self.price = price
        self.quantity = quantity
        self.image = product_image

# create class (object) for Database functions
class Database(object):
    # function to connect to Database and crete cursor
    def __init__(self):
        self.conn = sqlite3.connect('sales.db')
        self.cursor = self.conn.cursor()

    # function for INSERT AND UPDATE query
    def commiting(self, query, values):
        self.cursor.execute(query, values)
        self.conn.commit()

    # function for executing SELECT query
    def single_commiting(self, query):
        self.cursor.execute(query)

    # function to fetch data for SELECT query
    def fetching(self):
        return self.cursor.fetchall()

# function to upload image into table
def image_file():
    app.logger.info('in upload route')
    cloudinary.config(cloud_name ="djcpeeu7k", api_key="168276427645577",
                      api_secret="z7qzuUnTfhyh9ylrxV0UXM_SvPc")
    upload_result = None
    if request.method == 'POST' or request.method =='PUT':
        image = request.files['product-image']
        app.logger.info('%s file_to_upload', image)
        if image:
            upload_result = cloudinary.uploader.upload(image)
            app.logger.info(upload_result)
            return upload_result['url']


# fetch username and password from the users table
def fetch_users():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        new_data = []

        for data in users:
            new_data.append(User(data[0], data[3], data[4], data[5]))
    return new_data

#
def fetch_products():
    with sqlite3.connect('sales.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM all_products")
        products = cursor.fetchall()

        new_data = []

        for data in products:
            new_data.append(Product(data[0], data[1], data[2], data[3], data[4], data[5]))
    return new_data

#
# # call function to fetch username and password
users = fetch_users()
# # call function to fetch all products
allproducts = fetch_products()


# create user table
def init_user_table():
    conn = sqlite3.connect('sales.db')
    conn.execute("CREATE TABLE IF NOT EXISTS user(user_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                 "first_name TEXT NOT NULL,"
                 "last_name TEXT NOT NULL,"
                 "username TEXT NOT NULL,"
                 "password TEXT NOT NULL,"
                 "email TEXT NOT NULL)")
    print("user table created successfully")
    conn.close()


# create product table
def init_product_table():
    with sqlite3.connect('sales.db') as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS all_products (product_id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     "product_name TEXT NOT NULL,"
                     "product_type TEXT NOT NULL,"
                     "price TEXT NOT NULL,"
                     "quantity TEXT NOT NULL,"
                     "product_image TEXT NOT NULL)")
    print("items table created successfully")
    conn.close()


# calling function to create the three tables above
init_user_table()
# init_cart_table()
init_product_table()

# fetch data to use for JWT token
username_table = {u.username: u for u in users}
userid_table = {u.id: u for u in users}


# authenticate login using username and password created when the account was registered to return the user profile
def authenticate(username, password):
    user = username_table.get(username, None)
    if user and hmac.compare_digest(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    return userid_table.get(user_id, None)

# app configuration
app = Flask(__name__)
CORS(app)
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'abdullahtest585@gmail.com'
app.config['MAIL_PASSWORD'] = 'testing0909'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

jwt = JWT(app, authenticate, identity)


@app.route('/protected')
@jwt_required()
def protected():
    return '%s' % current_identity


# create various end-points using SQL to fetch and post data to/from tables in DB


# creating registration end-point
@app.route('/registration/', methods=["POST"])
def user_registration():
    response = {}
    db = Database()

    if request.method == "POST":
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        if (re.search(regex,email)):

            query = "INSERT INTO user(first_name,last_name,username,password,email) VALUES(?, ?, ?, ?, ?)"
            values = first_name, last_name, username, password, email
            db.commiting(query, values)
            mail = Mail(app)
            msg = Message('Successfully registered', sender='abdullahtest585@gmail.com', recipients=[email])
            msg.body = "Welcome to the future"
            mail.send(msg)
            response["message"] = "success"
            response["status_code"] = 201
            return response

        else:
            return "Error Invalid Email"


# create end-point to delete products
@app.route("/delete-product/<int:product_id>")
@jwt_required()
def delete(product_id):
    response = {}
    db = Database()

    query = "DELETE FROM all_products WHERE product_id=" + str(product_id)
    db.single_commiting(query)
    #error handling to check if the id exists
    if id == []:
        return "product does not exist"
    else:
        response['status_code'] = 200
        response['message'] = "item deleted successfully."
        return response


# create end-point to allow the user to view their profile
@app.route("/view-profile/<int:user_id>", methods=["GET"])
@jwt_required()
def view_profile(user_id):
    response = {}
    db = Database()

    query = "SELECT * FROM user WHERE user_id= " + str(user_id)
    db.single_commiting(query)

    if user_id == []:

        return "User does not exist"
    else:
        response['status_code'] = 200
        response['data'] = db.fetching()

        return response


# end-point to allow user to view all available products
@app.route("/view-all-products/", methods=["GET"])
@jwt_required()
def view_all():
    response = {}
    db = Database()

    query = "SELECT * FROM  all_products"
    db.single_commiting(query)

    response['status_code'] = 200
    response['data'] = db.fetching()

    return response


# end-point to allow the owner of the business to add products to the list of products available
@app.route("/add-to-product-table/", methods=["POST"])
@jwt_required()
def add():
    response = {}
    db = Database()

    if request.method == "POST":
        product_name = request.form['product_name']
        quantity = request.form['quantity']
        product_type = request.form['product_type']
        price = request.form['price']

        try:
            testq = int(quantity)
            testp = int(price)
            query = "INSERT INTO all_products(product_name,product_type,price,quantity, product_image) VALUES(?, ?, ?, ?, ?)"
            values = product_name, product_type, price, quantity, image_file()
            db.commiting(query, values)
            response["status_code"] = 201
            response['description'] = "item added successfully"

            return response

        except ValueError:
            return "Please enter integer values for price and quantity"



# create end-point to edit existing products/
@app.route("/updating-products/<int:product_id>", methods=["PUT"])
@jwt_required()
def edit(product_id):
    response = {}
    db = Database()

    if request.method == "PUT":
        product_name = request.form['product_name']
        product_type = request.form['product_type']
        price = request.form['price']
        quantity = request.form['quantity']

        try:
            testq = int(quantity)
            testp = int(price)

            query = "UPDATE all_products SET product_name=?, product_type=?, price=?, quantity=?, product_image=?" \
                    " WHERE product_id='" + str(product_id) + "'"
            values = product_name, product_type, price, quantity, image_file()

            db.commiting(query, values)

            response['message'] = 200
            response['message'] = "Product successfully updated "

            return response

        except ValueError:
            return "Please enter integer values for price and quantity"


if __name__ == '__main__':
    app.debug = True
    app.run()