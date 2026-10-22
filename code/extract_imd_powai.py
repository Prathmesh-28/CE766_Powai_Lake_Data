"""
Extract IMD 0.25 deg daily gridded rainfall (Pai et al. 2014) at Powai Lake and aggregate to monthly totals.

IMD yearly binary files: little-endian float32, shape (days, 129 lat, 135 lon), C order.
Grid: lat 6.5-38.5 N, lon 66.5-100.0 E, step 0.25 deg; missing value -999.
Powai (19.13 N, 72.91 E) is bilinearly interpolated from the four surrounding grid points:
    (19.00, 72.75), (19.00, 73.00), (19.25, 72.75), (19.25, 73.00)
    phi = (19.13 - 19.00)/0.25 = 0.52,  lam = (72.91 - 72.75)/0.25 = 0.64

Usage (needs internet access to imdpune.gov.in):
    python code/extract_imd_powai.py 2001 2025
Writes data/imd_rainfall_powai_daily.csv and data/imd_rainfall_powai_monthly_from_script.csv
"""
import os, sys, calendar
import numpy as np, pandas as pd

URL = "https://imdpune.gov.in/cmpg/Griddata/rainfall.php"   # form field: rain=<year>
NLAT, NLON, LAT0, LON0, STEP = 129, 135, 6.5, 66.5, 0.25
LAT, LON = 19.13, 72.91

def weights(lat=LAT, lon=LON):
    i0, j0 = int((lat - LAT0) // STEP), int((lon - LON0) // STEP)
    phi = (lat - (LAT0 + i0 * STEP)) / STEP
    lam = (lon - (LON0 + j0 * STEP)) / STEP
    return [(i0, j0, (1 - phi) * (1 - lam)), (i0, j0 + 1, (1 - phi) * lam),
            (i0 + 1, j0, phi * (1 - lam)), (i0 + 1, j0 + 1, phi * lam)]

def point_series(raw_bytes, year):
    a = np.frombuffer(raw_bytes, dtype="<f4")
    days = 366 if calendar.isleap(year) else 365
    if a.size != days * NLAT * NLON:
        raise ValueError(f"{year}: unexpected file size {a.size}")
    a = a.reshape(days, NLAT, NLON)
    out = np.zeros(days)
    for i, j, w in weights():
        x = a[:, i, j]
        if np.any(x < -900):
            raise ValueError(f"{year}: missing value at grid cell ({i}, {j})")
        out += w * x
    return pd.Series(out, index=pd.date_range(f"{year}-01-01", periods=days, freq="D"))

def download(year):
    import requests
    r = requests.post(URL, data={"rain": str(year)}, timeout=120)
    r.raise_for_status()
    return r.content

if __name__ == "__main__":
    y0, y1 = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) == 3 else (2001, 2025)
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    daily = pd.concat([point_series(download(y), y) for y in range(y0, y1 + 1)])
    daily.rename("rain_mm").to_csv(os.path.join(root, "data", "imd_rainfall_powai_daily.csv"), index_label="date")
    monthly = daily.groupby([daily.index.year, daily.index.month]).sum().unstack().round(1)
    monthly.to_csv(os.path.join(root, "data", "imd_rainfall_powai_monthly_from_script.csv"))
    print(monthly.sum(axis=1).describe())
