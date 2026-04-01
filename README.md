
# Geospatial Population Estimation and Clustering

## Overview

This project estimates population at building level using GIS data and identifies clusters using a machine learning approach. Results are visualized on an interactive map.

## Features

* Area-based population estimation
* Automatic clustering of buildings
* Population density heatmap
* Cluster centers and global center

## Output

* Interactive HTML map with clusters and population distribution

## Screenshot

![Output Map](output.png)


## How to Run

```bash
py -3.11 -m venv venv311
venv311\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Files

* `main.py` – main code
* `Gorabazar.geojson` – dataset
* `requirements.txt` – dependencies

## Author

Rejuanul Karim

