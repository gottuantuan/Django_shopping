from . import views

from django.conf.urls import url


urlpatterns = [
    url(r'^cart/$', views.CartViews.as_view()),
     url(r'^cart/selection/$', views.CartSelectAllView.as_view()),
]