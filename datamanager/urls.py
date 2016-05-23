# coding:utf-8
from django.conf.urls import patterns, include, url
from datamanager.views import *

urlpatterns = patterns('',
                       url(r'^list/$', list, name='list'),
                       url(r'^post/$', post, name='post'),
                       url(r'^file_sync', file_sync, name='file_sync')
)
