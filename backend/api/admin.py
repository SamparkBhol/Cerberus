from django.contrib import admin
from .models import TrafficLog, Alert

admin.site.register(TrafficLog)
admin.site.register(Alert)
