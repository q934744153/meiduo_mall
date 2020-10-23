from django.urls import path,re_path
from . import views
urlpatterns = [
    path('usernames/<username:username>/count/',views.UsernameCountView.as_view()),
    path('mobiles/<mobile:mobile>/count/',views.MobileCountView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/',views.LoginView.as_view()),
]  #http://www.meiduo.site:8000/mobiles/15800239534/count/