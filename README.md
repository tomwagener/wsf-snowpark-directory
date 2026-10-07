# WSF Snowpark Directory & Core Plugin

Official programmatic Snowpark Guide & Directory platform for the **World Snowboard Federation (WSF)**.

## Project Structure

* **`wordpress-snowpark-plugin/`**: Custom WordPress plugin providing:
  * Custom Post Type (`snowpark`) and Taxonomies (`snowpark_location`, `facility_type`).
  * 34-column ACF Pro field group auto-loader.
  * Native CSV and automated Google Sheets background sync engine (WP Cron).
  * Single Snowpark dynamic template (Hero, 4-column Quick-Stats, Level Breakdown, Pipe Specs, Infrastructure & Transit).
  * Directory Archive shortcode `[wsf_snowpark_directory]` with real-time AJAX filtering (Search, Country, Facility Type, Superpipe, Nightpark, WSF Verified).
  * Yoast SEO Schema.org JSON-LD integration (`SportsActivityLocation`, `SkiResort`, GeoCoordinates, Ratings).
* **`wsf_park_guide_master.csv` & `wsf_park_guide_master.xlsx`**: Canonical master dataset of 175+ snowparks across 20+ countries.
* **`import-tools/`**: Utilities and clean import CSVs.
* **`acf-json/`**: ACF field group JSON definitions.
* **`build_park_guide.py` & `build_wp_assets.py`**: Data compilation and asset generation pipelines.

## License

All rights reserved © World Snowboard Federation (WSF).
