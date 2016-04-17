# coding:utf-8


from jumpserver.api import *
from jVM.models import userapply


def db_add_userapply(**kwargs):
    """添加用戶申請到數據庫"""
    applylist = userapply(**kwargs)
    applylist.save()


def get_userapply(**kwargs):
    applylist = get_object(userapply, **kwargs)
    return applylist

def db_add_confirmapply(**kwargs):
	"""添加确认申请单到数据库"""
	confirm_apply = userapply_confirm(**kwargs)
	confirm_apply.save()