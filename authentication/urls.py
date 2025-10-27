from django.urls import path


urlpatterns = [
    path('logout/', logout_view, name='logout'),
]
