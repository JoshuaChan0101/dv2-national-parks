## What this repository is
 
A single scrolling web page that compares wildlife in 12 Australian national parks, built with Vega-Lite. It follows the assigned topic, *National Park Wildlife*: compare species diversity, conservation status and visitor observations across parks, and show why protected areas matter for biodiversity.
 
The 12 parks are Uluru-Kata Tjuta, Kakadu, Ikara-Flinders Ranges, Daintree, Blue Mountains, Cradle Mountain-Lake St Clair, Kalbarri, Freycinet, Wilsons Promontory, Flinders Chase, Karijini and the Grampians. The page is for the average Australian who visits parks and wants to know where the wildlife is, which animals are threatened, and when to go.
 
## How the folder is organised
 
| Path | Purpose |
|---|---|
| `index.html` | The web page: story text, layout, styling, sources, notes. It loads the charts with Vega-Embed. |
| `specs/` | One Vega-Lite JSON file per chart (readable, indented). Each file loads its data from `data/`. |
| `data/` | The four data files the charts read (see below). |
| `prep_data.py` | Script that builds `park_species.csv` and `observations.csv` from the raw ALA downloads. Included so the data processing can be checked. |
| `sketch.pdf` | The hand-drawn sketch the page was built from. |
 
To view the page locally, open the folder in VS Code and run `index.html` with the Live Server extension. Opening the file directly will not work, because browsers block local JSON loading.
 
## The charts (`specs/`)
 
| File | Chart | Idiom |
|---|---|---|
| `01_richness_map.json` | Which parks hold the most wildlife? | Proportional-symbol map: size = species, colour = threatened species |
| `09_species_area_scatter.json` | Do bigger parks hold more species? | Scatter plot on log axes with fitted trend line and annotations |
| `02_animal_group_maps.json` | Different parks, different animals | Symbol map with radio buttons for birds, mammals, reptiles, frogs (fixed circle scale) |
| `04_park_group_heatmap.json` | The mix of wildlife in each park | Heatmap, park by animal group |
| `03_species_finder_map.json` | Where could you see it? | Symbol map with a dropdown to choose an animal |
| `05_threatened_waffles.json` | Threatened animals inside each park | Waffle (unit) chart, small multiples by park |
| `10_most_seen_threatened.json` | Threatened animals visitors see most | Lollipop chart |
| `06_parallel_coordinates.json` | Comparing parks side by side | Parallel coordinates, each axis scaled lowest to highest, hover highlight |
| `08_park_season_heatmap.json` | When do visitors log wildlife? | Heatmap, month by park (parks ordered north to south) |
| `07_observations_streamgraph.json` | Sightings logged year by year | Streamgraph by animal group |
 
The numbering follows the order the charts were built; on the page they appear in four sections: Which parks hold the most wildlife?, Who lives where?, Why protected areas matter, and When do visitors see wildlife?
 
## Data (`data/`)
 
| File | Columns | What it is and where it comes from |
|---|---|---|
| `states.topojson` | object `states`, property `STATE_NAME` | State and territory outlines used only as the map background. Source: [rowanhogan/australian-states](https://github.com/rowanhogan/australian-states), converted to TopoJSON with mapshaper.org. |
| `parks.csv` | `park, state, area_ha, lat, lon` | One row for each of the 12 parks. From CAPAD 2024 Terrestrial (DCCEEW, data.gov.au). Only national-park rows were kept and all pieces of a park were added up. Area is the gazetted area, or the area calculated from the boundary where the gazetted figure was 0. The map point is the centre of the park's largest piece. |
| `park_species.csv` | `park, species, common, class, status, records` | One row per species per park: scientific name, common name, animal group (Birds, Mammals, Reptiles, Frogs), national conservation status (Critically Endangered, Endangered, Vulnerable or Not listed) and number of sightings. Built by `prep_data.py` from Atlas of Living Australia (ALA) records. |
| `observations.csv` | `park, class, year, month, records` | Sightings per park, animal group, year and month. Built by `prep_data.py` from the same ALA records. |
