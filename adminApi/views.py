from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from android.models import BasicSetting
from django.http import JsonResponse, HttpResponseRedirect, HttpResponseNotFound
from .models import AdminInfo
from deviceAdmin.views import getDeviceByPageMethod
from softAdmin.views import getAllCategory
from softAdmin.views import getCategoriesByPageMethod
from softAdmin.views import getChannelsByPageMethod
from deviceAdmin.views import getDeviceNum
from softAdmin.views import getCategoryCount, getChannelCount
from android.views import getStartCount
from datetime import datetime, timedelta
from android.views import getStartCountByDate
from utils import need_login, api_need_login
# 新增导入：密码哈希、CSRF防护、日志
from django.contrib.auth.hashers import check_password, make_password
from django.views.decorators.csrf import csrf_protect
import logging

# 配置日志
logger = logging.getLogger(__name__)

def notFound(request, exception=""):
    """404页面"""
    return render(request, 'error.html')


def logout(request):
    """退出登录：清空会话"""
    request.session.flush()
    logger.info("管理员退出登录")
    return HttpResponseRedirect(reverse('login'))

# 修改账号密码：新增CSRF防护、密码哈希、判空、日志
@api_need_login
@csrf_protect
def changePassword(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nickname = request.POST.get('nickname')
        avatar = request.POST.get('avatar')
        
        # 判空：管理员信息不存在
        d = AdminInfo.objects.first()
        if not d:
            logger.warning("修改密码失败：管理员信息不存在")
            return JsonResponse({"code": 400, "msg": "修改失败: 账号不存在"}, status=400)
        
        # 更新字段：密码需哈希存储
        try:
            if username: 
                d.username = username
                logger.info(f"管理员账号更新为: {username}")
            if password: 
                d.password = make_password(password)  # 密码哈希
                logger.info("管理员密码已更新（哈希存储）")
            if nickname: d.nickname = nickname
            if avatar: d.avatar = avatar
            d.save()
            return JsonResponse({"code": 200, "msg": "修改成功"})
        except Exception as e:
            logger.error(f"修改管理员信息失败：{str(e)}")
            return JsonResponse({"code": 500, "msg": f"修改失败: {str(e)}"}, status=500)
    else:
        return JsonResponse({"code": 401, "msg": "请求方式错误"}, status=405)


# 后台登陆：新增CSRF防护、密码哈希校验、统一响应格式、日志
@csrf_protect
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # 参数校验
        if not username or not password:
            logger.warning("登录失败：账号/密码为空")
            return JsonResponse({"code": 400, "msg": "登陆失败: 账号或密码不能为空", "redirect": ""}, status=400)
        
        d = AdminInfo.objects.filter(username=username).first()
        if d:
            # 密码哈希校验（替换明文对比）
            if check_password(password, d.password):
                request.session['logged_in'] = True
                request.session.set_expiry(0)  # 会话随浏览器关闭失效
                logger.info(f"管理员 {username} 登录成功")
                return JsonResponse({"code": 200, "msg": "登陆成功", "redirect": "/admin/main"})
            else:
                logger.warning(f"管理员 {username} 登录失败：密码错误")
                return JsonResponse({"code": 400, "msg": "登陆失败: 账号或密码错误", "redirect": ""}, status=400)
        else:
            logger.warning(f"登录失败：账号 {username} 不存在")
            return JsonResponse({"code": 401, "msg": "登陆失败: 账号不存在", "redirect": ""}, status=404)
    else:
        return render(request, 'login.html')

# 获取图表展示信息：优化循环可读性
def getCharts():
    """获取近7天启动量图表数据"""
    charts = []
    current_date = datetime.now().date()
    for i in range(7):
        target_date = current_date - timedelta(days=i)
        date_str = target_date.strftime("%m-%d")
        count = getStartCountByDate(target_date.strftime("%Y-%m-%d"))
        charts.append([date_str, count])
    # 反转：让时间从旧到新展示（可选，根据前端需求）
    charts.reverse()
    return charts


@need_login
def mainPage(request):
    """后台首页：补充异常捕获"""
    try:
        content = {
            "title": "后台首页",
            "startCount": getStartCount(),
            "deviceCount": getDeviceNum(),
            "cateCount": getCategoryCount(),
            "channelCount": getChannelCount(),
            "charts": getCharts()
        }
        return render(request, 'index.html', content)
    except Exception as e:
        logger.error(f"加载后台首页失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"首页加载失败: {str(e)}"}, status=500)

# 设备管理：补充异常捕获
@need_login
def devicePage(request):
    try:
        d, b = getDeviceByPageMethod(1)
        cates = getAllCategory()
        content = {
            "title": "设备管理",
            "allPages": b,
            "cates": cates,
        }
        return render(request, 'device.html', content)
    except Exception as e:
        logger.error(f"加载设备管理页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"设备管理页面加载失败: {str(e)}"}, status=500)

# epg设置：新增判空、异常捕获
@need_login
def epgPage(request):
    try:
        setting = BasicSetting.objects.first()
        # 判空：基础设置未初始化
        if not setting:
            logger.warning("EPG设置页面加载失败：基础设置未初始化")
            return render(request, 'error.html', {"msg": "EPG设置加载失败: 基础配置未初始化"}, status=400)
        
        content = {
            "title": "EPG设置",
            "epg": setting.epgUrl,
        }
        return render(request, 'epg.html', content)
    except Exception as e:
        logger.error(f"加载EPG设置页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"EPG设置加载失败: {str(e)}"}, status=500)

# 分类管理：补充异常捕获
@need_login
def categoryPage(request):
    try:
        content = {
            "title": "分类管理",
            "allPages": getCategoriesByPageMethod(1)[1]
        }
        return render(request, 'category.html', content)
    except Exception as e:
        logger.error(f"加载分类管理页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"分类管理页面加载失败: {str(e)}"}, status=500)

# 频道管理：补充异常捕获
@need_login
def channelPage(request):
    try:
        content = {
            "title": "频道管理",
            "allPages": getChannelsByPageMethod(1)[1],
            "cates": getAllCategory()
        }
        return render(request, 'channel.html', content)
    except Exception as e:
        logger.error(f"加载频道管理页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"频道管理页面加载失败: {str(e)}"}, status=500)

# 软件公告：新增判空、异常捕获
@need_login
def announcementPage(request):
    try:
        setting = BasicSetting.objects.first()
        if not setting:
            logger.warning("软件公告页面加载失败：基础设置未初始化")
            return render(request, 'error.html', {"msg": "软件公告加载失败: 基础配置未初始化"}, status=400)
        
        content = {
            "title": "软件公告",
            "content": setting.adtext,
            "showtime": setting.showTime
        }
        return render(request, 'announcement.html', content)
    except Exception as e:
        logger.error(f"加载软件公告页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"软件公告加载失败: {str(e)}"}, status=500)

# 软件启动图：新增判空、异常捕获
@need_login
def startImgPage(request):
    try:
        setting = BasicSetting.objects.first()
        if not setting:
            logger.warning("启动图设置页面加载失败：基础设置未初始化")
            return render(request, 'error.html', {"msg": "启动图设置加载失败: 基础配置未初始化"}, status=400)
        
        imgUrl = setting.imgStart
        content = {
            "title": "软件启动图",
            "startImg": imgUrl
        }
        return render(request, 'startimg.html', content)
    except Exception as e:
        logger.error(f"加载启动图设置页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"启动图设置加载失败: {str(e)}"}, status=500)

# 软件退出图：新增判空、异常捕获
@need_login
def exitImgPage(request):
    try:
        setting = BasicSetting.objects.first()
        if not setting:
            logger.warning("退出图设置页面加载失败：基础设置未初始化")
            return render(request, 'error.html', {"msg": "退出图设置加载失败: 基础配置未初始化"}, status=400)
        
        imgUrl = setting.imgEnd
        content = {"title": "软件退出图", "exitImg": imgUrl}
        return render(request, 'exitimg.html', content)
    except Exception as e:
        logger.error(f"加载退出图设置页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"退出图设置加载失败: {str(e)}"}, status=500)

# 系统设置：移除明文密码返回、新增判空、异常捕获
@need_login
def settingPage(request):
    try:
        data = AdminInfo.objects.first()
        if not data:
            logger.warning("系统设置页面加载失败：管理员信息未初始化")
            return render(request, 'error.html', {"msg": "系统设置加载失败: 管理员信息未初始化"}, status=400)
        
        content = {
            "title": "系统设置",
            "username": data.username,
            "password": "******",  # 替换明文密码为掩码
            "nickname": data.nickname,
            "avatar": data.avatar
        }
        return render(request, 'setting.html', content)
    except Exception as e:
        logger.error(f"加载系统设置页面失败：{str(e)}")
        return render(request, 'error.html', {"msg": f"系统设置加载失败: {str(e)}"}, status=500)

# 安装: 初始化数据：防重复执行、新增异常捕获、日志
@need_login
def install(request):
    try:
        # 判重：避免重复初始化导致主键冲突
        if BasicSetting.objects.exists():
            logger.warning("基础设置初始化失败：数据已存在")
            return JsonResponse({"code": 400, "msg": "数据已初始化，无需重复操作!"}, status=400)
        
        # 插入软件基础设置数据
        BasicSetting.objects.create(
            adtext="欢迎使用本软件，这里是广告位，10秒后消失！",
            showTime=10,
            imgStart="",
            imgEnd="",
            epgUrl="",
            ua="SYTV/1.6"
        )
        logger.info("基础设置数据初始化成功")
        return JsonResponse({"code": 200, "msg": "初始化数据成功!"})
    except Exception as e:
        logger.error(f"基础设置初始化失败：{str(e)}")
        return JsonResponse({"code": 500, "msg": f"初始化失败: {str(e)}"}, status=500)
