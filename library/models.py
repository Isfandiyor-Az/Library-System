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
    returned = models.BooleanField(default=False)
    status = models.CharField(default="pending")

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




