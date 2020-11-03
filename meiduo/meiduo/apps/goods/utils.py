
from django.template import loader
from django.conf import settings
import os
from .models import GoodsCategory,GoodsChannel,SKUSpecification,SKU,SPUSpecification,SpecificationOption
from copy import deepcopy


def get_breadcrumb(category_id):
    # 根据category_id获取导航信息
    ret_dict = {}

    category = GoodsCategory.objects.get(pk=category_id)
    # 1级
    if not category.parent:
        ret_dict['cat1'] = category.name
    # 2级
    elif not category.parent.parent:
        ret_dict['cat2'] = category.name
        ret_dict['cat1'] = category.parent.name
    # 3级
    elif not category.parent.parent.parent:
        ret_dict['cat3'] = category.name
        ret_dict['cat2'] = category.parent.name
        ret_dict['cat1'] = category.parent.parent.name

    return ret_dict


def get_categories():
    # ============1、构建模版参数categories=========
    categories = {} # # 商品分类频道

    # 按照组id排序，再按照sequence排序
    channels = GoodsChannel.objects.order_by(
        'group_id',
        'sequence'
    )

    # 遍历每一个频道。把频道插入以"组id"为键的键值对中
    for channel in channels:
        # 当前组不存在的时候(第一次构建)
        if channel.group_id not in categories:
            # categories[1] = {}
            categories[channel.group_id] = {
                'channels': [], # 一级分类信息
                'sub_cats': [] # 二级分类
            }
        # 一级分类
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id': cat1.id,
            'name': cat1.name,
            'url': channel.url
        })

        # 二级分类
        cat2s = cat1.subs.all()
        for cat2 in cat2s:
            # cat2：每一个二级分类对象

            # 当前二级分类关联的三级分类
            cat3s_list = []
            cat3s = cat2.subs.all()
            for cat3 in cat3s:
                # cat3：当前二级分类关联的每一个三级分类对象
                cat3s_list.append({
                    'id': cat3.id,
                    'name': cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3s_list # 三级分类
            })

    return categories

# 5星级别
def get_goods_and_spec(sku_id):
    # 当前SKU商品
    sku = SKU.objects.get(pk=sku_id)

    # 记录当前sku的选项组合
    cur_sku_spec_options = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')
    cur_sku_options = [] # [1,4,7]
    for temp in cur_sku_spec_options:
        # temp是SKUSpecification中间表对象
        cur_sku_options.append(temp.option_id)


    # spu对象(SPU商品)
    goods = sku.spu
    # 罗列出和当前sku同类的所有商品的选项和商品id的映射关系
    # {(1,4,7):1, (1,3,7):2}
    sku_options_mapping = {}
    skus = SKU.objects.filter(spu=goods)
    for temp_sku in skus:
        # temp_sku:每一个sku商品对象
        sku_spec_options = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')
        sku_options = []
        for temp in sku_spec_options:
            sku_options.append(temp.option_id) # [1,4,7]
        sku_options_mapping[tuple(sku_options)] = temp_sku.id # {(1,4,7):1}



    # specs当前页面需要渲染的所有规格
    specs = SPUSpecification.objects.filter(spu=goods).order_by('id')
    for index, spec in enumerate(specs):
        # spec每一个规格对象
        options = SpecificationOption.objects.filter(spec=spec)

        # 每一次选项规格的时候，准备一个当前sku的选项组合列表，便于后续使用
        temp_list = deepcopy(cur_sku_options) # [1,4,7]

        for option in options:
            # 每一个选项，动态添加一个sku_id值，来确定这个选项是否属于当前sku商品

            temp_list[index] = option.id # [1,3,7] --> sku_id?

            option.sku_id = sku_options_mapping.get(tuple(temp_list)) # 找到对应选项组合的sku_id

        # 在每一个规格对象中动态添加一个属性spec_options来记录当前规格有哪些选项
        spec.spec_options = options

    return goods, sku, specs
