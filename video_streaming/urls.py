from django.urls import path
from .views import create_live_stream, view_streams, login_view, signup
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', login_view, name='login'),
    path('view-streams/', view_streams, name='view_streams'),
    path('create_stream/', create_live_stream, name='create_live_stream'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', signup, name='signup'),
]
