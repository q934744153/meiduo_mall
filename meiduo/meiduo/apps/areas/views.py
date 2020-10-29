from django.views import View
from django import http
from . models import Area
from django.core.cache import  cache

class ProvinceAreasView(View):
    """省级地区"""

    def get(self, request):
        """提供省级地区数据
        1.查询省级数据
        2.序列化省级数据
        3.响应省级数据
        """
        province_list = cache.get('province_list')
        province_list = None
        if province_list:
            return http.JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'province_list': province_list
            })

        try:
            # 1.查询省级数据
            province_model_list = Area.objects.filter(parent__isnull=True)
        except Exception as e:
            # 如果报错, 则返回错误原因:
            return http.JsonResponse({'code': 400, 'errmsg': '省份数据错误'})

        province_list = []
        for province_models in province_model_list:
            province_list.append({'id':province_models.id,
                                  'name':province_models.name})

            # 3.返回整理好的省级数据
        cache.set('province_list',province_list,3600)
        return http.JsonResponse({'code': 0, 'errmsg': 'OK', 'province_list': province_list})


class SubAreaView(View):

    def get(self, request, pk):
        # 1、提取参数
        # 2、校验参数
        # 3、业务数据处理 —— 根据路径pk主键值，过滤出子级行政区数据

        # ========(1)、通读策略之"读缓存，命中直接构建响应返回"=========
        sub_data = cache.get('sub_area_'+str(pk))
        if sub_data:
            return http.JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'sub_data': sub_data
            })

        # ========(2)、通读策略之"读mysql"=========
        try:
            parent_area = Area.objects.get(pk=pk)
            # sub_areas = Area.objects.filter(parent=parent_area)
            sub_areas = Area.objects.filter(parent_id=pk)
        except Exception as e:
            return http.JsonResponse({'code': 400, 'errmsg': '数据库错误'})

        sub_list = []
        for sub in sub_areas:
            # sub：子级行政区对象
            sub_list.append({
                'id': sub.id,
                'name': sub.name
            })

        # 缓存数据
        sub_data = {
                'id': parent_area.id,
                'name': parent_area.name,
                'subs': sub_list
        }

        # ========(3)、通读策略之"回填缓存"=========
        # 需要记录的数据是：某一个父级行政区，对应的子级行政区数据
        cache.set('sub_area_'+str(pk), sub_data, 3600)

        # 4、构建响应
        return http.JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'sub_data': sub_data
        })

