from django.urls import path
from . import views
app_name = 'api'

urlpatterns = [
    path('firebase-listener/', views.firestore_listener, name='firebase-listener'),
]


