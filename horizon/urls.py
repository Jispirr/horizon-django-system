from django.urls import path
from . import views

urlpatterns = [
    # Public
    path('',                        views.home,            name='home'),
    path('catalog/',                views.catalog,         name='catalog'),
    path('search/',                 views.search,              name='search'),
    path('search/autocomplete/',    views.search_autocomplete, name='search_autocomplete'),
    path('catalog/<int:pk>/',       views.vehicle_detail,  name='vehicle_detail'),
    path('contact/submit/',         views.contact_submit,        name='contact_submit'),
    path('test-drive/',                  views.test_drive_request,   name='test_drive_request'),
    path('releases/',               views.releases,        name='releases'),
    path('client-releases/',              views.client_releases, name='client_releases'),
    path('client-releases/submit/',       views.submit_review,   name='submit_review'),
    path('ticket/',                  views.ticket_lookup,    name='ticket_lookup'),
    path('inquiry/<str:token>/',          views.inquiry_thread,  name='inquiry_thread'),
    path('inquiry/<str:token>/reply/',    views.inquiry_reply,   name='inquiry_reply'),
    path('inquiry/<str:token>/poll/',     views.inquiry_poll,    name='inquiry_poll'),


    # Live chat widget (public — all pages)
    # NOTE: static paths must come BEFORE the <str:token> wildcard patterns
    path('widget/chat/start/',               views.widget_chat_start,    name='widget_chat_start'),
    path('widget/chat/lookup/',              views.widget_chat_lookup,   name='widget_chat_lookup'),
    path('widget/chat/lookup-by-token/',     views.widget_chat_by_token, name='widget_chat_by_token'),
    path('widget/chat/<str:token>/send/',    views.widget_chat_send,     name='widget_chat_send'),
    path('widget/chat/<str:token>/poll/',    views.widget_chat_poll,     name='widget_chat_poll'),

    # Admin auth
    path('admin-panel/login/',  views.admin_login,  name='admin_login'),
    path('admin-panel/logout/', views.admin_logout, name='admin_logout'),
    path('admin-panel/',        views.admin_dashboard, name='admin_dashboard'),

    # Cars
    # NOTE: static paths must come BEFORE the <int:pk> wildcard patterns
    path('admin-panel/cars/',                    views.admin_cars,       name='admin_cars'),
    path('admin-panel/cars/add/',                views.admin_car_add,    name='admin_car_add'),
    path('admin-panel/cars/export/pdf/',         views.export_cars_pdf,  name='export_cars_pdf'),
    path('admin-panel/cars/<int:pk>/edit/',      views.admin_car_edit,   name='admin_car_edit'),
    path('admin-panel/cars/<int:pk>/delete/',    views.admin_car_delete, name='admin_car_delete'),

    # Orders
    path('admin-panel/orders/',              views.admin_orders,     name='admin_orders'),
    path('admin-panel/orders/add/',          views.admin_order_add,  name='admin_order_add'),
    path('admin-panel/orders/<int:pk>/edit/',views.admin_order_edit, name='admin_order_edit'),

    # Customers
    path('admin-panel/customers/',       views.admin_customers,    name='admin_customers'),
    path('admin-panel/customers/add/',   views.admin_customer_add, name='admin_customer_add'),

    # Test Drives
    path('admin-panel/test-drives/',                    views.admin_test_drives,        name='admin_test_drives'),
    path('admin-panel/test-drives/<int:pk>/update/',    views.admin_test_drive_update,  name='admin_test_drive_update'),
    path('admin-panel/test-drives/<int:pk>/delete/',    views.admin_test_drive_delete,  name='admin_test_drive_delete'),

    # Reviews (admin-managed)
    path('admin-panel/reviews/',                  views.admin_reviews,       name='admin_reviews'),
    path('admin-panel/reviews/add/',              views.admin_review_add,    name='admin_review_add'),
    path('admin-panel/reviews/<int:pk>/toggle/',  views.admin_review_toggle, name='admin_review_toggle'),
    path('admin-panel/reviews/<int:pk>/delete/',  views.admin_review_delete, name='admin_review_delete'),

    # Inquiries
    # NOTE: static 'unread/' path before <int:pk> wildcards for clarity
    path('admin-panel/inquiries/',                         views.admin_inquiries,           name='admin_inquiries'),
    path('admin-panel/inquiries/unread/',                  views.admin_inquiries_unread,    name='admin_inquiries_unread'),
    path('admin-panel/inquiries/<int:pk>/',                views.admin_inquiry_detail,      name='admin_inquiry_detail'),
    path('admin-panel/inquiries/<int:pk>/update/',         views.admin_inquiry_update,      name='admin_inquiry_update'),
    path('admin-panel/inquiries/<int:pk>/delete/',         views.admin_inquiry_delete,      name='admin_inquiry_delete'),
    path('admin-panel/inquiries/<int:pk>/reply/',          views.admin_inquiry_reply,       name='admin_inquiry_reply'),
    path('admin-panel/inquiries/<int:pk>/thread-poll/',    views.admin_inquiry_thread_poll, name='admin_inquiry_thread_poll'),
    path('admin-panel/inquiries/<int:pk>/toggle-read/',    views.admin_inquiry_toggle_read, name='admin_inquiry_toggle_read'),

    # Live Chats (admin)
    # NOTE: static path 'unread/' must come BEFORE the <int:pk> wildcard patterns
    path('admin-panel/chats/',                views.admin_chats,         name='admin_chats'),
    path('admin-panel/chats/unread/',         views.admin_chats_unread,  name='admin_chats_unread'),
    path('admin-panel/chats/<int:pk>/open/',  views.admin_chat_open,     name='admin_chat_open'),
    path('admin-panel/chats/<int:pk>/reply/', views.admin_chat_reply,    name='admin_chat_reply'),
    path('admin-panel/chats/<int:pk>/poll/',  views.admin_chat_poll,     name='admin_chat_poll'),
    path('admin-panel/chats/<int:pk>/update/',views.admin_chat_update,   name='admin_chat_update'),
    path('admin-panel/chats/<int:pk>/close/', views.admin_chat_close,    name='admin_chat_close'),

    # Brands
    path('admin-panel/brands/',                   views.admin_brands,        name='admin_brands'),
    path('admin-panel/brands/add/',               views.admin_brand_add,     name='admin_brand_add'),
    path('admin-panel/brands/<int:pk>/edit/',     views.admin_brand_edit,    name='admin_brand_edit'),
    path('admin-panel/brands/<int:pk>/delete/',   views.admin_brand_delete,  name='admin_brand_delete'),

    # Categories
    path('admin-panel/categories/',                   views.admin_categories,        name='admin_categories'),
    path('admin-panel/categories/add/',               views.admin_category_add,      name='admin_category_add'),
    path('admin-panel/categories/<int:pk>/edit/',     views.admin_category_edit,     name='admin_category_edit'),
    path('admin-panel/categories/<int:pk>/delete/',   views.admin_category_delete,   name='admin_category_delete'),

    # System
    path('admin-panel/settings/',  views.admin_settings,  name='admin_settings'),
    path('admin-panel/discounts/', views.admin_discounts,  name='admin_discounts'),
    # Wishlist (session-based)
    path('wishlist/',                    views.wishlist,          name='wishlist'),
    path('wishlist/toggle/<int:pk>/',    views.wishlist_toggle,   name='wishlist_toggle'),
    path('wishlist/status/',             views.wishlist_status,   name='wishlist_status'),

    # Comparison (session-based)
    path('compare/',                     views.compare,           name='compare'),
    path('compare/add/<int:pk>/',        views.compare_add,       name='compare_add'),
    path('compare/remove/<int:pk>/',     views.compare_remove,    name='compare_remove'),
    path('compare/clear/',               views.compare_clear,     name='compare_clear'),
    path('compare/status/',              views.compare_status,    name='compare_status'),
]