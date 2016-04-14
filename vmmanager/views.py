#-*- coding:utf-8 -*-

from jumpserver.api import *
from jumpserver.models import Setting
from vmmanager.models import Application, Approvel
from juser.models import User
from vmmanager.jvm_api import *
from django.db.models import Q
import datetime

# Create your views here.


@require_role('admin')
def VM_list(request):
    username = request.user.username
    applylist = Application.objects.filter(apply_status='SM')
    apply_confirm_list = Approvel.objects.filter(appro_status='AP')
    return my_render('jvmanager/test_manage.html', locals(), request)


@require_role(role='user')
def apply_machine(request):
    """
    用户申请机器
    """
    username = request.user.username
    user = get_object(User, username=username)

    if request.method == 'POST':
        env_type = request.POST.get('env_type', '')
        fun_type = request.POST.get('fun_type', '')
        cpu = int(request.POST.get('cpu', ''))
        memory = int(request.POST.get('memory', ''))
        os_type = request.POST.get('os_type', '')
        data_disk = int(request.POST.get('data_disk', ''))
        request_num = int(request.POST.get('request_num', ''))
        apply_reason = request.POST.get('apply_reason', '')
        app_name = request.POST.get('app_name', '')
        submitt = request.POST.get('submit', '')
        if submitt == 'submit':
            apply_status = "SM"
        else:
            apply_status = "HD"

        try:
            db_add_userapply(env_type=env_type, fun_type=fun_type, cpu=cpu, memory_gb=memory, os_type=os_type,
                             datadisk_gb=data_disk, request_vm_num=request_num,
                             apply_status=apply_status, app_name=app_name, apply_reason=apply_reason, apply_date=datetime.datetime.now(), user=user)
        except ServerError:
            pass
        else:
            return HttpResponseRedirect(reverse('resource_view'))

    return my_render('jvmanager/apply_machine.html', locals(), request)


@require_role(role='user')
def resource_view(request):
    """
    用户资源概览
    """
    username = request.user.username
    applylist = Application.objects.all()

    return my_render('jvmanager/resource_view.html', locals(), request)
