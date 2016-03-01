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
|序号(ID)|IntergerField|100|系统自动递增|主键|
|申请机器ID(machine_ID)|CharField|100|(不显示)| 类：李四_3 外键|
|环境名称(env_name)|CharField|120|用户自定义||
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem) |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntergerField | 10 | 2｜4｜8｜16 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntergerField|10|50G(不可选)||
|数据盘(data_disk)|IntergerField|10|0G(default)|用户自填|
|申请数量(apply_num)|IntergerField|5|1(defualt)~6|1~6区间|
|申请原因(apply_reason)|TextField|||根据申请数量显示申请原因表格行数|
|状态(machine_status)|BoolenField||True｜False(default)|机器激活与否|

#### 管理员审核数据表(manager_verify_table)
| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|申请人(apply_username)|CharField|120|||
|序号(ID)|IntergerField|100|系统自动递增|主键|
|申请机器ID(machine_ID)|CharField|100|(不显示)| 类：李四_3 外键|
|环境名称(env_name)|CharField|120|用户自定义||
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem) |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntergerField | 10 | 2｜4｜8｜16 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntergerField|10|50G(不可选)||
|数据盘(data_disk)|IntergerField|10|0G(default)|用户自填|
|申请数量(apply_num)|IntergerField|5|1(defualt)~6|1~6区间|
|申请原因(apply_reason)|TextField|||根据申请数量显示申请原因表格行数|
|状态(machine_status)|BoolenField||True｜False(default)|机器激活与否|
|审核状态(verify_status)|IntergerField|10| 1｜2｜3｜4 |审批中，已审批，环境生成中，已处理|  

#### VM生成表(VM_gen_table)
| 名称  | 数据类型 | 长度 | 可选项 |注释 | 
| ----- | :------:|:----:| :-----:| :----: |
|申请人(apply_username)|CharField|120|||
|序号(ID)|IntergerField|100|系统自动递增|主键|
|申请机器ID(machine_ID)|CharField|100|(不显示)| 类：李四_3 外键|
|环境名称(env_name)|CharField|120|用户自定义||
| 环境类型(env_type) | CharField | 120 | 生产环境｜开发环境｜测试环境 || 
| 主机类型(maintence_type) | CharField | 80 | 标准型(2cpu/4G mem)｜高IO型(2 cpu/8G mem) |tips：was应用选择标准型。数据库 选择高IO型。|
| CPU(cpu) | IntergerField | 10 | 2｜4｜8｜16 ||
|操作系统(operation_system)|CharField|80|windows｜SUSE|此项为可编辑参数，具体选项待定|
|系统盘(system_disk)|IntergerField|10|50G(不可选)||
|数据盘(data_disk)|IntergerField|10|0G(default)|用户自填|
|申请数量(apply_num)|IntergerField|5|1(defualt)~6|1~6区间|
|申请原因(apply_reason)|TextField|||根据申请数量显示申请原因表格行数|
|状态(machine_status)|BoolenField||True｜False(default)|机器激活与否|
|审核状态(verify_status)|IntergerField|10| 1｜2｜3｜4 |审批中，已审批，环境生成中，已处理|  
|IP地址(IP_address)|CharField|200|||
|生成log(gen_log)|TextField|||VM生成log，用于展示|
|生成时间(gen_time)|TimeField|||用于记录机器生成时间及进度|


## UI界面概览
#### 用户申请资源
![用户申请页面](https://github.com/Cheukdarsy/learngit/blob/master/VMmanager-2.png)
#### 用户资源管理
![用户管理页面](https://github.com/Cheukdarsy/learngit/blob/master/user_sources.png)
#### 管理者资源管理
![管理者资源管理](https://github.com/Cheukdarsy/learngit/blob/master/manager_page.png)
