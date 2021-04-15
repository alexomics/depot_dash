import sys
from ast import literal_eval
from datetime import datetime, timedelta
import re
from urllib import request


def f_time(s):
    day = datetime.now()
    ago, time = re.findall(
        "^Last updated:&nbsp(.*) \((\d+:\d+ [AP]M)\)$",
        s,
    )[0]

    if "ago" in ago:
        ago, units = re.findall("(\d+) ([A-Za-z]+)", ago)[0]
        unit_conv = {"mins": "minutes", "min": "minutes", "hour": "hours", "day": "days"}
        units = unit_conv.get(units, units)
        day = day - timedelta(**{units: int(ago)})

    t = f"{day.date().isoformat()} {time}"
    return datetime.strptime(t, "%Y-%m-%d %I:%M %p").isoformat()


url = "https://portal.rockgympro.com/portal/public/4f7e4c65977f6cd9be6d61308c7d7cc2/occupancy?&iframeid=occupancyCounter&fId="

DATA = re.compile("var data = ({.*?});", re.DOTALL)
GYMS = {
    "BLD": "Big Depot Leeds",
    "BIR": "Depot Birmingham",
    "SHF": "Depot Climbing Sheffield",
    "LED": "Depot Leeds (Pudsey)",
    "MAN": "Depot Manchester",
    "NOT": "Depot Nottingham",
}

with request.urlopen(url) as resp:
    html = resp.read().decode()

matches = DATA.search(html)
match = matches.group(1)
x = literal_eval(match)
res = []
for k, v in x.items():
    res.append(
        [
            GYMS[k],
            str(v["count"]),
            str(v["capacity"]),
            datetime.now().replace(microsecond=0).isoformat(),
        ]
    )


with open(sys.argv[1], "a") as fh:
    print("\n".join(("\t".join(row) for row in res)), file=fh)
