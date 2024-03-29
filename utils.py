# -*- coding: utf-8 -*-
# @Time : 2023/12/28  下午 01:23
# @Author : Andy Hsieh
# @Desc :
import pendulum, asyncio
from settings import msg_content
from pyecharts.charts import Bar, Line
from pyecharts import options as opts


class BadException(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class ForbiddenException(BadException):
    pass


async def message_generator(request):
    while True:
        content = msg_content.content

        if not await request.is_disconnected():
            if content:
                print('message = ', content)
                yield {
                    "event": "message",
                    "retry": 30000,
                    "data": content
                }
                msg_content.content = ''
            else:

                yield {
                    "event": "message",
                    "retry": 30000,
                    "data": ''
                }
        await asyncio.sleep(1)


def tsFormat(ts):
    return pendulum.from_timestamp(ts, tz='Asia/Taipei').format('YYYY/MM/DD')


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


def markLine(t, x, y):
    ml = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            "數量",
            y,
            markpoint_opts=opts.MarkPointOpts(data=[opts.MarkPointItem(type_="min")]),
        )

        .set_global_opts(title_opts=opts.TitleOpts(title=t),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100), )
    )
    return ml


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
        .set_global_opts(title_opts=opts.TitleOpts(title=""),
                         tooltip_opts=opts.TooltipOpts(trigger="axis"),
                         datazoom_opts=opts.DataZoomOpts(range_start=0, range_end=100),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-15))
                         )
    )
    return c


def usd2nt_Line(x, y):
    c = (
        Line()
        .add_xaxis(xaxis_data=x)
        .add_yaxis(
            '美金對台幣',
            y,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            markpoint_opts=opts.MarkPointOpts(
                data=[opts.MarkPointItem(name="400張", coord=[x[-1], y[-1]], value=y[-1])]
            ),
            color='blue',
            linestyle_opts=opts.LineStyleOpts(width=8)
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
