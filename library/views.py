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

    
@api_view(['POST'])
def register(request):
    data = request.data

    user = User(
        username=data['username'],
        role=data.get('role', 'USER')
    )
    user.set_password(data['password'])  
    user.save()

    return Response({"message": "User registered successfully"})

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'destroy']:
            return [IsOperator()]
        return [IsAuthenticated()]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        return [IsOperator()]

    def perform_create(self, serializer):
        order = serializer.save()

        if order.returned:
            days = (date.today() - order.taken_date).days

            if days > 0:
                penalty = order.book.daily_price * days * 0.01
                order.penalty = penalty
                order.save()

    @action(detail=True, methods=['post'], permission_classes=[IsOperator()])
    
    def accept_order(self, request, pk=None):
        """
        Endpoint for operators to accept/confirm an order
        POST /api/orders/{id}/accept_order/
        """
        order = self.get_object()

        # Check if order is already accepted (if you wanted to track acceptance status)
        # For now, we just confirm the order exists and is valid

        return Response({
            "message": "Order accepted successfully",
            "order_id": order.id,
            "user": order.user.username,
            "book": order.book.title,
            "taken_date": order.taken_date,
            "expected_return_date": order.return_date,
            "daily_price": order.book.daily_price,
            "status": "accepted"
        }, status=200)

class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer

    def get_permissions(self):
        return [IsUser()]

    def perform_create(self, serializer):
        book = serializer.validated_data['book']

        if not book.available:
            raise Exception("Book is not available for reservation")
        
        book.available = False
        book.save()

        serializer.save(user=self.request.user)

class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer

    def get_permissions(self):
        return [IsUser()]

    def perform_create(self, serializer):
        user = self.request.user
        book = serializer.validated_data['book']

        if not Order.objects.filter(user=user, book=book, returned=True).exists():
            raise Exception("You must read the book first")

        serializer.save(user=user)


