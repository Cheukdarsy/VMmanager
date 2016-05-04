$(function(){
var request_id,id;
$(".modify-btn").click(function(event) {
     request_id = $(this).parents(".detail-table").children('td:first-child').attr("id");

     $.post('{% url "show_apply_machinedetail" %}', { "id": request_id}, function(data) {
       var detail_list = eval($.parseJSON(data));
       //数据获取
       $(".dropdownMenu1").text(detail_list[0].fields.env_type).append('&nbsp;<span class="caret"></span>');
       $("#"+request_id+"modal input[value='"+detail_list[0].fields.fun_type+"']").prop("checked",true).parent("label").addClass('active').siblings('label').removeClass('active');
       $(".dropdownMenu2").text(detail_list[0].fields.os_type).append('&nbsp;<span class="caret"></span>');
       $("#"+request_id+"modal ."+detail_list[0].fields.cpu+"C").prop('checked',true).parent("label").addClass('active').siblings('label').removeClass('active');
       $("#"+request_id+"modal ."+detail_list[0].fields.memory+"G").prop('checked',true).parent("label").addClass('active').siblings('label').removeClass('active');   
       $("#"+request_id+"modal input[name='data_volume']").val(detail_list[0].fields.data_disk);
       $("#"+request_id+"modal input[name='request_num']").val(detail_list[0].fields.request_num);
     });
     var saving_data_disk = $("#"+request_id+"data_volume").val();
     var saving_request_num = $("#"+request_id+"request_num").val();

     $("#"+request_id+"modifyslider").slider({
            range:"min",
            min:0,
            max:100,
            value:parseInt(saving_data_disk),
            slide:function(event,ui){
                $("#"+request_id+"data_volume").val(ui.value);
            }
        });
      $("#"+request_id+"modifyslider_num").slider({
            value:parseInt(saving_request_num),
            min:0,
            max:6,
            step:1,
            slide:function(event,ui){
               $("#"+request_id+"request_num").val(ui.value);
            }
        }); 
});

$(".agree-btn").click(function(event) {
     id = $(this).parents(".detail-table").children('td:first-child').attr("id");
});
$(".delete-btn").click(function(event) {
     id = $(this).parents(".detail-table").children('td:first-child').attr("id");
     var reason = prompt("确认删除？填写原因，将会退回给申请人哦")
     if(reason){
       reason = $.trim(reason);
       var dict = {
        "id":id,
        "reason":reason,
       }
       $.post('{% url "delete_apply" %}', dict, function(data) {
         alert("删除成功");
        setTimeout(function(e){
            $("#"+id+"tr").remove()
          },200);
       });
     }
});
$(".modify-save-btn").click(function(event) {
      var saving_fun_type = $("#"+request_id+"modal input[name='fun_type']:checked").val();
      var saving_env_type = $("#"+request_id+"modal input[name='env_type']").val();
      var saving_cpu_num = $("#"+request_id+"modal input[name='cpu']:checked").val();
      var saving_memory_num = $("#"+request_id+"modal input[name='memory']:checked").val();
    　　var saving_os_type = $("#"+request_id+"modal input[name='os_type']").val();
      var saving_data_disk = $("#"+request_id+"modal input[name='data_volume']").val();
      var saving_form = {
        "request_id":request_id,
        "saving_fun_type":saving_fun_type,
        "saving_env_type":saving_env_type,
        "saving_cpu_num":saving_cpu_num,
        "saving_memory_num":saving_memory_num,
        "saving_os_type":saving_os_type,
        "saving_data_disk":saving_data_disk,
      }
      $.post('{% url "confirm_machine_detail" %}', saving_form, function(data) {
          alert("保存成功！");
          setTimeout(function(e){
            location.href = '{% url "VM_list" %}'
          },200);
      });

});
$(".conf-agree-btn").click(function(event) {
      var confirm_fun_type = $("#"+id+"fun_type").val();
      var confirm_env_type = $("#"+id+"env_type").val();
      var confirm_cpu_num = $("#"+id+"cpu").val();
      var confirm_memory_num = $("#"+id+"memory").val();
    　　var confirm_os_type = $("#"+id+"os_type").val();
      var confirm_data_disk = $("#"+id+"data_disk").val();
      var confirm_form = {
        "request_id":id,
        "confirm_fun_type":confirm_fun_type,
        "confirm_env_type":confirm_env_type,
        "confirm_cpu_num":confirm_cpu_num,
        "confirm_memory_num":confirm_memory_num,
        "confirm_os_type":confirm_os_type,
        "confirm_data_disk":confirm_data_disk,
      }
      $.post('{% url "agree_apply" %}', confirm_form, function(data) {
          var list = eval($.parseJSON(data));
          alert("提交成功！");
          $("#"+id+"AGModal").modal("hide")
          var html = "<tr><td class='text-center'>"+list[0].pk+"</td><td class='text-center'>"+list[0].fields.request_id+"</td><td class='text-center'>"+list[0].fields.approving_env_type+'/'+list[0].fields.approving_fun_type+'/'+list[0].fields.approving_os_type+"</td><td class='text-center'><input type='checkbox' name='option1' id=''></td><td class='text-center'>"+list[0].fields.approving_status+"</td><td class='text-center'></td></tr>"
          setTimeout(function(e){
            $("#agree-table").prepend(html)
            $("#"+id+"tr").remove()
          },200);          
      });
});
function selectMenu(factor,name){
            factor.next().find("a").click(function(){
            factor.text($(this).text()).append('&nbsp;<span class="caret"></span>');
            name.val($(this).text());
        })}
        
selectMenu($(".dropdownMenu1"),$(".env_type"));
selectMenu($(".dropdownMenu2"),$(".os_type"));
$("#selectall").click(function () {
    if($("#selectall").prop("checked")){
        $("#agree-table :checkbox").prop("checked",true);
    }else{
        $("#agree-table :checkbox").prop("checked",false);
    }
});
function select_binding(type,cpu,memory){
         type.click(function(event) {
         /* Act on the event */
             $("."+cpu+"C").parent("label").addClass('active').siblings('label').removeClass('active');
             $("."+cpu+"C").val(cpu)
             $("."+memory+"G").parent("label").addClass('active').siblings('label').removeClass('active');
             $("."+memory+"G").val(memory)
     });
}
select_binding($(".normal-type"),2,4);
select_binding($(".was-type"),4,8);
select_binding($(".database-type"),4,16);
});