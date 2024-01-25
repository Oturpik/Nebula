from django.urls import path
from . import views

urlpatterns = [
    #path('', views.index, name='index'), 
    #path('login/', views.login, name='login'),
    path('api/health-check', views.fetch_health_check, name='health_check'),
    path('api/test-db-connection', views.fetch_dbconnection_check, name='db_check'),
    path('api/students', views.fetch_students, name='all_students_list')
     
]