# -*- coding: utf-8 -*-
# @Time : 2024/5/28  17:21
# @Author : Andy Hsieh
# @Desc :
from pyecharts.charts import Bar, Line
from pyecharts import options as opts


def stockChart(date_arr, jer_min, jer_max, jfm, jfx, differset, joboffs, global_title):
    bar = (
        Bar(init_opts=opts.InitOpts(width='1024px', height='600px'))
        .add_xaxis(date_arr)
        .add_yaxis("jer_min", jer_min, color='orange')
        .add_yaxis("jer_max", jer_max, color='blue')
        .add_yaxis("jer_full_min", jfm, color='#FF00FF')
        .add_yaxis("jer_full_max", jfx, color='#8600FF')
        .extend_axis(
            yaxis=opts.AxisOpts(
                name="工作差集件數",
                type_="value",
                # min_=0,
                # max_=20,
                # interval=2,
                axislabel_opts=opts.LabelOpts(formatter="{value}"),
            ))
        .set_global_opts(title_opts=opts.TitleOpts(title=global_title),
                         yaxis_opts=opts.AxisOpts(
                             name="JER",
                             type_="value",
                             axislabel_opts=opts.LabelOpts(formatter="{value}"),
                             axistick_opts=opts.AxisTickOpts(is_show=True),
                             splitline_opts=opts.SplitLineOpts(is_show=True),
                         ),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts
                         (rotate=-15))

                         )

    )
    line = (
        Line()
        .add_xaxis(xaxis_data=date_arr)
        .add_yaxis(
            series_name="新增職缺數",
            yaxis_index=1,
            y_axis=differset,
            label_opts=opts.LabelOpts(is_show=False),
            color='red',
        )
        .add_yaxis(
            series_name="關閉職缺數",
            yaxis_index=1,
            y_axis=joboffs,
            label_opts=opts.LabelOpts(is_show=False),
            color='green',
        )
    )

    return bar.overlap(line)


def HolderLine(title, x, y1, y2, y1_name, y2_name):
    c = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            y1_name,
            y1,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="400張", coord=[x[-1], y1[-1]], value=y1[-1])]
            ),
            color='blue',
            linestyle_opts=opts.LineStyleOpts(width=8)
        )
        .add_yaxis(
            y2_name,
            y2,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="1000張", coord=[x[-1], y2[-1]], value=y2[-1])]
            ),
            linestyle_opts=opts.LineStyleOpts(width=8),
            color='red',
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title),
                         tooltip_opts=opts.TooltipOpts(trigger="axis"),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
                         )
    )
    return c


def TopHolderLine(title, x, y1, y2, y3, y4, y1_name, y2_name, y3_name, y4_name):
    c = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            y1_name,
            y1,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="董監HR", coord=[x[-1], y1[-1]], value=y1[-1])]
            ),
            color='red',
            linestyle_opts=opts.LineStyleOpts(width=6)
        )
        .add_yaxis(
            y2_name,
            y2,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="經理HR", coord=[x[-1], y2[-1]], value=y2[-1])]
            ),
            linestyle_opts=opts.LineStyleOpts(width=6),
            color='green',
        )
        .add_yaxis(
            y3_name,
            y3,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="董監PR", coord=[x[-1], y3[-1]], value=y3[-1])]
            ),
            linestyle_opts=opts.LineStyleOpts(width=6),
            color='blue',
        )
        .add_yaxis(
            y4_name,
            y4,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="經理PR", coord=[x[-1], y4[-1]], value=y4[-1])]
            ),
            linestyle_opts=opts.LineStyleOpts(width=6),
            color='orange',
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=title),
                         tooltip_opts=opts.TooltipOpts(trigger="axis"),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
                         )
    )
    return c


def fundBar(x, y, industry_name):
    bar = (
        Bar()
        .add_xaxis(x)
        .add_yaxis("資金%", y)
        .set_global_opts(title_opts=opts.TitleOpts(title=f"{industry_name}-資金流向"))
        # title_opts标题
    )
    return bar


def fundLine(title, data_dict):
    colors = ['red', 'blue', 'green', 'orange', 'Purple']
    x_data = data_dict.pop('x_data')
    line_chart = Line().add_xaxis(xaxis_data=x_data)
    for k in data_dict:
        line_chart.add_yaxis(k,
                             data_dict[k],
                             markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
                             markpoint_opts=opts.MarkPointOpts(
                                 data=[opts.MarkPointItem(name=k, coord=[x_data[-1], data_dict[k][-1]], value=data_dict[k][-1])]
                             ),
                             color=colors.pop(0),
                             linestyle_opts=opts.LineStyleOpts(width=8)
                             )
    line_chart.set_global_opts(
        title_opts=opts.TitleOpts(title=title),
        tooltip_opts=opts.TooltipOpts(trigger="axis"),
        datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
        xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
    )

    return line_chart
