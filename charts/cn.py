# -*- coding: utf-8 -*-
# @Time : 2024/5/23  16:35
# @Author : Andy Hsieh
# @Desc :
from pyecharts.charts import Line
from pyecharts import options as opts


def jer_chart(x, y1, y2):
    c = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            'JER',
            y1,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="JER%數", coord=[x[-1], y1[-1]], value=y1[-1])]
            ),
            color='blue',
            linestyle_opts=opts.LineStyleOpts(width=6)
        )
        .add_yaxis(
            '生產製造研發',
            y2,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="生產製造研發人數", coord=[x[-1], y2[-1]], value=y2[-1])]
            ),
            linestyle_opts=opts.LineStyleOpts(width=6),
            color='red',
        )
        .set_global_opts(title_opts=opts.TitleOpts(title='JER & 生產人數 趨勢'),
                         tooltip_opts=opts.TooltipOpts(trigger="axis"),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
                         )
    )
    return c


