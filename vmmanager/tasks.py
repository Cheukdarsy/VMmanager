from celery import task
from pyVmomi import vim

from .vc_api import *


@task
def vmtask_trace(vcid, vmtaskid, vmorder=None, begin_per=0, weight=100, parse_result=False, retry=5, nexttask=None):
    vc = VCenter.objects.get(pk=vcid)
    content = vc.connect()
    vmtask = get_task(content, vmtaskid)
    if not vmtask:
        return vmtask_trace.delay(vcid, vmtaskid, vmorder, begin_per, weight, parse_result, retry - 1, nexttask)
    status = vmtask.info.state
    if not vmorder:
        print("Status: " + str(status))
        if status == 'running':
            return vmtask_trace.delay(vcid, vmtaskid, vmorder, begin_per, weight, parse_result, retry - 1, nexttask)
    if status == 'running':
        vmorder.gen_progress = begin_per + vmtask.info.progress * weight / 100
        vmorder.save(update_fields=['gen_progress'])
        return vmtask_trace.apply_async((vcid, vmtaskid, vmorder, begin_per, weight, parse_result, 5, nexttask),
                                        countdown=3)
    elif status == 'success':
        vmorder.gen_progress = begin_per + weight
        vmtask_name = vmtask.info.descriptionId
        period_log = vmtask_name + " : Succeed."
        vmorder.add_log(period_log)
        vmorder.save(update_fields=['gen_progress', 'gen_log'])
        if isinstance(vmtask.info.result, vim.VirtualMachine):
            result_vm, create = VirtualMachine.create_or_update_by_vim(vmtask.info.result, vc, related=False)
        else:
            result_vm = None
        if isinstance(nexttask, tuple):
            task_fun = nexttask[0]
            if hasattr(task_fun, '__call__'):
                kwargs = nexttask[1]
                if parse_result and result_vm:
                    task_fun.delay(from_result=result_vm, **kwargs)
                else:
                    task_fun.delay(**kwargs)
            else:
                raise Exception("next task illegal")
        elif not nexttask:
            vmorder.gen_status = 'SUCCESS'
            vmorder.save(update_fields=['gen_status'])
        else:
            raise Exception("Invalid nexttask!")
    elif status == 'error':
        vmorder.gen_status = 'FAILED'
        vmtask_name = vmtask.info.descriptionId
        period_log = vmtask_name + " : Failed."
        vmorder.add_log(period_log)
        vmorder.save(update_fields=['gen_status', 'gen_log'])


@task
def vmtask_poweron_vm(vmorder, virtualmachine):
    # host = None
    # if virtualmachine.resourcepool:
    #     clus = virtualmachine.resourcepool.owner
    #     if isinstance(clus,ComputeResource):
    #         for host in clus.hostsystem_set.all():
    #             pass
    result, msg = poweron_vm(virtualmachine)
    if result:
        vmorder.gen_status = 'SUCCESS'
        vmorder.add_log("Power On the VM : Succeed.")
        vmorder.gen_time = datetime.now()
    else:
        vmorder.gen_status = 'FAILED'
        vmorder.add_log("Power On the VM : Failed.\nMsg: " + msg)
    vmorder.save()


@task
def vmtask_reconfig_vm(vmorder, from_result=None, virtualmachine=None, begin_per=0, weight=100, parse_result=False,
                       nexttask=None):
    if from_result and isinstance(from_result, VirtualMachine):
        virtualmachine = from_result
    if isinstance(virtualmachine, VirtualMachine):
        vcid = virtualmachine.vcenter_id
        content = virtualmachine.vcenter.connect()
        vim_vm = get_obj(content, vimtype=[vim.VirtualMachine], moid=str(virtualmachine.moid))
    else:
        print("No vm to reconfig")
        return
    application = vmorder.approvel.application
    annotation_username = application.user.get_full_name()
    annotation = str(annotation_username) + str(' - ') + str(application.apply_reason)
    templ = vmorder.src_template
    order_cpu = vmorder.approvel.appro_cpu
    templ_cpu = templ.cpu_cores * templ.cpu_num
    adjust_cpu = (order_cpu != templ_cpu)
    order_mem = vmorder.approvel.appro_memory_gb
    templ_mem = round(float(templ.memory_mb) / 1024)
    adjust_mem = (order_mem != templ_mem)
    order_disk = vmorder.approvel.appro_datadisk_gb if vmorder.approvel.appro_datadisk_gb else 0
    adjust_disk = (order_disk != 0)
    kwargs = {}
    if adjust_cpu:
        if order_cpu % 2 == 0:
            tg_cpu_num = order_cpu
            tg_cpu_cores = order_cpu / 2
        else:
            tg_cpu_num = order_cpu
            tg_cpu_cores = order_cpu
        kwargs['tg_cpu_num'] = tg_cpu_num
        kwargs['tg_cpu_cores'] = tg_cpu_cores
    if adjust_mem:
        tg_mem_mb = order_mem * 1024
        kwargs['tg_mem_mb'] = tg_mem_mb
    if adjust_disk:
        kwargs['tg_datadisk_gb'] = order_disk
    reconfig_taskid, errmsg = vim_vm_reconfig(vim_vm, tg_annotation=annotation, **kwargs)
    vmtask_trace.delay(vcid, reconfig_taskid, vmorder, begin_per=begin_per, weight=weight,
                       nexttask=(vmtask_poweron_vm, {'vmorder': vmorder, 'virtualmachine': virtualmachine}))


@task
def vmtask_clone_vm(vmorder, begin_per=0, weight=100, parse_result=False, nexttask=None):
    template = vmorder.src_template
    vcid = template.vcenter_id
    content = template.vcenter.connect()

    order_cpu = vmorder.approvel.appro_cpu
    templ_cpu = template.cpu_cores * template.cpu_num
    adjust_cpu = (order_cpu == templ_cpu)

    order_mem = vmorder.approvel.appro_memory_gb
    templ_mem = round(float(template.memory_mb) / 1024)
    adjust_mem = (order_mem == templ_mem)

    order_disk = vmorder.approvel.appro_datadisk_gb if vmorder.approvel.appro_datadisk_gb else 0
    adjust_disk = (order_disk == 0)

    clone_taskid, errmsg = clone_vm(content, vmorder.src_template, vmorder.loc_hostname, vmorder.loc_ip,
                                    vmorder.loc_storage,
                                    vmorder.loc_cluster, vmorder.loc_resp)
    vmorder.gen_status = 'RUNNING'
    vmorder.save(update_fields=['gen_status'])
    vmtask_trace.delay(vcid, clone_taskid, vmorder, begin_per=0, weight=60, parse_result=True,
                       nexttask=(vmtask_reconfig_vm, {'vmorder': vmorder, 'begin_per': 60, 'weight': 40}))


@task
def vctask_create_cluster(vcid, cluster_name, dc_name=None):
    content = VCenter.objects.get(pk=vcid).connect()
    if content:
        print(vim_create_cluster(content, cluster_name, dc_name))
