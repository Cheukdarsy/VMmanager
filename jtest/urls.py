# coding:utf-8
from django.conf.urls import patterns, include, url
from jtest.views import *

urlpatterns = patterns('',
                       url(r'^list/(\w+)/$','jtest.views.test_list', name='test_list'),
                      )
