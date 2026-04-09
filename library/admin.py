from django.contrib import admin
from .models import *

admin.site.register(Book)
admin.site.register(Order)
admin.site.register(Reservation)
admin.site.register(Rating)
admin.site.register(User)
