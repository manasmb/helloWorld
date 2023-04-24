from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime as dt
db = SQLAlchemy()

class Product(db.Model):
    __tablename__ = 'product'
    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_category.category_id'))
    product_name = db.Column(db.String(100), nullable=False)
    product_code = db.Column(db.String(30), nullable=False)
    product_description = db.Column(db.Text)
    product_image = db.Column(db.String(100))
    product_price = db.Column(db.Float, nullable=False)

    def __init__(self, product_name, product_code, product_description, product_image, product_price, category_id):
        self.product_name = product_name
        self.product_code = product_code
        self.product_description = product_description
        self.product_image = product_image
        self.product_price = product_price
        self.category_id = category_id

    def __repr__(self):
        return f"{self.product_name}"


class ProductCategory(db.Model):
    __tablename__ = 'product_category'

    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(30), nullable=False)
    products = db.relationship('Product', backref='products')

    def __init__(self, category_id, category_name):
        self.category_id = category_id
        self.category_name = category_name

    def __repr__(self):
        return f"{self.category_id} - {self.category_name}"

class StoreOrder(db.Model):
    __tablename__ = 'store_order'

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_date = db.Column(db.DateTime, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.customer_id'))
    first_name = db.Column(db.String(30), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone_number = db.Column(db.String(10))
    email = db.Column(db.String(100))
    address = db.Column(db.String(100))
    city = db.Column(db.String(100))
    state = db.Column(db.String(2))
    zip = db.Column(db.String(9))
    status = db.Column(db.String(20), default='PENDING PAYMENT')
    payment_type = db.Column(db.String(10))
    customers = db.relationship('Customer', backref='customers')

    def __init__(self, customer_id, first_name, last_name, phone_number, email, address, city, state, zip, order_date=dt.now()):
        self.customer_id = customer_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.email = email
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip
        self.order_date = order_date

class OrderItem(db.Model):
    __tablename__ = 'order_item'

    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('store_order.order_id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.product_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price_charged = db.Column(db.Float, nullable=False)

    def __init__(self, order_id, product_id, quantity):
        product = Product.query.filter_by(product_id=product_id).first()

        self.order_id = order_id
        self.product_id = product_id
        self.quantity = quantity
        self.price_charged = product.product_price * quantity


class Customer(db.Model):
    __tablename__ = 'customer'

    customer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False, unique=True)
    users = db.relationship('User', backref='users')

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return f"{self.user_id}"


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True)
    first_name = db.Column(db.String(30))
    last_name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))

    def __init__(self, username, first_name, last_name, email, password, role='PUBLIC'):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.role = role

    # Function for flask_login manager to provider a user ID to know who is logged in
    def get_id(self):
        return(self.user_id)

    def __repr__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"