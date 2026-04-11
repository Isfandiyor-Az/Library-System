from .models import *
from rest_framework import serializers

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'book', 'book_title', 'taken_date', 'due_date', 'return_date', 'penalty', 'total_price', 'returned', 'status']

    def to_representation(self, instance):
        # If the book is out, refresh the math before showing it to the user
        if not instance.returned:
            instance.calculate_bill()
        return super().to_representation(instance)

class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username',read_only=True)
    book_title = serializers.ReadOnlyField(source='book.title',read_only=True)

    class Meta:
        model = Reservation
        fields = ["id","user","book","book_title","reservation_at","expires_at"]
        read_only_fields = ['user', 'expires_at']

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ['user']
