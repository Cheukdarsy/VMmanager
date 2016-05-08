# coding:utf-8


from jumpserver.api import *
from vmmanager.models import Approvel, Application


def db_add_userapply(**kwargs):
    """添加用戶申請或则保存信息到Application數據庫"""
    applylist = Application(**kwargs)
    applylist.save()
    return applylist

def db_add_approvel(**kwargs):
	"""添加审核（用户申请）信息到审核表"""
	approvel = Approvel(**kwargs)
	approvel.save()

def get_userapply(**kwargs):
    applylist = get_object(Application, **kwargs)
    return applylist


def db_add_confirmapply(**kwargs):
    """添加确认申请单到数据库"""
    confirm_apply = Approvel(**kwargs)
    confirm_apply.save()
    return confirm_apply