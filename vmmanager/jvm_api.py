# coding:utf-8


from jumpserver.api import *
from vmmanager.models import Application


def db_add_userapply(**kwargs):
    """添加用戶申請到數據庫"""
    applylist = Application(**kwargs)
    applylist.save()


def get_userapply(**kwargs):
    applylist = get_object(Application, **kwargs)
    return applylist
