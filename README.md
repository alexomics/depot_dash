depot dashboard
---

This is a simple bokeh dashboard showing the historical capacity data for 
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
cd ..
bokeh serve --show depot_dash
```
