from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import ProductRequest, Sneaker

@receiver(post_save, sender=ProductRequest)
def create_sneaker_on_approval(sender, instance, created, **kwargs):

    if (instance.status or "").lower() != "approved":
        return

    # avoid duplicates
    if Sneaker.objects.filter(name=instance.name, image=instance.image).exists():
        return

    Sneaker.objects.create(
        name=instance.name,
        image=instance.image,
        description=getattr(instance, "description", ""),
        end_time=timezone.now() + timedelta(minutes=5),  # ✅ 5 min bidding
    )