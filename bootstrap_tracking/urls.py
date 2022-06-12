"""Alex_Tracking URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.urls import path, include
from requests import session
from core import views
from core.models import Operation, Job, Worker, Location

urlpatterns = [
    # Infrastructural
    path('admin/shell/', include('django_admin_shell.urls')),
    path('admin/', admin.site.urls),
    path('', views.Index.as_view(), name='index'),
    path('login/', views.Login.as_view(), name='login'),
    path('signout/', views.Logout.as_view(), name='signout'),

    # Main
    path('upload/', views.UploadOps.as_view(), name='upload'),
    path('uploadlocs/', views.UploadLocs.as_view(), name='uploadlocs'),
    path('mgsetup/', views.MgSetup.as_view(), name='mgsetup'),
    
    # Model-based
    path('jobs/', views.ModelView.as_view(model=Job), name='jobs'),
    path('locations/', views.ModelView.as_view(model=Location), name='locations'),
    path('workers/', views.ModelView.as_view(model=Worker), name='workers'),
    path('operations/', views.ModelView.as_view(model=Operation), name='operations'),
      
    # Detail Views
    path('operation/<slug:link_slug>', views.Op_OperationDash.as_view(), name='opdetail'),
    path('job/<slug:link_slug>', views.JobDetail.as_view(), name='jobdetail'),
    path('location/<slug:link_slug>', views.LocDetail.as_view(), name='locdetail'),
    path('worker/<slug:link_slug>', views.WorkerDetail.as_view(), name='workerdetail'),
    
    #Operator Dashboard Views
    path('operation/', views.Op_OperationDash.as_view(), name='operation'),
    path('machine/', views.Op_MachineView.as_view(), name='machine'),
    path('factory/', views.Op_FactoryFloor.as_view(), name='factory'),

    path('generic/', views.GenericView.as_view(), name='generic'),


    # Templates/ Placeholders
    #path('operator/', views.OperatorDash.as_view(), name='operator'),
    #path('cards/', views.Cards.as_view(), name='cards'),
    #path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
]
