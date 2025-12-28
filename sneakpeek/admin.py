from django.contrib import admin
from django.core.mail import send_mail
from .models import SignUpSeller
from .models import Sneaker

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

                # Send email notification
                send_mail(
                    subject="Your SneakPeek Seller Account is Verified ✅",
                    message=f"""
Hello {seller.Name},

Your seller account has been verified successfully.
You can now log in and start listing sneakers.

– SneakPeek Team
""",
                    from_email="no-reply@sneakpeek.com",
                    recipient_list=[seller.Email],
                    fail_silently=True
                )

    verify_seller.short_description = "Verify selected sellers & notify"


admin.site.register(Sneaker)

