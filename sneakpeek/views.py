from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, 'sneakpeek/home.html', {'title': 'SneakPeek Home'})

def Login(request):
    return render(request, 'sneakpeek/login.html', {'title': 'SneakPeek Login'})

def Signup(request):
    return render(request, 'sneakpeek/signup.html', {'title': 'SneakPeek Signup'})

def bids(request):
    return render(request, 'sneakpeek/bids.html', {'title': 'SneakPeek Bids'})

def sell(request):
    return render(request, 'sneakpeek/sell.html', {'title': 'SneakPeek Sell'})

def marketplace(request):
    return render(request, 'sneakpeek/marketplace.html', {'title': 'SneakPeek Marketplace'})    