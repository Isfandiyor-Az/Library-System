from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils.timezone import now
from datetime import date, timedelta,datetime
from .models import User, Book, Order, Reservation, Rating
from .serializers import BookSerializer, OrderSerializer, ReservationSerializer, RatingSerializer
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework import status
from .permissions import IsAdmin, IsOperator



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
class BookListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get_permissions(self):
        if self.request.method in ['POST','PUT', 'DELETE']:
            return [IsAuthenticated(), (IsAdmin | IsOperator)()]
        return [IsAuthenticated()]

    def get(self, request):
        books = Book.objects.only('id','title','daily_price','book_status')
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(data=request.data) 
        if serializer.is_valid():
            serializer.save() # Save to DB
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400) 
        

class BookDetailAPIView(BookListCreateAPIView):

    def get_object(self, pk):
        try:
            return Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"message": "Book not found"}, status=404)

    def get(self,request,pk):
        book = self.get_object(pk)
        if not book:
            return Response({"message":"Book not found"},status=404)
        serializer = BookSerializer(book)
        return Response(serializer.data)

    def put(self, request, pk):
        book = self.get_object(pk)
        if not book:
            return Response({"message": "Book not found"}, status=404)
        
        serializer = BookSerializer(book, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        book = self.get_object(pk)
        if not book:
            return Response({"message": "Book not found"}, status=404)
        book.delete()
        return Response(status=200) 


class ReservationAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reservations = Reservation.objects.only(
            'id', 'user', 'book', 'reservation_at', 'expires_at')
        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data)

    def post(self, request, book_id):
        try:
            book = Book.objects.get(pk=book_id)
        except Book.DoesNotExist:
            return Response({"message": "Book not found"}, status=404)
        try:
            reservation = Reservation.objects.create(
                user=request.user,
                book=book,
            )
            return Response({
                "message": "Book reserved successfully for 24 hours",
                "reservation_id": reservation.id
            }, status=201)
        
        except ValueError as e:
            return Response({"message": str(e)}, status=400)


class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin | IsOperator]

    def get(self, request):
        orders = Order.objects.only(
            'id', 'user', 'book_price', 'taken_date', 
            'due_date', 'penalty', 'total_price'
        )
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class MarkAsReturnedView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin | IsOperator]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        raw_date = request.data.get('return_date')
        provided_date = None

        if raw_date:
            try:
                provided_date = datetime.strptime(raw_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=400)

        try:
            order.mark_returned(provided_date=provided_date)
            return Response({
                "message": "Returned successfully",
                "total_price": order.total_price,
                "penalty": order.penalty,
                "return_date": order.return_date
            }, status=200)
        except ValidationError as e:
            return Response({"message": str(e.message)}, status=400)

class RatingListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ratings = Rating.objects.only('id', 'user', 'book', 'stars')
        serializer = RatingSerializer(ratings, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RatingSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)

        




























