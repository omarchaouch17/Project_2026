# Suicide Mortality Rate in Tunisia — A Data Analysis (2000-2021)

Analysis of the suicide mortality rate in Tunisia over 22 years, based on WHO/World Bank Health Indicators.

## Data Source
World Bank Health Indicators for Tunisia, via [Humanitarian Data Exchange (HDX)](https://data.humdata.org/dataset/world-bank-health-indicators-for-tunisia)

## Method
- Loaded and cleaned the data with Pandas
- Extracted the suicide mortality rate (per 100,000 population) and visualized it over time
- Created both a static chart (matplotlib) and an animated GIF version

## Key Finding
The rate shows two notable declines: 2010→2011 (close to the Tunisian Revolution) and 2019→2020 (COVID-19 pandemic). Both periods coincide with major societal disruptions, which likely affected data collection itself — not just the underlying reality. The WHO itself notes that mental health data in Tunisia has historically been underestimated, due to gaps in reporting and a large share of cases never being formally recorded.

## Files
- `analyse.py` — full analysis code
- `suizidrate_tunesien.png` — static chart
- `suizidrate_animation.gif` — animated version

## Technical Details
- Language: Python
- Libraries: pandas, matplotlib

## A Note on Interpretation
A drop in a recorded rate is not automatically good news. In this case, it more likely reflects a disruption in data collection during periods of crisis than a genuine improvement in mental health outcomes — a reminder that health statistics need to be read in their social and political context, not taken at face value.