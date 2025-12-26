from django.contrib import admin

# Register your models here.
from .models import SignUpSeller

class SellerAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Email', 'is_verified')
    list_editable = ('is_verified',)

admin.site.register(SignUpSeller, SellerAdmin)