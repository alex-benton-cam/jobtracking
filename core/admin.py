from django.contrib import admin
from .models import *

admin.site.register(Job)
admin.site.register(Operation)
admin.site.register(Worker)
admin.site.register(Location)
admin.site.register(Entry)
admin.site.register(FieldDict)

# Register your models here.
