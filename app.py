import hmac
import sqlite3

from flask import Flask, request
from flask_jwt import JWT, jwt_required, current_identity
from flask_cors import CORS, cross_origin
from flask_mail import Mail, Message
import re
import cloudinary
import cloudinary.uploader
from werkzeug.utils import redirect

# email validation
regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'

# create class for user log in details
class User(object):
    def __init__(self, id, username, password, email):
        self.id = id
        self.username = username
        self.password = password
        self.email = email

# class Admin(object):
#     def __init__(self, admin_id, admin_username, admin_password):
#         self.admin_id = admin_id
#         self.admin_username = admin_username
#         self.admin_password = admin_password


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
        self.conn.commit()

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
        image = request.form['product_image']
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

# def fetch_admin():
#     with sqlite3.connect('shopping.db') as conn:
#         cursor = conn.cursor()
#         cursor.execute("SELECT * FROM admin")
#         users_data = cursor.fetchall()
#
#         new_data = []
#
#         for data in users_data:
#             new_data.append(Admin(data[0], data[1], data[2]))
#
#         return new_data

#
# # call function to fetch username and password
users = fetch_users()
# # call function to fetch all products
allproducts = fetch_products()

#fetch admin
# admin = fetch_admin()


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

# def init_admin_table():
#     with sqlite3.connect('sales.db') as conn:
#         conn.execute("CREATE TABLE IF NOT EXISTS admin(admin_id INTEGER PRIMARY KEY AUTOINCREMENT,"
#                      "admin_username TEXT NOT NULL,"
#                      "admin_password TEXT NOT NULL)")
#         print("admin table created successfully")


# calling function to create the three tables above
init_user_table()
# init_cart_table()
init_product_table()
# init_admin_table()

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
CORS(app, resources={r"/*":{"origins": "*"}})
app.debug = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'abdullah.isaacs@gmail.com'
app.config['MAIL_PASSWORD'] = 'yolo0909!'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['CORS_HEADERS'] = ['Content-Type']

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
        # if (re.search(regex,email)):

        query = "INSERT INTO user(first_name,last_name,username,password,email) VALUES(?, ?, ?, ?, ?)"
        values = first_name, last_name, username, password, email
        db.commiting(query, values)
        mail = Mail(app)
        msg = Message('Successfully registered', sender='abdullah.isaacs@gmail.com', recipients=[email])
        msg.body = "Welcome to the future"
        mail.send(msg)
        response["message"] = "success"
        response["status_code"] = 201
        return response



# create end-point to delete products
@app.route("/delete-product/<int:product_id>")
# @jwt_required()
# @cross_origin()
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

# create end-point to delete user
@app.route("/delete-profile/<email>")
# @jwt_required()
# @cross_origin()
def delete_profile(email):

    response = {}
    db = Database()

    query = "DELETE FROM user WHERE email='" + email + "'"
    db.single_commiting(query)
    #error handling to check if the id exists
    if email == []:
        return "user does not exist"
    else:
        response['status_code'] = 200
        response['message'] = "profile deleted successfully."
        return response



# create end-point to allow the user to view their profile
@app.route("/view-profile/<email>/", methods=["GET"])
# @jwt_required()
# @cross_origin()
def view_profile(email):

    response = {}
    db = Database()

    query = "SELECT * FROM user WHERE email= '" + email + "'"
    db.single_commiting(query)

    if db.fetching() == []:

        return "User does not exist"
    else:
        response['status_code'] = 200
        response['data'] = db.fetching()

        return response

# select a product
@app.route("/view-product/<int:product_id>/", methods=["GET"])
# @jwt_required()
# @cross_origin()
def view_product(product_id):

    response = {}
    db = Database()

    query = "SELECT * FROM all_products WHERE product_id= '" + str(product_id) + "'"
    db.single_commiting(query)

    if db.fetching() == []:

        return "product does not exist"
    else:
        response['status_code'] = 200
        response['data'] = db.fetching()

        return response


# end-point to allow user to view all available products
@app.route("/view-all-products/", methods=["GET"])

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
# @jwt_required()
# @cross_origin()
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
            return {
                "error": "failed to insert into DB"
            }




# create end-point to edit existing products/
@app.route("/updating-products/<int:product_id>", methods=["PUT"])
# @jwt_required()
# @cross_origin()
def edit(product_id):

    response = {}
    db = Database()

    if request.method == "PUT":
        product_name = request.json['product_name']
        product_type = request.json['product_type']
        price = request.json['price']
        quantity = request.json['quantity']

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

# create end-point to edit existing profiles/
@app.route("/updating-profile/<emailv>", methods=["PUT"])
# @jwt_required()
# @cross_origin()
def edit_user(emailv):

    response = {}
    db = Database()

    if request.method == "PUT":
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        username = request.json['username']
        password = request.json['password']
        email = request.json['email']

        query = "UPDATE user SET first_name=?, last_name=?, username=?, password=?, email=?" \
                " WHERE email='" + emailv + "'"
        values = first_name, last_name, username, password, email

        db.commiting(query, values)

        response['message'] = 200
        response['message'] = "Profile successfully updated "

        return response



if __name__ == '__main__':
    app.debug = True
    app.run()
