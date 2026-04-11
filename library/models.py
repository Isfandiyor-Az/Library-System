from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date, timedelta
from django.utils.timezone import now
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('OPERATOR', 'Operator'),
        ('USER', 'User'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

class Book(models.Model):
    title = models.CharField(max_length=255)
    daily_price = models.IntegerField()
    available = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    taken_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)  
    return_date = models.DateField(null=True, blank=True)
    penalty = models.FloatField(default=0.0)
    total_price = models.FloatField(default=0.0)
    returned = models.BooleanField(default=False)
    status = models.CharField(default="pending")

    def calculate_bill(self):
        """
        Calculates the penalty (1% per day) and the total price.
        """
        # 1. Decide which date to use (today, or the day they actually returned it)
        end_date = self.return_date if self.return_date else date.today()

        # 2. Basic Daily Rental Fee
        days_borrowed = (end_date - self.taken_date).days
        if days_borrowed <= 0 : days_borrowed = 1 # minimum 1 day charge
        base_rent = self.book.daily_price * days_borrowed

        # 3. Penalty Logic (Your readable logic)
        self.penalty = 0.0
        if end_date > self.due_date:
            late_days = (end_date - self.due_date).days
            self.penalty = self.book.daily_price * 0.01 * late_days


        self.total_price = base_rent + self.penalty
        self.save()

    def __str__(self):
        return f"{self.user.username} - {self.book.title}"

class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    reservation_at = models.DateTimeField(auto_now_add=now)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = now() + timedelta(days=1)  
        super().save(*args, **kwargs)

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    stars = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ],
        help_text="Enter a rating between 0 and 5"
    )

    def __str__(self):
        return f"{self.book.title} - {self.stars}"




