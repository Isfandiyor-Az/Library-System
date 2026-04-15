from .models import Book, Order, Reservation, Rating, User
from rest_framework import serializers
from django.utils.timezone import now
from datetime import timedelta, date


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ["id","title","daily_price","book_status"]

class OrderSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    book_title = serializers.CharField(source='book.title', read_only=True)
    # 1. You MUST define this here because 'username' isn't in the Order model
    username = serializers.CharField(write_only=True)
    due_date = serializers.DateField(required=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'book', 'book_title', 'book_price','total_price',
                 'taken_date', 'due_date', 'penalty', 'order_status','username','return_date']

        read_only_fields = ['user', 'book_price','total_price', 'penalty']

    def to_representation(self, instance):
        # If the book is out, refresh the math before showing it to the user
        if instance.order_status != "RETURNED":
            instance.calculate_bill()

        return super().to_representation(instance)

    def validate(self,data):
        # 1. Validate User
        book = data.get('book')
        username = data.get('username')

        # 1. Check if username was even provided
        if not username:
            raise serializers.ValidationError({"username": "This field is required."})

        try:
            data['target_user'] = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError(f"User '{username}' not found")

        # 2. Handle Reservation Logic
        reservation = Reservation.objects.filter(book=book).first()
        if reservation and reservation.expires_at < now():
            reservation.delete()  # Clear expired reservation
            book.book_status = "AVAILABLE"
            book.save()
            raise serializers.ValidationError("Reservation expired. Book is now available.")
        else:
            # Active reservation? Store it to delete during create
            data['active_reservation'] = reservation
        # 3 Check Availability
        if book.book_status not in ["AVAILABLE", "RESERVED"]:
            raise serializers.ValidationError("Book is not available for borrowing ")
        
        return data

    def create(self,validated_data):
        username = validated_data.pop('username', None) # Remove the string "Acer"
        target_user = validated_data.pop('target_user')
        reservation = validated_data.pop('active_reservation', None)

        taken_date = validated_data.pop('taken_date')
        due_date = validated_data.pop('due_date')

        if not due_date and not  taken_date:
            raise serializers.ValidationError({"due_date": "Please enter the due_date."})
        
        
        book = validated_data['book']


        if reservation: reservation.delete()

        book.book_status = "BORROWED"
        book.save()

        return Order.objects.create(
            user = target_user,
            taken_date = taken_date,
            due_date = due_date,
            order_status="ACTIVE",
            **validated_data
        )


class ReservationSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username',read_only=True)
    book_title = serializers.ReadOnlyField(source='book.title',read_only=True)
    user_id = serializers.ReadOnlyField(source='user.id',read_only=True)

    class Meta:
        model = Reservation
        fields = ["id","user","user_id","book","book_title","reservation_at","expires_at"]
        read_only_fields = ['user', 'expires_at']

class RatingSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username',read_only=True)
    book_title = serializers.ReadOnlyField(source='book.title',read_only=True)
    class Meta:
        model = Rating
        fields = ["id","user","user_name","book","stars","book_title"]
        read_only_fields = ['user']

    def validate(self, attrs):
        # 1. Access the user from the context
        user = self.context.get('request').user
        book = attrs.get('book')

        # 2. Logic: Must have a 'RETURNED' order to rate
        has_returned = Order.objects.filter(
            user=user, 
            book=book, 
            order_status="RETURNED"
        ).exists()

        if not has_returned:
            raise serializers.ValidationError("You must read (and return) the book before rating it.")

        # 3. Logic: No duplicate ratings
        if Rating.objects.filter(user=user, book=book).exists():
            raise serializers.ValidationError("You have already rated this book.")

        return attrs

    def create(self, validated_data):
        # Automatically attach the user during creation
        user = self.context.get('request').user
        return Rating.objects.create(user=user, **validated_data)
        
