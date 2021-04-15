depot dashboard
---

This is an interactive (but static) dashboard showing capacity data for 
[Depot Climbing](https://www.theclimbingdepot.co.uk/) gyms. 


## Quickstart

Requires:

 - `>=python3.6`
 - [`pandas`](https://pypi.org/project/pandas/)
 - [`bokeh`](https://pypi.org/project/bokeh/)

```bash
git clone https://github.com/alexomics/depot_dash.git
cd depot_dash
python3 -m venv venv
source venv/bin/activate
pip install -U pip -r requirements.txt
python static.py
python -m http.server 5007
```

## Getting Data

Example crontab settings:

```cron
# https://crontab.guru/#00-59/5_6-22_*_*_*
00-59/5 6-22 * * * /path/to/venv/bin/python /path/to/scrape.py /path/to/output.tsv
# https://crontab.guru/#1_23_*_*_*
1 23 * * * /path/to/venv/bin/python /path/to/scrape.py /path/to/output.tsv
```
