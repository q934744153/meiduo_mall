from django.urls import path,re_path
from . import views

urlpatterns=[
    re_path(r'^carts/$', views.AddToCarts.as_view()),
    re_path(r'^carts/selection/',views.AllSeleCart.as_view()),
    re_path(r'^carts/simple/$',views.CartsSimpleView.as_view()),

]