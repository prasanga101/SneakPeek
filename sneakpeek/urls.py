from django.urls import path
from . import views
#current directory bata view import garcha
urlpatterns = [
    path('',views.home , name ='SneakPeek-home'),
    path('Login/', views.loginn , name ='SneakPeek-Login'),
    path('SignupBuyer/', views.signuppB , name ='SneakPeek-Signup'),
    path('Signup/', views.signup , name ='sign'),
    path('SignupSeller/', views.signuppS , name ='SneakPeek-SignupSeller'),
    path('bids/' , views.bids , name ='SneakPeek-bids'),
    path('sell/' , views.sell , name ='SneakPeek-sell'),
    path('marketplace/' , views.marketplace , name ='SneakPeek-marketplace'),
    path('Logout/' , views.logoutt , name ='SneakPeek-logout'),
    #path('about/', views.about , name ='SneakPeek-about'),
    #path('contact/', views.contact , name ='SneakPeek-contact'),
]
