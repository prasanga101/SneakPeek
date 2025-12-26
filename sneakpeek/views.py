from django.shortcuts import render

from django.contrib.auth.hashers import make_password,check_password
from django.shortcuts import render, redirect
from .models import SignUpBuyer, SignUpSeller


import base64
import uuid
from django.core.files.base import ContentFile

# Create your views here.
def home(request):
   
    return render(request, 'home.html')

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
       

       # After creating seller account
        request.session['signup_message'] = 'Your account is submitted for verification. You will be notified once approved.'
        return render(request, 'signup_seller.html', {'success': True})

    return render(request, 'signup_seller.html')

def bids(request):
    context = {
        'is_logged_in': request.session.get('is_logged_in')
    }
   
    return render(request, 'bids.html', context)

def sell(request):
    return render(request, 'sell.html', {'title': 'SneakPeek Sell'})

def marketplace(request):
     context = {
        'is_logged_in': request.session.get('is_logged_in')
    }
   

     return render(request, 'marketplace.html', context)    