# -*- coding:utf8 -*-

import atexit
import ssl
import warnings
from datetime import datetime
from os import system

from django.db import models
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim

from juser.models import User, UserGroup


# Create your models here.
class SheetField(models.Model):
    sheet_name = models.CharField(max_length=45)
    field_name = models.CharField(max_length=45)
    option = models.CharField(max_length=45, null=True)
    option_display = models.CharField(max_length=50, null=True)


class VCenter(models.Model):
    uuid = models.CharField(max_length=50, unique=True)
    version = models.CharField(max_length=30)
    ip = models.GenericIPAddressField(protocol='ipv4')
    port = models.PositiveIntegerField()
    user = models.CharField(max_length=30)
    password = models.CharField(max_length=30)
    last_connect = models.DateTimeField(null=True)

    @classmethod
    def discover(cls, ip='localhost', port=443, user='root', pwd='vmware'):
        si = SmartConnect(host=ip, user=user, pwd=pwd, port=port)
        if not si:
            return None
        content = si.RetrieveContent()
        new_uuid = content.about.instanceUuid
        new_version = content.about.apiVersion
        Disconnect(si)
        vc = cls(ip=ip, port=port, user=user, password=pwd, uuid=new_uuid, version=new_version,
                 last_connect=datetime.now())
        vc.save()
        return vc

    def connect(self):
        warnings.filterwarnings("ignore")
        si = SmartConnect(host=self.ip, user=self.user, pwd=self.password, port=self.port)
        if not si:
            self.last_connect = None
            self.save(force_update=True)
            return None
        content = si.RetrieveContent()
        uuid = content.about.instanceUuid
        if uuid != self.uuid:
            self.uuid = uuid
            print("UUID of VCenter changed, it might be another VCenter!!")
            self.save()
        atexit.register(Disconnect, si)
        return content


class VMObject(models.Model):
    vcenter = models.ForeignKey('VCenter')
    moid = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    hash_value = models.CharField(max_length=80, editable=False, default='')

    class Meta:
        abstract = True
        unique_together = ('vcenter', 'moid')

    def _sum_hash(self):
        return (
            hash(self.vcenter_id) + hash(self.moid) + hash(self.name)
        )

    def save(self, *args, **kwargs):
        if not self.hash_value:
            hash_old = 0
        else:
            hash_old = long(self.hash_value)
        hash_new = self._sum_hash()
        if (hash_old == hash_new):
            return
        for k, v in kwargs.items():
            if k == 'update_fields' and ('hash_value' not in v):
                v.append('hash_value')
        self.hash_value = str(hash_new)
        super(VMObject, self).save(*args, **kwargs)


class ComputeResource(VMObject):
    is_cluster = models.BooleanField()
    ha = models.NullBooleanField()
    drs = models.NullBooleanField()

    def _sum_hash(self):
        return (
            super(ComputeResource, self)._sum_hash() +
            hash(self.is_cluster) + hash(self.ha) + hash(self.drs)
        )

    def update_by_vim(self, vimobj):
        if not isinstance(vimobj, vim.ComputeResource):
            return
        self.name = vimobj.name
        self.is_cluster = isinstance(vimobj, vim.ClusterComputeResource)
        if self.is_cluster:
            config = vimobj.configuration
            self.ha = config.dasConfig.enabled
            self.drs = config.drsConfig.enabled
        self.save()

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.ComputeResource):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj)
        return new_obj, created


class ResourcePool(VMObject):
    share_cpu_level = models.CharField(max_length=30)
    share_mem_level = models.CharField(max_length=30)
    limit_cpu_mhz = models.BigIntegerField()
    limit_mem_mb = models.BigIntegerField()
    # related fields
    owner = models.ForeignKey('ComputeResource', null=True)
    parent = models.ForeignKey('ResourcePool', null=True)

    def _sum_hash(self):
        return (
            super(ResourcePool, self)._sum_hash() +
            hash(self.share_cpu_level) + hash(self.share_mem_level) +
            hash(self.limit_cpu_mhz) + hash(self.limit_mem_mb) +
            hash(self.owner_id) + hash(self.parent_id)
        )

    def update_by_vim(self, vimobj, vc, related=False):
        if not isinstance(vimobj, vim.ResourcePool):
            return
        self.name = vimobj.name
        config = vimobj.config
        self.share_cpu_level = config.cpuAllocation.shares.level
        self.share_mem_level = config.memoryAllocation.shares.level
        self.limit_cpu_mhz = config.cpuAllocation.limit
        self.limit_mem_mb = config.memoryAllocation.limit
        if related:
            # update owner
            clus = vimobj.owner
            if isinstance(clus, vim.ComputeResource):
                try:
                    self.owner = ComputeResource.objects.get(vcenter=vc, moid=clus._GetMoId())
                except:
                    pass
            # update parent
            resp = vimobj.parent
            if isinstance(resp, vim.ResourcePool):
                parent = None
                try:
                    parent = ResourcePool.objects.get(vcenter=vc, moid=resp._GetMoId())
                except:
                    parent = ResourcePool.create_by_vim(resp, vc, related)
                finally:
                    self.parent = parent
        self.save()

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc, related=False):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.ResourcePool):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj, vc, related)
        return new_obj, created


def bin2str(i_bin):
    if len(i_bin) < 32:
        i_bin = i_bin.rjust(32, str(0))
    i_raw = [i_bin[i * 8:i * 8 + 8] for i in range(4)]
    i_str = [str(int(subn, 2)) for subn in i_raw]
    return '.'.join(i_str)


def str2bin(i_str):
    i_raw = [bin(int(subn)) for subn in i_str.split('.')]
    if len(i_raw) != 4:
        return '0' * 32
    i_bin = [subn[2:].rjust(8, str(0)) for subn in i_raw]
    return ''.join(i_bin)


class Network(VMObject):
    net = models.GenericIPAddressField(protocol='ipv4')
    netmask = models.PositiveSmallIntegerField(default=24)

    def _sum_hash(self):
        return (
            super(Network, self)._sum_hash() +
            hash(self.net) + hash(self.netmask)
        )

    def update_nw(self, nw='', mask=24):
        if isinstance(mask, str):
            if mask.count('.') == 3:
                mask = str2bin(mask).index('0')
            else:
                return
        if nw:
            try:
                self.net = nw
            except:
                self.net = "1.1.1.0"
            finally:
                self.netmask = mask

    def update_by_vim(self, vimobj, nw=None, mask=24):
        if not isinstance(vimobj, vim.Network):
            return
        name = vimobj.name.strip()
        self.name = name
        if not nw:
            nw = name.split('-')[-1]
        if not (self.net and self.netmask):
            self.update_nw(nw, mask)
        self.save()

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.Network):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj)
        return new_obj, created


class IPUsage(models.Model):
    ipaddress = models.GenericIPAddressField(protocol='ipv4')
    network = models.ForeignKey('Network')
    vm = models.ForeignKey('VirtualMachine', null=True)
    used_manage = models.BooleanField(default=False)
    used_manage_app = models.CharField(max_length=30, null=True)
    used_occupy = models.BooleanField(default=False)
    use_unknown = models.BooleanField(default=False)

    class Meta:
        unique_together = ('network', 'ipaddress')

    @classmethod
    def create(cls, network):
        if not isinstance(network, Network):
            return None, False
        qset = cls.objects.filter(network=network)
        if qset.exists():
            return qset, False
        mask = network.netmask
        net_bin = str2bin(network.net)
        if '1' in net_bin[mask:]:
            return None, False
        iplist_int = range(int(net_bin, 2) + 1,
                           int(net_bin[:mask] + '1' * (32 - mask), 2))
        iplist_bin = [bin(subn)[2:].rjust(32, str(0)) for subn in iplist_int]
        gw = cls.objects.create(ipaddress=bin2str(iplist_bin.pop()), network=network, used_manage=True,
                                used_manage_app='GW')
        new_ipusage = [gw]
        for ip_bin in iplist_bin:
            new_ipusage.append(
                cls.objects.create(ipaddress=bin2str(ip_bin), network=network))
        return new_ipusage, True

    def occupy(self):
        self.used_manage = False
        self.use_unknown = False
        self.used_occupy = True
        self.save(update_fields=['used_manage', 'use_unknown', 'use_occupy'])

    def manage(self, app):
        self.use_unknown = False
        self.used_occupy = False
        self.used_manage = True
        self.used_manage_app = app
        self.save(update_fields=['used_manage', 'used_manage_app', 'use_unknown', 'use_occupy'])

    def ping(self):
        status = system("ping -c 3 " + self.ipaddress)
        return status == 0

    @classmethod
    def select_ip(cls, network, occupy=True):
        test_list = cls.objects.filter(network=network, used_manage=False, used_occupy=False, use_unknown=False,
                                       vm__isnull=True)
        for ipusage in test_list:
            if ipusage.ping():
                ipusage.use_unknown = True
                ipusage.save(update_fields=['use_unknown'])
                continue
            else:
                if occupy:
                    ipusage.occupy()
                return ipusage


class Datastore(VMObject):
    MT_NORM = 'normal'
    MT_INMT = 'inMaintenance'
    MT_TOMT = 'enteringMaintenance'
    MT_MODE_CHOICE = (
        (MT_NORM, 'normal'),
        (MT_INMT, 'in maintenance'),
        (MT_TOMT, 'entering maintenance')
    )
    multi_hosts_access = models.BooleanField()
    url = models.CharField(max_length=80, null=True)
    total_space_mb = models.BigIntegerField(null=True)
    # dynamic field
    accessible = models.BooleanField()
    maintenance_mode = models.CharField(max_length=10, choices=MT_MODE_CHOICE)
    free_space_mb = models.BigIntegerField(null=True)

    def _sum_hash(self):
        return (
            super(Datastore, self)._sum_hash() +
            hash(self.multi_hosts_access) + hash(self.url) + hash(self.total_space_mb) +
            hash(self.accessible) + hash(self.maintenance_mode) + hash(self.free_space_mb)
        )

    def update_by_vim(self, vimobj, dynamic=False):
        if not isinstance(vimobj, vim.Datastore):
            return
        ds_summary = vimobj.summary
        self.accessible = ds_summary.accessible
        self.maintenance_mode = ds_summary.maintenanceMode
        if ds_summary.accessible:
            self.free_space_mb = ds_summary.freeSpace / 1024 ** 2
        if not dynamic:
            self.name = ds_summary.name
            self.multi_hosts_access = ds_summary.multipleHostAccess
            if ds_summary.accessible:
                self.url = ds_summary.url
                self.total_space_mb = ds_summary.capacity / 1024 ** 2
        self.save()

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.Datastore):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj)
        return new_obj, created


class HostSystem(VMObject):
    vmotion_enable = models.BooleanField()
    total_cpu_cores = models.PositiveSmallIntegerField()
    total_cpu_mhz = models.PositiveIntegerField()
    total_mem_mb = models.PositiveIntegerField()
    # dynamic fields
    connection_state = models.CharField(max_length=30)
    in_maintenance_mode = models.BooleanField()
    usage_cpu_mhz = models.PositiveIntegerField()
    usage_mem_mb = models.PositiveIntegerField()
    # related fields
    cluster = models.ForeignKey('ComputeResource', null=True)
    networks = models.ManyToManyField('Network')
    datastores = models.ManyToManyField('Datastore')

    def cpu_total(self):
        return self.total_cpu_mhz * self.total_cpu_cores

    def free_mem_mb(self):
        return self.total_mem_mb - self.usage_mem_mb

    def free_mem_percent(self):
        return self.free_mem_mb() / self.total_mem_mb

    def _sum_hash(self):
        return (
            super(HostSystem, self)._sum_hash() +
            hash(self.vmotion_enable) +
            hash(self.total_cpu_cores) + hash(self.total_cpu_mhz) + hash(self.total_mem_mb) +
            hash(self.connection_state) + hash(self.in_maintenance_mode) +
            hash(self.usage_cpu_mhz) + hash(self.usage_mem_mb) +
            hash(self.cluster_id)
        )

    def update_by_vim(self, vimobj, vc, related=False, dynamic=False):
        host_summary = vimobj.summary
        host_runtime = vimobj.runtime
        self.usage_cpu_mhz = host_summary.quickStats.overallCpuUsage
        self.usage_mem_mb = host_summary.quickStats.overallMemoryUsage
        self.connection_state = host_runtime.connectionState
        self.in_maintenance_mode = host_runtime.inMaintenanceMode
        if not dynamic:
            self.name = vimobj.name
            self.vmotion_enable = host_summary.config.vmotionEnabled
            self.total_cpu_cores = host_summary.hardware.numCpuCores
            self.total_cpu_mhz = host_summary.hardware.cpuMhz
            self.total_mem_mb = host_summary.hardware.memorySize / 1024 ** 2
            if related:
                # update cluster
                clus = vimobj.parent
                if isinstance(clus, vim.ComputeResource):
                    try:
                        self.cluster = ComputeResource.objects.get(vcenter=vc, moid=clus._GetMoId())
                    except:
                        pass
        self.save()
        if dynamic or (not related):
            return True
        # update networks
        try:
            for vimnet in vimobj.network:
                net = Network.objects.get(vcenter=vc, moid=vimnet._GetMoId())
                self.networks.add(net)
        except:
            pass
        # update datastores
        try:
            for vimds in vimobj.datastore:
                ds = Datastore.objects.get(vcenter=vc, moid=vimds._GetMoId())
                self.datastores.add(ds)
        except:
            pass

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc, related=False):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.HostSystem):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj, vc, related)
        return new_obj, created


class VirtualMachine(VMObject):
    istemplate = models.BooleanField()
    annotation = models.TextField()
    cpu_num = models.PositiveSmallIntegerField()
    cpu_cores = models.PositiveSmallIntegerField()
    memory_mb = models.PositiveIntegerField()
    storage_mb = models.PositiveIntegerField()
    guestos_shorname = models.CharField(max_length=30)
    guestos_fullname = models.CharField(max_length=50)
    hostsystem = models.ForeignKey('HostSystem', null=True)
    resourcepool = models.ForeignKey('ResourcePool', null=True)
    networks = models.ManyToManyField('Network')
    datastores = models.ManyToManyField('Datastore')

    def _sum_hash(self):
        return (
            super(VirtualMachine, self)._sum_hash() +
            hash(self.template) + hash(self.annotation) +
            hash(self.cpu_num) + hash(self.cpu_cores) +
            hash(self.memory_mb) + hash(self.storage_mb) +
            hash(self.guestos_shorname) + hash(self.guestos_fullname) +
            hash(self.hostsystem_id) + hash(self.resourcepool_id)
        )

    def update_ipusage(self, vimobj):
        vm_guest = vimobj.guest
        count_ip = 0
        try:
            for vimip in vm_guest.net:
                ip = IPUsage.objects.get(network__name=vimip.network.strip(), ipaddress=vimip.ipAddress)
                ip.used_occupy = False
                ip.vm = self
                ip.save(update_fields=['vm', 'used_occupy'])
                count_ip += 1
        except:
            pass
        finally:
            return count_ip

    def update_by_vim(self, vimobj, vc, related=False):
        self.name = vimobj.name
        vm_config = vimobj.config
        self.template = vm_config.template
        self.annotation = vm_config.annotation
        self.cpu_num = vm_config.hardware.numCPU
        self.cpu_cores = vm_config.hardware.numCoresPerSocket
        self.memory_mb = vm_config.hardware.memoryMB
        self.storage_mb = vimobj.summary.storage.committed / 1024 ** 2
        vm_guest = vimobj.guest
        self.guestos_shorname = vm_guest.guestId
        self.guestos_fullname = vm_guest.guestFullName
        if related:
            # update hostsystem
            host = vimobj.runtime.host
            if host:
                try:
                    self.hostsystem = HostSystem.objects.get(vcenter=vc, moid=host._GetMoId())
                except:
                    pass
            # update resourcepool
            resp = vimobj.resourcePool
            if resp:
                try:
                    self.resourcepool = ResourcePool.objects.get(vcenter=vc, moid=resp._GetMoId())
                except:
                    pass
        self.save()
        if not related:
            return True
        # update networks
        try:
            for vimnet in vimobj.network:
                net = Network.objects.get(vcenter=vc, moid=vimnet._GetMoId())
                self.networks.add(net)
        except:
            pass
        # update datastores
        try:
            for vimds in vimobj.datastore:
                ds = Datastore.objects.get(vcenter=vc, moid=vimds._GetMoId())
                self.datastores.add(ds)
        except:
            pass
        # update ipusage_set
        self.update_ipusage(vimobj)

    @classmethod
    def create_or_update_by_vim(cls, vimobj, vc, related=False):
        new_obj = None
        created = False
        if not isinstance(vimobj, vim.VirtualMachine):
            return new_obj, created
        moid = vimobj._GetMoId()
        qset = cls.objects.filter(moid=moid, vcenter=vc)
        if qset.exists():
            new_obj = qset[0]
        else:
            created = True
            new_obj = cls(moid=moid, vcenter=vc)
        new_obj.update_by_vim(vimobj, vc, related)
        return new_obj, created


class Template(VirtualMachine):
    USG_CHOICE = (
        ('WAS', 'Web Application Server'),
        ('ORA', 'Oracle Database'),
        ('BASE', 'Operation System Only')
    )
    usage = models.CharField(max_length=30, choices=USG_CHOICE)

    class Meta:
        pass

    @classmethod
    def select_template(cls, vc, usage, guestos):
        match_os = cls.objects.filter(vcenter=vc, guestos_shorname=guestos)
        match_all = match_os.filter(usage=usage)
        if match_all.exists():
            return match_all
        elif match_os.filter(usage='BASE').exists():
            return match_os.filter(usage='BASE')
        elif match_os.exists():
            return match_os
        else:
            return None


class Application(models.Model):
    """用户申请表"""
    APPLY_STATUS_CHOICE = (
        ('SM', 'submit'),
        ('HD', 'hold')
    )

    env_type = models.CharField(max_length=20)
    fun_type = models.CharField(max_length=20)
    # master_type = models.CharField(max_length=80)
    cpu = models.SmallIntegerField()
    memory_gb = models.IntegerField()
    os_type = models.CharField(max_length=20)
    datadisk_gb = models.IntegerField(null=True)
    request_vm_num = models.IntegerField()
    apply_status = models.CharField(max_length=20, choices=APPLY_STATUS_CHOICE)
    app_name = models.CharField(max_length=20)
    apply_reason = models.TextField()
    apply_date = models.DateTimeField()
    user = models.ForeignKey(User)

    # operation_system = models.CharField(max_length=120,unique=True)
    # apply_reason = models.CharField(, max_length=50)

    def __unicode__(self):
        return self.env_type


class Approvel(models.Model):
    """审核表"""
    APPROVE_STATUS = (
        ('AP', 'approved'),
        ('AI', 'approving'),
        ('RB', 'return back')
    )
    application = models.OneToOneField('Application')
    appro_env_type = models.CharField(max_length=20)
    appro_fun_type = models.CharField(max_length=20)
    appro_cpu = models.SmallIntegerField()
    appro_memory_gb = models.IntegerField()
    appro_os_type = models.CharField(max_length=20)
    appro_datadisk_gb = models.IntegerField()
    appro_vm_num = models.IntegerField()
    appro_status = models.CharField(max_length=20, choices=APPROVE_STATUS)
    appro_date = models.DateTimeField()

    # approving_des = models.ForeignKey(computerresource)
    def __unicode__(self):
        return self.appro_env_type


class VMOrder(models.Model):
    """生成表"""
    GEN_STATUS = (
        ('FAIL', 'failed'),
        ('SUCCESS', 'success'),
        ('RUNNING', 'running')
    )
    approvel = models.ForeignKey('Approvel')
    src_template = models.ForeignKey('Template')
    loc_hostname = models.CharField(max_length=20)
    loc_ip = models.ForeignKey('IPUsage')
    loc_cluster = models.ForeignKey('ComputeResource')
    loc_resp = models.ForeignKey('ResourcePool', null=True)
    loc_storage = models.ForeignKey('Datastore')
    gen_status = models.CharField(max_length=20, choices=GEN_STATUS)
    gen_log = models.TextField(null=True)
    gen_time = models.DateTimeField(null=True)
    gen_progress = models.PositiveIntegerField()
