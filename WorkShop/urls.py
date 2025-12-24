from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),

    path('reception/create/', views.reception_create_order, name='order-create'),
    path('reception/ready/', views.reception_ready_orders, name='reception-ready'),

    path('workshop/', views.workshop_order_list, name='workshop-list'),
    path('workshop/<int:order_id>/',
         views.workshop_update_order, name='workshop-update'),
    path(
        'reception/deliver/<int:order_id>/',
        views.deliver_order,
        name='deliver-order'
    ),
    path(
        'reception/archive/',
        views.delivered_orders_archive,
        name='delivered-archive'
    ),
    path('dashboard/', views.dashboard, name='dashboard'),

]
