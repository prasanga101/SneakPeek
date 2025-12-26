from django.db import models

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