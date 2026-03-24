from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                        views.home,            name='home'),
    path('catalog/',                views.catalog,         name='catalog'),
    path('catalog/<int:pk>/',       views.vehicle_detail,  name='vehicle_detail'),
    path('contact/submit/',         views.contact_submit,  name='contact_submit'),
    path('releases/',               views.releases,        name='releases'),
    path('ticket/',                  views.ticket_lookup,   name='ticket_lookup'),


    # Live chat widget (public — all pages)
    path('widget/chat/start/',               views.widget_chat_start, name='widget_chat_start'),
    path('widget/chat/<str:token>/send/',     views.widget_chat_send,  name='widget_chat_send'),
    path('widget/chat/<str:token>/poll/',     views.widget_chat_poll,  name='widget_chat_poll'),
    path('widget/chat/lookup/',                  views.widget_chat_lookup,   name='widget_chat_lookup'),
    path('widget/chat/lookup-by-token/',          views.widget_chat_by_token, name='widget_chat_by_token'),

    # Admin auth
    path('admin-panel/login/',  views.admin_login,  name='admin_login'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/',        views.admin_dashboard, name='admin_dashboard'),

    # Cars
    path('admin-panel/cars/',                views.admin_cars,       name='admin_cars'),
    path('admin-panel/cars/add/',            views.admin_car_add,    name='admin_car_add'),
    path('admin-panel/cars/<int:pk>/edit/',  views.admin_car_edit,   name='admin_car_edit'),
    path('admin-panel/cars/<int:pk>/delete/',views.admin_car_delete, name='admin_car_delete'),

    # Orders
    path('admin-panel/orders/',              views.admin_orders,     name='admin_orders'),
    path('admin-panel/orders/add/',          views.admin_order_add,  name='admin_order_add'),
    path('admin-panel/orders/<int:pk>/edit/',views.admin_order_edit, name='admin_order_edit'),

    # Customers
    path('admin-panel/customers/',       views.admin_customers,    name='admin_customers'),
    path('admin-panel/customers/add/',   views.admin_customer_add, name='admin_customer_add'),

    # Inquiries
    path('admin-panel/inquiries/',                         views.admin_inquiries,          name='admin_inquiries'),
    path('admin-panel/inquiries/<int:pk>/',                views.admin_inquiry_detail,     name='admin_inquiry_detail'),
    path('admin-panel/inquiries/<int:pk>/update/',         views.admin_inquiry_update,     name='admin_inquiry_update'),
    path('admin-panel/inquiries/<int:pk>/delete/',         views.admin_inquiry_delete,     name='admin_inquiry_delete'),
    path('admin-panel/inquiries/<int:pk>/toggle-read/',    views.admin_inquiry_toggle_read,name='admin_inquiry_toggle_read'),

    # Live Chats (admin)
    path('admin-panel/chats/',                views.admin_chats,         name='admin_chats'),
    path('admin-panel/chats/<int:pk>/open/',  views.admin_chat_open,     name='admin_chat_open'),
    path('admin-panel/chats/<int:pk>/reply/', views.admin_chat_reply,    name='admin_chat_reply'),
    path('admin-panel/chats/<int:pk>/poll/',  views.admin_chat_poll,     name='admin_chat_poll'),
    path('admin-panel/chats/<int:pk>/update/',views.admin_chat_update,   name='admin_chat_update'),
    path('admin-panel/chats/<int:pk>/close/', views.admin_chat_close,    name='admin_chat_close'),
    path('admin-panel/chats/unread/',         views.admin_chats_unread,  name='admin_chats_unread'),

    # System
    path('admin-panel/settings/',  views.admin_settings,  name='admin_settings'),
    path('admin-panel/discounts/', views.admin_discounts,  name='admin_discounts'),
]
