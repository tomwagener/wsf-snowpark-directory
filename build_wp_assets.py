import csv
import json
import re

def parse_coord(val):
    if not val:
        return ""
    val = str(val).strip()
    if "." in val:
        return float(val)
    # E.g. 42581 -> 42.581, -41171 -> -41.171
    if val.startswith("-"):
        prefix = val[:3]
        suffix = val[3:]
        return float(f"{prefix}.{suffix}")
    else:
        prefix = val[:2]
        suffix = val[2:]
        return float(f"{prefix}.{suffix}")

# 1. Clean CSV for WP All Import
input_csv = "wsf_park_guide_master.csv"
output_csv = "import-tools/wsf_park_guide_clean_import.csv"

rows = []
with open(input_csv, "r", encoding="utf-8") as f:
    # Skip potential broken header lines
    lines = [line for line in f if line.strip() and not line.startswith("wsf_park_guide_master,,,,")]
    reader = csv.DictReader(lines)
    for row in reader:
        # Normalize booleans to 1/0 for ACF
        for bool_field in ["has_pipe", "progression_features", "has_park_lift", "dedicated_groomer", 
                           "daily_shape", "dedicated_snowmaking", "has_nightpark", "wsf_verified"]:
            val = row.get(bool_field, "").strip().lower()
            row[bool_field + "_bool"] = "1" if val in ["yes", "1", "true"] else "0"
        
        # Clean coordinates
        try:
            row["latitude_clean"] = str(parse_coord(row.get("latitude", "")))
            row["longitude_clean"] = str(parse_coord(row.get("longitude", "")))
        except:
            row["latitude_clean"] = row.get("latitude", "")
            row["longitude_clean"] = row.get("longitude", "")

        rows.append(row)

if rows:
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Generated clean import CSV with {len(rows)} records at {output_csv}")

# 2. Build ACF JSON field group
acf_group = {
    "key": "group_snowpark_details",
    "title": "Snowpark Details & Specifications",
    "fields": [
        {
            "key": "field_sp_tab_sys",
            "label": "System & Identification",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_id",
            "label": "Park ID",
            "name": "park_id",
            "type": "text",
            "required": 1
        },
        {
            "key": "field_sp_verified",
            "label": "WSF Verified",
            "name": "wsf_verified",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_resort",
            "label": "Resort / Mountain Name",
            "name": "resort_name",
            "type": "text"
        },
        {
            "key": "field_sp_elev",
            "label": "Elevation (masl)",
            "name": "elevation_masl",
            "type": "text"
        },
        {
            "key": "field_sp_tab_setup",
            "label": "Obstacles & Park Setup",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_size_cat",
            "label": "Size Category",
            "name": "size_category",
            "type": "select",
            "choices": {
                "20 to 39 Features": "20 to 39 Features",
                "40 to 79 Features": "40 to 79 Features",
                "80+ Features": "80+ Features"
            }
        },
        {
            "key": "field_sp_obst_total",
            "label": "Total Obstacles",
            "name": "total_obstacles",
            "type": "number"
        },
        {
            "key": "field_sp_jumps",
            "label": "Jump Count",
            "name": "jump_count",
            "type": "number"
        },
        {
            "key": "field_sp_jibs",
            "label": "Jib Count",
            "name": "jib_count",
            "type": "number"
        },
        {
            "key": "field_sp_has_pipe",
            "label": "Has Pipe",
            "name": "has_pipe",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_pipe_type",
            "label": "Pipe Type / Spec",
            "name": "pipe_type",
            "type": "text",
            "conditional_logic": [
                [
                    {
                        "field": "field_sp_has_pipe",
                        "operator": "==",
                        "value": "1"
                    }
                ]
            ]
        },
        {
            "key": "field_sp_progression",
            "label": "Progression Features",
            "name": "progression_features",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_tab_ratings",
            "label": "Ratings & WSPL Stars",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_wspl_stars",
            "label": "Overall WSPL Stars",
            "name": "overall_wspl_stars",
            "type": "number",
            "min": 1,
            "max": 5
        },
        {
            "key": "field_sp_rate_beg",
            "label": "Rating Beginner / Easy Lines",
            "name": "rating_beginner",
            "type": "number",
            "min": 1,
            "max": 5
        },
        {
            "key": "field_sp_rate_int",
            "label": "Rating Intermediate / Medium Lines",
            "name": "rating_intermediate",
            "type": "number",
            "min": 1,
            "max": 5
        },
        {
            "key": "field_sp_rate_adv",
            "label": "Rating Advanced Lines",
            "name": "rating_advanced",
            "type": "number",
            "min": 1,
            "max": 5
        },
        {
            "key": "field_sp_rate_pro_xl",
            "label": "Rating Pro / XL Lines",
            "name": "rating_pro_xl",
            "type": "number",
            "min": 1,
            "max": 5
        },
        {
            "key": "field_sp_tab_infra",
            "label": "Infrastructure & Shaping",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_shaper_crew",
            "label": "Shaper Crew",
            "name": "shaper_crew",
            "type": "text"
        },
        {
            "key": "field_sp_daily_shape",
            "label": "Daily Shape",
            "name": "daily_shape",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_groomer",
            "label": "Dedicated Groomer",
            "name": "dedicated_groomer",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_snowmaking",
            "label": "Dedicated Snowmaking",
            "name": "dedicated_snowmaking",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_has_lift",
            "label": "Has Park Lift",
            "name": "has_park_lift",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_has_nightpark",
            "label": "Has Nightpark",
            "name": "has_nightpark",
            "type": "true_false",
            "ui": 1
        },
        {
            "key": "field_sp_season",
            "label": "Season Window",
            "name": "season_window",
            "type": "text"
        },
        {
            "key": "field_sp_tab_travel",
            "label": "Travel & Geo Location",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_transit",
            "label": "Public Transit Score",
            "name": "public_transit_score",
            "type": "select",
            "choices": {
                "Good": "Good",
                "Moderate": "Moderate",
                "Poor": "Poor"
            }
        },
        {
            "key": "field_sp_train",
            "label": "Nearest Train Station",
            "name": "nearest_train_station",
            "type": "text"
        },
        {
            "key": "field_sp_airport",
            "label": "Nearest Airport",
            "name": "nearest_airport",
            "type": "text"
        },
        {
            "key": "field_sp_lat",
            "label": "Latitude",
            "name": "latitude",
            "type": "number",
            "step": "any"
        },
        {
            "key": "field_sp_lng",
            "label": "Longitude",
            "name": "longitude",
            "type": "number",
            "step": "any"
        },
        {
            "key": "field_sp_tab_links",
            "label": "Links & Social Media",
            "type": "tab",
            "placement": "top"
        },
        {
            "key": "field_sp_insta",
            "label": "Instagram Handle",
            "name": "instagram_handle",
            "type": "text"
        },
        {
            "key": "field_sp_website",
            "label": "Official Website URL",
            "name": "website_url",
            "type": "url"
        },
        {
            "key": "field_sp_events",
            "label": "Event Calendar URL",
            "name": "event_calendar_url",
            "type": "url"
        }
    ],
    "location": [
        [
            {
                "param": "post_type",
                "operator": "==",
                "value": "snowpark"
            }
        ]
    ],
    "menu_order": 0,
    "position": "normal",
    "style": "default",
    "label_placement": "top",
    "instruction_placement": "label",
    "hide_on_screen": "",
    "active": True,
    "description": "ACF Pro field group for WSF Snowpark Directory matching wsf_park_guide_master.csv",
    "show_in_rest": 1
}

with open("wordpress-snowpark-plugin/acf-json/group_snowpark_details.json", "w", encoding="utf-8") as f:
    json.dump(acf_group, f, indent=2)

with open("acf-json/group_snowpark_details.json", "w", encoding="utf-8") as f:
    json.dump(acf_group, f, indent=2)

print("Generated ACF JSON field group.")
