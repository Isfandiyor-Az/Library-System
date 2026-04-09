from django.core.management.base import BaseCommand
from django.utils.timezone import now
from library.models import Reservation

class Command(BaseCommand):
    help = 'Delete expired reservations'

    def handle(self, *args, **kwargs):
        expired = Reservation.objects.filter(expires_at__lt=now())

        count = expired.count()

        for res in expired:
            
            book = res.book
            book.available = True
            book.save()

        expired.delete()

        self.stdout.write(f"Deleted {count} expired reservations")
