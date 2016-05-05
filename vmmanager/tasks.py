from celery import task
from pyVmomi import vim

from .models import VirtualMachine
from .vc_api import clone_vm, vim_vm_reconfig, vim_vm_poweron, get_obj


@task
def vmtask_trace(vmtask, vmorder, begin_per=0, weight=100, parse_result=False, nexttask=None):
    status = vmtask.info.state
    if status == 'running':
        vmorder.vm_gen_progress = begin_per + vmtask.info.progress * weight / 100
        vmorder.save(update_fields=['vm_gen_progress'])
        return vmtask_trace.apply_async((vmtask, vmorder, weight, parse_result), countdown=1)
    elif status == 'success':
        vmorder.vm_gen_progress = begin_per + weight
        vmtask_name = vmtask.info.name
        period_log = vmtask_name + " : Succeed.\n"
        vmorder.vm_gen_log += period_log
        vmorder.save(update_fields=['vm_gen_progress', 'vm_gen_log'])
        if isinstance(nexttask, tuple):
            task_fun = nexttask[0]
            if hasattr(nexttask, '__call__'):
                kwargs = nexttask[1]
                if parse_result:
                    task_fun(from_result=vmtask.info.result, **kwargs)
                else:
                    task_fun(**kwargs)
    elif status == 'error':
        pass


@task
def vmtask_vm_reconfig(vmorder, from_result=None, virtualmachine=None, begin_per=0, weight=100, parse_result=False,
                       nexttask=None):
    if from_result:
        vim_vm = from_result
    elif isinstance(virtualmachine, VirtualMachine):
        content = virtualmachine.vcenter.connect()
        vim_vm = get_obj(content, vimtype=[vim.VirtualMachine], moid=str(virtualmachine.moid))
    else:
        print("No vm to reconfig")
        return
    application = vmorder.approvel.application
    annotation_username = application.user.get_full_name()
    annotation = str(annotation_username) + str(' - ') + str(application.apply_reason)
    templ = vmorder.src_template
    order_cpu = vmorder.approvel.appr_cpu_cores
    templ_cpu = templ.cpu_cores * templ.cpu_num
    adjust_cpu = (order_cpu == templ_cpu)
    order_mem = vmorder.approvel.appr_mem_gb
    templ_mem = round(float(templ.memory_mb) / 1024)
    adjust_mem = (order_mem == templ_mem)
    order_disk = vmorder.approvel.appr_disk_gb if vmorder.approvel.appr_disk_gb else 0
    adjust_disk = (order_disk == 0)
    kwargs = {}
    if adjust_cpu:
        if order_cpu % 2 == 0:
            tg_cpu_num = order_cpu / 2
            tg_cpu_cores = 2
        else:
            tg_cpu_num = order_cpu
            tg_cpu_cores = 1
        kwargs['tg_cpu_num'] = tg_cpu_num
        kwargs['tg_cpu_cores'] = tg_cpu_cores
    if adjust_mem:
        tg_mem_mb = order_mem * 1024
        kwargs['tg_mem_mb'] = tg_mem_mb
    if adjust_disk:
        kwargs['tg_datadisk_gb'] = order_disk
    reconfig_task, errmsg = vim_vm_reconfig(vim_vm, tg_annotation=annotation, **kwargs)
    vmtask_trace(reconfig_task, vmorder, begin_per=begin_per, weight=weight,
                 nexttask=(vim_vm_poweron, {'vim_vm': vim_vm}))


@task
def vmtask_clone_vm(vmorder, begin_per=0, weight=100, parse_result=False, nexttask=None):
    template = vmorder.src_template
    content = template.vcenter.connect()

    order_cpu = vmorder.approvel.appr_cpu_cores
    templ_cpu = template.cpu_cores * template.cpu_num
    adjust_cpu = (order_cpu == templ_cpu)

    order_mem = vmorder.approvel.appr_mem_gb
    templ_mem = round(float(template.memory_mb) / 1024)
    adjust_mem = (order_mem == templ_mem)

    order_disk = vmorder.approvel.appr_disk_gb if vmorder.approvel.appr_disk_gb else 0
    adjust_disk = (order_disk == 0)

    clone_task, errmsg = clone_vm(content, vmorder.src_template, vmorder.loc_hostname, vmorder.loc_ip,
                                  vmorder.loc_storage,
                                  vmorder.loc_cluster, vmorder.loc_resp)
    vmtask_trace(clone_task, vmorder, begin_per=0, weight=60, parse_result=True,
                 nexttask=(vmtask_vm_reconfig, {'vmorder': vmorder, 'begin_per': 60, 'weight': 40}))
