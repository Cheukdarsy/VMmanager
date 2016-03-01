# VMmanager
这是基于jumpserver学习的一个小项目，关于jumpserver请联系[jumpserver](http://www.jumpserver.org)

此次主要是基于jumpserver进行测试类云平台功能的二次开发

##测试平台需求文档
   鉴于现在测试环境管理现状以及建设运维平台的需求，为了更加方便地对测试环境进行搭建以及管理，现准备基于开源堡垒机jumpserver平台进行二次开发，建成类云平台的测试环境平台。

####准备工作：
 
 1.jumpserver的安装
   具体教程请参考[jumpserver安装](https://github.com/jumpserver/jumpserver/wiki/Quickinstall)

2.IDE根据个人喜好，个人目前用pycharm，可用sublime等～

3.关于git协同作业，具体教程可参考[廖雪峰git教程](http://www.liaoxuefeng.com/wiki/0013739516305929606dd18361248578c67b8067c8c017b000)


4.[python django框架知识](http://www.ziqiangxuetang.com/django/django-tutorial.html)


5.[关于django models数据类型](http://lishiguang.iteye.com/blog/1243560)

####测试平台：
 1. 测试申请流程图:
     ![流程图](https://github.com/Cheukdarsy/learngit/blob/master/xmid.png)
 2. 测试平台ER图：
     ![ER图](https://github.com/Cheukdarsy/learngit/blob/master/ER.png)
 
#### 用户申请数据表(user_apply_table)
| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|申请人(apply_username)|CharField|120|不可选，系统获取||
|申请人ID(apply_userid)|Field|20|||
|序号(apply_id)|IntegerField|100|系统自动递增|主键 外键|
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem)｜其他类型 |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntegerField | 10 | 2｜4｜8｜16 ||
| 内存(memory) | IntegerField | 10 | 4｜8｜16｜32 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntegerField|10|50G(不可选)||
|数据盘(data_disk)|IntegerField|10|0G(default)|用户自填|
|申请数量(apply_num)|IntegerField|5|1(defualt)~6|1~6区间|
|申请用途(env_name)|CharField|120|用户自定义||
|申请原因(apply_reason)|TextField|||根据申请数量显示申请原因表格行数|
|提交状态(machine_status)|BoolenField||True｜False(default)|待提交，已提交|

#### 管理员审核数据表(manager_verify_table)
| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|申请人(apply_username)|CharField|120|||
|申请人ID(apply_userid)|IntegerField|20|||
|序号(apply_id)|IntegerField|100||主键|
|申请机器ID(verify_id)|IntegerField|100||外键|
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem)｜其他类型 |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntegerField | 10 | 2｜4｜8｜16 ||
| 内存(memory) | IntegerField | 10 | 4｜8｜16｜32 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntegerField|10|50G(不可选)||
|数据盘(data_disk)|IntegerField|10|0G(default)|用户自填|
|申请数量(apply_num)|IntegerField|5|1(defualt)~6|1~6区间|
|环境名称(env_name)|CharField|120|用户自定义||
|申请原因(apply_reason)|TextField|||根据申请数量显示申请原因表格行数|
|提交状态(machine_status)|BoolenField||True｜False(default)|机器是否激活|
|审核状态(verify_status)|IntegerField|10| 1｜2｜3｜4 |审批中，已审批，环境生成中，已处理|  

#### VM生成表(VM_gen_table)
| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|申请人(apply_username)|CharField|120|||
|序号(ID)|IntegerField|100|系统自动递增|主键|
|申请机器ID(verify_id)|IntegerField|100||外键|
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem)｜其他类型 |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntegerField | 10 | 2｜4｜8｜16 ||
| 内存(memory) | IntegerField | 10 | 4｜8｜16｜32 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntegerField|10|50G(不可选)||
|数据盘(data_disk)|IntegerField|10|0G(default)|用户自填|
|环境名称(env_name)|CharField|120|用户自定义||
|状态(machine_status)|BoolenField||True｜False(default)|机器激活与否|
|IP地址(IP_address)|CharField|200|||
|生成log(gen_log)|TextField|||VM生成log，用于展示|
|生成时间(gen_time)|TimeField|||用于记录机器生成时间及进度|

#### 参数配置

| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|序号|IntegerField|10||
|配置名称|CharField|120||


## UI界面概览
#### 用户申请资源
**用户可根据自己的业务需求选择相关资源，其中可选择对应的环境类型（目前只提供测试环境），再根据是否是was应用或者数据库来
判定选择标准型主机类型或者高IO型，不同的主机类型对应不同的CPU及内存。用户可选择配置表中提供的操作系统类型进行申请，由于
VM需要，在磁盘配置方面，系统盘需固定为50G，而数据盘可根据需要选择，综合我们自身资源，提供0~50G范围的选择空间。最后用户需根
据要求填写申请用途（比如：新业务DB等），同时阐述原因，方便记录审计。在填写完所有申请需求后，用户可选择向管理员申请或者先保
存。**
![用户申请页面](https://github.com/Cheukdarsy/learngit/blob/master/VMmanager-2.png)
#### 用户资源管理
**用户在进行资源管理的时候，可以查看到已保存的申请资源，申请中的资源，以及通过后生成的资源。在已保存而未申请的资源列表上，
用户可选择继续编辑再提交申请或者直接删除此申请资源。查看申请中的资源列表，用户可以看到管理员的审核状态以及机器的生成状态，
如资源申请被拒绝，将会看到拒绝原因。最后通过后生成资源的一项，用户可以看到关于自己申请资源的IP地址、用户等相关信息。**
![用户管理页面](https://github.com/Cheukdarsy/learngit/blob/master/user_sources.png)
#### 管理者资源管理
**管理者在接收到各个用户提交的资源申请后将会生成一个资源列表，此列表包括待审核的资源，已通过的资源，同时还会有生成资源的
进度显示。待审核资源可拒绝并退回或者重新编辑后通过，已经审核通过的资源等待生成即可。**
![管理者资源管理](https://github.com/Cheukdarsy/learngit/blob/master/manager_page.png)
