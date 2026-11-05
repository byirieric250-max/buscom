from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from commerce.views import AddressViewSet, BusinessViewSet, CategoryViewSet, ComplaintViewSet, ConversationViewSet, FavoriteViewSet, NotificationViewSet, ProductViewSet, OrderViewSet, BookingViewSet, ServiceViewSet, ReviewViewSet, RegisterView, LoginView, MeView, LogoutView, SellerReportsView, HealthView, GuidanceView, PaymentWebhookView, PrivateMediaView, ProductMediaView
router=DefaultRouter()
router.register('businesses', BusinessViewSet, basename='business')
router.register('categories', CategoryViewSet, basename='category')
router.register('products', ProductViewSet, basename='product')
router.register('orders', OrderViewSet, basename='order')
router.register('bookings', BookingViewSet, basename='booking')
router.register('services', ServiceViewSet, basename='service')
router.register('reviews', ReviewViewSet, basename='review')
router.register('addresses', AddressViewSet, basename='address')
router.register('favorites', FavoriteViewSet, basename='favorite')
router.register('notifications', NotificationViewSet, basename='notification')
router.register('conversations', ConversationViewSet, basename='conversation')
router.register('complaints', ComplaintViewSet, basename='complaint')
urlpatterns=[path('admin/',admin.site.urls),path('media/products/<path:path>',ProductMediaView.as_view()),path('media/<path:path>',PrivateMediaView.as_view()),path('api/health/',HealthView.as_view()),path('api/ai-guidance/',GuidanceView.as_view()),path('api/auth/register/',RegisterView.as_view()),path('api/auth/login/',LoginView.as_view()),path('api/auth/me/',MeView.as_view()),path('api/auth/logout/',LogoutView.as_view()),path('api/seller/reports/',SellerReportsView.as_view()),path('api/payments/webhook/',PaymentWebhookView.as_view()),path('api/',include(router.urls))]
