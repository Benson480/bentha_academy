from django.utils import timezone
from datetime import timedelta
from .models import MpesaTransaction

def mark_timeouts():
    limit = timezone.now() - timedelta(minutes=5)
    MpesaTransaction.objects.filter(
        status='PENDING',
        created_at__lt=limit
    ).update(status='TIMEOUT')
