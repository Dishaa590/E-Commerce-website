from flask import Flask,render_template,url_for,request,redirect

from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime



app = Flask(__name__)

client = MongoClient('localhost',27017)


#Just to add product details 
@app.route("/", methods=['GET','POST'])
def product():
    if request.method=='POST':
        product_name = request.form['product-name']
        product_price = request.form['product-price']
        product_quantity = request.form['product-quantity']

        todos.insert_one({
            'product_name': product_name,
            'product_price': product_price,
            'product_quantity': product_quantity
        })
        return redirect(url_for('product'))
    all_todos=todos.find()
    return render_template('product.html',todos=all_todos)


#To view the Data using pagination
@app.route("/List", methods=['GET'])
def product_list():
    try:
        # Set default values for limit and offset
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))

      
        # Fetch products with pagination
        products = list(todos.find().skip(offset).limit(limit))

        return render_template('plist.html', products=products,offset=offset)
    except Exception as e:
        return render_template('error.html', error=str(e))


#filter by minprice and max price
@app.route("/filter", methods=['POST'])
def product_filter():
    min_price=request.form['min_price']
    max_price=request.form['max_price']
    offset =0
    filter={"product_price": {"$gte": float(min_price),"$lte":float(max_price)}}
    products=todos.find(filter)
    return render_template('plist.html',products=products,offset=offset)
    

#To send product with no of quantities to database
@app.post("/<product_id>/addtocart/")
def addtocart(product_id):
    try:
        # Try to fetch product details using ObjectId
        product_details = todos.find_one({"_id": ObjectId(product_id)})
        bq=request.form['quantity']
        # If product_details is not found using ObjectId, try using string representation
        if not product_details:
            product_details = todos.find_one({"_id": product_id})

       
        if product_details:
            # Add product details to the order collection
            cart.insert_one({
                '_id':product_id,
                'product_name': product_details['product_name'],
                'product_price': product_details['product_price'],
                'brought_quantity':bq                   
            })
            return redirect(url_for('product_list'))
        else:
            return f"Product with ID {product_id} not found"
    except Exception as e:
        return str(e)



@app.route("/cart", methods=['GET'])
def product_cart():
    try:
        products = list(cart.find())
        total_price = sum(float(item['product_price']) * int(item['brought_quantity']) for item in cart.find())
        return render_template('productcart.html', products=products,tp=total_price)
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route("/order", methods=['POST'])
def order():
    try:
        # Get address details from the form
        city = request.form['city']
        country = request.form['country']
        zip_code = request.form['zip_code']

        # Get product details from the form
        products = []
        total_price = 0

        for product in cart.find():
            product_id = str(product['_id'])
            brought_quantity = int(product['brought_quantity'])

            if brought_quantity > 0:
                # Calculate the total price for each product
                product_price = float(product['product_price'])
                total_price += product_price * brought_quantity

                # Add product details to the order collection
                products.append({
                    'product_id': product_id,
                    'product_name': product['product_name'],
                    'product_price': product_price,
                    'brought_quantity': brought_quantity
                })

        # Add order details to the order collection
        order_details = {
            'createdOn': datetime.now(),
            'address': {
                'city': city,
                'country': country,
                'zip_code': zip_code
            },
            'products': products,
            'total_price': total_price
        }

        orders.insert_one(order_details)

        
        # Clear the cart
        cart.delete_many({})


        return render_template('ordered.html', order_details=order_details)

    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/<product_id>/delete')
def delete(product_id):
    pro = cart.find_one({'_id':product_id})
    cart.delete_one(pro)
    return redirect('/cart')


@app.route("/orderlist", methods=['GET'])
def orderlist():
    try:
        # Fetch products with pagination
        products = orders.find()

        return render_template('porders.html', order=products)
    except Exception as e:
        return render_template('error.html', error=str(e))


db = client.product_database

cart=db.cart
todos = db.todos
orders=db.orders

if __name__ == "__main__":
    app.run(debug=True)
