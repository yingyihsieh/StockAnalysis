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


def stockChart(date_arr, jer_min, jer_max, jfm, jfx, differset, joboffs, emps):
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
        .set_global_opts(title_opts=opts.TitleOpts(title=f"員工人數: {emps}"),
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
        .add_xaxis(x)
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
        .add_xaxis(x)
        .add_yaxis(
            y1_name,
            y1,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            color='red',
            linestyle_opts=opts.LineStyleOpts(width=5)
        )
        .add_yaxis(
            y2_name,
            y2,
            markline_opts=opts.MarkLineOpts(data=[opts.MarkLineItem(type_="average")]),
            linestyle_opts=opts.LineStyleOpts(width=5),
            color='blue',
        )
        .set_global_opts(title_opts=opts.TitleOpts(title=""))
    )
    return c