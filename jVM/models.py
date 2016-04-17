#-*- coding:utf8 -*-

from django.db import models
from juser.models import User, UserGroup
import datetime

# Create your models here.


class sheet_field(models.Model):
    sheet_name = models.CharField(max_length=45)
    field_name = models.CharField(max_length=45)
    option = models.CharField(max_length=45, null=True)
    option_display = models.CharField(max_length=50, null=True)

class Vcenter(models.Model):
    uuid = models.CharField(max_length=50)
    ip = models.IntegerField(unique=True)
    port = models.PositiveIntegerField()
    user = models.CharField(max_length=30,editable=False,default="")
    password = models.CharField(max_length=30)

class VMObject(models.Model):
    vcid = models.CharField(max_length=30)
    moid = models.CharField(max_length=30)
    hash_value = models.CharField(max_length=80,editable=False,default="")

    class Meta:
        abstract = True
        unique_together=("vcid","moid")

class Network(VMObject):
    name = models.CharField(max_length=30)

class Datastore(VMObject):
    STATUS = (
        ('NORMALMODE','normal mode'),
        ('SERVEDMODE','served mode'),
        ('SERVINGMODE','serving mode')
        )
    accessible = models.BooleanField()
    maintenance_mode = models.CharField(max_length=30,choices=STATUS)
    name = models.CharField(max_length=30)
    multi_hosts_access = models.BooleanField()
    url = models.CharField(max_length=80)
    total_space = models.BigIntegerField()   
    free_space = models.BigIntegerField()

class IP_Pool(models.Model):
    ipaddress = models.CharField(max_length=50,unique=True)
    network = models.ForeignKey(Network)
    vm = models.ForeignKey("VitualMachine",null=True)
    manage_used = models.BooleanField(default=False)


class Compute_Resource(models.Model):
    TYPE=(
        ('CLUSTER','cluster'),
        ('MAINTENANCE','maintenance')
        )
    type = models.CharField(max_length=30,choices=TYPE)
    name = models.CharField(max_length=30)


class HostSystem(VMObject):
    name = models.CharField(max_length=30)
    vmotion_enable = models.BooleanField()
    memory = models.PositiveSmallIntegerField()
    connection_state = models.CharField(max_length=30)
    in_maintenance_mod = models.BooleanField()
    compute_resource = models.ForeignKey(Compute_Resource)
    network = models.ManyToManyField(Network)
    datastore = models.ManyToManyField(Datastore)

class VitualMachine(VMObject):
    name = models.CharField(max_length=30)
    template = models.BooleanField()
    annotation = models.TextField()
    num_cpu = models.PositiveSmallIntegerField()
    memory_mb = models.PositiveIntegerField()
    num_core_per_cpu = models.PositiveSmallIntegerField()
    guest_id = models.CharField(max_length=30)
    guest_fullname = models.CharField(max_length=50)
    hostsystem = models.ForeignKey(HostSystem)
    network = models.ManyToManyField(Network)
    datastore = models.ManyToManyField(Datastore)


    pre_occupied = models.BooleanField(default=False)

class userapply(models.Model):

    """用户申请表"""
    APPLY_STATUS_CHOICE = (
        ('SM', 'submit'),
        ('HD', 'hold'),
        ('AP', 'approved'),
        ('RB', 'return back')
        )

    env_type = models.CharField(max_length=20)
    fun_type = models.CharField(max_length=20)
    # master_type = models.CharField(max_length=80)
    cpu = models.SmallIntegerField()
    memory = models.IntegerField()
    os_type = models.CharField(max_length=20)
    data_disk = models.IntegerField(null=True)
    request_num = models.IntegerField()
    apply_status = models.CharField(max_length=20, choices=APPLY_STATUS_CHOICE)
    app_name = models.CharField(max_length=20)
    apply_reason = models.TextField()
    apply_date = models.DateTimeField()
    user = models.ForeignKey(User)
    # operation_system = models.CharField(max_length=120,unique=True)
    # apply_reason = models.CharField(, max_length=50)

    def __unicode__(self):
        return self.env_type

class userapply_confirm(models.Model):

    """审核表"""
    APPROVE_STATUS = (
        ('AP', 'approved'),
        ('RB', 'return back')
        )
    request_id = models.OneToOneField(userapply)
    approving_env_type = models.CharField(max_length=20)
    approving_fun_type = models.CharField(max_length=20)
    approving_cpu_num = models.SmallIntegerField()
    approving_memory_num = models.IntegerField()
    approving_os_type = models.CharField(max_length=20)
    approving_data_disk = models.IntegerField()
    approving_appply_num = models.IntegerField()
    approving_status = models.CharField(max_length=20, choices=APPROVE_STATUS)
    approving_datetime = models.DateTimeField()
    # approving_des = models.ForeignKey(computerresource)
    def __unicode__(self):
        return self.approving_env_type

class userapply_generate(models.Model):
    """生成表"""
    GEN_STATUS=(
        ('FAIL','failed'),
        ('SUCCESS','success'),
        ('RUNNING','running')
        )
    apply_id  = models.ForeignKey(userapply)
    vm_gen_hostname = models.CharField(max_length=20)
    vm_gen_ip = models.ForeignKey(IP_Pool)
    vm_gen_host = models.ForeignKey(HostSystem)
    vm_gen_storage  = models.ForeignKey(Datastore)
    vm_gen_status  = models.CharField(max_length=20,choices=GEN_STATUS)
    vm_gen_task = models.CharField(max_length=20)
    vm_gen_log  = models.TextField(null=True)
    vm_gen_datetime = models.DateTimeField(null=True)
    vm_gen_progress  = models.PositiveIntegerField()





 		
