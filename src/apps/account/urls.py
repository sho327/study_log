# coding: utf-8
from django.urls import path
from rest_framework import routers

from .views.login import LoginView
from .views.signup import SignupView
from .views.account_activate import AccountActivateView
from .views.password_reset import PasswordResetView
from .views.password_reset_confirm import PasswordResetConfirmView
from .views.account_withdraw import AccountWithdrawView

app_name = "account"

router = routers.DefaultRouter()
urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('account_activate/', AccountActivateView.as_view(), name='account_activate'),
    path('account_withdraw/', AccountWithdrawView.as_view(), name='account_withdraw'),
]
