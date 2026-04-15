from django.urls import path
from . import views
from .views import BookListCreateAPIView, BookDetailAPIView,ReservationAPIView,OrderListCreateView,MarkAsReturnedView,RatingListCreateView



urlpatterns = [
    # Auth
    path('register/', views.register, name='register'),

    # Books
    path('books/', BookListCreateAPIView.as_view(), name='book-list-create'),

    path('books/<int:pk>/', BookDetailAPIView.as_view(), name='book-detail'),

    # Orders
    path('orders/create/', OrderListCreateView.as_view(), name='order-list-create'),
    path('orders/<int:pk>/return/', MarkAsReturnedView.as_view(), name='order-return'),

    # Reservations
    path('reservations/<int:book_id>/', ReservationAPIView.as_view(), name='reserve-book'),
    path('reservations/', ReservationAPIView.as_view(), name='get-reservations'),

    # Ratings
    path('ratings/',RatingListCreateView.as_view(), name='create-rating'),
]






















