from django.core.management.base import BaseCommand
from django.utils.timezone import now
from library.models import Reservation, Book
from django.db.models import transaction

class Command(BaseCommand):
    help = 'Delete expired reservations and release books'

    def handle(self, *args, **kwargs):
        expired = Reservation.objects.filter(expires_at__lt=now())
        count = expired.count()

        if count == 0:
            self.stdout.write(self.style.WARNING("No expired reservations found."))
            return
        book_ids = expired.values_list('book_id', flat=True)

        #  Use Atomic Transaction (All or Nothing)
        with transaction.atomic():
            # Mark associated books as available
            Book.objects.filter(id__in=book_ids).update(available=True)

            # Delete expired reservations
            expired.delete()

        self.stdout.write(self.style.SUCCESS(f"Successfully deleted {count} expired reservations"))
