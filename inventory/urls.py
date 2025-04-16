from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('shelves/', views.ShelfListView.as_view(), name='shelf-list'),
    path('shelf/<int:pk>/', views.ShelfDetailView.as_view(), name='shelf-detail'),
    path('items/', views.InventoryItemListView.as_view(), name='item-list'),
    path('acquisition/create/', views.AcquisitionCreateView.as_view(),
         name='acquisition-create'),
]