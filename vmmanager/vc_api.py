# coding: utf-8

"""
Python program for VCenter Operations
"""
import time

from pyVmomi import vim

from jumpserver.settings import TIME_ZONE, DNS_LIST
from .models import *

_typeMap = {
    vim.ComputeResource: ComputeResource,
    vim.ResourcePool: ResourcePool,
    vim.Network: Network,
    vim.Datastore: Datastore,
    vim.HostSystem: HostSystem,
    vim.VirtualMachine: VirtualMachine
}


def _map_vimtype(vmtype):
    for k, v in _typeMap.items():
        if v == vmtype:
            return k


def _map_vmtype(vimtype):
    return _typeMap[vimtype]


def _refresh_vim_objs(model, content, *args, **kwargs):
    """
    update all VirtualMachine
    @param content: the service content of VCenter.
    @param related: weather to update the relationship between assets
    """

    if model not in _typeMap.keys():
        return False
    vc = VCenter.objects.get(uuid=content.about.instanceUuid)
    if kwargs.has_key('container'):
        container = kwargs.pop('container')
        if not isinstance(container, vim.ManagedEntity):
            logger.warning("Not a valid container entity, using rootFolder as default...")
            container = content.rootFolder
    else:
        container = content.rootFolder

    # discover or update model
    vimView = content.viewManager.CreateContainerView(container, [model], True)
    updList = []
    for obj in vimView.view:
        updList.append(obj._GetMoId())
        _map_vmtype(model).create_or_update_by_vim(obj, vc, *args, **kwargs)
    # delete invalid objects
    qset = _map_vmtype(model).objects.filter(vcenter=vc)
    if qset.count() > len(updList):
        for obj in qset:
            if obj.moid not in updList:
                print("Delete invalid obj: " + str(obj.moid))
                obj.delete()
    vimView.Destroy()
    return True


def get_obj(content, container=None, vimtype=list(), name='', moid=''):
    """
    Return an object by name, if name is None the
    first found object is returned
    """
    if container == None:
        container = content.rootFolder
    objView = content.viewManager.CreateContainerView(container, vimtype, True)
    obj = None
    for c in objView.view:
        if name:
            if c.name == name:
                obj = c
                break
        elif moid:
            if c._GetMoId() == moid:
                obj = c
                break
        else:
            obj = c
            break

    objView.Destroy()
    return obj


def refresh_all_vms(content, related=False):
    """
    update all VirtualMachine
    @param content: the service content of VCenter.
    @param related: weather to update the relationship between assets
    """
    return _refresh_vim_objs(vim.VirtualMachine, content, related)


def refresh_some_vms(vmobject, related=False):
    vmtype = type(vmobject)
    if vmtype in [ComputeResource, ResourcePool, Datastore, HostSystem]:
        vimtype = _map_vimtype(vmtype)
        content = vmobject.vcenter.connect()
        container = get_obj(content, vimtype=[vimtype], moid=vmobject.getMoid())
        return _refresh_vim_objs(vim.VirtualMachine, content, container=container, related=related)
    else:
        return False


def refresh_all_assets(content, related=False):
    """
    update all assets including ComputeResource, ResourcePool, Network, Datastore, Hostsystem
    @param content: the service content of VCenter.
    @param related: weather to update the relationship between assets
    """
    successList = []
    if _refresh_vim_objs(vim.ComputeResource, content):
        successList.append('ComputeResource')

    if _refresh_vim_objs(vim.Network, content):
        successList.append('Network')

    if _refresh_vim_objs(vim.Datastore, content):
        successList.append('Datastore')

    if _refresh_vim_objs(vim.ResourcePool, content, related=related):
        successList.append('ResourcePool')

    if _refresh_vim_objs(vim.HostSystem, content, related=related):
        successList.append('HostSystem')


def _is_ipv4(ipstr):
    ipstr = str(ipstr)
    part = []
    if ipstr.count('.') == 2:
        if ipstr.split('.')[1]:
            return False
        part.append(int(ipstr.split('.')[0]))
        part.append(int(ipstr.split('.')[2]))
    elif ipstr.count('.') == 3:
        for i in range(4):
            part.append(int(ipstr.split('.')[i]))
    else:
        return False
    for i in part:
        if i < 0 or i > 255:
            return False
    return True


def refresh_ipusage(content):
    vc = VCenter.objects.get(uuid=content.about.instanceUuid)
    container = content.rootFolder
    ipusages = IPUsage.objects.all()
    # update ESXi Server IP Address
    hostlist = [host.name for host in HostSystem.objects.filter(vcenter=vc) if _is_ipv4(host.name)]
    for host in hostlist:
        qset = IPUsage.objects.filter(ipaddress=host)
        if qset.count() == 1:
            qset[0].manage('ESXi')

    # update VM IP Address
    vmlist = VirtualMachine.objects.filter(vcenter=vc)
    for vm in vmlist:
        vimobj = get_obj(content, container, [vim.VirtualMachine], moid=str(vm.moid))
        vm.update_ipusage(vimobj)


def wait_for_task(task):
    """ wait for a vCenter task to finish """
    task_done = False
    while not task_done:
        status = task.info.state
        if status == 'success':
            return True, task.info.result
        elif status == 'error':
            return False, str(task.info.error)
        time.sleep(5)


def vim_create_cluster(content, cluster_name, dc_name=None):
    dc_folder = content.rootFolder
    dc = None
    for vimobj in dc_folder.childEntity:
        if isinstance(vimobj, vim.Datacenter):
            if (not dc_name) or (vimobj.name == dc_name):
                dc = vimobj
                break
    if not dc:
        raise Exception("No DataCenter found")
    spec = vim.cluster.ConfigSpec()
    # start create cluster task
    try:
        cluster_moid = dc.hostFolder.CreateCluster(name=cluster_name, spec=spec)._GetMoId()
    except Exception, e:
        print(e)
        raise e
    return cluster_moid


def _vim_vm_poweron(vim_vm, host=None):
    if isinstance(vim_vm, vim.VirtualMachine):
        try:
            if isinstance(host, vim.HostSystem):
                return wait_for_task(vim_vm.PowerOn(host))
            else:
                return wait_for_task(vim_vm.PowerOn())
        except Exception, e:
            raise e


def poweron_vm(vm, host=None):
    content = vm.vcenter.connect()
    vim_vm = get_obj(content, vimtype=[vim.VirtualMachine], moid=vm.getMoid())

    vim_host = None
    if host:
        vim_host = get_obj(content, vimtype=[vim.HostSystem], moid=host.getMoid())
    return _vim_vm_poweron(vim_vm, vim_host)


def _vim_gen_spec_customize(is_windows, ipusage=None, hostname=None):
    custspec = vim.vm.customization.Specification()
    # ipsettings
    if ipusage:
        ipsetting = vim.vm.customization.IPSettings()
        fixip = vim.vm.customization.FixedIp()
        fixip.ipAddress = ipusage.ipaddress
        ipsetting.ip = fixip
        network = ipusage.network
        ipsetting.subnetMask = network.getmask_str()
        try:
            gateway = network.ipusage_set.get(used_manage_app='GW').ipaddress
        except:
            pass
        else:
            ipsetting.gateway = [gateway]
        if is_windows:
            ipsetting.dnsServerList = DNS_LIST
        ipadapter = vim.vm.customization.AdapterMapping()
        ipadapter.adapter = ipsetting
        custspec.nicSettingMap = [ipadapter]
    glb_ipsetting = vim.vm.customization.GlobalIPSettings()
    if not is_windows:
        pass
    if hostname and not is_windows:
        identity = vim.vm.customization.LinuxPrep()
        namegen = vim.vm.customization.FixedName()
        namegen.name = hostname
        identity.hostName = namegen
        identity.domain = hostname + '.site'
        identity.hwClockUTC = False
        identity.timeZone = TIME_ZONE
    else:
        identity = vim.vm.customization.IdentitySettings()
    custspec.globalIPSettings = glb_ipsetting
    custspec.identity = identity
    return custspec


def _vim_set_customize(vim_vm, *args, **kwargs):
    try:
        guestos = vim_vm.guest.guestFamily
    except:
        print("Cannot get guest os type")
        return -1
    if 'win' in str(guestos).lower():
        is_windows = True
    else:
        is_windows = False
    vim_vm.Customize(_vim_gen_spec_customize(is_windows, *args, **kwargs))


def _vim_vm_clone(vim_src_vm, vm_name, vim_datastore, vim_resp, ipusage, power_on=False):
    try:
        guestos = vim_src_vm.summary.config.guestId
    except:
        print("Cannot get guest os type")
        return -1
    if 'win' in str(guestos).lower():
        is_windows = True
    else:
        is_windows = False
    vm_folder = vim_src_vm.parent
    while (isinstance(vm_folder.parent, vim.Folder)):
        vm_folder = vm_folder.parent
    # set relospec
    relospec = vim.vm.RelocateSpec()
    relospec.datastore = vim_datastore
    relospec.pool = vim_resp
    # set clonespec
    clonespec = vim.vm.CloneSpec()
    clonespec.location = relospec
    clonespec.powerOn = power_on
    clonespec.template = False
    clonespec.customization = _vim_gen_spec_customize(is_windows, ipusage, vm_name)
    # start clone task
    try:
        taskid = vim_src_vm.Clone(folder=vm_folder, name=vm_name, spec=clonespec)._GetMoId()
    except Exception, e:
        taskid = None
        print(taskid)
        raise e
    return taskid, ""


def clone_vm(content, src_vm, vm_name, ipusage, datastore, cluster=None, resourcepool=None, power_on=False):
    task = None
    errmsg = ""
    if not isinstance(src_vm, VirtualMachine):
        errmsg = "Src_vm not a VirtualMachine instance"
        return task, errmsg
    if src_vm.vcenter.uuid != content.about.instanceUuid:
        errmsg = "Src_vm not belong to the connected vcenter"
        return task, errmsg
    # Get vim_vm_obj
    vim_src_vm = get_obj(content, vimtype=[vim.VirtualMachine], moid=str(src_vm.moid))
    # Get vim_datastore_obj
    if not datastore:
        datastore = src_vm.datastores[0]
    freespace = datastore.free_space_mb if datastore.free_space_mb else 0
    if freespace < src_vm.storage_mb * 2:
        errmsg = "Datastore not enough space!"
        return task, errmsg
    vim_datastore = get_obj(content, vimtype=[vim.Datastore], moid=str(datastore.moid))
    # Get vim_resp_obj
    if resourcepool:
        if not isinstance(resourcepool, ResourcePool):
            errmsg = "resourcepool not a ResourcePool instance"
            return task, errmsg
        vim_resourcepool = get_obj(content, vimtype=[vim.ResourcePool], moid=str(resourcepool.moid))
    elif cluster:
        if not isinstance(resourcepool, ResourcePool):
            errmsg = "cluster not a ComputeResource instance"
            return task, errmsg
        try:
            resourcepool = cluster.resourcepool_set.get(parent__isnull=True)
        except:
            errmsg = "Cannot allocate resource pool"
            return task, errmsg
        vim_resourcepool = get_obj(content, vimtype=[vim.ResourcePool], moid=str(resourcepool.moid))
    else:
        errmsg = "Neither Cluster nor ResourcePool is given as a parameter"
        return task, errmsg
    return _vim_vm_clone(vim_src_vm, vm_name, vim_datastore, vim_resourcepool, ipusage, power_on)


def _vim_gen_spec_disk(disk_size, unit_number, controller_key, thin_disk=False):
    new_disk_kb = int(disk_size) * 1024 * 1024
    disk_spec = vim.vm.device.VirtualDeviceSpec()
    disk_spec.fileOperation = "create"
    disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
    disk_spec.device = vim.vm.device.VirtualDisk()
    disk_spec.device.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
    disk_spec.device.backing.thinProvisioned = thin_disk
    disk_spec.device.backing.diskMode = 'persistent'
    disk_spec.device.unitNumber = unit_number
    disk_spec.device.capacityInKB = new_disk_kb
    disk_spec.device.controllerKey = controller_key
    return disk_spec


def vim_vm_reconfig(vim_vm, tg_annotation='', tg_cpu_num=-1, tg_cpu_cores=-1, tg_mem_mb=-1, tg_datadisk_gb=-1):
    configspec = vim.vm.ConfigSpec()
    if tg_annotation:
        configspec.annotation = tg_annotation
    if tg_cpu_num > 0:
        configspec.numCPUs = tg_cpu_num
    if tg_cpu_cores > 0:
        configspec.numCoresPerSocket = tg_cpu_cores
    if tg_mem_mb > 0:
        configspec.memoryMB = tg_mem_mb
    if tg_datadisk_gb > 0:
        # get all disks on a VM, set unit_number to the next available, and get controller
        controller_key = None
        unit_number = 0
        for dev in vim_vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller_key = dev.key
        disk_spec = _vim_gen_spec_disk(tg_datadisk_gb, unit_number, controller_key)
        configspec.deviceChange = [disk_spec]
    # start reconfig task
    try:
        taskid = vim_vm.Reconfigure(spec=configspec)._GetMoId()
    except Exception, e:
        taskid = None
        print(taskid)
        raise e
    return taskid, ""


def reconfig_vm(content, vm, tg_annotation='', tg_cpu_num=-1, tg_cpu_cores=-1, tg_mem_mb=-1, tg_datadisk_gb=-1):
    task = None
    errmsg = ""
    if not isinstance(vm, VirtualMachine):
        errmsg = "Src_vm not a VirtualMachine instance"
        return task, errmsg
    if vm.vcenter.uuid != content.about.instanceUuid:
        errmsg = "Src_vm not belong to the connected vcenter"
        return task, errmsg
    # Get vim_vm_obj
    vim_vm = get_obj(content, vimtype=[vim.VirtualMachine], moid=str(vm.moid))
    return vim_vm_reconfig(vim_vm, tg_annotation, tg_cpu_num, tg_cpu_cores, tg_mem_mb, tg_datadisk_gb)


def get_task(content, taskid):
    tasklist = content.taskManager.recentTask
    vimtask = None
    for vt in tasklist:
        if taskid == vt._GetMoId():
            vimtask = vt
    return vimtask


def get_capi_datastore(cluster):
    hostlist = cluster.hostsystem_set.all()
    result_list = []
    ds_count = set()
    for host in hostlist:
        dslist = host.datastores.filter(multi_hosts_access=True)
        for ds in dslist:
            if ds.accessible and ds.id not in ds_count:
                ds_count.add(ds.id)
                result_list.append({
                    'datastore_id': ds.id,
                    'datastore_name': ds.name,
                    'free_space_gb': ds.free_space_mb / 1024,
                    'total_space_gb': ds.total_space_mb / 1024,
                    'free_percent': ds.free_space_mb * 100 / ds.total_space_mb
                })
    return result_list


def get_capi_cluster(env_type):
    """
    :param env_type: environment type
    :type env_type:unicode
    :return:
    """
    qset = VCenter.objects.all()
    vc_set = []
    for vc in qset:
        envt_dict = json.loads(vc.env_type)
        if envt_dict[env_type]:
            vc_set.append(vc)
    result_list = []
    for vc in vc_set:
        for clus in vc.computeresource_set.all():
            print(clus.name)
            hostnum = clus.hostsystem_set.count()
            stor_capi = get_capi_datastore(clus)
            free_space_all = 0
            total_space_all = 0
            for capi in stor_capi:
                free_space_all += capi['free_space_gb']
                total_space_all += capi['total_space_gb']
            stor_capi_percent = free_space_all * 100 / total_space_all
            clus_capi = {
                'cluster_id': clus.id,
                'cluster_name': clus.name,
                'host_num': hostnum,
                'free_cpu': clus.free_cpu(),
                'free_memory': clus.free_mem(),
                'ds_num': len(stor_capi),
                'free_space': stor_capi_percent
            }
            result_list.append(clus_capi)
    return result_list


def get_lociphostname(env_type, os_type, vm_num):
    nw_set = []
    qset = Network.objects.all()
    for nw in qset:
        envt_dict = json.loads(nw.env_type)
        ost_dict = json.loads(nw.os_type)
        if envt_dict[env_type] and ost_dict[os_type]:
            nw_set.append(nw)
    ip_list = []
    for nw in nw_set:
        ip_count = len(ip_list)
        if ip_count < vm_num:
            ip_list.extend(IPUsage.select_ip(nw, ip_num=vm_num - ip_count))
        else:
            break
    result_list = []
    for ipusage in ip_list:
        prefix = str(env_type)[0].upper() + str(env_type)[1:].lower()
