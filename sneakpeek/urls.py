from django.urls import path
from . import views
#current directory bata view import garcha
urlpatterns = [
    path('',views.home , name ='SneakPeek-home'),
    path('Login/', views.Login , name ='SneakPeek-Login'),
    path('Signup/', views.Signup , name ='SneakPeek-Signup'),
    path('bids/' , views.bids , name ='SneakPeek-bids'),
    path('sell/' , views.sell , name ='SneakPeek-sell'),
    path('marketplace/' , views.marketplace , name ='SneakPeek-marketplace'),
    #path('about/', views.about , name ='SneakPeek-about'),
    #path('contact/', views.contact , name ='SneakPeek-contact'),
]
