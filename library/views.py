from rest_framework import viewsets
from .models import *
from .serializers import *
from datetime import date, timedelta
from .permissions import IsAdmin, IsOperator, IsUser
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from rest_framework.exceptions import ValidationError

    
@api_view(['POST'])
def register(request):
    data = request.data

    user = User(
        username=data['username'],
        role=data.get('role', 'USER').upper()
    )
    user.set_password(data['password'])  
    user.save()

    return Response({"message": "User registered successfully"})

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy','partial_update']:
            return [(IsOperator | IsAdmin)()]
        return [IsAuthenticated()]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action in ['create','update','destroy','mark_as_returned']:
            return [(IsOperator | IsAdmin)()]
        return [IsAuthenticated()]

    # CREATE ORDER (book taken)
    def perform_create(self, serializer):
        book = serializer.validated_data['book']

        if not book.available:
            raise ValidationError("Book is not available")

        book.available = False
        book.save()

        serializer.save(
            user=self.request.user,
            taken_date=date.today(),
            due_date=date.today() + timedelta(days=1),  # borrowing period
            returned=False
        )

    def perform_update(self, serializer):
        
        instance = serializer.save()

        if instance.returned and instance.status != "completed":
            instance.status = "completed"
            instance.return_date = date.today()

            instance.calculate_bill()  # This will calculate penalty and total price, and save the order
            

            instance.book.available = True
            instance.book.save()
            instance.save()
    
    @action(detail=True, methods=['post'])
    def mark_as_returned(self, request, pk=None):
        order = self.get_object()

        if order.returned:
            return Response({"message": "Order is already marked as returned"}, status=400)

        order.returned = True
        order.return_date = date.today()
        order.status = "completed"

        order.calculate_bill()  # This will calculate penalty and total price, and save the order

        order.book.available = True
        order.book.save()

        return Response({"message": "Order marked as returned successfully",
        "book": order.book.title,
        "daily_price": order.book.daily_price,
        "penalty": order.penalty,
        "total_price": order.total_price
        }, status=200)

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get_permissions(self):
        if self.action in ['confirm_reservation']:
            return [(IsOperator | IsAdmin)()]
        return [(IsUser | IsAdmin)()]

    def perform_create(self, serializer):
        book = serializer.validated_data['book']

        if not book.available:
            raise ValidationError("Book is not available for reservation")
        
        elif not book:
            raise ValidationError({"book": "Book does not exist"})
        
        book.available = False
        book.save()

        serializer.save(
            user=self.request.user,
            expires_at = now() + timedelta(days=1)
        )

    @action(detail=True, methods=['post']) 
    def confirm_reservation(self, request, pk=None):
        reservation = self.get_object()

        if reservation.expires_at < now():
            # If expired, make book available again and error out
            reservation.book.available = True
            reservation.book.save()
            reservation.delete()
            raise ValidationError("Reservation has expired and has been deleted")

        # Create an order for the reserved book
        order = Order.objects.create(
            user=reservation.user,
            book=reservation.book,
            taken_date=date.today(),
            due_date=date.today() + timedelta(days=1),
            returned=False
        )

        # Delete the reservation after confirming
        reservation.delete()

        return Response({"message": "Reservation confirmed and order created successfully",
                        "order_id": order.id
                        }, status=200)  
                         

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        return [(IsUser | IsAdmin)()]

    def perform_create(self, serializer):
        user = self.request.user
        book = serializer.validated_data['book']

        has_returned = Order.objects.filter(user=user, book=book, returned=True).exists()

        if not Order.objects.filter(user=user, book=book, returned=True).exists():
            raise ValidationError("You must read the book first")

        if Rating.objects.filter(user=user, book=book).exists():
            raise ValidationError("You have already rated this book")

        serializer.save(user=user)


