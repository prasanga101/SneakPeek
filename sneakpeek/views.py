from django.shortcuts import render, get_object_or_404

from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect
from .models import SignUpBuyer, SignUpSeller,Sneaker, Bid
from django.contrib import messages

import base64
import uuid
from django.core.files.base import ContentFile


def bidding_result(request, sneaker_id):
    sneaker = get_object_or_404(Sneaker, id=sneaker_id)
    highest_bid = sneaker.bids.order_by('-amount').first()
    return render(request, 'bidding_result.html', {
        'sneaker': sneaker,
        'highest_bid': highest_bid
    })

def place_bid_view(request, sneaker_id):
    if not request.session.get('is_logged_in'):
        messages.warning(request, "You must log in to place a bid.")
        return redirect('/Login')

    sneaker = get_object_or_404(Sneaker, id=sneaker_id)
    bids = sneaker.bids.order_by('-amount')

    # Pass the logged-in user's email to template
    current_user_email = request.session.get('signup_email', '')

    context = {
        'sneaker': sneaker,
        'bids': bids,
        'is_logged_in': True,
        'current_user_email': current_user_email  # <-- Pass to template
    }
    return render(request, 'place_bid.html', context)


def submit_bid(request, sneaker_id):
    if request.method != "POST":
        return redirect('place_bid', sneaker_id=sneaker_id)

    # Check if user is logged in
    is_logged_in = request.session.get('is_logged_in', False)
    user_role = request.session.get('role', None)
    buyer_email = request.session.get('signup_email', None)

    if not is_logged_in or user_role != 'buyer':
        mess='You must be logged in as a buyer to place a bid.'
        request.session['mess_seller']=mess
        return redirect('/Login')

    sneaker = get_object_or_404(Sneaker, id=sneaker_id)

    # Safely get the buyer
    try:
        buyer = get_object_or_404(SignUpBuyer, Email=buyer_email)
    except Exception:
        messages.error(request, "Buyer account not found. Please log in again.")
        request.session.flush()
        return redirect('/Login')

    # Get bid amount and validate
    amount_str = request.POST.get("amount")
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except (ValueError, TypeError):
        messages.error(request, "Please enter a valid positive bid amount.")
        return redirect('place_bid', sneaker_id=sneaker_id)

    # Create bid
    Bid.objects.create(sneaker=sneaker, buyer=buyer, amount=amount)
    messages.success(request, f"Your bid of Rs {amount} has been placed successfully!")

    return redirect('place_bid', sneaker_id=sneaker_id)



# Create your views here.
def home(request):
    sneak = Sneaker.objects.filter(is_featured=True).order_by('-id')
    context = {
        'sneakers': sneak,
        'is_logged_in': request.session.get('is_logged_in', False)  # pass login status
    }
    return render(request, 'home.html', context)


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