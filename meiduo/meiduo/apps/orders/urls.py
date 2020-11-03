from django.urls import re_path,path
from . import views

urlpatterns = [
    re_path(r'^orders/settlement/$', views.OrderSettlementView.as_view()),
    path('orders/commit/', views.OrderCommitView.as_view()),
]