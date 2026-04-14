#from rest_framework.routers import DefaultRouter
#from .views import BookViewSet, OrderViewSet, ReservationViewSet, RatingViewSet
from django.urls import path
from . import views


'''rounter = DefaultRouter()
rounter.register('books', BookViewSet)
rounter.register('orders', OrderViewSet)
rounter.register('reservations', ReservationViewSet)
rounter.register('ratings', RatingViewSet)

urlpatterns = rounter.urls '''

urlpatterns = [
    # Auth
    path('register/', views.register, name='register'),

    # Books
    path('books/', views.book_list_create, name='book-list-get'),

    path('books/<int:pk>/', views.book_detail, name='book-get'),

    # Orders
    path('orders/create/', views.create_order, name='order-list-create'),
    path('orders/<int:pk>/return/', views.mark_as_returned, name='order-return'),

    # Reservations
    path('reservations/<int:book_id>/', views.make_reservation, name='reserve-book'),
    path('reservations/', views.get_reservations, name='get-reservations'),

    # Ratings
    path('ratings/', views.create_rating, name='create-rating'),
]