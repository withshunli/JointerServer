# encoding:utf-8

from django.shortcuts import render,render_to_response,HttpResponse

# Create your views here.
from cmdb.models import *

import os
import xlrd,xlwt
import json
import random
import string
import traceback
import time,datetime

# CMDB表格上传文件存放目录
file_upload = './data/cmdb/upload'
file_export = './static/download/cmdb/'

def management(request):
    return render_to_response('cmdb-management.html')

'''
验证函数，用于CMDB在线编辑、资产导入时的权限认证管理
'''
def modify_verify(function=None):
    def user_chk(request):
        chk_group = 'admin'
        username = request.user
        try:
            username.groups.get(name=chk_group)
            return function(request)
        except:
            data = {"status":"error","msg":"错误：无权限操作！"}
            return HttpResponse(json.dumps(data))

    return user_chk

'''
日志记录函数，用于记录CMDB操作事件
'''
def eventLogs(user,action,logs):
    sqlData = EventLogs(
        user = user,
        action = action,
        logs = logs
    )
    sqlData.save()

'''
服务器事件日志，用于记录单台服务器详细资产日志
'''
def cmdb_logs(user,action,id,logs):
    logsData = OptionLogs(
        user = user,
        action = action,
        logs = logs
    )
    logsData.save()
    CmdbLogs = CmdbConf.objects.get(id=id)
    CmdbLogs.logs.add(logsData)
    CmdbLogs.save()

def index(request):
    try:
        query = request.GET['query']
    except:
        query = None

    try:
        size = request.GET['size']
    except:
        size = 15

    sqlData = CmdbConf.objects.all()
    queryData = {}
    if query:
        for k,v in request.GET.items():
            if len(v) ==0:
                continue
            else:
                if k =='idc':
                    sqlData = sqlData.filter(idc__contains = v.strip())
                    queryData[k] = v
                elif k =='ip':
                    sqlData = sqlData.filter(ip=v.strip())
                    queryData[k] = v
                elif k =='sn':
                    sqlData = sqlData.filter(sn=v.strip())
                    queryData[k] = v
                elif k =='op':
                    sqlData = sqlData.filter(op=v.strip())
                    queryData[k] = v
                elif k =='rd':
                    sqlData = sqlData.filter(rd=v.strip())
                    queryData[k] = v
                elif k =='attribute':
                    sqlData = sqlData.filter(attribute__contains=v.strip())
                    queryData[k] = v
                elif k =='recycle':
                    if v =='再分配':
                        continue
                    else:
                        sqlData = sqlData.filter(recycle=v.strip())
                        queryData[k] = v
                elif k =='ipMore':
                    ipList = list(set(v.split('\r\n')))
                    ipMoreData = []
                    for i in ipList:
                        try:
                            ipQuery = sqlData.get(ip=i.strip())
                            ipMoreData.append(ipQuery)
                        except:
                            pass
                    queryData[k] = ipList
                    sqlData = ipMoreData
                elif k =='anum':
                    sqlData = sqlData.filter(anum=v.strip())
                    queryData[k] = v

    # 更新查询日志
    if query:
        eventLogs(request.user,'查询','查询了%s台服务器' %len(sqlData))

    reData = {
        "request" : request,
        "dataResult" : sqlData,
        "queryData" : queryData,
        "size" : size
    }
    return render_to_response('cmdb-index.html',reData)

def upload(request):
    def handle_uploaded_file(f):
        try:
            destination = open('%s/text.xls' %file_upload, 'wb')
            for chunk in f.chunks():
                destination.write(chunk)
            destination.close()
            fileName = 'text.xls'
            return {'code':0,'data':fileName}
        except Exception,e:
            print Exception,e
            return {'code':1,'msg':'系统异常'}

    # 文件校验函数
    def handle_table(fileName,cloName):
        try:
            fileData = xlrd.open_workbook('%s/text.xls' %file_upload)
            table = fileData.sheets()[0]
            for i in range(0,table.ncols):
                if table.col_values(i)[0] != colName[i]:
                    return {'code':1,'msg':'提示：表格数据不规范，导入失败。'}
            return {'code':0}
        except Exception,e:
            print Exception,e
            return {'code':1,'msg':'提示：文件格式错误，请检查!'}

    # 数据库更新函数
    def handle_sqlData(fileName):
        fileData = xlrd.open_workbook('%s/text.xls' %file_upload)
        table = fileData.sheets()[0]
        tableDic = {}
        # 临时IP列表，用于存放更新失败的IP地址
        falseList = []
        count =0
        for row in range(0,table.nrows):
            for col in range(0,table.ncols):
                if row ==0:
                    continue
                else:
                    # 更新数据
                    tableDic[colName[col]] = table.row_values(row)[col]
            try:
                tableDic['SN'] = str(tableDic['SN']).replace('.0','')
            except:
                pass

            if len(tableDic) !=0:
                try:
                    assetNum = CmdbConf.objects.get(anum=tableDic['资产编号'])
                    updateTag =1
                except:
                    updateTag =0

                if updateTag ==0:
                    while True:
                        '''
                     生成唯一资产ID
                     '''
                        assetNum = string.join(random.sample((string.digits),6)).replace(' ','')
                        try:
                            assetChk = CmdbConf.objects.get(anum=assetNum)
                            continue
                        except:
                            break
                    try:
                        sqlData = CmdbConf(
                            idc = tableDic['机房'],
                            ip = tableDic['IP'],
                            sn = tableDic['SN'],
                            anum = assetNum,
                            type = tableDic['类型'],
                            model = tableDic['型号'],
                            cpu = tableDic['CPU'],
                            mem = tableDic['内存'],
                            disk = tableDic['硬盘'],
                            position = tableDic['机架位置'],
                            op = tableDic['运维人'],
                            rd = tableDic['使用人'],
                            dept = tableDic['部门'],
                            useReason = tableDic['使用原因'],
                            attribute = tableDic['资产属性'],
                            remark = tableDic['备注']
                            )
                        sqlData.save()
                        count +=1
                        # 更新服务器详细操作日志
                        cmdb_logs(request.user,'新增',sqlData.id,'通过Excel新增导入服务器资产信息')
                    except Exception,e:
                        falseList.append(tableDic['IP'])
                        print Exception,e
                elif updateTag ==1:
                    sqlData = CmdbConf.objects.get(anum=assetNum.anum)
                    sqlData.idc = tableDic['机房']
                    sqlData.ip = tableDic['IP']
                    sqlData.sn = tableDic['SN']
                    sqlData.type = tableDic['类型']
                    sqlData.model = tableDic['型号']
                    sqlData.cpu = tableDic['CPU']
                    sqlData.mem = tableDic['内存']
                    sqlData.disk = tableDic['硬盘']
                    sqlData.position = tableDic['机架位置']
                    sqlData.op = tableDic['运维人']
                    sqlData.rd = tableDic['使用人']
                    sqlData.dept = tableDic['部门']
                    sqlData.useReason = tableDic['使用原因']
                    sqlData.attribute = tableDic['资产属性']
                    sqlData.remark = tableDic['备注']
                    try:
                        sqlData.save()
                        count +=1
                    except Exception,e:
                        falseList.append(tableDic['IP'])
                        print Exception,e
        # 更新操作日志
        if count !=0:
            eventLogs(request.user,'导入','导入更新了%s台服务器' %count)
        return falseList

    if request.method == 'POST':
        # 定义表格列名规范，后续可配置数据库
        colName = ['机房','IP','资产编号','SN','类型','型号','CPU','内存','硬盘','机架位置','运维人','使用人','部门','使用原因','资产属性','备注']
        fileUpload = handle_uploaded_file(request.FILES['file'])
        if fileUpload['code'] ==0:
            fileName = fileUpload['data']
            check = handle_table(fileName,colName)
            if check['code'] !=0:
                return HttpResponse(json.dumps(check))
            else:
                # 执行更新入库
                update_status = handle_sqlData(fileName)

        if len(update_status) !=0:
            ipText = ''
            for i in update_status:
                ipText +='%s<br />' %i
            data = {'code':0,'msg':'提示：以下IP地址导入失败<br /><br />%s' %ipText}
        else:
            data = {'code':0,'msg':'提示：数据导入成功'}
        return HttpResponse(json.dumps(data))

def export(request):
    try:
        queryData = request.POST['data']
    except:
        queryData = None
    sqlData = CmdbConf.objects.values_list('idc','ip','anum','sn','type','model','cpu','mem','disk','position','op','rd','dept','useReason','attribute','remark')

    if queryData:
        for k,v in eval(queryData).items():
            if k =='idc':
                sqlData = sqlData.filter(idc__contains = v)
            elif k =='ip':
                sqlData = sqlData.filter(ip=v)
            elif k =='sn':
                sqlData = sqlData.filter(sn=v)
            elif k =='op':
                sqlData = sqlData.filter(op=v)
            elif k =='rd':
                sqlData = sqlData.filter(rd=v)
            elif k =='attribute':
                sqlData = sqlData.filter(attribute__contains=v)
            elif k =='recycle':
                sqlData = sqlData.filter(recycle=v)
            elif k =='ipMore':
                ipList = v
                ipMoreData = []
                for i in ipList:
                    try:
                        ipQuery = sqlData.get(ip=i)
                        ipMoreData.append(ipQuery)
                    except:
                        pass
                sqlData = ipMoreData
            elif k =='anum':
                sqlData = sqlData.filter(anum=v.strip())
                queryData[k] = v

    def set_style(name,height,bold=False):
        style = xlwt.XFStyle() # 初始化样式
        font = xlwt.Font() # 为样式创建字体
        font.name = name # 'Times New Roman'
        font.color_index = 4
        font.height = height
        style.font = font
        style.num_format_str = 'yyyy-mm-dd'
        return style

    # 定义表格数据文件存放路径
    dateTime = time.strftime('%Y%m%d%H%M%S')
    dataFile = "%s/%s.xls" %(file_export,dateTime)

    f = xlwt.Workbook(encoding = 'utf-8', style_compression=2) #创建工作簿

    '''
    初始化数据:
    '''
    sheet1 = f.add_sheet(u'CMDB资产数据',cell_overwrite_ok=True) #创建sheet
    row0 = ['机房','IP','资产编号','SN','类型','型号','CPU','内存','硬盘','机架位置','运维人','使用人','部门','使用原因','资产属性','备注']

    # 数据统计页sheet
    for i in range(0,len(row0)):
        sheet1.write(0,i,row0[i],set_style('Times New Roman',280,True))

    for row in range(0,len(sqlData)):
        for col in range(0,len(sqlData[row])):
            sheet1.write(row+1,col,sqlData[row][col],set_style('Times New Roman',220))

    f.save(dataFile) #保存文件

    # 更新操作日志
    eventLogs(request.user,'导出','导出了%s台服务器' %len(sqlData))

    data = {'code':0,'data':'<a href="/static/download/cmdb/%s.xls" target="_blank">数据导出成功，点击下载</a>' %dateTime}
    return HttpResponse(json.dumps(data))

def modify(request):
    id = request.POST['pk']
    object = request.POST['name']
    value = request.POST['value']
    sqlData = CmdbConf.objects.get(id=id)
    ipAddr = sqlData.ip
    def ipFormatChk(ip_str):
        q = ip_str.split('.')
        return len(q) == 4 and len(filter(lambda x: x >= 0 and x <= 255, \
        map(int, filter(lambda x: x.isdigit(), q)))) == 4
    if object == 'ip':
        if ipFormatChk(value):
            try:
                oldData = sqlData.ip
                sqlData.ip = value
                sqlData.save()
                data = {"status":"success","msg":"update complete."}
            except:
                data = {"status":"error","msg":"错误：更新失败"}
        else:
            data = {"status":"error","msg":"错误：非法的IP地址"}
    elif object == 'idc':
        try:
            oldData = sqlData.idc
            sqlData.idc = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'op':
        try:
            oldData = sqlData.op
            sqlData.op = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'rd':
        try:
            oldData = sqlData.rd
            sqlData.rd = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'dept':
        try:
            oldData = sqlData.dept
            sqlData.dept = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'allotTime':
        try:
            oldData = sqlData.allotTime
            sqlData.allotTime = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'allotReason':
        try:
            oldData = sqlData.allotReason
            sqlData.allotReason = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'attribute':
        try:
            oldData = sqlData.attribute
            sqlData.attribute = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}
    elif object == 'recycle':
        try:
            oldData = sqlData.recycle
            sqlData.recycle = value
            sqlData.save()
            data = {"status":"success","msg":"update complete."}
        except:
            data = {"status":"error","msg":"错误：请检查输入内容"}

    # 更新操作日志
    if data['status'] =='success':
        eventLogs(request.user,'修改','将服务器%s的%s更新为"%s"  ' %(ipAddr,object,value))

    # 更新服务器详细操作日志
    cmdb_logs(request.user,'修改',sqlData.id,'服务器的【%s】项由"%s"变更为"%s"' %(object,oldData,value))

    return HttpResponse(json.dumps(data))

def bulkPost(request):
    jsonData = request.POST
    editItems = json.loads(jsonData['editItems'])
    ipData = editItems['ipData']
    sqlData = CmdbConf.objects.all()
    data = {"status":None}
    for object,value in editItems.items():
        if object =='ipData':
            continue
        else:
            # 开始更新数据
            for i in ipData:
                ipSql = sqlData.get(ip=i)
                if object == 'idc':
                    try:
                        oldData = ipSql.idc
                        ipSql.idc = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'model':
                    try:
                        oldData = ipSql.model
                        ipSql.model = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'cpu':
                    try:
                        oldData = ipSql.cpu
                        ipSql.cpu = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'mem':
                    try:
                        oldData = ipSql.mem
                        ipSql.mem = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'disk':
                    try:
                        oldData = ipSql.disk
                        ipSql.disk = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'op':
                    try:
                        oldData = ipSql.op
                        ipSql.op = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'rd':
                    try:
                        oldData = ipSql.rd
                        ipSql.rd = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'dept':
                    try:
                        oldData = ipSql.dept
                        ipSql.dept = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'allotTime':
                    try:
                        oldData = ipSql.allotTime
                        ipSql.allotTime = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'allotReason':
                    try:
                        oldData = ipSql.allotReason
                        ipSql.allotReason = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'attribute':
                    try:
                        oldData = ipSql.attribute
                        ipSql.attribute = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'recycle':
                    try:
                        oldData = ipSql.recycle
                        ipSql.recycle = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}
                elif object == 'remark':
                    try:
                        oldData = ipSql.remark
                        ipSql.remark = value
                        ipSql.save()
                    except:
                        data = {"status":"error","msg":"%s的%s项更新失败，请检查！" %(i,object)}

                # 更新服务器详细操作日志
                cmdb_logs(request.user,'修改',ipSql.id,'服务器的【%s】项由"%s"变更为"%s"' %(object,oldData,value))

                if data["status"] =="error":
                    return HttpResponse(json.dumps(data))

    data = {"status":"success","msg":"数据批量修改成功！"}
    # 更新操作日志
    eventLogs(request.user,'修改','使用批量修改功能更新%s台服务器信息"  ' %len(ipData))
    return HttpResponse(json.dumps(data))

# Ajax服务器变更记录函数
def ajaxOptionLogs(request):
    serverId = request.POST['id']
    sqlData = CmdbConf.objects.get(id=serverId)
    dataTable = ''
    for i in sqlData.logs.order_by('-id')[:10]:
        dataTable += '<tr><td>%s</td><td>%s</td><td>%s</td><td nowrap>%s</td></tr>' %(
        i.action,
        i.user.first_name,
        i.logs,
        i.date)
    return HttpResponse(dataTable)

# Ajax服务器资产备注信息
def ajaxServerRemark(request):
    serverId = request.POST['id']
    sqlData = CmdbConf.objects.get(id=serverId)
    if len(sqlData.remark) ==0:
        data = '该服务器没有备注信息！'
    else:
        data = sqlData.remark
    return HttpResponse(data)

# Ajax服务器变更记录函数
def ajaxServerLogs(request):
    serverId = request.POST['id']
    sqlData = Servers.objects.get(id=serverId)
    dataTable = ''
    for i in sqlData.changeLogs.all():
        dataTable += '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %(
        i.subject,
        i.operator,
        i.content,
        i.time,
        i.memo)
    return HttpResponse(dataTable)

# Ajax服务器详细信息函数
def ajaxServerDetail(request):
    serverId = request.POST['id']
    sqlData = CmdbConf.objects.get(id=serverId)
    dataTable = '''
    <table class="table table-striped table-hover table-bordered">
      <tbody>
        <tr><td>机房</td><td>%s</td></tr>
        <tr><td>IP地址</td><td>%s</td></tr>
        <tr><td>宿主机</td><td>%s</td></tr>
        <tr><td>SN号</td><td>%s</td></tr>
        <tr><td>资产编号</td><td>%s</td></tr>
        <tr><td>设备类型</td><td>%s</td></tr>
        <tr><td>设备型号</td><td>%s</td></tr>
        <tr><td>CPU</td><td>%s</td></tr>
        <tr><td>内存</td><td>%s</td></tr>
        <tr><td>磁盘</td><td>%s</td></tr>
        <tr><td>机架位置</td><td>%s</td></tr>
        <tr><td>运维人</td><td>%s</td></tr>
        <tr><td>使用人</td><td>%s</td></tr>
        <tr><td>使用部门</td><td>%s</td></tr>
        <tr><td>使用时间</td><td>%s</td></tr>
        <tr><td>使用原因</td><td>%s</td></tr>
        <tr><td>资产属性</td><td>%s</td></tr>
        <tr><td>备注信息</td><td>%s</td></tr>
      </tbody>
    </table>
    ''' %(sqlData.idc,
          sqlData.ip,
          sqlData.owner,
          sqlData.sn,
          sqlData.anum,
          sqlData.type,
          sqlData.model,
          sqlData.cpu,
          sqlData.mem,
          sqlData.disk,
          sqlData.position,
          sqlData.op,
          sqlData.rd,
          sqlData.dept,
          sqlData.useTime,
          sqlData.useReason,
          sqlData.attribute,
          sqlData.remark)

    return HttpResponse(dataTable)

