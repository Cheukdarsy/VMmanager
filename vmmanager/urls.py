# coding:utf-8
from django.conf.urls import patterns, include, url
from vmmanager.views import *

urlpatterns = patterns('',
                       url(r'^list/$',VM_list, name='VM_list'),
                       url(r'^apply/$',apply_machine,name='apply_machine'),
                       url(r'^resource/$',resource_view,name='resource_view'),
                      )
