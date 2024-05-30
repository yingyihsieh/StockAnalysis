# -*- coding: utf-8 -*-
# @Time : 2024/5/24  11:56
# @Author : Andy Hsieh
# @Desc :
from pyecharts.charts import Line
from pyecharts import options as opts


def usd2nt_Line(x, y):
    c = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            '美金對台幣',
            y,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="NT/USD", coord=[x[-1], y[-1]], value=y[-1])]
            ),
            color='blue',
            linestyle_opts=opts.LineStyleOpts(width=4)
        ).set_global_opts(title_opts=opts.TitleOpts(title="千日匯率變化"),
                          tooltip_opts=opts.TooltipOpts(trigger="axis"),
                          datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                          xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
                          ).extend_axis(
            yaxis=opts.AxisOpts(
                type_="value",
                min_=28,
                max_=35,
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
            ))
    )
    return c