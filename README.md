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

![Output Map](Sector_I_Output_Screenshot.png)

## How to Run

```bash
py -3.11 -m venv venv311
venv311\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Dataset

* Small datasets are included in the repository
* Large dataset (`Maghyamgram_2km.zip`) must be extracted before running

## Files

* `main.py` – main code
* `data/` – dataset files
* `requirements.txt` – dependencies


## Authors

* Rejuanul Karim – B.Tech CSE Student
* Debalina Paul – B.Tech CSE Student
* Kalyan Kumar Das – Supervisor
* Anirban Mukhopadhyay – Co-Supervisor
