import math
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from bokeh.io import save, output_file
from bokeh.layouts import column, layout, row
from bokeh.models import (
    Div,
    Panel,
    Span,
    Tabs,
    Range1d,
    BasicTicker,
    ColorBar,
    LinearColorMapper,
    PrintfTickFormatter,
    HoverTool,
)
from bokeh.plotting import curdoc, figure
from bokeh.palettes import Colorblind7 as week_palette
from bokeh.palettes import RdYlGn9 as deciles_palette


def load_data():
    df = pd.read_csv(
        DATASET,
        sep="\t",
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


def plot_week(df, gym):
    dt = datetime.now()
    days = [datetime.strftime(dt - timedelta(days=dx), "%Y-%m-%d") for dx in range(7)]
    df = df[df["nice_date"].isin(days)]
    w_min = df["scrape_time"].min().date()
    w_max = df["scrape_time"].max().date()

    p = figure(
        title=f"{gym}: {w_min} - {w_max}",
        x_axis_label="Time",
        y_axis_label="No of Climbers",
        x_axis_type="datetime",
        tools="xbox_zoom,xpan,reset,save",
        tooltips=[("day", "@day"), ("time", "@nice_time"), ("# climbers", "@count")],
    )
    # Add capacity line
    cap = Span(
        location=df["capacity"].iloc[0],
        dimension="width",
        line_color="red",
        line_width=3,
    )
    p.add_layout(cap)
    # Set padding manually
    y_max = df["capacity"].iloc[0]
    y_min = 0
    pad = (y_max - y_min) * 0.1 / 2
    p.y_range = Range1d(y_min - pad, y_max + pad)
    for (name, group), colour in zip(df.groupby("nice_date"), week_palette):
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
    p.toolbar.logo = None
    p.legend.location = "top_left"
    p.legend.click_policy = "mute"
    p.sizing_mode = "stretch_width"
    return p


def plot_heat(df, gym):
    data = (
        df.groupby(["hour", "day"], as_index=False)
        .agg({"pc_capacity": "mean", "count": "mean"})
        .round({"count": 0, "pc_capacity": 0})
    )

    hours = list(sorted(df["hour"].unique()))
    weekdays = list(reversed(list(DAYS_MAP.values())))

    colors = list(deciles_palette) + ["#a50026"]
    mapper = LinearColorMapper(palette=colors, low=0, high=100)

    p = figure(
        title=f"{gym}: Percentage capacity (over {WEEKS} week{PLURAL})",
        x_range=hours,
        y_range=weekdays,
        x_axis_location="above",
        toolbar_location=None,
        active_drag=None,
        tooltips=[
            ("day, hour", "@day @hour:00-@hour:59"),
            ("% capacity used", "@pc_capacity%"),
            ("on average", "@count climbers"),
        ],
    )

    p.sizing_mode = "stretch_width"

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
DATASET = DATA_DIR.joinpath("dataset.tsv")

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

DF = load_data()
GYMS = list(DF["gym"].unique())
D_MIN = DF["scrape_time"].min().date()
D_MAX = DF["scrape_time"].max().date()
WEEKS = math.ceil((D_MAX - D_MIN).days / 7)
PLURAL = {1: ""}.get(WEEKS, "s")

GYMS = [
    "Depot Nottingham",
    "Depot Manchester",
    "Depot Leeds (Pudsey)",
    "Depot Birmingham",
    "Big Depot Leeds",
    "Depot Climbing Sheffield",
]
reload_str = f"<a href='index.html'>Gym selector</a> Page last updated: <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>"

tabs = ["<html>", "<head>", "<title>Depot Capacity Report</title>", "</head>", "<body>", "<h1>Gyms:</h1>", "<ul>"]

for gym in GYMS:
    df = DF[DF["gym"].eq(gym)]
    last_refresh = Div(text=reload_str)
    heat = plot_heat(df, gym)
    line = plot_week(df, gym)
    col = column(last_refresh, heat, line)
    col.sizing_mode = "scale_both"

    fn = gym.replace(" ", "_").lower() + ".html"
    output_file(filename=fn, title=f"Depot Capacity Report - {gym}")
    save(col, filename=fn)
    tabs.append(f"<li><a href='{fn}'>{gym}</a></li>")


tabs.extend(["</ul>", "</body>", "</html>"])
with open("index.html", "w") as fh:
    fh.write("\n".join(tabs))

