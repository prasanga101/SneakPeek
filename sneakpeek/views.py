from django.shortcuts import render, get_object_or_404

from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect ,HttpResponse
from .models import SignUpBuyer, SignUpSeller,Sneaker, Bid,Payment,ProductRequest
from django.contrib import messages
from django.conf import settings
import base64
import uuid
from django.core.files.base import ContentFile
from django.core.files.base import ContentFile
import os
from django.core.files import File
from itertools import chain
import stripe
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta


@csrf_exempt
def store_payment_id(request, payment_id):
    """Store payment ID in session for later retrieval"""
    if request.method == "POST":
        request.session['current_payment_id'] = payment_id
        request.session.save()  # Explicitly save session
        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def create_checkout_session(request, bid_id):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        bid = get_object_or_404(Bid, id=bid_id)
        
        # Determine which item this bid belongs to
        if bid.sneaker:
            item_id = bid.sneaker.id
            item_name = bid.sneaker.name
            item_image = bid.sneaker.image
        else:
            item_id = bid.product_request.id
            item_name = bid.product_request.name
            item_image = bid.product_request.image
        
        # Store both bid_id and item_id in session for payment success lookup
        request.session['current_bid_id'] = bid_id
        request.session['current_item_id'] = item_id
        request.session.save()
        
        # Build product images list - only include valid URLs
        images = []
        if item_image:
            try:
                images = [request.build_absolute_uri(item_image.url)]
            except:
                images = []
        
        # Create the Stripe session
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Bid Payment for {item_name}",
                            "images": images,
                        },
                        "unit_amount": int(bid.amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            success_url=request.build_absolute_uri("/payment/success/"),
            cancel_url=request.build_absolute_uri("/payment/failure/"),
        )
        
        return JsonResponse({"id": session.id})
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

def seller_products(request):
    if not request.session.get('is_logged_in') or request.session.get('role') != 'seller':
        return redirect('/Login')

    seller = SignUpSeller.objects.get(id=request.session.get('seller_id'))

    products = ProductRequest.objects.filter(seller=seller).order_by('-created_at')

    return render(request, 'seller_products.html', {
        'products': products,
        'is_logged_in': True,
        'role': 'seller'
   })


def payment_success(request):
    buyer_email = request.session.get('signup_email')
    payment_id = request.session.get('current_payment_id')
    bid_id = request.session.get('current_bid_id')
    item_id = request.session.get('current_item_id')
    
    if not buyer_email:
        return HttpResponse("User not logged in", status=401)
    
    try:
        payment = None
        
        # Method 1: Look up by bid_id and item_id (most reliable - exact match)
        if bid_id and item_id:
            payment = Payment.objects.filter(
                product_id=f"SNK-{item_id}-BID-{bid_id}",
                status="PENDING"
            ).first()
        
        # Method 2: Look up by payment_id stored in session
        if not payment and payment_id:
            payment = Payment.objects.filter(
                id=payment_id,
                status="PENDING"
            ).first()
        
        # Method 3: Fallback - get most recent pending payment for buyer
        if not payment:
            payment = Payment.objects.filter(
                email=buyer_email,
                status="PENDING"
            ).order_by('-id').first()
        
        if not payment:
            return render(request, "payment_failure.html", {
                "error": "Payment record not found. Please contact support."
            })
        
        # Mark as successful
        payment.status = "SUCCESS"
        payment.save()
        
        # Clear session data
        for key in ['current_payment_id', 'current_bid_id', 'current_item_id']:
            if key in request.session:
                del request.session[key]
        request.session.save()
                
    except Exception as e:
        return render(request, "payment_failure.html", {
            "error": f"Error processing payment: {str(e)}"
        })

    return render(request, "payment_success.html")

def payment_failure(request):
    return render(request, "payment_failure.html")


def add_product_request(request):
    if request.session.get('role') != 'seller':
        return redirect('/Login')

    seller = get_object_or_404(SignUpSeller, id=request.session.get('seller_id'))

    if request.method == "POST":
        ProductRequest.objects.create(
            seller=seller,
            name=request.POST['name'],
            description=request.POST['description'],
            image=request.FILES['image'],
            end_time=request.POST['end_time'],
        )
        messages.success(request, "Product sent for admin approval.")
        return redirect('/')

    # ✅ Handle GET requests properly
    return render(request, 'add_product.html')


def approve_products(self, request, queryset):
    for req in queryset.filter(status='pending'):
        if req.image:
            req.image.open()
            img_file = File(req.image)  # copy the uploaded file
        else:
            img_file = None

        Sneaker.objects.create(
            name=req.name,
            description=req.description,
            image=img_file,
            end_time=req.end_time,
            is_featured=True
        )

        req.status = 'approved'
        req.save()


stripe.api_key = settings.STRIPE_SECRET_KEY

def get_valid_highest_bid(item, sneaker_id):
    """
    Get the highest bid that hasn't timed out waiting for payment.
    Item can be either Sneaker or ProductRequest.
    sneaker_id: The ID of the item (Sneaker or ProductRequest) for exact payment lookup.
    """
    # Get bids for this item
    if isinstance(item, Sneaker):
        all_bids = item.bids.order_by('-amount')
    else:
        # It's a ProductRequest
        all_bids = Bid.objects.filter(product_request=item).order_by('-amount')
    
    timeout_minutes = 1
    
    for bid in all_bids:
        # Check if there's a payment record for this bid using exact product_id match
        payment = Payment.objects.filter(
            product_id=f"SNK-{sneaker_id}-BID-{bid.id}"
        ).first()
        
        if not payment:
            # No payment record yet - this bid is valid
            return bid, None
        
        # Check if payment is still PENDING and not timed out
        if payment.status == "PENDING":
            time_since_creation = timezone.now() - payment.created_at
            if time_since_creation < timedelta(minutes=timeout_minutes):
                # Payment is pending and within timeout - this is the current winner
                return bid, payment
            else:
                # Payment timed out - mark as FAILED and continue to next bidder
                payment.status = "FAILED"
                payment.save()
                continue
        
        elif payment.status == "SUCCESS":
            # Payment completed - this is the winner
            return bid, payment
        
        else:
            # Payment failed - try next bidder
            continue
    
    # No valid bids found
    return None, None


def bidding_result(request, sneaker_id):
    # 1️⃣ Get the sneaker or product request
    sneaker = Sneaker.objects.filter(id=sneaker_id).first()
    product_request = None
    item = None
    
    if not sneaker:
        # Check if it's a ProductRequest
        product_request = ProductRequest.objects.filter(id=sneaker_id, status='approved').first()
        if not product_request:
            return HttpResponse("Item not found.", status=404)
        item = product_request
        # Create a temporary object to display product request like sneaker
        class TempSneaker:
            id = product_request.id
            name = product_request.name
            description = product_request.description
            image = product_request.image
            end_time = product_request.end_time
        sneaker = TempSneaker()
    else:
        item = sneaker

    # 2️⃣ Get the highest valid bid (considering timeouts)
    highest_bid, payment = get_valid_highest_bid(item, sneaker_id)

    # 3️⃣ Check if user is logged in and is the winner
    buyer_email = request.session.get('signup_email')
    
    if not highest_bid:
        # No bids placed yet
        return render(request, "bidding_result.html", {
            "sneaker": sneaker,
            "highest_bid": None,
            "show_payment": False,
            "payment_id": None,
            "stripe_key": settings.STRIPE_PUBLIC_KEY,
        })
    
    # Only the winner can view this page
    if not buyer_email or buyer_email != highest_bid.buyer.Email:
        return HttpResponse("Access denied. Only the bidding winner can view this page.", status=403)
    
    # 4️⃣ User is the winner - prepare payment info
    show_payment = False
    payment_id = None
    
    if not payment:
        # Create a consistent, deterministic transaction ID (not random)
        # This ensures the same bid always has the same payment record
        transaction_uuid = f"SNK-{sneaker_id}-BID-{highest_bid.id}"
        
        # Check if a payment with this exact ID already exists
        payment = Payment.objects.filter(product_id=transaction_uuid).first()
        if not payment:
            payment = Payment.objects.create(
                email=highest_bid.buyer.Email,
                amount=float(highest_bid.amount),
                product_id=transaction_uuid,
                status="PENDING"
            )
    
    # Only show payment button if status is PENDING (not SUCCESS or FAILED)
    show_payment = (payment.status == "PENDING")
    payment_id = payment.id

    # 5️⃣ Render template with Stripe
    return render(request, "bidding_result.html", {
        "sneaker": sneaker,
        "highest_bid": highest_bid,
        "show_payment": show_payment,
        "payment_id": payment_id,
        "stripe_key": settings.STRIPE_PUBLIC_KEY,
    })



# def place_bid_view(request, sneaker_id):
#     if not request.session.get('is_logged_in'):
#         messages.warning(request, "You must log in to place a bid.")
#         return redirect('/Login')

#     sneaker = get_object_or_404(Sneaker, id=sneaker_id)
#     bids = sneaker.bids.order_by('-amount')

#     # Pass the logged-in user's email to template
#     current_user_email = request.session.get('signup_email', '')

#     context = {
#         'sneaker': sneaker,
#         'bids': bids,
#         'is_logged_in': True,
#         'current_user_email': current_user_email  # <-- Pass to template
#     }
#     return render(request, 'place_bid.html', context)
def place_bid_view(request, sneaker_id):
    if not request.session.get('is_logged_in'):
        messages.warning(request, "You must log in to place a bid.")
        return redirect('/Login')

    # Try to get the sneaker first
    sneaker = Sneaker.objects.filter(id=sneaker_id).first()
    product_request = None

    # If not found in Sneaker, check ProductRequest (approved only)
    if not sneaker:
        product_request = ProductRequest.objects.filter(id=sneaker_id, status='approved').first()
        if not product_request:
            return HttpResponse("Item not found.", status=404)

        # Dynamically treat ProductRequest as Sneaker for display
        class TempSneaker:
            id = product_request.id
            name = product_request.name
            description = product_request.description
            image = product_request.image
            end_time = product_request.end_time

            @property
            def bids(self):
                # Get bids related to this product_request
                return Bid.objects.filter(product_request_id=self.id).order_by('-amount')

        sneaker = TempSneaker()
    else:
        # Get bids for this sneaker
        bids = sneaker.bids.order_by('-amount')

    # Get bids (from either sneaker or product_request)
    if product_request:
        bids = Bid.objects.filter(product_request_id=product_request.id).order_by('-amount')
    else:
        bids = Bid.objects.filter(sneaker_id=sneaker.id).order_by('-amount')

    current_user_email = request.session.get('signup_email', '')

    context = {
        'sneaker': sneaker,
        'bids': bids,
        'is_logged_in': True,
        'current_user_email': current_user_email
    }
    return render(request, 'place_bid.html', context)


# def submit_bid(request, sneaker_id):
#     if request.method != "POST":
#         return redirect('place_bid', sneaker_id=sneaker_id)

#     # Check if user is logged in
#     is_logged_in = request.session.get('is_logged_in', False)
#     user_role = request.session.get('role', None)
#     buyer_email = request.session.get('signup_email', None)

#     if not is_logged_in or user_role != 'buyer':
#         mess='You must be logged in as a buyer to place a bid.'
#         request.session['mess_seller']=mess
#         return redirect('/Login')

#     sneaker = get_object_or_404(Sneaker, id=sneaker_id)
#     print(sneaker)

#     # Safely get the buyer
#     try:
#         buyer = get_object_or_404(SignUpBuyer, Email=buyer_email)
#     except Exception:
#         # messages.error(request, "Buyer account not found. Please log in again.")
#         # mes='Buyer account not found. Please log in again.'
#         request.session['mes']='Buyer account not found. Please log in again.'
#         # request.session.flush()
#         return redirect('/Login')

#     # Get bid amount and validate
#     amount_str = request.POST.get("amount")
#     try:
#         amount = float(amount_str)
#         if amount <= 0:
#             raise ValueError
#     except (ValueError, TypeError):
#         messages.error(request, "Please enter a valid positive bid amount.")
#         return redirect('place_bid', sneaker_id=sneaker_id)

#     # Create bid
#     Bid.objects.create(sneaker=sneaker, buyer=buyer, amount=amount)
#     messages.success(request, f"Your bid of Rs {amount} has been placed successfully!")

#     return redirect('place_bid', sneaker_id=sneaker_id)


def submit_bid(request, sneaker_id):
    if request.method != "POST":
        return redirect('place_bid', sneaker_id=sneaker_id)

    is_logged_in = request.session.get('is_logged_in', False)
    user_role = request.session.get('role', None)
    buyer_email = request.session.get('signup_email', None)

    if not is_logged_in or user_role != 'buyer':
        request.session['mess_seller'] = 'You must be logged in as a buyer to place a bid.'
        return redirect('/Login')

    # Try to get Sneaker first
    sneaker = Sneaker.objects.filter(id=sneaker_id).first()
    product_request = None
    
    if not sneaker:
        # Check if it's an approved ProductRequest
        product_request = ProductRequest.objects.filter(id=sneaker_id, status='approved').first()
        if not product_request:
            return HttpResponse("Item not found.", status=404)

    # Get buyer
    try:
        buyer = SignUpBuyer.objects.get(Email=buyer_email)
    except SignUpBuyer.DoesNotExist:
        request.session['mes'] = 'Buyer account not found. Please log in again.'
        return redirect('/Login')

    # Get bid amount
    amount_str = request.POST.get("amount")
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Please enter a valid positive bid amount.")
        return redirect('place_bid', sneaker_id=sneaker_id)

    # Create bid - set either sneaker or product_request
    if sneaker:
        Bid.objects.create(sneaker=sneaker, buyer=buyer, amount=amount)
    else:
        Bid.objects.create(product_request=product_request, buyer=buyer, amount=amount)

    messages.success(request, f"Your bid of Rs {amount} has been placed successfully!")

    return redirect('place_bid', sneaker_id=sneaker_id)



# Create your views here.
# def home(request):
#     sneak = Sneaker.objects.filter(is_featured=True).order_by('-id')
#     sneakk=ProductRequest.objects.filter(status="approved").order_by('-id')
#     context = {
#         'sneakers': sneak,
#         'sneaker_requests': sneakk,
#         'is_logged_in': request.session.get('is_logged_in', False),
#         'role': request.session.get('role')
#     }
#     return render(request, 'home.html', context)


# def home(request):
#     sneakers = Sneaker.objects.filter(is_featured=True)
#     approved_requests = ProductRequest.objects.filter(status='approved')

#     all_items = list(chain(sneakers, approved_requests))

#     return render(request, 'home.html', {
#         'items': all_items,
#         'is_logged_in': request.session.get('is_logged_in', False)
#     })

def home(request):
    sneakers = Sneaker.objects.filter(is_featured=True).order_by('-id')
    approved_requests = ProductRequest.objects.filter(status='approved').order_by('-id')
    for sneaker in sneakers:
        sneaker.item_type = 'sneaker'  # to identify in template
    # Treat approved requests as sneakers for display
    for r in approved_requests:
        r.item_type = 'sneaker'  # now they also get the Place Bid button

    all_items = list(chain(sneakers, approved_requests))

    return render(request, 'home.html', {
        'items': all_items,
        'is_logged_in': request.session.get('is_logged_in', False),
        'role': request.session.get('role')
    })
# def home(request):
#     sneakers = Sneaker.objects.filter(is_featured=True).order_by('-id')
#     return render(request, 'home.html', {
#         'sneakers': sneakers,
#         'is_logged_in': request.session.get('is_logged_in', False)
#     })



# def place_bid(request, sneaker_id):
#     sneaker = get_object_or_404(Sneaker, id=sneaker_id)
#     return render(request, 'bid_page.html', {'sneaker': sneaker})

def logoutt(request):
    request.session.flush()  # Clear all session data
    return redirect('/Login')  # Redirect to login page


# def loginn(request):
#      if request.method=="POST":
#         eemail=request.POST.get("email")
#         ppassword=request.POST.get("password")
#         # password=make_password(request.POST.get("Password")) if u do this again diiferent hash will be generated because everytime u do this unique or differernt salt is generated and hence hasing is different each time
#         try:
#             user=SignUpBuyer.objects.get(Email=eemail)
         
#             # if check_password(password,user.Password): or we can also do this of down
#             if check_password(ppassword,user.Password):
        
#                 # make_password() → adds random salt and hashes once when saving.

#                 # check_password() → extracts the salt from stored hash and verifies properly.
#                 # return render(request,'dashboard.html',{'name':namee})
#                  request.session['signup_name']=user.FName
#                  request.session['is_logged_in']=True
#                  return redirect('/')
#             else:##if password is incorrect 
#                 return render(request,'login.html',{'error':'True','message':'Invalid Password'})
            
#         except SignUpBuyer.DoesNotExist:
#             return render(request,'login.html',{'error':'True','message':'Email doesnot exists'})
        
#         # Try Seller next
#         try:
#             seller = SignUpSeller.objects.get(Email=email)
#             if not seller.is_verified:
#                 return render(request, "login.html", {'error': True, 'message': 'Your account is not verified yet.'})
#             if check_password(password, seller.Password):
#                 request.session['seller_id'] = seller.id
#                 return redirect('/')  # seller dashboard
#             else:
#                 return render(request, "login.html", {'error': True, 'message': 'Invalid password.'})
#         except SignUpSeller.DoesNotExist:
#             return render(request, "login.html", {'error': True, 'message': 'Email not registered.'})
        
#      return render(request,'login.html',{'Email':request.session.get('signup_email',''),'Password':request.session.get('signup_password',''),'messagee':request.session.get('signup_message',''),'error':False})
#     # return render(request, 'login.html', {'title': 'SneakPeek Login'})
def loginn(request):
    if request.method=="POST":
        eemail = request.POST.get("email")
        ppassword = request.POST.get("password")

        # Try Buyer first
        try:
            user = SignUpBuyer.objects.get(Email=eemail)
            if check_password(ppassword, user.Password):
                request.session['signup_name'] = user.FName
                request.session['is_logged_in'] = True
                request.session['signup_email'] = user.Email
                request.session['role'] = 'buyer'
                return redirect('/')  # buyer dashboard
            else:
                return render(request,'login.html',{'error':True,'message':'Invalid Password'})
        except SignUpBuyer.DoesNotExist:
            pass  # continue to check seller

        # Try Seller
        try:
            seller = SignUpSeller.objects.get(Email=eemail)
            if not seller.is_verified:
                return render(request, "login.html", {'error': True, 'message': 'Your account is not verified yet.'})
            if check_password(ppassword, seller.Password):
                request.session['seller_id'] = seller.id
                request.session['is_logged_in'] = True
                request.session['role'] = 'seller'
                return redirect('/')  # seller dashboard
            else:
                return render(request, "login.html", {'error': True, 'message': 'Invalid password.'})
        except SignUpSeller.DoesNotExist:
            return render(request,"login.html", {'error': True, 'message': 'Email not registered.'})

    return render(request,'login.html',{
        'Email': request.session.get('signup_email',''),
        'Password': request.session.get('signup_password',''),
        'messagee': request.session.get('signup_message',''),
        'SellerErrorMessage': request.session.get('mess_seller',''),
        'error': False
    })


def signuppB(request):
     if request.method=="POST":
        fname=request.POST.get("first_name")
        lname=request.POST.get("last_name")
        email=request.POST.get("email")
        password=request.POST.get("password")
        cpassword=request.POST.get("confirm_password")
        
        if password != cpassword:
            return render(request,'signup_buyer.html',{'error':'True','message':'Password and Confirm Password do not match'})
        
        SignUpBuyer.objects.create(FName=fname,LName=lname,Email=email,Password=make_password(password))
        # return render(request,'login.html',{'Email':email,'Password':password,'mess':'Account created successfully, please login','error':'False'})
        request.session['signup_email']=email
        request.session['signup_password']=password
        request.session['role'] = 'buyer'
        request.session['signup_message']='Account created successfully, please login'
        return redirect('/Login')
        
    # return render(request,'signup.html')
     return render(request, 'signup_buyer.html')

def signup(request):
    return render(request, 'signup.html')

def signuppS(request):
    if request.method == "POST":
        name = request.POST.get("seller_name")
        email = request.POST.get("seller_email")
        password = request.POST.get("seller_password")
        phone = request.POST.get("seller_phone")
        address = request.POST.get("seller_address")
        business = request.POST.get("seller_business", "")
        live_photo = request.POST.get("seller_live_photo")  # Base64 from camera
        id_image = request.FILES.get("seller_id_image")     # Uploaded document

        # Basic validation
        if not all([name, email, password, phone, address, id_image, live_photo]):
            return render(request, 'signup_seller.html', {
                'error': True,
                'message': 'Please fill all required fields and upload documents/photos.'
            })

        # Convert base64 live photo to actual image file
        format, imgstr = live_photo.split(';base64,')
        ext = format.split('/')[-1]
        live_photo_file = ContentFile(base64.b64decode(imgstr), name=f"{uuid.uuid4()}.{ext}")

        # Create seller account
        SignUpSeller.objects.create(
            Name=name,
            Email=email,
            Password=make_password(password),
            Phone=phone,
            Address=address,
            BusinessName=business,
            IDImage=id_image,
            LivePhoto=live_photo_file  # ✅ use the actual file here
        )

        # Save session info (optional)
        request.session['signup_email'] = email
        request.session['signup_password'] = password
        request.session['role'] = 'seller'

       # After creating seller account
        request.session['signup_message'] = 'Your account is submitted for verification. You will be notified once approved.'
        # return render(request, 'signup_successful', {'success': True})
        return redirect('/signup_successful')

    return render(request, 'signup_seller.html')

def SignSuccess(request):
    message = request.session.get('signup_message', '')

    # Optional: remove message after showing once
    request.session.pop('signup_message', None)

    return render(request, 'signup_successful.html', {
        'message': message
    })

def bids(request):
    # Check if user is logged in
    is_logged_in = request.session.get('is_logged_in', False)
    role = request.session.get('role', None)

    if not is_logged_in or role != 'buyer':
        messages.warning(request, "You must log in as a buyer to view your bids.")
        return redirect('/Login')

    buyer_email = request.session.get('signup_email', None)
    if not buyer_email:
        messages.error(request, "Session expired. Please log in again.")
        request.session.flush()
        return redirect('/Login')

    # Get buyer safely
    buyer = SignUpBuyer.objects.filter(Email=buyer_email).first()
    if not buyer:
        messages.error(request, "Buyer account not found. Please log in again.")
        request.session.flush()
        return redirect('/Login')

    # Get all bids of this buyer
    user_bids = Bid.objects.filter(buyer=buyer).order_by('-id')

    context = {
        'is_logged_in': True,
        'bids': user_bids,
    }
    return render(request, 'bids.html', context)



def sell(request):
    return render(request, 'sell.html', {'title': 'SneakPeek Sell'})

def marketplace(request):
     context = {
        'is_logged_in': request.session.get('is_logged_in')
    }
   

     return render(request, 'marketplace.html', context)