from django.contrib import admin
from django.urls import path

from authentication.views import login_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),

]
