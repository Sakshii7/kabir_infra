from django.urls import path

from . import views

urlpatterns = [
    path('login', views.login, name='login'),
    path('my_profile', views.my_profile, name='User Profile'),
    path('get_country_list', views.get_country_list, name='Get Country list'),
    path('get_state_list', views.get_state_list, name='Get State list'),
    path('get_city_list', views.get_city_list, name='Get City list'),
    path('get_site_list', views.get_site_list, name='Get Site list'),
    path('get_vendor_list', views.get_vendor_list, name='Get Vendor list'),
    path('get_grn_list', views.get_grn_list, name='Get GRN list'),
    path('view_grn', views.view_grn, name='GRN View'),
    path('ref_purchase_order_list', views.ref_purchase_order_list, name='Ref Purchase order List'),
    path('add_grn', views.add_grn, name='Add GRN'),
    path('get_pending_purchase_order_list', views.get_pending_purchase_order_list,
         name='Get Pending Purchase Order list'),
    path('view_purchase_order', views.view_purchase_order, name='Purchase Order View'),
    path('get_material_requisition_list', views.get_material_requisition_list, name='Get Material Requisition List'),
    path('view_material_requisition', views.view_material_requisition, name='Material Requisition View'),
    path('add_material_requisition', views.add_material_requisition, name='Add Material Requisition'),
    path('get_company_list', views.get_company_list, name='Get Company List'),
    path('management_dashboard', views.management_dashboard, name='Management Dashboard'),
]
