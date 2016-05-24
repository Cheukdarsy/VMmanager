//jumpserver 自定义js 2015-01-29

//此函数用于checkbox的全选和反选
var checked=false;
function check_all(form) {
    var checkboxes = document.getElementById(form);
    if (checked == false) {
        checked = true
    } else {
        checked = false
    }
    for (var i = 0; i < checkboxes.elements.length; i++) {
        if (checkboxes.elements[i].type == "checkbox") {
            checkboxes.elements[i].checked = checked;
        }
    }
}

function checkAll(id, name){
    var checklist = document.getElementsByName(name);
    if(document.getElementById(id).checked)
        {
        for(var i=0;i<checklist.length;i++)
        {
          checklist[i].checked = 1;
        }
    }else{
        for(var j=0;j<checklist.length;j++)
        {
         checklist[j].checked = 0;
        }
    }
}

//提取指定行的数据，JSON格式
function GetRowData(row){
    var rowData = {};
    for(var j=0;j<row.cells.length; j++) {
        name = row.parentNode.rows[0].cells[j].getAttribute("Name");
        if (name) {
            var value = row.cells[j].getAttribute("Value");
            if (!value) {
                value = row.cells[j].innerHTML;
            }
            rowData[name] = value;
        }
    }
    return rowData;
}

//此函数用于在多选提交时至少要选择一行
function GetTableDataBox() {
    var tabProduct = document.getElementById("editable");
    var tableData = new Array();
    var returnData = new Array();
    var checkboxes = document.getElementById("contents_form");
    var id_list = new Array();
    len = checkboxes.elements.length;
    for (var i=0; i < len; i++) {
        if (checkboxes.elements[i].type == "checkbox" && checkboxes.elements[i].checked == true && checkboxes.elements[i].value != "checkall") {
            id_list.push(i);
         }
        }
    console.log(id_list);
    for (i in id_list) {
        console.log(tabProduct);
        tableData.push(GetRowData(tabProduct.rows[id_list[i]]));
    }

    if (id_list.length == 0){
        alert('请至少选择一行！');
    }
    returnData.push(tableData);
    returnData.push(id_list.length);
    return returnData;
}

function move(from, to, from_o, to_o) {
    $("#" + from + " option").each(function () {
        if ($(this).prop("selected") == true) {
            $("#" + to).append(this);
            if( typeof from_o !== 'undefined'){
                $("#"+to_o).append($("#"+from_o +" option[value='"+this.value+"']"));
            }
        }
    });
}

function move_left(from, to, from_o, to_o) {
    $("#" + from + " option").each(function () {
        if ($(this).prop("selected") == true) {
            $("#" + to).append(this);
            if( typeof from_o !== 'undefined'){
                $("#"+to_o).append($("#"+from_o +" option[value='"+this.value+"']"));
            }
        }
        $(this).attr("selected",'true');
    });
}

//function move_all(from, to) {
//    $("#" + from).children().each(function () {
//        $("#" + to).append(this);
//    });
//}
//

//function selectAllOption(){
//         var checklist = document.getElementsByName ("selected");
//            if(document.getElementById("select_all").checked)
//            {
//            for(var i=0;i<checklist.length;i++)
//            {
//              checklist[i].checked = 1;
//            }
//            }else{
//            for(var j=0;j<checklist.length;j++)
//            {
//             checklist[j].checked = 0;
//            }
//            }
//
//        }


function selectAll(){
    // 选择该页面所有option
    $('option').each(function(){
        $(this).attr('selected', true)
    })
}


//
//function move_all(from, to){
//    $("#"+from).children().each(function(){
//        $("#"+to).append(this);
//    });
//}

//function commit_select(form_array){
//    $('#{0} option'.format(form_array)).each(function(){
//        $(this).prop('selected', true)
//        })
//}

function getIDall() {
    var check_array = [];
    $(".gradeX input:checked").each(function () {
        var id = $(this).attr("value");
        check_array.push(id);
    });
    return check_array.join(",");
}

//滑块
$("#slider").slider({
            range:"min",
            min:0,
            max:100,
            value:0,
            step:10,
            slide:function(event,ui){
                $("#data_volume").val(ui.value);
            }
        });
        $("#data_volume").val($("#slider").slider("value"));
 $("#slider1").slider({
            value:1,
     　　　　　　　range: "min",
            min:1,
            max:6,
            step:1,
            slide:function(event,ui){
                $("#amount").val(ui.value);
                               
            }
        });
        $("#amount").val($("#slider1").slider("value"));
      /*下拉框选择*/
function selectMenu(factor,name){
            factor.next().find("a").click(function(){
            factor.text($(this).text()).append('&nbsp;<span class="caret"></span>');
            name.val($(this).attr('name'));
        })
        }
        
        selectMenu($(".dropdownMenu1"),$(".env_type"));
        selectMenu($(".dropdownMenu2"),$(".os_type"));

        //submit or save
       
//绑定数据
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
     select_binding($(".was-type"),2,8);
     select_binding($(".database-type"),4,8);

//全选
/*$("#selectall").click(function () {//反选  
         $("#agree-table :checkbox").each(function () {  
         $(this).prop("checked", !$(this).prop("checked"));  
     });  
});*/
