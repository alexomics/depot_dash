import math
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from bokeh.layouts import column, layout, row
from bokeh.models import (
    Select,
    Div,
    Panel,
    Tabs,
    Button,
    DatePicker,
    BasicTicker,
    ColorBar,
    LinearAxis,
    LinearColorMapper,
    PrintfTickFormatter,
    HoverTool,
)
from bokeh.plotting import curdoc, figure
from bokeh.palettes import Colorblind7 as week_palette
from bokeh.palettes import RdYlGn9 as deciles_palette

from .helpers import sha256sum, get_remote_hash


def update_gym(attr, old, new):
    plots.children[0] = plot_line()
    plots.children[1] = plot_heat()
    plot2.children[0] = plot_week_line()


def update_date(attr, old, new):
    plots.children[0] = plot_line()
    plot2.children[0] = plot_week_line()


def update():
    global DF
    DF = load_data()
    plots.children[0] = plot_line()
    plots.children[1] = plot_heat()
    plot2.children[0] = plot_week_line()
    reload_str = f"Dataset last loaded <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"
    last_refresh.update(text=reload_str)


def reload_counter(new):
    _iframe.update(text="")
    _iframe.update(text=IFRAME)


def load_data():
    df = pd.read_csv(
        DATASET,
        sep="\t",
        # names=["gym", "count", "capacity", "update_time", "scrape_time"],
        # parse_dates=["update_time", "scrape_time"],
        names=["gym", "count", "capacity", "scrape_time"],
        parse_dates=["scrape_time"],
        dtype={"gym": "category"},
    )

    df["day"] = df["scrape_time"].dt.dayofweek.map(DAYS_MAP)
    df["hour"] = df["scrape_time"].dt.hour.astype("str").str.zfill(2)
    df["pc_capacity"] = df["count"] / df["capacity"] * 100
    df["nice_time"] = df["scrape_time"].dt.strftime("%H:%M")
    df["norm_time"] = pd.to_datetime(df["nice_time"], format="%H:%M")
    df["nice_date"] = df["scrape_time"].dt.strftime("%Y-%m-%d")
    return df


def plot_line():
    df = DF[DF["gym"].eq(gyms.value) & DF["nice_date"].eq(date.value)]

    p = figure(
        title=f"{gyms.value} - {date.value}",
        x_axis_label="Time",
        y_axis_label="No of Climbers",
        x_axis_type="datetime",
        tooltips=[("time", "@nice_time"), ("# climbers", "@count")],
        tools="hover,xpan,xbox_zoom,reset,save",
        plot_width=550,
        plot_height=550,
    )
    p.line(x=df["scrape_time"], y=df["capacity"], line_width=2, color="red")
    p.line(x="scrape_time", y="count", source=df, line_width=1)
    p.toolbar.logo = None
    return p


def plot_week_line():
    dt = datetime.strptime(date.value, "%Y-%m-%d")
    days = [datetime.strftime(dt - timedelta(days=dx), "%Y-%m-%d") for dx in range(7)]
    df = DF[DF["gym"].eq(gyms.value) & DF["nice_date"].isin(days)]
    w_min = df["scrape_time"].min().date()
    w_max = df["scrape_time"].max().date()

    p = figure(
        title=f"{gyms.value} - {w_min} to {w_max}",
        x_axis_label="Time",
        y_axis_label="No of Climbers",
        x_axis_type="datetime",
        tools="xbox_zoom,xpan,reset,save",
        plot_width=1230,
        plot_height=550,
    )
    p.line(x=df["norm_time"], y=df["capacity"], line_width=2, color="red")
    lines = []
    for (name, group), colour in zip(df.groupby("nice_date"), week_palette):
        lines.append(
            p.line(
                x="norm_time", 
                y="count", 
                source=group, 
                line_width=2, 
                color=colour,
                alpha=0.8, 
                legend_label=name,
                muted_color=colour,
                muted_alpha=0.1,
            )
        )
    p.toolbar.logo = None
    p.legend.location = "top_left"
    p.legend.click_policy="mute"
    hover = HoverTool(
        tooltips=[("day", "@day"), ("time", "@nice_time"), ("# climbers", "@count")],
        renderers=lines,
    )
    p.add_tools(hover)
    # p.hover.mode = "vline"
    return p


def plot_heat():
    df = DF[DF["gym"].eq(gyms.value)]
    data = (
        df.groupby(["hour", "day"], as_index=False)
        .agg({"pc_capacity": "mean", "count": "mean"})
        .round({"count": 0, "pc_capacity": 0})
    )

    hours = list(sorted(df["hour"].unique()))
    weekdays = list(reversed(list(DAYS_MAP.values())))

    colors = [
        "#ffffe0",
        "#e0f2b4",
        "#c5e391",
        "#b0d374",
        "#a2c05e",
        "#9dac4c",
        "#9f9540",
        "#a67a38",
        "#b35933",
        "#c31432",
    ]
    # colors = list(deciles_palette) + ["#a50026"]

    mapper = LinearColorMapper(palette=colors, low=0, high=100)

    p = figure(
        title=f"{gyms.value} - Percentage capacity (over {WEEKS} week{PLURAL})",
        x_range=hours,
        y_range=weekdays,
        x_axis_location="above",
        plot_width=700,
        plot_height=550,
        toolbar_location=None,
        active_drag=None,
        tooltips=[
            ("day, hour", "@day @hour:00-@hour:59"),
            ("% capacity used", "@pc_capacity%"),
            ("on average", "@count climbers"),
        ],
    )

    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "14px"
    p.axis.major_label_standoff = 0

    p.rect(
        x="hour",
        y="day",
        width=1,
        height=1,
        source=data,
        fill_color={"field": "pc_capacity", "transform": mapper},
        line_color=None,
    )

    color_bar = ColorBar(
        color_mapper=mapper,
        major_label_text_font_size="14px",
        ticker=BasicTicker(desired_num_ticks=len(colors)),
        formatter=PrintfTickFormatter(format="%d%%"),
        label_standoff=10,
        border_line_color=None,
        location=(0, 0),
    )
    p.add_layout(color_bar, "right")
    return p


DATA_DIR = Path(__file__).parent.joinpath("data")
DATASET = DATA_DIR.joinpath('dataset.tsv')
HASH = sha256sum(DATASET)
REMOTE_DATASET = "https://raw.githubusercontent.com/alexomics/depot_dash/master/data/dataset.tsv.xz"
REMOTE_SHA256 = "https://raw.githubusercontent.com/alexomics/depot_dash/master/data/dataset.tsv.xz.sha256"
REMOTE_HASH = get_remote_hash(REMOTE_SHA256)

DAYS_MAP = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday",
}
GYM = "Depot Nottingham"
IFRAME = (
    "<iframe id='occupancyCounter' "
    "src='https://portal.rockgympro.com/portal/public/"
    "4f7e4c65977f6cd9be6d61308c7d7cc2/occupancy?&iframeid"
    "=occupancyCounter&fId=' height=250 width=100% "
    "scrolling='no' style='border:0px;'></iframe>"
)
DF = load_data()
GYMS = list(DF["gym"].unique())
D_MIN = DF["scrape_time"].min().date()
D_MAX = DF["scrape_time"].max().date()
WEEKS = math.ceil((D_MAX - D_MIN).days / 7)
PLURAL = {1:""}.get(WEEKS, "s")

gyms = Select(value=GYM, options=GYMS)
gyms.on_change("value", update_gym)

date = DatePicker(value=str(D_MAX), min_date=str(D_MIN), max_date=str(D_MAX))
date.on_change("value", update_date)

reload_str = f"Dataset last loaded <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"
last_refresh = Div(text=reload_str)

reload_btn = Button(label="Reload Counter", button_type="primary")
reload_btn.on_click(reload_counter)
_iframe = Div(text=IFRAME)
INFO_TEXT = f"""Dataset file: <pre>{DATASET}</pre>"""
#     <br>Remote file: <pre>{REMOTE_DATASET}</pre>
#     <br>Hashes: <pre>{HASH}<br>{REMOTE_HASH}</pre>
#     <br>If the hashes do not match the dataset has been updated on GitHub"""
dataset_info = Div(text=INFO_TEXT)

extras = row(column(_iframe), column(dataset_info), column(reload_btn))

drops = row(gyms, date, last_refresh)
plots = row(plot_line(), plot_heat())
plot2 = row(plot_week_line())

tabs = Tabs(
    tabs=[
        Panel(child=column(drops, plots, plot2), title="Historic Data"),
        Panel(child=extras, title="Extras"),
    ]
)

l = row(tabs)
curdoc().add_root(l)
curdoc().title = "Depot Climbing Gym Dashboard"
curdoc().add_periodic_callback(update, 300000)  # 5 minute update

