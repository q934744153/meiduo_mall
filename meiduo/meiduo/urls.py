"""meiduo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.urls import register_converter
from meiduo.utils import converters


register_converter(converters.UsernameConverters,'username')
register_converter(converters.MobileConverter,'mobile')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('',include('users.urls')),
    path('',include('verification.urls')),
    path('',include('oauth.urls')),
    path('',include(('areas.urls'))),
]
