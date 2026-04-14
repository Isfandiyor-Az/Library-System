from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsOperator, IsUser
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import date, timedelta
from .models import User, Book, Order, Reservation, Rating
from .serializers import BookSerializer, OrderSerializer, ReservationSerializer, RatingSerializer



# --- USER AUTH ---
@api_view(['POST'])
def register(request):
    data = request.data
    # create_user hashes the password automatically
    user = User.objects.create_user(
        username=data['username'],
        password=data['password'],
        role=data.get('role', 'USER').upper()
    )
    return Response({"message": "User registered successfully"})

# --- BOOK MANAGEMENT ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def book_list_create(request):
    if request.method == 'GET':
        books = Book.objects.only('id','title','daily_price','book_status') # SELECT only necessary fields for listing
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        if request.user.role not in ['ADMIN', 'OPERATOR']   :
            return Response({"message": "Permission denied"}, status=403)
        
        serializer = BookSerializer(data=request.data) # Create serializer instance with incoming data Json format
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

@api_view(['GET', 'PUT', 'DELETE']) 
@permission_classes([IsAuthenticated])
def book_detail(request, pk):
    try:
        book = Book.objects.get(pk=pk)
    except Book.DoesNotExist:
        return Response({"message": "Book not found"}, status=404)

    if request.method == 'GET':
        serializer = BookSerializer(book)
        return Response(serializer.data)

    elif request.method == 'PUT':

        if request.user.role not in ['ADMIN', 'OPERATOR']:
            return Response({"message": "Permission denied"}, status=403)

        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        if request.user.role not in ['ADMIN', 'OPERATOR']:
            return Response({"message": "Permission denied"}, status=403)

        book.delete()
        return Response(status=204)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_reservation(request,book_id):
    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        return Response({"message": "Book not found"}, status=404)

    try:
        # Autometically calls .save() in Reservation model
        reservation = Reservation.objects.create(
            user=request.user,
            book=book,
    )
        return Response({"message": "Book reserved successfully for 24 hours",
                     "reservation_id": reservation.id}, status=201)

    except ValueError as e:
        return Response({"message": str(e)}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_reservations(request):
    reservations = Reservation.objects.only('id','user','book','reservation_at','expires_at') # SELECT only necessary fields for listing
    serializer = ReservationSerializer(reservations, many=True)
    return Response(serializer.data)

# --- ORDERS (Borrow & Return) ---
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdmin | IsOperator])
def create_order(request):
    if request.method == 'GET':
        # Just return the list, don't validate a serializer with no data!
        orders = Order.objects.only('id','user','book_price','taken_date','due_date','penalty', 'total_price')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # ONLY do this for POST
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin | IsOperator])
def mark_as_returned(request, pk):

    order = get_object_or_404(Order,pk=pk)

    try:
        order.mark_returned()
        return Response(
            {
                "message": "Returned successfully",
                "total_price": order.total_price,
                "penalty": order.penalty
            }, status=200)
    except ValidationError as e:
        return Response({"message": e.message},status=400)


# --- RATINGS ---

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_rating(request):
    # We pass 'context' so the serializer can see 'request.user'
    serializer = RatingSerializer(data=request.data, context={'request':request})

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
        
    # If the user hasn't read the book, the error will be in serializer.errors
    return Response(serializer.errors, status=400)

        





































'''
from rest_framework import viewsets
from .permissions import IsAdmin, IsOperator, IsUser


from django.contrib.auth.hashers import make_password
from rest_framework.permissions import IsAuthenticated

from rest_framework.exceptions import ValidationError

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

        serializer.save(user=user)'''


