import geopandas as gpd
import folium
import numpy as np
import matplotlib.pyplot as plt
import webbrowser
import os
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from folium.plugins import HeatMap


# 1. Load Dataset and Reproject 

buildings = gpd.read_file('Sector_I.geojson').to_crs(epsg=32645)


# 2. Compute Area
 
buildings['area'] = buildings.geometry.area

 
# 3. Updated Population Estimation Model
 

# Select density factor based on region
rho = 0.15   # Urban
# rho = 0.07 # Semi-Urban
# rho = 0.03 # Rural

# Compute population for each building
buildings['population'] = (rho * buildings['area']).round().astype(int)

 
# 4. Compute Centroids
 
buildings['centroid'] = buildings.geometry.centroid
buildings['cent_x'] = buildings['centroid'].x
buildings['cent_y'] = buildings['centroid'].y

coords = buildings[['cent_x', 'cent_y']].values

 
# 5. Dynamic EPS
 
min_samples = 4
neighbors = NearestNeighbors(n_neighbors=min_samples)
neighbors_fit = neighbors.fit(coords)
distances, _ = neighbors_fit.kneighbors(coords)
k_distances = np.sort(distances[:, min_samples - 1])

eps_dynamic = np.percentile(k_distances, 96)

print("--- Analysis Report ---")
print(f"EPS selected: {eps_dynamic:.2f} meters")

 
# 6. DBSCAN Clustering
 
dbscan = DBSCAN(eps=eps_dynamic, min_samples=min_samples)
buildings['cluster'] = dbscan.fit_predict(coords)

 
# 7. Reassign ONLY DBSCAN Noise
 
area_noise_mask = (buildings['area'] < 20) | (buildings['area'] > 6000)
dbscan_noise_mask = (buildings['cluster'] == -1) & (~area_noise_mask)

noise = buildings[dbscan_noise_mask]
clustered = buildings[buildings['cluster'] != -1]

if len(noise) > 0 and len(clustered) > 0:
    nbrs = NearestNeighbors(n_neighbors=1).fit(clustered[['cent_x','cent_y']])
    distances, indices = nbrs.kneighbors(noise[['cent_x','cent_y']])
    nearest_clusters = clustered.iloc[indices.flatten()]['cluster'].values
    buildings.loc[dbscan_noise_mask, 'cluster'] = nearest_clusters

buildings.loc[area_noise_mask, 'cluster'] = -1

 
# 8. Weighted Center Function
 
def get_weighted_center(df):
    total_pop = df['population'].sum()
    if total_pop == 0:
        return df['cent_x'].mean(), df['cent_y'].mean()
    w_x = (df['cent_x'] * df['population']).sum() / total_pop
    w_y = (df['cent_y'] * df['population']).sum() / total_pop
    return w_x, w_y

clustered_data = buildings
final_x, final_y = get_weighted_center(clustered_data)

cluster_centers = {}
for c in clustered_data['cluster'].unique():
    subset = clustered_data[clustered_data['cluster'] == c]
    cluster_centers[c] = get_weighted_center(subset)

 
# 9. Convert to Lat/Lon
 
buildings_4326 = buildings.to_crs(epsg=4326)
centroids_4326 = gpd.GeoSeries(
    gpd.points_from_xy(buildings['cent_x'], buildings['cent_y']),
    crs=32645
).to_crs(epsg=4326)

final_point_gdf = gpd.GeoDataFrame(
    geometry=gpd.points_from_xy([final_x], [final_y]),
    crs=32645
).to_crs(epsg=4326)

final_lat = final_point_gdf.geometry.y.iloc[0]
final_lon = final_point_gdf.geometry.x.iloc[0]

 
# 10. Create Map
 
m = folium.Map(location=[final_lat, final_lon], zoom_start=15, tiles='CartoDB positron')

colors = ['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6']
buildings_to_map = buildings_4326.drop(columns=['centroid'])

folium.GeoJson(
    buildings_to_map,
    name="Building Clusters",
    style_function=lambda x: {
         'fillColor': '#808080' if x['properties']['cluster'] == -1
         else colors[x['properties']['cluster'] % len(colors)],
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=['area', 'population', 'cluster'],
        aliases=['Area (m²)', 'Estimated Population', 'Cluster ID']
    )
).add_to(m)

 
# 11. Heatmap
 
max_pop = buildings['population'].max()
heat_data = [[pt.y, pt.x, pop / max_pop] for pt, pop in zip(centroids_4326, buildings['population'])]
HeatMap(heat_data, name="Population Density", radius=15, blur=12).add_to(m)

 
# 12. Add Cluster Centers
 
cluster_group = folium.FeatureGroup(name="Cluster Centers")
for c, (cx, cy) in cluster_centers.items():
    if c == -1: continue
    cp_gdf = gpd.GeoDataFrame(geometry=gpd.points_from_xy([cx], [cy]), crs=32645).to_crs(epsg=4326)
    folium.CircleMarker(
        location=[cp_gdf.geometry.y.iloc[0], cp_gdf.geometry.x.iloc[0]],
        radius=8, color='blue', fill=True, fill_opacity=0.9, popup=f"Cluster {c} Center"
    ).add_to(cluster_group)
cluster_group.add_to(m)

 
# 13. Add Global Center
 
folium.Marker(
    location=[final_lat, final_lon],
    icon=folium.Icon(color='darkgreen', icon='star'),
    popup="Global Population Center"
).add_to(m)

folium.LayerControl().add_to(m)

 
# 14. Save & Final Execution
 
legend_html = """
<div style="position: fixed; bottom: 20px; left: 20px; background-color: white; border-radius: 10px; 
box-shadow: 0 3px 10px rgba(0,0,0,0.3); padding: 8px 12px; font-size:12px; z-index:9999;">
<b style="font-size:13px;">Map Legend</b><br>
<span style="color:darkgreen;">★</span> Global Center<br>
<span style="color:blue;">●</span> Cluster Center<br>
<div style="display:inline-block; width:10px; height:10px; background:gray; margin-right:5px;"></div> Noise/Outliers<br>
<div style="display:inline-block; width:10px; height:10px; background:red; margin-right:5px;"></div> Building Clusters
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))

output_file = 'Sector_I_Output.html'
m.save(output_file)

print("Map saved successfully!")
print(f"Total Buildings: {len(buildings)}")
print(f"Total Clusters: {len(cluster_centers)-1}")

# Automatically open the map in your default browser
webbrowser.open('file://' + os.path.realpath(output_file))