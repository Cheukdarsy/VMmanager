# -*- coding:utf-8 -*-

from .jvm_api import *
from .tasks import vmtask_clone_vm
from .vc_api import *


# Create your views here.


@require_role('admin')
def VM_list(request):
    username = request.user.username
    applylist = Approvel.objects.filter(appro_status='AI').order_by('-id')
    apply_confirm_list = Approvel.objects.filter(
        appro_status='AP').order_by('-appro_date')
    vmorder = VMOrder.objects.all()
    applylist, p, applys, page_range, current_page, show_first, show_end = pages(applylist, request)

    return my_render('jvmanager/test_manage.html', locals(), request)


@require_role('user')
def show_apply_machinedetail(request):
    """ajax获取申请机器详细信息"""
    if request.method == "POST":
        id = int(request.POST.get('id', ''))
        applydetail = Application.objects.filter(id=id)
        applydetail_dict = simplejson.dumps(applydetail, cls=QuerySetEncoder)

        return JsonResponse(applydetail_dict)
    else:
        error_dict = {'error': 'ajax not good'}
        return JsonResponse(error_dict)

@require_role('admin')
def show_approv_machinedetail(request):
    """ajax获取审核机器详细信息"""
    if request.method == "POST":
        id = int(request.POST.get('id', ''))
        approvdetail = Approvel.objects.filter(id=id)
        approvdetail_dict = simplejson.dumps(approvdetail, cls=QuerySetEncoder)
        return JsonResponse(approvdetail_dict)
    else:
        error_dict = {'error': 'ajax not good'}
        return JsonResponse(error_dict)

@require_role('user')
def modify_saving_detail(request):
    if request.method == "POST":
        id = request.POST.get("request_id",'')
        env_type = request.POST.get('env_type', '')
        fun_type = request.POST.get('fun_type', '')
        cpu = int(request.POST.get('cpu', ''))
        memory_gb = int(request.POST.get('memory', ''))
        os_type = request.POST.get('os_type', '')
        datadisk_gb = int(request.POST.get('data_volume', ''))
        request_vm_num = int(request.POST.get('request_num', ''))
        apply_reason = request.POST.get('apply_reason', '')
        app_name = request.POST.get('app_name', '')
        try:
            application = Application.objects.filter(pk=id)
            application.update(env_type=env_type,fun_type=fun_type,cpu=cpu,memory_gb=memory_gb,os_type=os_type,datadisk_gb=datadisk_gb,request_vm_num=request_vm_num,app_name=app_name,apply_reason=apply_reason)
        except Exception, e:
            raise e
        else:
            success_dict = {'success': 'update'}
            return JsonResponse(success_dict)

@require_role('admin')
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
        saving_apply_status = 'AI'
        saving_datetime = datetime.now()
        try:
            Approvel.objects.filter(id=request_id).update(appro_fun_type=saving_fun_type,
                                                                      appro_os_type=saving_os_type,
                                                                      appro_cpu=saving_cpu_num,
                                                                      appro_env_type=saving_env_type,
                                                                      appro_memory_gb=saving_memory_num,
                                                                      appro_datadisk_gb=saving_data_disk,
                                                                      appro_vm_num=saving_apply_num,
                                                                      appro_date=saving_datetime,
                                                                      appro_status=saving_apply_status)
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
        approvel_id = int(request.POST['approvel_id'])
        vm_num = int(request.POST['vm_num'])
        assign_data = json.loads(request.POST['assign_data'])
        if not isinstance(assign_data, list) or vm_num != len(assign_data):
            raise Exception("Accepted data illegal")
        try:
            approvel = Approvel.objects.get(id=approvel_id)
            env_type = approvel.appro_env_type
            os_type = approvel.appro_os_type
            src_template = Template.match(env_type=env_type, os_type=os_type)[0]
            for each_order in assign_data:
                loc_ip = IPUsage.objects.get(ipaddress=each_order['ipaddress'])
                loc_hostname = str(each_order['vmname'])
                loc_cluster = ComputeResource.objects.get(pk=int(each_order['cluster']))
                loc_storage = Datastore.objects.get(pk=int(each_order['storage']))
                loc_resp = ResourcePool.objects.get(pk=int(each_order['resourcepool']))
                VMOrder.objects.create(approvel=approvel, loc_ip=loc_ip, loc_hostname=loc_hostname,
                                       loc_cluster=loc_cluster, loc_storage=loc_storage,
                                       loc_resp=loc_resp, src_template=src_template)
                loc_ip.get_occupy()
            approvel.appro_date = datetime.now()
            approvel.appro_status = "AP"
            approvel.save(update_fields=['appro_date', 'appro_status'])
        except Exception, e:
            logger.error(e)
            raise e
        else:
            success_dict = {"info": "success"}
            return JsonResponse(success_dict)
    else:
        error_dict = {'error': 'pajax post not good'}
        return JsonResponse(error_dict)


@require_role('admin')
def delete_apply(request):
    """删除申请"""
    if request.method == 'POST':
        id = int(request.POST.get("id", ""))
        application_id = int(request.POST.get("application_id", ""))
        reason = request.POST.get("reason", "")
        try:
            Approvel.objects.filter(id=id).update(approv_status='RB')
            Application.objects.filter(id=application_id).update(apply_status='RB', apply_reason=reason)
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


@require_role('admin')
def ajax_get_agree_form(request):
    agree_form = []
    if request.method == 'POST':
        pk = request.POST.get('id', '')
        try:
            agree_form = Approvel.objects.filter(application_id=pk)

        except Exception, e:
            raise e
        else:
            return JsonResponse(simplejson.dumps(agree_form, cls=QuerySetEncoder))
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


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
        submitt = request.POST.get('submit', '')
        if submitt == 'submit':
            apply_status = "SM"
            try:
                application = db_add_userapply(env_type=env_type, fun_type=fun_type, cpu=cpu, memory_gb=memory,
                                               os_type=os_type,
                                               datadisk_gb=data_disk, request_vm_num=request_num,
                                               apply_status=apply_status, apply_reason=apply_reason,
                                               apply_date=datetime.now(), user=user)
                db_add_approvel(application=application, appro_env_type=env_type, appro_fun_type=fun_type,
                                appro_cpu=cpu, appro_memory_gb=memory, appro_os_type=os_type,
                                appro_datadisk_gb=data_disk, appro_vm_num=request_num, appro_status='AI',
                                appro_date=datetime.now())

            except ServerError:
                pass
            else:
                return HttpResponseRedirect(reverse('resource_view'))
        else:
            apply_status = "HD"
            try:
                application = db_add_userapply(env_type=env_type, fun_type=fun_type, cpu=cpu, memory_gb=memory,
                                               os_type=os_type,
                                               datadisk_gb=data_disk, request_vm_num=request_num,
                                               apply_status=apply_status, apply_reason=apply_reason,
                                               apply_date=datetime.now(), user=user)
            except Exception, e:
                raise e
            else:
                return HttpResponseRedirect(reverse('saving_resource_view'))
    return my_render('jvmanager/apply_machine.html', locals(), request)


@require_role(role='user')
def resource_view(request):
    """
    用户资源概览
    """
    username = request.user.username
    user=get_object(User,username=username)
    applylist = Application.objects.exclude(apply_status="HD").filter(user=user).order_by('-id')
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


@require_role('admin')
def set_vm(request):
    vcenter = VCenter.objects.all()
    ipusage = IPUsage.objects.all().order_by("-id")
    templates = Template.objects.all()
    envs = SheetField.objects.filter(field_name="env_type")
    os = SheetField.objects.filter(field_name="os_type")
    return my_render('jvmanager/set_vm.html', locals(), request)


def generate_machine(request):
    """
    前端返回一个ID列表{json}，然后根据ID去approv表获取相关参数生成机器，包括台数等
    """
    if request.method == 'POST':
        idlist = str(request.POST.get('id', ''))
        id = [int(x) for x in idlist.split(',')]
        try:
            for x in id:
                vmorder = VMOrder.objects.get(pk=x)
                if not vmorder.gen_status:
                    vmtask_clone_vm.delay(vmorder)
        except Exception, e:
            raise e
        else:
            success_dict = {"info": "success"}
            return JsonResponse(success_dict)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_get_process(request):
    """
    根据ID列表获取生成进度
    """
    if request.method == 'POST':
        result_list = []
        idlist = str(request.POST.get('id', ''))
        id = [int(x) for x in idlist.split(',')]
        try:
            for x in id:
                vmorder = VMOrder.objects.get(pk=x)
                if vmorder.gen_status:
                    result_list.append({'id': x, 'progress': vmorder.gen_progress, 'log': vmorder.gen_log,
                                        'status': vmorder.gen_status})
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_get_generatestatus():
    """
    根据ID列表获取生成日志
    """
    pass


def ajax_get_template():
    """
        前端返回cluster名称clustername，获取对应的template
        """
    pass


def ajax_get_cluster(request):
    """
    动态获取集群信息，需返回所有可用集群名称以及权重比(CPU+内存+存储)
    参数对照
        id: Approvel id审批表ID
    返回每个条目的字段对照
        集群ID           'cluster_id': clus.id,
        集群名称         'cluster_name': clus.name,
        集群主机数       'host_num': hostnum,
        CPU剩余百分比    'free_cpu': clus.free_cpu(),
        内存剩余百分比   'free_memory': clus.free_mem(),
        集群LUN数        'ds_num': len(stor_capi),
        LUN剩余百分比    'free_space': stor_capi_percent
    """
    if request.method == 'POST':
        approvel_id = int(request.POST['id'])
        try:
            approvel = Approvel.objects.get(pk=approvel_id)
            env_type = approvel.appro_env_type
            result_list = get_capi_cluster(env_type)
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_get_resource(request):
    """
    获取资源池名称
    参数对照POST
        id: cluster id集群id
    返回每个条目的字段对照
        资源池ID        'resp_id':resp.id,
        资源池名称      'resp_name':resp.name
    """
    if request.method == 'POST':
        cluster_id = int(request.POST['id'])
        try:
            cluster = ComputeResource.objects.get(pk=cluster_id)
            resp_set = cluster.resourcepool_set.filter(parent__isnull=False)
            result_list = []
            for resp in resp_set:
                result_list.append({
                    'resp_id': resp.id,
                    'resp_name': resp.name
                })
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_get_storage(request):
    """
    获取相关集群的剩余容量，需返回剩余容量值及百分比
    参数对照POST
        id: cluster id集群id
    返回每个条目的字段对照
        存储ID          'datastore_id': ds.id,
        存储名称        'datastore_name': ds.name,
        剩余容量GB      'free_space_gb': ds.free_space_mb / 1024,
        总容量GB        'total_space_gb': ds.total_space_mb / 1024,
        剩余百分比      'free_percent': ds.free_space_mb * 100 / ds.total_space_mb
    """
    if request.method == 'POST':
        cluster_id = int(request.POST['id'])
        try:
            cluster = ComputeResource.objects.get(pk=cluster_id)
            result_list = get_capi_datastore(cluster)
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


# VM参数配置页面

def ajax_initial_network(request):
    """
    初始化网络IP池
    参数对照POST
        net_id: 网络ID
        net_addr: 网络地址
        net_mask: 掩码位数
        gw_addr: 网关地址
    """
    if request.method == 'POST':
        net_id = int(request.POST['net_id'])
        net_addr = request.POST['network']
        net_mask = int(request.POST['net_mask'])
        gw_addr = request.POST['netgate']
        try:
            network = Network.objects.get(pk=net_id)
            network.update_manual(nw=net_addr, mask=net_mask)
            gw, countip = IPUsage.create(network, gw_addr=gw_addr)
        except Exception, e:
            raise e
        else:
            return countip
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_select_IP(request):
    """
    选取IP和VMNAME
    参数对照POST
        id: Approvel id审批表ID
        num: 需要获取的IP数量(可选,默认为所有,单独选取为1)
    返回每个条目的字段对照[dict]
        IP地址         'ipaddress': ipaddress,
        虚拟机名称     'vmname': vmname
    """
    if request.method == 'POST':
        approvel_id = int(request.POST['id'])
        try:
            approvel = Approvel.objects.get(pk=approvel_id)
            env_type = approvel.appro_env_type
            os_type = approvel.appro_os_type
            if request.POST.has_key('num'):
                vm_num = int(request.POST['num'])
            else:
                vm_num = approvel.appro_vm_num
            result_list = select_ip_and_vmname(env_type, os_type, vm_num)
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def ajax_select_template(request):
    """
    选取IP和VMNAME
    参数对照POST
        id: Approvel id审批表ID
    返回每个条目的字段对照[dict]
    """
    if request.method == 'POST':
        approvel_id = int(request.POST['id'])
        try:
            approvel = Approvel.objects.get(pk=approvel_id)
            env_type = approvel.appro_env_type
            os_type = approvel.appro_os_type
            result_list = select_template(env_type=env_type, os_type=os_type)
        except Exception, e:
            raise e
        else:
            return JsonResponse(result_list)
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)


def get_templates():
    """
    获取所有模板信息
    返回每个条目的字段对照
        环境类型       'env_type':templ.env_type,
        系统类型       'os_type':templ.os_type,
        虚拟机ID       'vmid':templ.virtualmachine_id,
        虚拟机名称     'vmname':templ.virtualmachine.name,
        虚拟机备注     'vm_anno':templ.virtualmachine.annotation
    """
    result_list = []
    try:
        # Return all templates
        for templ in Template.objects.all():
            result_list.append({
                'env_type': templ.env_type,
                'os_type': templ.os_type,
                'vmid': templ.virtualmachine_id,
                'vmname': templ.virtualmachine.name,
                'vm_anno': templ.virtualmachine.annotation
            })
    except Exception, e:
        raise e
    else:
        return json.dumps(result_list)


def ajax_add_template(request):
    """
    配置虚拟机模板
    参数对照POST
        vmid: 虚拟机ID
        os_typee: 操作系统类型
        env_type: 环境类型(开发、测试、生产、灾备)
    返回每个条目的字段对照
        环境类型       'env_type':templ.env_type,
        系统类型       'os_type':templ.os_type,
        虚拟机ID       'vmid':templ.virtualmachine_id,
        虚拟机名称     'vmname':templ.virtualmachine.name,
        虚拟机备注     'vm_anno':templ.virtualmachine.annotation
    """
    if request.method == 'POST':
        vmid = int(request.POST['vmid'])
        virtualmachine = VirtualMachine.objects.get(pk=vmid)
        os_type = str(request.POST['os_type'])
        env_type = str(request.POST['env_type'])
        try:
            template = Template(virtualmachine=virtualmachine, env_type=env_type)
            os_versions = SheetField.get_options(field='os_version', sheet='os_type_' + str(os_type))
            if os_versions.exists():
                try:
                    SheetField.add_option(virtualmachine.guestos_shortname, virtualmachine.guestos_fullname,
                                          field='os_version', sheet='os_type_' + str(os_type))
                except:
                    pass
            else:
                raise Exception("os_type not exist, please add it first!")
            template.save()

        except Exception, e:
            raise e
        else:
            # Return all templates
            return get_templates()
    else:
        error_dict = {"error": "ajax not good"}
        return JsonResponse(error_dict)

"""vc参数"""
def ajax_add_vc(request):
    if request.method == 'POST':
        ip = request.POST['vcip']
        port = request.POST['vcport']
        vcname = request.POST['vcname']
        vcpw = request.POST['vcpw-conf']
        env = {}
        env_type = SheetField.objects.filter(field_name="env_type")
        for x in env_type:
            if x.option in request.POST:
                env[x.option] = True

        try:
            vcenter = VCenter(ip=ip,port=port,env_type=env,user=vcname,password=vcpw)
            vcenter.save()
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "ok"})

def ajax_modify_vc(request):
    if request.method == "POST":
        logger.debug(request.POST)
        id = request.POST['id']
        ip = request.POST['vcip']
        port = request.POST['vcport']
        vcname = request.POST['vcname']
        vcpw = request.POST['vcpw']
        env = {}
        env_type = SheetField.objects.filter(field_name="env_type")
        for x in env_type:
            if x.option in request.POST:
                env[x.option] = True
        try:
            VCenter.objects.filter(id=id).update(ip=ip,port=port,env_type=env,user=vcname,password=vcpw)
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "ok"})

def ajax_delete_vc(request):
    if request.method == "POST":
        id = request.POST['id']
        try:
            del_vc = VCenter.objects.filter(id=id)
            del_vc.delete()
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "delete successfully"})

"""网络参数"""
def ajax_get_initial_ip(request):
    if request.method == "POST":
        net_list = []
        try:
            for net in Network.objects.all():
                net_list.append({
                    "id":net.id,
                    "net_name":net.name,
                    "net":net.net
                    })
        except Exception, e:
            raise e
        else:
            return JsonResponse(net_list)

def ajax_add_ip(request):
    if request.method == "POST":
        network_name = request.POST['r-network']
        ipaddress = request.POST['ipaddress']
        ipusage = int(request.POST['netusage'])
        gw_addr = request.POST['gw_addr']
        judge = False
        if ipusage == 1:
            judge = True
        else:
            judge = False

        network = Network.objects.filter(name=network_name)
        logger.debug(request.POST)
        try:
            ipuse = IPUsage.create(network=network,ipaddress=ipaddress)
            logger.debug("hello")
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "ok"})

"""环境参数"""
def ajax_add_env(request):
    if request.method == 'POST':
        
        env_option = request.POST['env_option']
        env_type = request.POST['env_type']  
        logger.debug(request.POST)  
        try:
            sheetfield = SheetField(sheet_name="global",field_name="env_type",option=env_option,option_display=env_type)
            sheetfield.save()
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "ok"})

def ajax_update_env(request):
    if request.method == 'POST':
        logger.debug(request.POST)  
        id = request.POST['id']
        env_option = request.POST['env_option']
        env_type = request.POST['env_type']

        try:
            SheetField.objects.filter(id=id).update(option=env_type,option_display=env_option)
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success": "ok"})


def ajax_delete_env(request):
    if request.method == "POST":
        id = int(request.POST['id'])
        logger.debug(id)
        try:
            del_env = SheetField.objects.filter(id=id)
            del_env.delete()
        except Exception, e:
            raise e
        else:
            return JsonResponse({"success":"delete successfull"})


def datamanager(request):
    return my_render('datamanager.html', locals(), request)