from django.urls import path
from . import views
from django.conf.urls.static import static
#current directory bata view import garcha


urlpatterns = [
    path('',views.home , name ='SneakPeek-home'),
    # path('bid/<int:sneaker_id>/', views.place_bid, name='place_bid'),
   path('create-checkout-session/<int:bid_id>/', views.create_checkout_session, name='create_checkout_session'),
    path('store-payment-id/<int:payment_id>/', views.store_payment_id, name='store_payment_id'),
    path('Login/', views.loginn , name ='SneakPeek-Login'),
    path('SignupBuyer/', views.signuppB , name ='SneakPeek-Signup'),
    path('Signup/', views.signup , name ='sign'),
    path('SignupSeller/', views.signuppS , name ='SneakPeek-SignupSeller'),
    path('bids/' , views.bids , name ='SneakPeek-bids'),
    path('sell/' , views.sell , name ='SneakPeek-sell'),
    path('marketplace/' , views.marketplace , name ='SneakPeek-marketplace'),
    path('Logout/' , views.logoutt , name ='SneakPeek-logout'),
    path('addproduct/' , views.add_product_request , name ='SneakPeek-product'),
    #path('about/', views.about , name ='SneakPeek-about'),
    #path('contact/', views.contact , name ='SneakPeek-contact'),
    path('signup_successful/', views.SignSuccess , name ='SneakPeek-signup_successful'),

    path('sneaker/<int:sneaker_id>/bid/', views.place_bid_view, name='place_bid'),
    path('sneaker/<int:sneaker_id>/bid/submit/', views.submit_bid, name='submit_bid'),
    # urls.py
    path('sneaker/<int:sneaker_id>/result/', views.bidding_result, name='bidding_result'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),

]
