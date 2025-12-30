from django.db import models
from tinymce.models import HTMLField
# Create your models here.

class SignUpBuyer(models.Model):
    FName=models.CharField(max_length=50)
    LName=models.CharField(max_length=50)
    Email=models.EmailField(unique=True)
    Password=models.CharField(max_length=500)##increased length for hashed password storage

class SignUpSeller(models.Model):
    Name = models.CharField(max_length=100)  # Full name
    Email = models.EmailField(unique=True)
    Password = models.CharField(max_length=500)  # For hashed password storage
    Phone = models.CharField(max_length=20)
    Address = models.TextField()
    BusinessName = models.CharField(max_length=100, blank=True, null=True)  # Optional
    IDImage = models.ImageField(upload_to='documents/')  # Uploaded document (Citizenship / PAN)
    LivePhoto = models.ImageField(upload_to='live_photos/')  # Captured live photo
    
    is_verified = models.BooleanField(default=False)
    def __str__(self):
        return self.Email
    

class Sneaker(models.Model):
    name = models.CharField(max_length=100)
    description = HTMLField()
    # description = models.TextField()
    image = models.ImageField(upload_to='sneakers/')
    end_time = models.DateTimeField()
    is_featured = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Bid(models.Model):
    sneaker = models.ForeignKey(Sneaker, on_delete=models.CASCADE, related_name='bids')
    #CASCADE = delete everything that depends on it

# In simple words:

# 🧨 “If the parent is deleted, delete the children automatically”
    buyer = models.ForeignKey(SignUpBuyer, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer.FName} - {self.amount} on {self.sneaker.name}"
    

class Payment(models.Model):
    email = models.EmailField()
    amount = models.FloatField()
    product_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="PENDING")


class ProductRequest(models.Model):
    seller = models.ForeignKey(SignUpSeller, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = HTMLField()
    image = models.ImageField(upload_to='product_requests/')
    end_time = models.DateTimeField()

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


