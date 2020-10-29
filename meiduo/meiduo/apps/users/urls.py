from django.urls import path,re_path
from . import views
urlpatterns = [
    path('usernames/<username:username>/count/',views.UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/',views.MobileCountView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/',views.LoginView.as_view()),
    path('logout/',views.LogoutView.as_view()),
    path('info/',views.UserInfoView.as_view()),
    path('emails/',views.EmailView.as_view()),
    re_path(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    re_path(r'^addresses/create/$',views.AddAddress.as_view()),
    re_path(r'^addresses/$',views.AddressShow.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/$',views.Update_address.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/default/$',views.Default_Address.as_view()),
    re_path(r'^addresses/(?P<address_id>\d+)/title/$',views.SetTitle.as_view()),
    re_path(r'^password/$',views.UpdatePassword.as_view()),
]  #http://www.meiduo.site:8000/mobiles/15800239534/count/
