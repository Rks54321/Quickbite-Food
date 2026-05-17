from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from .models import Customer, Restaurant, Item, Cart

import razorpay
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def say_hello(request):
    # return HttpResponse("Say Hello my app is working")
    return render(request, "index.html")

def open_signup(request):
    return render(request, "signup.html")

def open_signin(request):
    return render(request, "signin.html")

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get('password')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        address = request.POST.get('address')
    try:
        Customer.objects.get(username = username)
        return HttpResponse("Duplicate username!")
    except:
        Customer.objects.create(
            username = username,
            password = password,
            email = email,
            mobile = mobile,
            address = address,
        )
    return render(request, 'signin.html')

def signin(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
    
        try:
            Customer.objects.get(username = username, password = password)
            if username == 'admin':
                return render(request, 'admin_home.html')
            else: 
                restaurantList = Restaurant.objects.all()
                return render(request, 'customer_home.html', {"restaurantList" : restaurantList, "username":username})
        except Customer.DoesNotExist:
            return render(request, 'fail.html')
    
def open_add_restaurant(request):
    return render(request, 'add_restaurant.html')

def add_restaurant(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

    try:
        Restaurant.objects.get(name = name)
        return HttpResponse("Duplicate restaurant!")
    except:
        Restaurant.objects.create(
            name = name,
            picture = picture,
            cuisine = cuisine,              
            rating = rating,
        )
    return render(request, 'admin_home.html')
def open_show_restaurant(request):
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurant.html', {"restaurantList" : restaurantList})
        
def open_update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    return render(request, 'update_restaurant.html', {'restaurant' : restaurant})

def update_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        picture = request.POST.get('picture')
        cuisine = request.POST.get('cuisine')
        rating = request.POST.get('rating')

        restaurant.name = name
        restaurant.picture = picture
        restaurant.cuisine = cuisine
        restaurant.rating = rating

        restaurant.save()
    
    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurant.html',{'restaurantList' : restaurantList})

def delete_restaurant(request, restaurant_id):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    restaurant.delete()

    restaurantList = Restaurant.objects.all()
    return render(request, 'show_restaurant.html', {'restaurantList' : restaurantList})

def restaurant_menu(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        is_veg = request.POST.get('is_veg') == 'on'
        picture = request.POST.get('picture')

        Item.objects.create(
            restaurant = restaurant,
            name = name,
            description = description,
            price = price,
            is_veg = is_veg,
            picture = picture
        )
        return redirect('restaurant_menu', restaurant_id=restaurant.id)
    menu_items = restaurant.menu_items.all()
    return render(request, 'menu.html', {
        'restaurant': restaurant,
        'menu_items': menu_items,
    })

def update_menu(request, item_id):

    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':

        item.name = request.POST.get('name')
        item.description = request.POST.get('description')
        item.price = request.POST.get('price')
        item.picture = request.POST.get('picture')

        item.is_veg = 'is_veg' in request.POST

        item.save()

        return HttpResponse("Menu Updated Successfully")

    return render(request, 'update_menu.html', {'item': item})

def open_update_menu(request, item_id):
     menuItem = get_object_or_404(Item, id=item_id)
     return render(request, 'update_menu.html', {'menuItem':menuItem})

# CHANGED
def delete_menuItem(request, item_id):

    item = get_object_or_404(Item, id=item_id)

    restaurant_id = item.restaurant.id

    item.delete()

    return redirect(
        'restaurant_menu',
        restaurant_id=restaurant_id
    )


# For Customer
def view_menu(request, restaurant_id, username):
    restaurant = Restaurant.objects.get(id = restaurant_id)
    itemList = restaurant.menu_items.all()
    return render(request, 'customer_menu.html',
                  {"itemList" : itemList,
                   "restaurant" : restaurant,
                   "username" : username})

def add_to_cart(request, item_id, username):
    item = Item.objects.get(id = item_id)
    customer = Customer.objects.get(username = username)
    cart, created = Cart.objects.get_or_create(customer = customer)
    cart.items.add(item)
    return HttpResponse('added to cart')

def show_cart(request, username):
    customer = Customer.objects.get(username = username)
    cart = Cart.objects.filter(customer=customer).first()
    items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    return render(request, 'cart.html', {"items" : items, "total_price" : total_price, "username": username} )

def checkout(request, username):
    # Fetch Customer and their cart
    customer = get_object_or_404(Customer, username=username)
    cart =  Cart.objects.filter(customer=customer).first()
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    if total_price == 0:
        return render(request, 'checkout.html', {
            'error': 'Your cart is empty!',
        })
    
    # Initialize Razorpay client
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    # Avoid failing through systaem proxy eenv vars in local dev.
    client.session.trust_env = False

    # Create Razorpay order
    amount_paisa = int(total_price) * 100
    order_data = {
    "amount": amount_paisa,
    "currency": "INR",
    "payment_capture": "1"  #Automatically capture payments
    }
    try:
        order = client.order.create(data=order_data)
    except Exception:
        return render (request, 'checkout.html', {
            'customer': customer,
            'cart_items': cart_items,
            'total_price': total_price,
            'error': 'Payment service is currently unreachable. Please check your internet/proxy settings and try again.'
        })
    
    # Pass the order details to the fronted 
    return render(request, 'checkout.html', {
        'username': username,
        'cart_items': cart_items,
        'total_price': total_price,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'order_id': order['id'],  #Razorpay ordr ID
        'amount_paisa': order_data['amount'],
    })

@csrf_exempt
@require_POST
def payment_verify(request, username):
    """
    Razorpay Checkout returns payment_id/order_id/signature to the frontend.
    We verify the signature server-side and then redirect to the orders page.
    """
    razorpay_payment_id = request.POST.get("razorpay_payment_id")
    razorpay_order_id = request.POST.get("razorpay_order_id")
    razorpay_signature = request.POST.get("razorpay_signature")

    if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
        return HttpResponse("Missing payment details", status=400)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    client.session.trust_env = False

    try:
        client.utility.verify_payment_signature({
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_order_id": razorpay_order_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception:
        # Signature mismatch or invalid data
        return HttpResponse("Payment verification failed", status=400)

    return redirect(f"/orders/{username}/?payment=success")

def orders(request, username):
    customer = get_object_or_404(Customer, username=username)
    cart = Cart.objects.filter(customer=customer).first()
    payment_success = request.GET.get("payment") == "success"

    # Fetch cart item and total price before clearing the cart
    cart_items = cart.items.all() if cart else []
    total_price = cart.total_price() if cart else 0

    # Clear the cart after fetching its details
    if cart:
        cart.items.clear()
    
    return render(request, 'order.html', {
        'username': username,
        'customer': customer,
        'cart_items': cart_items,
        'total_price': total_price,
        'payment_success': payment_success,
    })