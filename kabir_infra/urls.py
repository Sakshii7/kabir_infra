from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('country_list', views.country_list, name='country_list'),
    path('state_list', views.state_list, name='state_list'),
    path('city_list', views.city_list, name='city_list'),
    path('grn_list', views.grn_list, name='grn_list'),
    path('purchase_order_list', views.purchase_order_list, name='purchase_order_list'),
    path('view_grn', views.view_grn, name='view_grn'),
    path('view_purchase_order', views.view_purchase_order, name='view_purchase_order'),
]
