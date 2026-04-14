from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date, timedelta
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.core.exceptions import ValidationError

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('OPERATOR', 'Operator'),
        ('USER', 'User'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES,default='USER')

class Book(models.Model):
    title = models.CharField(max_length=255)
    daily_price = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00) 

    BOOK_STATUS = (
        ("RESERVED", "Reserved"),
        ("BORROWED", "Borrowed"),
        ("AVAILABLE", "Available"),
    )

    book_status = models.CharField(max_length=20, choices=BOOK_STATUS, default="AVAILABLE")

    def __str__(self):
        return self.title

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)

    book_price = models.DecimalField(max_digits=10, decimal_places=2, default=1000.00)
    taken_date = models.DateField()
    due_date = models.DateField(null=True, blank=True) 
    return_date = models.DateField(null=True, blank=True) # Celery

    penalty = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("ACTIVE", "Active"),
        ("RETURNED", "Returned"),
    )
    order_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    def calculate_bill(self):
        """
        Calculates the penalty (1% per day) and the total price.
        """
        self.book_price = self.book.daily_price

        if not self.due_date:
            return 
        # 1. Decide which date to use (today, or the day they actually returned it)
        end_date = self.return_date if self.return_date else date.today()

        # 2. Basic Daily Rental Fee
        days_borrowed = (end_date - self.taken_date).days 

        if days_borrowed < 1: days_borrowed = 1

        base_rent = self.book_price * Decimal(days_borrowed)

        # 3. Penalty Logic (% 1 per day late)
        self.penalty = Decimal('0.00')
        if end_date > self.due_date:
            late_days = (end_date - self.due_date).days
            self.penalty = self.book_price * Decimal('0.01') * Decimal(late_days)
        else:
            self.penalty = Decimal('0.00')

        self.total_price = base_rent + self.penalty

        print(f"---Debug: Order {self.id} | Total: {self.total_price} | Penalty: {self.penalty} ---")

    def save(self, *args, **kwargs):


        if self.order_status in ["ACTIVE","RETURNED"]:
            if self.order_status == "ACTIVE":
                self.book.book_status = "BORROWED"
                self.book.save()
                self.calculate_bill()  # This will calculate penalty and total price

            if self.order_status == "RETURNED":
                if not self.return_date:
                    self.return_date = date.today()
            
                self.book.book_status = "AVAILABLE"
                self.book.save()
                self.calculate_bill()  # This will calculate penalty and total price

        super().save(*args, **kwargs)

    def mark_returned(self):
        if self.order_status == "RETURNED":
            raise ValidationError("Order is already marked as returned")
        
        self.order_status = "RETURNED"
        self.save() # This triggers your custom save logic

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reservation_at = models.DateTimeField(auto_now_add=True) 

    expires_at = models.DateTimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = now() + timedelta(days=1) 

        if self.book.book_status != "AVAILABLE" and not self.pk:
            raise ValueError("Book is not available for reservation")
        self.book.book_status = "RESERVED"
        self.book.save()

        super().save(*args, **kwargs)

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    stars = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        help_text="Enter a rating between 0 and 5"
    )
    class Meta:
        unique_together = ('user', 'book')  # Ensure a user can only rate a book once
    def __str__(self):
        return f"{self.book.title} - {self.stars}"




