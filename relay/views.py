from django.shortcuts import render,render_to_response,HttpResponse

# Create your views here.

def apply(request):
    return render_to_response('relay-apply.html')

def monitor(request):
    return render_to_response('relay-monitor.html')

def ajaxRelayApply(request):
    ipAddr = request.POST['ipAddr']
    sysUser = request.POST['sysUser']
    applyTime = request.POST['applyTime']
    remark = request.POST['remark']

    print ipAddr,sysUser,applyTime,remark
    return HttpResponse('ok')