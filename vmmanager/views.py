# -*- coding:utf-8 -*-

from .jvm_api import *
from .models import Application, Approvel


# Create your views here.


@require_role('admin')
def VM_list(request):
    username = request.user.username
    applylist = Application.objects.filter(apply_status='SM').order_by('-id')
    apply_confirm_list = Approvel.objects.filter(
        appro_status='AP').order_by('-appro_date')
    applylist, p, applys, page_range, current_page, show_first, show_end = pages(applylist, request)

    return my_render('jvmanager/test_manage.html', locals(), request)


@require_role('admin')
def show_apply_machinedetail(request):
    """ajax获取机器详细信息"""
    if request.method == "POST":
        id = int(request.POST.get('id', ''))
        applydetail = Application.objects.filter(id=id)
        applydetail_dict = simplejson.dumps(applydetail, cls=QuerySetEncoder)
        return JsonResponse(applydetail_dict)
    else:
        error_dict = {'error': 'ajax not good'}
        return JsonResponse(error_dict)


def modify_machine_detail(request, *call_args):
    """
    修改用户单个机器详细信息
    """
    if request.method == "POST":
        request_id = int(request.POST.get('request_id', ''))
        saving_env_type = request.POST.get('saving_env_type', '')
        saving_fun_type = request.POST.get('saving_fun_type', '')
        saving_cpu_num = int(request.POST.get('saving_cpu_num', ''))
        saving_memory_num = int(request.POST.get('saving_memory_num', ''))
        saving_os_type = request.POST.get('saving_os_type', '')
        saving_data_disk = int(request.POST.get('saving_data_disk', ''))
        saving_apply_num = int(request.POST.get('saving_request_num', ''))
        saving_apply_status = 'SM'
        saving_datetime = datetime.datetime.now()
        try:
            Application.objects.filter(id=request_id).update(fun_type=saving_fun_type, os_type=saving_os_type,
                                                             cpu=saving_cpu_num, env_type=saving_env_type,
                                                             memory_gb=saving_memory_num, datadisk_gb=saving_data_disk,
                                                             request_vm_num=saving_apply_num,
                                                             apply_date=saving_datetime,
                                                             apply_status=saving_apply_status)
        except Exception, e:
            raise e
        else:
            info_dict = {'success': "ajax post successfully!"}
            return JsonResponse(info_dict)
    else:
        error_dict = {'error': 'ajax post not good!'}
        return JsonResponse(error_dict)


@require_role('admin')
def agree_apply(request):
    """
    同意申请
    """
    if request.method == "POST":
        request_id = int(request.POST.get('request_id', ''))
        application = Application.objects.get(id=request_id)
        approving_env_type = request.POST.get('confirm_env_type', '')
        approving_fun_type = request.POST.get('confirm_fun_type', '')
        approving_cpu_num = int(request.POST.get('confirm_cpu_num', ''))
        approving_memory_num = int(request.POST.get('confirm_memory_num', ''))
        approving_os_type = request.POST.get('confirm_os_type', '')
        approving_data_disk = int(request.POST.get('confirm_data_disk', ''))
        approving_apply_num = 1
        approving_status = "AP"
        approving_datetime = datetime.datetime.now()
        try:
            Application.objects.filter(id=request_id).update(apply_status=approving_status)
            confirm_apply = Approvel(application=application, appro_env_type=approving_env_type,
                                     appro_fun_type=approving_fun_type,
                                     appro_cpu=approving_cpu_num, appro_memory_gb=approving_memory_num,
                                     appro_os_type=approving_os_type, appro_datadisk_gb=approving_data_disk,
                                     appro_vm_num=approving_apply_num, appro_status=approving_status,
                                     appro_date=approving_datetime)
            confirm_apply.save()
        except Exception, e:
            raise e
        else:

            confirmlist = Approvel.objects.filter(application=application)
            list_dict = simplejson.dumps(confirmlist, cls=QuerySetEncoder)
            return JsonResponse(list_dict)
    else:
        error_dict = {'error': 'pajax post not good'}
        return JsonResponse(error_dict)


@require_role('admin')
def delete_apply(request):
    """删除申请"""
    if request.method == 'POST':
        id = int(request.POST.get("id", ""))
        reason = request.POST.get("reason", "")
        try:
            Application.objects.filter(id=id).update(apply_status='RB')
        except Exception, e:
            raise e
        else:
            success_dict = {"info": "success"}
            return JsonResponse(success_dict)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


@require_role('admin')
def agree_apply_list(request):
    """
    通过列表
    """
    pass


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
                             apply_status=apply_status, app_name=app_name, apply_reason=apply_reason,
                             apply_date=datetime.datetime.now(), user=user)
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
    applylist = Application.objects.exclude(apply_status="HD").order_by('-id')
    applylist, p, applys, page_range, current_page, show_first, show_end = pages(
        applylist, request)
    return my_render('jvmanager/resource_view.html', locals(), request)


@require_role('user')
def saving_resource_view(request):
    s_apply_list = Application.objects.filter(apply_status="HD")
    s_apply_list, p, s_applys, page_range, current_page, show_first, show_end = pages(
        s_apply_list, request)
    return my_render('jvmanager/savingresource_view.html', locals(), request)


@require_role('user')
def submit_saving_resource(request):
    """ajax提交保存资源"""
    if request.method == 'POST':
        id = int(request.POST.get('id', ''))
        try:
            Application.objects.filter(id=id).update(apply_status="SM")
        except Exception, e:
            raise e
        else:
            success_dict = {"info": "success"}
            return JsonResponse(success_dict)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)
