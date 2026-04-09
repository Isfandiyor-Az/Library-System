from rest_framework.routers import DefaultRouter
from .views import *
from django.urls import path


rounter = DefaultRouter()
rounter.register('books', BookViewSet)
rounter.register('orders', OrderViewSet)
rounter.register('reservations', ReservationViewSet)
rounter.register('ratings', RatingViewSet)

urlpatterns = rounter.urls

urlpatterns += [
    path('register/', register, name='register'),
]