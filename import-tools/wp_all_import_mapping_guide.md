# WP All Import Pro Mapping Guide (WSF Snowpark Guide)

Diese Anleitung erklärt die Konfiguration des Imports in **WP All Import Pro** mit der bereinigten Datei `import-tools/wsf_park_guide_clean_import.csv` oder der Live Google Sheets CSV URL.

---

## 1. Import Erstellen
1. Gehe in WordPress zu **All Import > New Import**.
2. Wähle **Upload a file** (oder *Download from URL* für Google Sheets) und wähle `wsf_park_guide_clean_import.csv`.
3. Wähle im Dropdown **New Items** -> **Snowparks** (`snowpark`).
4. Klicke auf **Continue to Step 2** und **Continue to Step 3**.

---

## 2. Feld-Mapping (Step 3)

### Title & Content
- **Title:** `{park_name[1]}`
- **Content:** (Kann leer bleiben oder Standardtext z. B. `{park_name[1]} located at {resort_name[1]}, {region[1]} ({country[1]}).`)

### Taxonomies, Categories, Tags
- **Locations (`snowpark_location`):**
  - Wähle *Hierarchical (Parent > Child)*
  - Mapping: `{country[1]}` > `{region[1]}`
- **Facility Types (`facility_type`):**
  - Mapping: `{facility_type[1]}`

### Advanced Custom Fields (ACF Add-on Tab)
*Die Felder werden automatisch erkannt, wenn das ACF Add-on aktiv ist:*

| ACF Feld | Mapping Tag |
| :--- | :--- |
| **Park ID** | `{park_id[1]}` |
| **WSF Verified** | `{wsf_verified_bool[1]}` *(oder `[IF({wsf_verified[1]}="Yes")]1[ELSE]0[ENDIF]`)* |
| **Resort / Mountain Name** | `{resort_name[1]}` |
| **Elevation (masl)** | `{elevation_masl[1]}` |
| **Size Category** | `{size_category[1]}` |
| **Total Obstacles** | `{total_obstacles[1]}` |
| **Jump Count** | `{jump_count[1]}` |
| **Jib Count** | `{jib_count[1]}` |
| **Has Pipe** | `{has_pipe_bool[1]}` |
| **Pipe Type / Spec** | `{pipe_type[1]}` |
| **Progression Features** | `{progression_features_bool[1]}` |
| **Overall WSPL Stars** | `{overall_wspl_stars[1]}` |
| **Rating Beginner** | `{rating_beginner[1]}` |
| **Rating Intermediate** | `{rating_intermediate[1]}` |
| **Rating Advanced / Pro** | `{rating_advanced_pro[1]}` |
| **Shaper Crew** | `{shaper_crew[1]}` |
| **Daily Shape** | `{daily_shape_bool[1]}` |
| **Dedicated Groomer** | `{dedicated_groomer_bool[1]}` |
| **Dedicated Snowmaking**| `{dedicated_snowmaking_bool[1]}` |
| **Has Park Lift** | `{has_park_lift_bool[1]}` |
| **Has Nightpark** | `{has_nightpark_bool[1]}` |
| **Season Window** | `{season_window[1]}` |
| **Public Transit Score**| `{public_transit_score[1]}` |
| **Nearest Train Station**| `{nearest_train_station[1]}` |
| **Nearest Airport** | `{nearest_airport[1]}` |
| **Latitude** | `{latitude_clean[1]}` |
| **Longitude** | `{longitude_clean[1]}` |
| **Instagram Handle** | `{instagram_handle[1]}` |
| **Official Website URL**| `{website_url[1]}` |
| **Event Calendar URL** | `{event_calendar_url[1]}` |

---

## 3. Unique Identifier & Update-Regeln (Step 4)

1. Klicke auf **Auto-detect** oder trage manuell als **Unique Identifier** ein:
   ```
   {park_id[1]}
   ```
2. Unter **When WP All Import finds existing data:**
   - Wähle: **Update existing posts with the data in your file**
   - Wähle: **Choose which data to update**
   - Hake an: *Custom Fields* (damit tägliche Obstacle- oder Status-Änderungen überschrieben werden)
   - *Nicht anhaken:* Post Content & Author (damit manuelle redaktionelle Texte erhalten bleiben).

---

## 4. Automatisierter Cronjob (Hosting)

Sobald der Import gespeichert ist (z. B. Import ID = `1`), im Server-Crontab eintragen:

```bash
# Trigger-Cron: 1x täglich um 03:00 Uhr
0 3 * * * curl -s "https://DEINE-DOMAIN.com/wp-load.php?import_key=DEIN_KEY&import_id=1&action=trigger" > /dev/null 2>&1

# Processing-Cron: Alle 2 Minuten bis fertig
*/2 * * * * curl -s "https://DEINE-DOMAIN.com/wp-load.php?import_key=DEIN_KEY&import_id=1&action=processing" > /dev/null 2>&1
```
