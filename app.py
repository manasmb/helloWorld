import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from sqlalchemy import func
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from authorize import role_required
from models import *
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import datetime as dt


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'beyond_course_scope'
db.init_app(app)

# Product image parameters
app.config['PRODUCT_UPLOAD_PATH'] = 'static/products'

# Product order restrictions
app.config['MAX_QUANTITY_PER_ITEM'] = 99

login_manager = LoginManager()
login_manager.login_view = 'login' # default login route
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


### Routes for All Users ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    default_admin_route_function = 'product_view_all'
    default_customer_route_function = 'home'

    if request.method == 'GET':
        # Determine where to redirect user if they are already logged in
        if current_user and current_user.is_authenticated:
            if current_user.role in ['ADMIN']:
                return redirect(url_for(default_admin_route_function))
        else:
            redirect_route = request.args.get('next')
            return render_template('login.html', redirect_route=redirect_route)

    elif request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        redirect_route = request.form.get('redirect_route')

        user = User.query.filter_by(username=username).first()

        # Validate user credentials and redirect them to initial destination
        if user and check_password_hash(user.password, password):
            login_user(user)

            if current_user.role in ['ADMIN']:
                return redirect(redirect_route if redirect_route else url_for(default_admin_route_function))
            elif current_user.role == 'CUSTOMER':
                return redirect(redirect_route if redirect_route else url_for(default_customer_route_function))
        else:
            flash(f'Your login information was not correct. Please try again.', 'error')

        return redirect(url_for('login'))

    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    if 'cart' in session:
        del (session['cart'])

    logout_user()
    flash(f'You have been logged out.', 'success')
    return redirect(url_for('home'))

### Customer Routes ###
@app.route('/')
def home():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('home.html', products=products)


@app.route('/product/<int:product_id>')
def product_view(product_id):
    product = Product.query.filter_by(product_id=product_id).first()

    if product:
        return render_template('product_view.html', product=product)

    else:
        flash(f'Product attempting to be viewed could not be found! Please contact support for assistance', 'error')
        return redirect(url_for('home'))


@app.route('/cart/clear')
@login_required
def clear_cart():
    if 'cart' in session:
        del(session['cart'])
        flash(f"Cart Cleared", 'success')
    else:
        flash(f"Cart alredy empty", 'error')
    return redirect(url_for('home'))

@app.route('/cart/add/<int:product_id>', methods=['GET','POST'])
@login_required
def cart_add(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if 'product_quantity' in request.form:
        product_quantity = int(request.form['product_quantity'])
    elif request.method == 'GET':
        product_quantity = 1

    if product:
        if 'cart' not in session:
            session['cart'] = []

        found_item = next((item for item in session['cart'] if item['product_id'] == product_id), None)
        if found_item:
            found_item['product_quantity'] += product_quantity

            if found_item['product_quantity'] > app.config['MAX_QUANTITY_PER_ITEM']:
                found_item['product_quantity'] = app.config['MAX_QUANTITY_PER_ITEM']
                flash(f"You cannot exceed more than {app.config['MAX_QUANTITY_PER_ITEM']} of the same item.")

        else:
            session['cart'].append(
                {'product_id': product.product_id, 'product_name':product.product_name,
                 'product_image':product.product_image, 'product_quantity': product_quantity,
                 'product_price':product.product_price}
            )

        session['cart_total'] = sum(item['product_price']*item['product_quantity'] for item in session['cart'])

        flash(f"{product.product_name} has been successfully added to your cart.", 'success')
        return redirect(url_for('cart_view'))
    else:
        flash(f'Product could not be found. Please contact support if this problem persists.', 'error')


@app.route('/cart/remove/<int:index>', methods=['GET'])
@login_required
def cart_remove(index):
    if 'cart' in session:
        if index < len(session['cart']):
            product_name = session['cart'][index]['product_name']
            session['cart'].pop(index)
            flash(f"{product_name} has been successfully removed from your cart.", 'success')

        else:
            flash(f'Product is not in the cart and could not be removed.', 'error')

    session['cart_total'] = sum(item['product_price'] * item['product_quantity'] for item in session['cart'])

    return redirect(url_for('cart_view'))


@app.route('/cart/view', methods=['GET', 'POST'])
@login_required
def cart_view():
    if 'cart' in session:
        return render_template('cart_view.html', products=session['cart'], cart_count=len(session['cart']), cart_total=session['cart_total'])
    else:
        return render_template('cart_view.html', cart_count=0)


@app.route('/checkout')
@login_required
def checkout():
    return render_template('checkout.html', products=session['cart'], cart_count=len(session['cart']), cart_total=session['cart_total'])


@app.route('/process-order', methods=['GET', 'POST'])
@login_required
def process_order():
    if request.method == 'GET':
        return redirect(url_for('home'))
    elif request.method == 'POST':
        customer = Customer.query.filter_by(user_id=current_user.user_id).first()

        customer_id = customer.customer_id
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone']
        email = request.form['email']
        address = request.form['address']
        city = request.form['city']
        state = request.form['state']
        zip = request.form['zip']

        store_order = StoreOrder(customer_id=customer_id, first_name=first_name, last_name=last_name,phone_number=phone_number,
                                 email=email, address=address, city=city, state=state, zip=zip)
        db.session.add(store_order)
        db.session.flush()
        db.session.refresh(store_order)
        order_id = store_order.order_id

        for each_item in session['cart']:
            item_ordered = OrderItem(order_id, each_item['product_id'], each_item['product_quantity'])
            db.session.add(item_ordered)

        db.session.commit()

    if 'cart' in session:
        del(session['cart'])

    return render_template('thank_you.html', order_number=order_id)


### Admin Routes ###
@app.route('/product/view_all')
@login_required
@role_required(['ADMIN'])
def product_view_all():
    products = Product.query.order_by(Product.product_name).all()
    return render_template('product_view_all.html', products=products)


@app.route('/product/create', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def product_create():
    if request.method == 'GET':
        product_categories = ProductCategory.query.order_by(ProductCategory.category_name) \
        .order_by(ProductCategory.category_name) \
        .all()
        return render_template('product_entry.html', product_categories=product_categories, action='create')
    elif request.method == 'POST':
        product_name = request.form['product_name']
        product_category_id = request.form['product_category_id']
        product_code = request.form['product_code']
        product_description = request.form['product_description']
        product_price = request.form['product_price']
        product_image = request.files['product_image']
        product_filename = secure_filename(product_code + '-' + product_image.filename) #prepend unique product code to avoid filename collisions

        if product_image.filename != '':
            product_image.save(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product_filename))

        product = Product(product_name=product_name, category_id=product_category_id,
                          product_code=product_code, product_description=product_description,
                          product_price=product_price, product_image=product_filename if product_image else '')
        db.session.add(product)
        db.session.commit()
        flash(f'{product_name} was successfully added!', 'success')
        return redirect(url_for('product_view_all'))

    # Address issue where unsupported HTTP request method is attempted
    flash(f'Invalid request. Please contact support if this problem persists.', 'error')
    return redirect(url_for('product_view_all'))


@app.route('/product/update/<int:product_id>', methods=['GET', 'POST'])
@login_required
@role_required(['ADMIN'])
def product_edit(product_id):
    if request.method == 'GET':
        product = Product.query.filter_by(product_id=product_id).first()
        product_categories = ProductCategory.query.order_by(ProductCategory.category_name) \
        .order_by(ProductCategory.category_name) \
        .all()

        if product:
            return render_template('product_entry.html', product=product, product_categories=product_categories, action='update')

        else:
            flash(f'Product attempting to be edited could not be found!', 'error')

    elif request.method == 'POST':
        product = Product.query.filter_by(product_id=product_id).first()

        if product:
            product.product_name = request.form['product_name']
            product.category_id = request.form['product_category_id']
            product.product_code = request.form['product_code']
            product.product_description = request.form['product_description']
            product.product_price = request.form['product_price']
            product_image = request.files['product_image']

            # When a new image is provided, or there is a desire to delete the current image, attempt to delete it
            if ('delete_product_image' in request.form or product_image != '') and 'current_product_image' != '' :
                try:
                    os.remove(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product.product_image))
                    product.product_image = ''
                except:
                    pass # Nothing to do as file is no longer being stored


                product_filename = secure_filename(product.product_code + '-' + product_image.filename)  # prepend unique product code to avoid filename collisions

                if product_image.filename != '':
                    product_image.save(os.path.join(basedir, app.config['PRODUCT_UPLOAD_PATH'], product_filename))
                    product.product_image = product_filename if product_image else ''

            db.session.commit()
            flash(f'{product.product_name} was successfully updated!', 'success')
        else:
            flash(f'Product attempting to be edited could not be found!', 'error')

        return redirect(url_for('product_view_all'))

    # Address issue where unsupported HTTP request method is attempted
    flash(f'Invalid request. Please contact support if this problem persists.', 'error')
    return redirect(url_for('product_view_all'))


@app.route('/product/delete/<int:product_id>')
@login_required
@role_required(['ADMIN'])
def product_delete(product_id):
    product = Product.query.filter_by(product_id=product_id).first()
    if product:
        try:
            os.remove(os.path.join(app.config['PRODUCT_UPLOAD_PATH'], product.product_image))
        except:
            pass  # Nothing to do as file is no longer being stored
        db.session.delete(product)
        db.session.commit()
        flash(f'{product} was successfully deleted!', 'success')
    else:
        flash(f'Delete failed! Product could not be found.', 'error')

    return redirect(url_for('product_view_all'))


@app.route('/analytics-dashboard')
@login_required
@role_required(['ADMIN'])
def analytics_dashboard():

    # Product Count by Category Graph
    qry_product_counts = db.session.query(
        ProductCategory.category_name.label('category_names'),
        func.count(Product.category_id).label('category_counts')
    ) \
    .join(ProductCategory, Product.category_id == ProductCategory.category_id) \
    .group_by(Product.category_id) \
    .order_by(ProductCategory.category_name) \
    .all()

    df_product_counts = pd.DataFrame(qry_product_counts, columns=['category_names', 'category_counts'])

    product_counts_figure = px.bar(data_frame=df_product_counts, x='category_names', y='category_counts',
                                   title='Number of Products Offered by Category',
                                   labels={'category_names':'', 'category_counts':'Count'},
                                   color_discrete_sequence=['#990000'],
                                   text_auto = True
                            )

    product_counts_figure.update_layout(
        yaxis = {'tickmode':'linear', 'dtick':1},
        title = {'x':0.5}
    )

    product_counts_figure_JSON = product_counts_figure.to_json()


    # Number of Orders in the Past 30 Days
    qry_orders_past_30 = db.session.query(
        func.count(StoreOrder.order_id).label("order_count")
    ) \
    .filter(StoreOrder.order_date >= dt.datetime.now() - dt.timedelta(days=30)) \
    .all()

    df_orders_past_30 = pd.DataFrame(qry_orders_past_30, columns=['order_count'])

    orders_past_30_figure = px.pie(df_orders_past_30, names='order_count', values='order_count', title='Number of Orders in Past 30 Days',
            color_discrete_sequence=['#990000'])
    orders_past_30_figure.update_traces(textposition='inside', textinfo='label', hovertemplate=None, hoverinfo='none', textfont_size=24, showlegend=False)
    orders_past_30_figure.update_layout(
        title={'x': 0.5}
    )
    orders_past_30_figureJSON = orders_past_30_figure.to_json()


    # Order Distribution by State
    qry_orders_by_state = db.session.query(
        StoreOrder.state.label('states'),
        func.count(StoreOrder.order_id).label('order_counts')
    ) \
    .group_by(StoreOrder.state) \
    .order_by(StoreOrder.state) \
    .all()

    df_orders_by_state = pd.DataFrame(qry_orders_by_state, columns=['states', 'order_counts'])
    df_orders_by_state = df_orders_by_state.sort_values(by='states',
  ascending=True)

    labels = df_orders_by_state['states'].unique()
    print(labels)

    orders_by_state_figure = px.pie(df_orders_by_state, names='states', labels=labels, values='order_counts', title='All Orders Segmented by State',
            color_discrete_sequence=px.colors.qualitative.Antique)

    orders_by_state_figure.update_traces(textposition='inside', textinfo='label+percent', textfont_size=16)
    orders_by_state_figure.update_layout(
        title={'x': 0.5}
    )

    fig = go.Figure(
        data=[go.Pie(
            labels=labels,
            values=df_orders_by_state['order_counts'],
            # Second, make sure that Plotly won't reorder your data while plotting
            sort=False)
        ])
    fig.update_traces(textposition='inside', textinfo='label+percent', textfont_size=16)
    fig.update_layout(
        title={'x': 0.5})
    orders_by_state_figureJSON = fig.to_json()


    # Orders by Month (Example of a Custom SQL Query for SQLite)
    qry_orders_by_month = db.session.query(
        func.strftime('%Y-%m', StoreOrder.order_date).label('order_month'),
        func.count(StoreOrder.order_id).label("order_counts")
    ) \
    .group_by('order_month') \
    .order_by('order_month') \
    .all()

    df_orders_by_month = pd.DataFrame(qry_orders_by_month, columns=['order_month', 'order_counts'])

    orders_by_month_figure = px.line(df_orders_by_month, x='order_month', y='order_counts', title='All Orders Segmented by Month', markers=True,
            color_discrete_sequence=px.colors.qualitative.Antique,
            labels={'order_month': '', 'order_counts': 'Count'})
    orders_by_month_figure.update_layout(
        title={'x': 0.5}
    )
    orders_by_month_figureJSON = orders_by_month_figure.to_json()

    return render_template('analytics_dashboard.html',
            product_counts_graph=product_counts_figure_JSON,
            orders_past_30_graph=orders_past_30_figureJSON,
            orders_by_state_graph=orders_by_state_figureJSON,
            orders_by_date_graph=orders_by_month_figureJSON)


if __name__ == '__main__':
    app.run(debug=True)
