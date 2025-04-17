from django.urls import path
from . import views

app_name = 'circulation'

urlpatterns = [
    path('members/', views.member_list, name='member_list'),
    path('loans/', views.loan_list, name='loan_list'),
    path('loans/overdue/', views.loan_overdue_list, name='loan_overdue_list'),
    path('reservations/', views.reservation_list, name='reservation_list'),
]