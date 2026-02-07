from django.urls import path
from . import views
app_name = 'api'

urlpatterns = [
    # FIX: Wire the endpoint to the real Django view that accepts POST JSON.
    path('firebase-listener/', views.firebase_listener, name='firebase-listener'),
]


