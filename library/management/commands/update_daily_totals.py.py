from django.core.management.base import BaseCommand
from library.models import Order

class Command(BaseCommand):
    help = 'Runs every night to update penalties and totals for active orders'

    def handle(self, *args, **options):
        # We only care about books that haven't been returned
        active_orders = Order.objects.filter(returned=False)
        
        for order in active_orders:
            order.calculate_bill()
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {active_orders.count()} orders."))