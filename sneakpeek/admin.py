from django.contrib import admin
from django.core.mail import send_mail
from .models import SignUpSeller, Sneaker, ProductRequest
import os
from django.core.files.base import ContentFile
from django.core.files import File  # ✅ for proper file handling

# ---------------- Seller Admin ----------------
@admin.register(SignUpSeller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ('Name', 'Email', 'is_verified')
    list_filter = ('is_verified',)
    actions = ['verify_seller']

    def verify_seller(self, request, queryset):
        for seller in queryset:
            if not seller.is_verified:
                seller.is_verified = True
                seller.save()
                send_mail(
                    "Seller Account Verified",
                    f"Hello {seller.Name}, your seller account is now verified.",
                    "no-reply@sneakpeek.com",
                    [seller.Email],
                    fail_silently=True
                )
    verify_seller.short_description = "Verify selected sellers"

# ---------------- ProductRequest Admin ----------------
@admin.register(ProductRequest)
class ProductRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'status', 'created_at')
    list_filter = ('status',)
    actions = ['approve_products', 'reject_products']

    def approve_products(self, request, queryset):
        for req in queryset.filter(status='pending'):
            img_file = None
            if req.image:
                req.image.open()
                img_file = File(req.image)

            Sneaker.objects.create(
                name=req.name,
                description=req.description,
                image=img_file,
                end_time=req.end_time,
                is_featured=True
            )
            req.status = 'approved'
            req.save()

    def reject_products(self, request, queryset):
        queryset.update(status='rejected')

    approve_products.short_description = "Approve selected products"
    reject_products.short_description = "Reject selected products"

# ---------------- Register Sneaker ----------------
admin.site.register(Sneaker)
