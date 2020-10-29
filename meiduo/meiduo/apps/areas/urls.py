from  django.urls import re_path,path
from . import views


urlpatterns = [
    re_path(r'^areas/$',views.ProvinceAreasView.as_view()),
    path('areas/<int:pk>/',views.SubAreaView.as_view()),

]