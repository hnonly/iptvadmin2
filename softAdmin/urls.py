from django.urls import path, include
from . import views

urlpatterns = [
    path('getCategoriesByPage', views.getCategoriesByPage),  # 根据页码获取分类列表
    path('addCategory', views.addCategory),  # 添加分类
    path('deleteCategory', views.delCategory),  # 批量删除分类
    path('getCategoryPageNum', views.getCategoryPageNum),  # 获取分类总页数
    path('editCategory', views.editCategory),  # 编辑分类

    path('getChannelByPage', views.getChannelsByPage),  # 根据页码获取频道列表
    path('addChannel', views.addChannel),  # 添加频道
    path('deleteChannel', views.delChannel),  # 批量删除频道
    path('showChannel', views.showCahnnel), # 批量上下架频道
    path('editChannel', views.editChannel), # 编辑频道
    path('getChannelPageNum', views.getChannelPageNum),  # 获取频道总页数
    
    # ✅ 批量导入频道（我帮你统一格式，完全匹配前端）
    path('batchImportChannel', views.batch_import_channel),

    path('startImg', views.startImg),  # 启动图修改
    path('exitImg', views.exitImg),  # 退出图修改
    path('announcement', views.announcement),  # 公告/广告修改
    path('epg', views.epg), # EPG修改
]
