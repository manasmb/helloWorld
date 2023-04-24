from app import app, db
from models import Customer, User, Product, ProductCategory, StoreOrder
from werkzeug.security import generate_password_hash
import random
import datetime as dt

with app.app_context():
    db.drop_all()
    db.create_all()

    # Initial loading of customers
    customers = [
        {'user_id': 1}
    ]

    for each_customer in customers:
        print(f'{each_customer["user_id"]} inserted into customer')
        a_customer = Customer(each_customer["user_id"])
        db.session.add(a_customer)
        db.session.commit()

    # Initial loading of users
    users = [
        {'username': 'olive', 'email': 'opurchess@gmail.com', 'first_name':'Olive', 'last_name':'Perchases',
            'password': generate_password_hash('olive', method='sha256'), 'role':'CUSTOMER'},
        {'username': 'admin', 'email': 'abyer@my-store.com', 'first_name':'Anita', 'last_name':'Byer',
            'password': generate_password_hash('adminpw', method='sha256'), 'role':'ADMIN'}
    ]

    for each_user in users:
        print(f'{each_user["username"]} inserted into user')
        a_user = User(username=each_user["username"], email=each_user["email"], first_name=each_user["first_name"],
                      last_name=each_user["last_name"], password=each_user["password"], role=each_user["role"])
        db.session.add(a_user)
        db.session.commit()

    # Initial loading of product categories
    product_categories = [
        {'category_id': 1, 'category_name': 'Clothing'},
        {'category_id': 2, 'category_name': 'Graduation'},
        {'category_id': 3, 'category_name': 'Accessories'},
        {'category_id': 4, 'category_name': 'Home & Office'},
        {'category_id': 5, 'category_name': 'Outdoor & Recreation'},
        {'category_id': 6, 'category_name': 'Textbooks'}

    ]

    for each_product_category in product_categories:
        print(f'{each_product_category["category_name"]} inserted into product_category')
        a_product_category = ProductCategory(category_id=each_product_category['category_id'],
                                             category_name=each_product_category['category_name'])
        db.session.add(a_product_category)
        db.session.commit()

    # Initial loading of products
    products = [
        {'product_name':'Hat', 'product_code':'PROD-0555', 'product_description':'Show your Terp spirit by wearing this stylish hat.',
            'product_image':'PROD-0555-hat.png', 'product_price':14.95, 'category_id': 1},
        {'product_name': 'Men\'s Pullover Jacket', 'product_code': 'PROD-0123', 'product_description': 'This jacket will keep you warm and snuggly on those cold nights.',
            'product_image': 'PROD-0123-pullover-jacket.png', 'product_price':39.99, 'category_id': 1},
        {'product_name': 'Prep School Ringspun T-Shirt', 'product_code': 'PROD-0987', 'product_description': 'Maryland Terrapins Prep School Ringspun S/S Tee red',
            'product_image': 'PROD-0987-t-shirt.png', 'product_price':31.48, 'category_id': 1},
        {'product_name': 'Framing Success 13 x 17 Greystone Gold Medallion Bachelors/Masters Diploma Frame', 'product_code': 'PROD-0407',
         'product_description': 'FSC certified hardwood from well-managed forests features an anthracite veneer with an inner accent trim. Our Grey Suede/Gold mat features a gold-minted medallion of the official University seal and embossed University name. Made in the USA.',
         'product_image': 'PROD-0407-diploma.png', 'product_price': 235.00, 'category_id': 2}
    ]

    for each_product in products:
        print(f'{each_product["product_name"]} inserted into product')
        a_product = Product(product_name=each_product['product_name'], product_code=each_product['product_code'],
                            product_description=each_product['product_description'], product_image=each_product['product_image'],
                            product_price=each_product['product_price'], category_id=each_product['category_id'])
        db.session.add(a_product)
        db.session.commit()

    # Insert fake orders for analytics
    states = ['MD', 'DC', 'VA', 'TX', 'FL', 'NY', 'CA', 'DE']

    start_date = dt.datetime.now() - dt.timedelta(days=366)
    end_date = dt.datetime.now() - dt.timedelta(days=1)

    for i in range(1, 20000):
        an_order = StoreOrder(customer_id=1, first_name='Fake', last_name='Order', phone_number='', email='',
                              address='', city='', state=random.choice(states), zip='', order_date=start_date + (end_date - start_date) * random.random())
        db.session.add(an_order)
    db.session.commit()

    # Insert fake products for analytics
    categories = [each_category['category_id'] for each_category in product_categories]

    for i in range(1, 45):
        a_product = Product(product_name='Fake Product' + str(i), product_code='PROD-F'+ str(i), product_description='',
                            product_image='', product_price=random.randrange(1, 250), category_id=random.choice(categories))
        db.session.add(a_product)
    db.session.commit()