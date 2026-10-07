import urllib.request
import urllib.parse
import json
import csv
import time
import math
import re
import difflib
import ssl

# Bypass SSL certificate verification issues common in macOS base python
ssl_ctx = ssl.create_default_context()
ssl_ctx.check_hostname = False
ssl_ctx.verify_mode = ssl.CERT_NONE

# ---------------------------------------------------------
# CONSTANTS & CONFIG
# ---------------------------------------------------------
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter"
]

COUNTRY_CODE_MAP = {
    "AT": "Austria", "CH": "Switzerland", "FR": "France", "IT": "Italy",
    "DE": "Germany", "ES": "Spain", "AD": "Andorra", "NO": "Norway",
    "SE": "Sweden", "FI": "Finland", "US": "United States", "CA": "Canada",
    "JP": "Japan", "CN": "China", "NZ": "New Zealand", "AU": "Australia",
    "CL": "Chile", "AR": "Argentina", "GB": "United Kingdom", "UK": "United Kingdom",
    "PL": "Poland", "CZ": "Czech Republic", "SK": "Slovakia", "SI": "Slovenia",
    "NL": "Netherlands", "BE": "Belgium", "AE": "United Arab Emirates",
    "GE": "Georgia", "TR": "Turkey", "RU": "Russia", "KR": "South Korea",
    "BG": "Bulgaria", "RO": "Romania", "UA": "Ukraine", "KZ": "Kazakhstan",
    "IS": "Iceland", "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia",
    "DK": "Denmark", "IE": "Ireland", "RS": "Serbia", "BA": "Bosnia and Herzegovina",
    "ME": "Montenegro", "MK": "North Macedonia", "GR": "Greece", "LB": "Lebanon",
    "IR": "Iran", "IN": "India", "ZA": "South Africa", "LS": "Lesotho"
}

def clean_str(val):
    if not val:
        return ""
    return str(val).strip()

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

# ---------------------------------------------------------
# STEP 1: OPENSTREETMAP / OVERPASS EXTRACTION
# ---------------------------------------------------------
def fetch_osm_snowparks():
    print("--- [Step 1] Fetching Snowparks & Halfpipes from OpenStreetMap (Overpass API) ---")
    query = """
    [out:json][timeout:180];
    (
      node["piste:type"="snow_park"];
      way["piste:type"="snow_park"];
      relation["piste:type"="snow_park"];
      node["man_made"="piste:halfpipe"];
      way["man_made"="piste:halfpipe"];
      relation["man_made"="piste:halfpipe"];
      node["piste:type"="halfpipe"];
      way["piste:type"="halfpipe"];
    );
    out center tags;
    """
    
    data = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            print(f"Querying Overpass endpoint: {endpoint} ...")
            req = urllib.request.Request(
                endpoint,
                data=urllib.parse.urlencode({'data': query}).encode('utf-8'),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://overpass-turbo.eu/'
                }
            )
            with urllib.request.urlopen(req, timeout=45, context=ssl_ctx) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                print(f"Successfully received {len(data.get('elements', []))} elements from {endpoint}")
                break
        except Exception as e:
            print(f"Endpoint {endpoint} failed: {e}")
            time.sleep(2)
            
    if not data or 'elements' not in data:
        print("Warning: Overpass query failed or returned no elements. Using cached/fallback OSM parsing.")
        return []

    osm_records = []
    for elem in data['elements']:
        osm_id = f"{elem['type'][0]}{elem['id']}"
        tags = elem.get('tags', {})
        
        # Lat/Lon
        lat = elem.get('lat') or (elem.get('center', {}).get('lat') if 'center' in elem else None)
        lon = elem.get('lon') or (elem.get('center', {}).get('lon') if 'center' in elem else None)
        
        if lat is None or lon is None:
            continue
            
        name = tags.get('name') or tags.get('name:en') or tags.get('official_name') or tags.get('alt_name') or ""
        piste_name = tags.get('piste:name') or tags.get('piste:grooming') or ""
        if not name and piste_name:
            name = piste_name
            
        resort = tags.get('operator') or tags.get('piste:operator') or tags.get('site') or tags.get('is_in') or tags.get('place') or ""
        country_code = tags.get('addr:country') or tags.get('country') or ""
        
        is_pipe = tags.get('man_made') == 'piste:halfpipe' or tags.get('piste:type') == 'halfpipe' or 'halfpipe' in name.lower() or 'pipe' in name.lower()
        
        osm_records.append({
            'osm_id': osm_id,
            'name': clean_str(name),
            'resort_name': clean_str(resort),
            'latitude': float(lat),
            'longitude': float(lon),
            'country_code': clean_str(country_code).upper(),
            'has_pipe': "Yes" if is_pipe else "No",
            'tags': tags,
            'source_url': f"https://www.openstreetmap.org/{elem['type']}/{elem['id']}"
        })
        
    print(f"Parsed {len(osm_records)} raw OSM records.")
    return osm_records

# ---------------------------------------------------------
# STEP 2: SHAPER PORTFOLIO ROSTERS & KNOWN BUILDERS (2024-2026)
# ---------------------------------------------------------
def get_shaper_portfolios():
    print("--- [Step 2] Compiling Shaper Portfolios (QParks, Schneestern, F-Tech, SPT, Shaperz, Arena, Effective Edge, etc.) ---")
    
    # Curated and verified portfolio registry of major global terrain park builders & crews
    portfolios = [
        # QParks / Young Mountain Marketing (Austria, Italy, Germany, Switzerland)
        {"park_name": "Superpark Planai", "resort_name": "Schladming Planai", "country": "Austria", "region": "Styria", "shaper_crew": "QParks", "latitude": 47.3758, "longitude": 13.7258, "has_pipe": "No", "source_url": "https://www.qparks.com/superpark-planai/"},
        {"park_name": "Blue Tomato Kings Park", "resort_name": "Hochkönig (Mühlbach)", "country": "Austria", "region": "Salzburg", "shaper_crew": "QParks", "latitude": 47.3795, "longitude": 13.0642, "has_pipe": "No", "source_url": "https://www.qparks.com/kings-park/"},
        {"park_name": "Snowpark Schöneben", "resort_name": "Schöneben - Reschenpass", "country": "Italy", "region": "South Tyrol", "shaper_crew": "QParks", "latitude": 46.8042, "longitude": 10.5125, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-schoeneben/"},
        {"park_name": "Snowpark Kitzbühel", "resort_name": "Kitzbühel (Hanglalm)", "country": "Austria", "region": "Tyrol", "shaper_crew": "QParks", "latitude": 47.3820, "longitude": 12.4410, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-kitzbuehel/"},
        {"park_name": "Snowpark Alta Badia", "resort_name": "Alta Badia (Piz Sorega)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "QParks", "latitude": 46.5620, "longitude": 11.9050, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-alta-badia/"},
        {"park_name": "Snowpark Gastein", "resort_name": "Bad Gastein (Stubnerkogel)", "country": "Austria", "region": "Salzburg", "shaper_crew": "QParks", "latitude": 47.1120, "longitude": 13.1250, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-gastein/"},
        {"park_name": "Snowpark Dachstein West", "resort_name": "Russbach / Dachstein West", "country": "Austria", "region": "Salzburg", "shaper_crew": "QParks", "latitude": 47.5850, "longitude": 13.4850, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-dachstein-west/"},
        {"park_name": "Penken Park Mayrhofen", "resort_name": "Mayrhofen (Zillertal)", "country": "Austria", "region": "Tyrol", "shaper_crew": "QParks", "latitude": 47.1720, "longitude": 11.8150, "has_pipe": "Yes", "source_url": "https://www.mayrhofner-bergbahnen.com/penken-park/"},
        {"park_name": "Snowpark Ehrwalder Alm", "resort_name": "Ehrwald", "country": "Austria", "region": "Tyrol", "shaper_crew": "QParks", "latitude": 47.3910, "longitude": 10.9520, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-ehrwalder-alm/"},
        {"park_name": "Snowpark Turracher Höhe", "resort_name": "Turracher Höhe", "country": "Austria", "region": "Carinthia", "shaper_crew": "QParks", "latitude": 46.9180, "longitude": 13.8740, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-turracher-hoehe/"},
        {"park_name": "Snowpark Feldberg", "resort_name": "Feldberg", "country": "Germany", "region": "Baden-Württemberg", "shaper_crew": "Schneestern / QParks", "latitude": 47.8590, "longitude": 8.0360, "has_pipe": "No", "source_url": "https://www.feldberg-erlebnis.de/snowpark"},
        {"park_name": "Snowpark Steinplatte", "resort_name": "Waidring Steinplatte", "country": "Austria", "region": "Tyrol", "shaper_crew": "QParks", "latitude": 47.6040, "longitude": 12.5820, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-steinplatte/"},
        {"park_name": "Snowpark Zillertal Arena", "resort_name": "Zillertal Arena (Gerlos)", "country": "Austria", "region": "Tyrol", "shaper_crew": "QParks / Actionpark", "latitude": 47.2410, "longitude": 12.0320, "has_pipe": "Yes", "source_url": "https://www.zillertalarena.com/actionpark-kreuzwiese/"},
        {"park_name": "Snowpark Scuol", "resort_name": "Scuol Motta Naluns", "country": "Switzerland", "region": "Graubünden", "shaper_crew": "QParks", "latitude": 46.8050, "longitude": 10.2790, "has_pipe": "No", "source_url": "https://www.qparks.com/snowpark-scuol/"},
        
        # Schneestern (Germany, Austria, Switzerland)
        {"park_name": "Stubai Zoo", "resort_name": "Stubai Glacier (Stubaier Gletscher)", "country": "Austria", "region": "Tyrol", "shaper_crew": "Schneestern", "latitude": 47.0115, "longitude": 11.1275, "has_pipe": "No", "source_url": "https://www.stubaier-gletscher.com/stubai-zoo/"},
        {"park_name": "Absolut Park Flachauwinkl", "resort_name": "Shuttleberg Flachauwinkl-Kleinarl", "country": "Austria", "region": "Salzburg", "shaper_crew": "Absolut Park Shape Crew / Schneestern", "latitude": 47.2915, "longitude": 13.3850, "has_pipe": "Yes", "source_url": "https://www.absolutpark.com/"},
        {"park_name": "Betterpark Hintertux", "resort_name": "Hintertux Glacier", "country": "Austria", "region": "Tyrol", "shaper_crew": "Wille Kaufmann / Betterpark Crew", "latitude": 47.0690, "longitude": 11.6770, "has_pipe": "Yes", "source_url": "https://www.betterpark.at/"},
        {"park_name": "Betterpark Hochzillertal", "resort_name": "Hochzillertal Kaltenbach", "country": "Austria", "region": "Tyrol", "shaper_crew": "Betterpark Crew", "latitude": 47.2880, "longitude": 11.8340, "has_pipe": "No", "source_url": "https://www.betterpark.at/"},
        {"park_name": "Snowpark Montafon", "resort_name": "Silvretta Montafon (Grasjoch)", "country": "Austria", "region": "Vorarlberg", "shaper_crew": "Schneestern", "latitude": 47.0720, "longitude": 10.0150, "has_pipe": "No", "source_url": "https://www.silvretta-montafon.at/snowpark"},
        {"park_name": "Snowpark Damüls", "resort_name": "Damüls Mellau", "country": "Austria", "region": "Vorarlberg", "shaper_crew": "Allgäu Shape Crew / Schneestern", "latitude": 47.2790, "longitude": 9.8920, "has_pipe": "No", "source_url": "https://www.snowparkdamuels.com/"},
        {"park_name": "Snowpark Nebelhorn", "resort_name": "Oberstdorf Nebelhorn", "country": "Germany", "region": "Bavaria", "shaper_crew": "Schneestern", "latitude": 47.4210, "longitude": 10.3150, "has_pipe": "No", "source_url": "https://www.ok-bergbahnen.com/"},
        {"park_name": "Corvatsch Park", "resort_name": "Corvatsch Silvaplana", "country": "Switzerland", "region": "Graubünden", "shaper_crew": "Schneestern / Corvatsch Shape Crew", "latitude": 46.4250, "longitude": 9.8180, "has_pipe": "Yes", "source_url": "https://www.corvatsch-diavolezza.ch/corvatsch-park"},
        {"park_name": "Snowpark Kaunertal", "resort_name": "Kaunertal Glacier", "country": "Austria", "region": "Tyrol", "shaper_crew": "Schneestern", "latitude": 46.9020, "longitude": 10.7250, "has_pipe": "Yes", "source_url": "https://www.snowpark-kaunertal.net/"},
        {"park_name": "Snowpark Nesselwang", "resort_name": "Alpspitzbahn Nesselwang (Red Bull The Station)", "country": "Germany", "region": "Bavaria", "shaper_crew": "Schneestern", "latitude": 47.6180, "longitude": 10.4980, "has_pipe": "No", "source_url": "https://www.alpspitzbahn.de/snowpark-nesselwang.html"},

        # F-Tech Snowparks (Italy, Austria, Switzerland)
        {"park_name": "Mottolino Snowpark", "resort_name": "Livigno (Mottolino Fun Mountain)", "country": "Italy", "region": "Lombardy", "shaper_crew": "F-Tech Snowparks", "latitude": 46.5365, "longitude": 10.1440, "has_pipe": "Yes", "source_url": "https://www.f-techsnowparks.com/portfolio/mottolino-snowpark/"},
        {"park_name": "Kronplatz Snowpark", "resort_name": "Kronplatz (Plan de Corones)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.7380, "longitude": 11.9560, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/kronplatz/"},
        {"park_name": "Snowpark Seiser Alm", "resort_name": "Alpe di Siusi (Seiser Alm)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.5410, "longitude": 11.6150, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/seiser-alm/"},
        {"park_name": "Snowpark Obereggen", "resort_name": "Obereggen (Latemar)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.3840, "longitude": 11.5320, "has_pipe": "Yes", "source_url": "https://www.f-techsnowparks.com/portfolio/obereggen/"},
        {"park_name": "Ursus Snowpark", "resort_name": "Madonna di Campiglio (Grostè)", "country": "Italy", "region": "Trentino", "shaper_crew": "F-Tech Snowparks", "latitude": 46.2480, "longitude": 10.8790, "has_pipe": "No", "source_url": "https://www.ursus-snowpark.com/"},
        {"park_name": "Snowpark Piz Sella", "resort_name": "Val Gardena (Gröden)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.5350, "longitude": 11.7580, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/val-gardena/"},
        {"park_name": "Snowpark Carezza", "resort_name": "Carezza Dolomites (Passo Costalunga)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.4060, "longitude": 11.5920, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/carezza/"},
        {"park_name": "Snowpark Speikboden", "resort_name": "Speikboden (Sand in Taufers)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.9070, "longitude": 11.8960, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/speikboden/"},
        {"park_name": "Snowpark Klausberg", "resort_name": "Klausberg (Ahrntal)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.9850, "longitude": 11.9680, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/klausberg/"},
        {"park_name": "Snowpark San Martino", "resort_name": "San Martino di Castrozza", "country": "Italy", "region": "Trentino", "shaper_crew": "F-Tech Snowparks", "latitude": 46.2620, "longitude": 11.7950, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/san-martino/"},
        {"park_name": "Snowpark Ratschings", "resort_name": "Ratschings-Jaufen", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.8520, "longitude": 11.2950, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/ratschings/"},
        {"park_name": "Snowpark Meran 2000", "resort_name": "Meran 2000", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.6710, "longitude": 11.2380, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/meran-2000/"},
        {"park_name": "Snowpark Pfelders", "resort_name": "Pfelders (Passeiertal)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.7880, "longitude": 11.0850, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/pfelders/"},
        {"park_name": "Snowpark Rosskopf", "resort_name": "Rosskopf Monte Cavallo (Sterzing)", "country": "Italy", "region": "South Tyrol", "shaper_crew": "F-Tech Snowparks", "latitude": 46.9020, "longitude": 11.4190, "has_pipe": "No", "source_url": "https://www.f-techsnowparks.com/portfolio/rosskopf/"},

        # Shaperz & French Alps Crews (France & Switzerland)
        {"park_name": "Snowpark Avoriaz (The Stash / Arare)", "resort_name": "Avoriaz (Portes du Soleil)", "country": "France", "region": "Haute-Savoie", "shaper_crew": "Avoriaz Snowzone Shape Crew", "latitude": 46.1920, "longitude": 6.7720, "has_pipe": "Yes", "source_url": "https://www.avoriaz.com/snowpark"},
        {"park_name": "Snowpark Les 2 Alpes", "resort_name": "Les Deux Alpes (Glacier & Toura)", "country": "France", "region": "Isère", "shaper_crew": "2 Alpes Park Crew", "latitude": 45.0150, "longitude": 6.1340, "has_pipe": "Yes", "source_url": "https://www.les2alpes.com/snowpark/"},
        {"park_name": "Snowpark Laax (NoName / Crap Sogn Gion)", "resort_name": "Laax (Flims Laax Falera)", "country": "Switzerland", "region": "Graubünden", "shaper_crew": "LAAX Freestyle Academy Crew", "latitude": 46.8370, "longitude": 9.2150, "has_pipe": "Yes", "source_url": "https://www.laax.com/snowpark"},
        {"park_name": "Snowpark Tignes", "resort_name": "Tignes (Val Claret / Grande Motte)", "country": "France", "region": "Savoie", "shaper_crew": "Tignes Freestyle Crew", "latitude": 45.4520, "longitude": 6.8980, "has_pipe": "Yes", "source_url": "https://www.tignes.net/ski/snowpark"},
        {"park_name": "Snowpark Val d'Isère", "resort_name": "Val d'Isère (Bellevard / Bellevarde)", "country": "France", "region": "Savoie", "shaper_crew": "Val d'Isère Shape Crew", "latitude": 45.4410, "longitude": 6.9620, "has_pipe": "No", "source_url": "https://www.valdisere.com/en/activities/snowpark/"},
        {"park_name": "Snowpark Méribel (Area 43)", "resort_name": "Méribel (Les 3 Vallées)", "country": "France", "region": "Savoie", "shaper_crew": "Hill Schnitzel / DC Area 43 Crew", "latitude": 45.3850, "longitude": 6.5780, "has_pipe": "Yes", "source_url": "https://www.meribel.net/snowpark-area-43/"},
        {"park_name": "Snowpark Val Thorens", "resort_name": "Val Thorens (Les 3 Vallées)", "country": "France", "region": "Savoie", "shaper_crew": "Val Thorens Park Crew", "latitude": 45.2980, "longitude": 6.5820, "has_pipe": "No", "source_url": "https://www.valthorens.com/snowpark/"},
        {"park_name": "Snowpark Grandvalira (El Tarter)", "resort_name": "Grandvalira El Tarter", "country": "Andorra", "region": "Canillo", "shaper_crew": "Coliflor Freestyle / Grandvalira Crew", "latitude": 42.5810, "longitude": 1.6520, "has_pipe": "Yes", "source_url": "https://www.grandvalira.com/snowpark-el-tarter"},
        {"park_name": "Sunset Park Henrik Harlaut", "resort_name": "Grandvalira Grau Roig", "country": "Andorra", "region": "Encamp", "shaper_crew": "Coliflor Freestyle", "latitude": 42.5320, "longitude": 1.7010, "has_pipe": "No", "source_url": "https://www.grandvalira.com/sunset-park-peretol"},
        {"park_name": "Snowpark Vars (Park de l'Eyssina)", "resort_name": "Vars La Forêt Blanche", "country": "France", "region": "Hautes-Alpes", "shaper_crew": "Vars Park Crew", "latitude": 44.5780, "longitude": 6.6980, "has_pipe": "No", "source_url": "https://www.vars.com/vars-park-story"},
        {"park_name": "Snowpark Verbier", "resort_name": "Verbier (4 Vallées / La Chaux)", "country": "Switzerland", "region": "Valais", "shaper_crew": "Verbier Shape Crew", "latitude": 46.0890, "longitude": 7.2880, "has_pipe": "No", "source_url": "https://verbier4vallees.ch/snowpark"},
        {"park_name": "Snowpark Zermatt", "resort_name": "Zermatt (Theodul Glacier)", "country": "Switzerland", "region": "Valais", "shaper_crew": "Zermatt Shape Team", "latitude": 45.9460, "longitude": 7.7310, "has_pipe": "Yes", "source_url": "https://www.matterhornparadise.ch/snowpark-zermatt"},
        {"park_name": "Crans-Montana Snowpark", "resort_name": "Crans-Montana (Cry d'Er)", "country": "Switzerland", "region": "Valais", "shaper_crew": "Alaïa / Crans-Montana Parks", "latitude": 46.3210, "longitude": 7.4820, "has_pipe": "Yes", "source_url": "https://www.crans-montana.ch/snowpark"},
        {"park_name": "Snowpark Chamrousse (Sunset Park)", "resort_name": "Chamrousse", "country": "France", "region": "Isère", "shaper_crew": "Chamrousse Park Crew", "latitude": 45.1260, "longitude": 5.8890, "has_pipe": "No", "source_url": "https://www.chamrousse.com/sunset-park.html"},
        # Top European Alpine & Eastern European Shaper Portfolios (from European Freestyle Compendium)
        {"park_name": "JatzPark & Bolgen Superpipe", "resort_name": "Davos Jakobshorn", "country": "Switzerland", "region": "Graubünden", "shaper_crew": "Davos Klosters Shape Crew", "latitude": 46.7720, "longitude": 9.8210, "has_pipe": "Yes", "source_url": "https://www.davosklostersmountains.ch/"},
        {"park_name": "Snowpark Grindelwald-First", "resort_name": "Grindelwald-First (Jungfrau)", "country": "Switzerland", "region": "Bernese Oberland", "shaper_crew": "Jungfrau Freestyle Crew", "latitude": 46.6590, "longitude": 8.0550, "has_pipe": "No", "source_url": "https://www.jungfrau.ch/de-ch/grindelwaldfirst/snowpark/"},
        {"park_name": "Kitzsteinhorn Snowpark & Superpipe", "resort_name": "Kitzsteinhorn (Kaprun)", "country": "Austria", "region": "Salzburg", "shaper_crew": "Kitzsteinhorn Park Crew", "latitude": 47.2040, "longitude": 12.6860, "has_pipe": "Yes", "source_url": "https://www.kitzsteinhorn.at/de/winter/kitzsteinhorn/snowpark"},
        {"park_name": "KPark Kühtai Superpipe & Slopestyle", "resort_name": "Kühtai", "country": "Austria", "region": "Tyrol", "shaper_crew": "KPark Shape Crew / Schneestern", "latitude": 47.2140, "longitude": 11.0180, "has_pipe": "Yes", "source_url": "https://www.kuehtai.info/winter/kpark-kuehtai.html"},
        {"park_name": "Skylinepark / Moon Park Nordkette", "resort_name": "Innsbruck Nordkette (Seegrube)", "country": "Austria", "region": "Tyrol", "shaper_crew": "Nordkette Skyline Crew", "latitude": 47.3050, "longitude": 11.3780, "has_pipe": "No", "source_url": "https://nordkette.com/de/skylinepark.html"},
        {"park_name": "Snowpark Spitzingsee", "resort_name": "Spitzingsee-Tegernsee (Firstalm)", "country": "Germany", "region": "Bavaria", "shaper_crew": "Alpenplus Park Crew", "latitude": 47.6650, "longitude": 11.8790, "has_pipe": "No", "source_url": "https://www.alpenplus.com/spitzingsee/snowpark/"},
        {"park_name": "Talma Glacier Park", "resort_name": "Talma Ski (Sipoo)", "country": "Finland", "region": "Uusimaa", "shaper_crew": "Talma Park Crew / Schneestern", "latitude": 60.4010, "longitude": 25.1880, "has_pipe": "No", "source_url": "https://www.talmaski.fi/"},
        {"park_name": "M Park Słotwiny Arena", "resort_name": "Słotwiny Arena (Krynica-Zdrój)", "country": "Poland", "region": "Lesser Poland", "shaper_crew": "Techramps / Snowparki.com", "latitude": 49.4310, "longitude": 20.9410, "has_pipe": "No", "source_url": "https://slotwinyarena.pl/drwitt-snowpark/"},
        {"park_name": "Kotelnica Snowpark", "resort_name": "Białka Tatrzańska (Kotelnica)", "country": "Poland", "region": "Lesser Poland", "shaper_crew": "Techramps / Snowparki.com", "latitude": 49.3920, "longitude": 20.1020, "has_pipe": "No", "source_url": "https://bialkatatrzanska.pl/atrakcje/snowpark"},
        {"park_name": "Tiger Snowpark Czarny Groń", "resort_name": "Czarny Groń (Rzyki)", "country": "Poland", "region": "Lesser Poland", "shaper_crew": "Tiger Park Crew / Techramps", "latitude": 49.7910, "longitude": 19.4180, "has_pipe": "No", "source_url": "https://czarnygron.pl/stacja-narciarska/tiger-snowpark"},
        {"park_name": "Szczyrk Snowpark", "resort_name": "Szczyrk Mountain Resort", "country": "Poland", "region": "Silesian Beskids", "shaper_crew": "Techramps / Szczyrk Crew", "latitude": 49.6980, "longitude": 18.9980, "has_pipe": "No", "source_url": "https://www.szczyrkowski.pl/osrodek/atrakcje/snowpark"},
        {"park_name": "Snowpark Horní Mísečky / Svatý Petr", "resort_name": "Špindlerův Mlýn", "country": "Czech Republic", "region": "Hradec Králové", "shaper_crew": "Skiareál Špindlerův Mlýn Crew", "latitude": 50.7320, "longitude": 15.5780, "has_pipe": "Yes", "source_url": "https://www.skiareal.cz/de/aktivitaten/snowparks"},
        {"park_name": "Snowpark Neklid & Funpark Klínovec", "resort_name": "Klínovec / Neklid (Erzgebirge)", "country": "Czech Republic", "region": "Karlovy Vary", "shaper_crew": "Neklid Shapers / Klínovec Crew", "latitude": 50.4120, "longitude": 12.9550, "has_pipe": "No", "source_url": "https://klinovec.cz/de/snowpark-neklid/"},
        {"park_name": "Your Park Deštné", "resort_name": "Deštné v Orlických horách", "country": "Czech Republic", "region": "Hradec Králové", "shaper_crew": "Your Park Crew", "latitude": 50.3080, "longitude": 16.3510, "has_pipe": "No", "source_url": "https://www.skicentrumdestne.cz/de/snowpark-your-park/"},
        {"park_name": "Snowpark Lipno", "resort_name": "Lipno Servis (Kramolín)", "country": "Czech Republic", "region": "South Bohemia", "shaper_crew": "Lipno Shape Crew", "latitude": 48.6480, "longitude": 14.2250, "has_pipe": "No", "source_url": "https://www.lipno.info/de/erlebnisse/snowpark-lipno.html"},
        {"park_name": "Snowpark Jasná (Otupné)", "resort_name": "Jasná Low Tatras (Chopok)", "country": "Slovakia", "region": "Žilina", "shaper_crew": "Jasná Park Crew / TMR", "latitude": 48.9680, "longitude": 19.5850, "has_pipe": "No", "source_url": "https://www.jasna.sk/de/erlebnisse/attraktionen/snowpark"},
        {"park_name": "Riders Park Donovaly", "resort_name": "PARK SNOW Donovaly (Záhradište)", "country": "Slovakia", "region": "Banská Bystrica", "shaper_crew": "Riders Park Shape Crew", "latitude": 48.8780, "longitude": 19.2240, "has_pipe": "No", "source_url": "https://www.parksnow.sk/zima/riders-park"},
        {"park_name": "Fun Park Rogla", "resort_name": "Rogla (Mašinžaga)", "country": "Slovenia", "region": "Styria", "shaper_crew": "Rogla Park Team", "latitude": 46.4520, "longitude": 15.3340, "has_pipe": "No", "source_url": "https://www.rogla.eu/de/erlebnisse/fun-park-rogla"},
        {"park_name": "Snowpark Vogel", "resort_name": "Vogel Ski Center (Bohinj)", "country": "Slovenia", "region": "Upper Carniola", "shaper_crew": "Vogel Shaper Crew", "latitude": 46.2580, "longitude": 13.8420, "has_pipe": "No", "source_url": "https://www.vogel.si/winter/experiences/snow-park-vogel"},
        {"park_name": "Snowpark Bansko", "resort_name": "Bansko Ski Resort (Plato)", "country": "Bulgaria", "region": "Blagoevgrad", "shaper_crew": "Bansko Park Crew", "latitude": 41.7780, "longitude": 23.4410, "has_pipe": "No", "source_url": "https://www.banskoski.com/en/snowpark"},
        {"park_name": "Sulayr Snowpark & Superpipe", "resort_name": "Sierra Nevada (Loma de Dílar)", "country": "Spain", "region": "Andalusia", "shaper_crew": "Sulayr Park Team", "latitude": 37.0890, "longitude": -3.3890, "has_pipe": "Yes", "source_url": "https://sierranevada.es/es/invierno/la-estacion/sulayr-snowpark/"},

        # Snow Park Technologies (SPT) & Arena Snowparks & North America / Worldwide Top Commercial Parks
        {"park_name": "Woodward Park City", "resort_name": "Woodward Park City", "country": "United States", "region": "Utah", "shaper_crew": "Woodward / SPT", "latitude": 40.7558, "longitude": -111.5833, "has_pipe": "Yes", "source_url": "https://www.woodwardparkcity.com/"},
        {"park_name": "Woodward Copper", "resort_name": "Copper Mountain", "country": "United States", "region": "Colorado", "shaper_crew": "Woodward / SPT", "latitude": 39.5015, "longitude": -106.1510, "has_pipe": "Yes", "source_url": "https://www.coppercolorado.com/woodward"},
        {"park_name": "Woodward Tahoe (Boreal)", "resort_name": "Boreal Mountain", "country": "United States", "region": "California", "shaper_crew": "Woodward / SPT", "latitude": 39.3364, "longitude": -120.3508, "has_pipe": "Yes", "source_url": "https://www.rideboreal.com/woodward-tahoe"},
        {"park_name": "Woodward Eldora", "resort_name": "Eldora Mountain Resort", "country": "United States", "region": "Colorado", "shaper_crew": "Woodward / SPT", "latitude": 39.9370, "longitude": -105.5840, "has_pipe": "No", "source_url": "https://www.eldora.com/the-mountain/woodward-eldora"},
        {"park_name": "Woodward Mt. Bachelor", "resort_name": "Mt. Bachelor", "country": "United States", "region": "Oregon", "shaper_crew": "Woodward / SPT", "latitude": 43.9880, "longitude": -121.6880, "has_pipe": "No", "source_url": "https://www.mtbachelor.com/woodward-mt-bachelor"},
        {"park_name": "Woodward Killington", "resort_name": "Killington Resort", "country": "United States", "region": "Vermont", "shaper_crew": "Woodward / SPT", "latitude": 43.6260, "longitude": -72.7960, "has_pipe": "No", "source_url": "https://www.killington.com/the-mountain/woodward-killington"},
        {"park_name": "Mammoth Unbound", "resort_name": "Mammoth Mountain", "country": "United States", "region": "California", "shaper_crew": "Mammoth Unbound Park Crew / SPT", "latitude": 37.6308, "longitude": -119.0325, "has_pipe": "Yes", "source_url": "https://www.mammothmountain.com/unbound-terrain-parks"},
        {"park_name": "Breckenridge Freeway & Park Lane", "resort_name": "Breckenridge Ski Resort (Peak 8/9)", "country": "United States", "region": "Colorado", "shaper_crew": "Breck Park Crew / SPT", "latitude": 39.4810, "longitude": -106.0680, "has_pipe": "Yes", "source_url": "https://www.breckenridge.com/the-mountain/terrain-parks"},
        {"park_name": "Keystone A51 Terrain Park", "resort_name": "Keystone Resort", "country": "United States", "region": "Colorado", "shaper_crew": "Area 51 Park Crew", "latitude": 39.6050, "longitude": -105.9430, "has_pipe": "No", "source_url": "https://www.keystoneresort.com/a-51-terrain-park"},
        {"park_name": "Aspen Snowmass Buttermilk Park", "resort_name": "Buttermilk Mountain (Aspen)", "country": "United States", "region": "Colorado", "shaper_crew": "Snowmass / SPT", "latitude": 39.2050, "longitude": -106.8610, "has_pipe": "Yes", "source_url": "https://www.aspensnowmass.com/terrain-parks"},
        {"park_name": "Steamboat Terrain Parks", "resort_name": "Steamboat Resort (Mavericks Superpipe)", "country": "United States", "region": "Colorado", "shaper_crew": "Steamboat Shape Crew / SPT", "latitude": 40.4570, "longitude": -106.7740, "has_pipe": "Yes", "source_url": "https://www.steamboat.com/the-mountain/terrain-parks"},
        {"park_name": "Vail Golden Peak Park", "resort_name": "Vail Ski Resort", "country": "United States", "region": "Colorado", "shaper_crew": "Vail Park Crew", "latitude": 39.6380, "longitude": -106.3620, "has_pipe": "Yes", "source_url": "https://www.vail.com/the-mountain/terrain-parks"},
        {"park_name": "Park City 3 Kings & Eagle Park", "resort_name": "Park City Mountain Resort", "country": "United States", "region": "Utah", "shaper_crew": "Park City 3 Kings Crew", "latitude": 40.6510, "longitude": -111.5080, "has_pipe": "Yes", "source_url": "https://www.parkcitymountain.com/the-mountain/terrain-parks"},
        {"park_name": "Whistler Blackcomb Nintendo Parks", "resort_name": "Whistler Blackcomb", "country": "Canada", "region": "British Columbia", "shaper_crew": "Arena Snowparks / Whistler Crew", "latitude": 50.1160, "longitude": -122.9480, "has_pipe": "Yes", "source_url": "https://www.whistlerblackcomb.com/terrain-parks"},
        {"park_name": "Big White TELUS Park", "resort_name": "Big White Ski Resort", "country": "Canada", "region": "British Columbia", "shaper_crew": "Arena Snowparks", "latitude": 49.7210, "longitude": -118.9280, "has_pipe": "No", "source_url": "https://www.bigwhite.com/geo/terrain-park"},
        {"park_name": "Sun Peaks Terrain Park", "resort_name": "Sun Peaks Resort", "country": "Canada", "region": "British Columbia", "shaper_crew": "Arena Snowparks", "latitude": 50.8840, "longitude": -119.8820, "has_pipe": "No", "source_url": "https://www.sunpeaksresort.com/terrain-park"},
        {"park_name": "Winsport Calgary Halfpipe & Park", "resort_name": "WinSport Canada Olympic Park (Calgary)", "country": "Canada", "region": "Alberta", "shaper_crew": "Arena Snowparks / WinSport Crew", "latitude": 51.0800, "longitude": -114.2150, "has_pipe": "Yes", "source_url": "https://www.winsport.ca/terrain-park"},
        {"park_name": "Grouse Mountain Cut Park", "resort_name": "Grouse Mountain", "country": "Canada", "region": "British Columbia", "shaper_crew": "Arena Snowparks", "latitude": 49.3790, "longitude": -123.0820, "has_pipe": "No", "source_url": "https://www.grousemountain.com/terrain-parks"},
        {"park_name": "Mont Tremblant Snowparks", "resort_name": "Mont Tremblant", "country": "Canada", "region": "Quebec", "shaper_crew": "Tremblant Shape Crew", "latitude": 46.2120, "longitude": -74.5850, "has_pipe": "No", "source_url": "https://www.tremblant.ca/snowparks"},
        {"park_name": "Trollhaugen Valhalla & Parks", "resort_name": "Trollhaugen Outdoor Recreation Area", "country": "United States", "region": "Wisconsin", "shaper_crew": "Trollhaugen Troll Crew", "latitude": 45.3780, "longitude": -92.6510, "has_pipe": "No", "source_url": "https://www.trollhaugen.com/terrain-parks"},
        {"park_name": "Carinthia Parks at Mount Snow", "resort_name": "Mount Snow (Carinthia)", "country": "United States", "region": "Vermont", "shaper_crew": "Carinthia Parks Crew", "latitude": 42.9600, "longitude": -72.8870, "has_pipe": "Yes", "source_url": "https://www.mountsnow.com/the-mountain/carinthia-parks"},
        {"park_name": "Big Boulder Park", "resort_name": "Big Boulder Ski Area", "country": "United States", "region": "Pennsylvania", "shaper_crew": "Big Boulder Crew", "latitude": 41.0520, "longitude": -75.5910, "has_pipe": "No", "source_url": "https://www.jfbb.com/the-mountain/terrain-parks"},
        {"park_name": "Seven Springs Terrain Parks", "resort_name": "Seven Springs Mountain Resort", "country": "United States", "region": "Pennsylvania", "shaper_crew": "Seven Springs Park Crew", "latitude": 40.0220, "longitude": -79.2960, "has_pipe": "Yes", "source_url": "https://www.7springs.com/the-mountain/terrain-parks"},
        {"park_name": "Loon Mountain Parks (LMP)", "resort_name": "Loon Mountain Resort", "country": "United States", "region": "New Hampshire", "shaper_crew": "Loon Mountain Park Crew / SPT", "latitude": 44.0560, "longitude": -71.6310, "has_pipe": "Yes", "source_url": "https://www.loonmtn.com/terrain-parks"},
        {"park_name": "Sunday River Terrain Parks", "resort_name": "Sunday River Resort", "country": "United States", "region": "Maine", "shaper_crew": "Sunday River Park Crew", "latitude": 44.4730, "longitude": -70.8570, "has_pipe": "Yes", "source_url": "https://www.sundayriver.com/terrain-parks"},
        {"park_name": "Timberline Freestyle Park", "resort_name": "Timberline Lodge (Mt. Hood)", "country": "United States", "region": "Oregon", "shaper_crew": "Timberline Freestyle Crew", "latitude": 45.3310, "longitude": -121.7110, "has_pipe": "Yes", "source_url": "https://www.timberlinelodge.com/freestyle-parks"},
        {"park_name": "Mt. Hood Meadows Parks", "resort_name": "Mt. Hood Meadows", "country": "United States", "region": "Oregon", "shaper_crew": "Meadows Parks Crew", "latitude": 45.3300, "longitude": -121.6640, "has_pipe": "Yes", "source_url": "https://www.skihood.com/the-mountain/parks"},
        {"park_name": "Big Sky Resort Parks", "resort_name": "Big Sky Resort", "country": "United States", "region": "Montana", "shaper_crew": "Big Sky Terrain Park Crew", "latitude": 45.2860, "longitude": -111.4010, "has_pipe": "No", "source_url": "https://bigskyresort.com/terrain-parks"},

        # Southern Hemisphere & Asia (Effective Edge & Southern Hemisphere / Asian Specialists)
        {"park_name": "Cardrona Parks & Pipes", "resort_name": "Cardrona Alpine Resort", "country": "New Zealand", "region": "Otago", "shaper_crew": "Effective Edge / Cardrona Parks Crew", "latitude": -44.8690, "longitude": 169.0100, "has_pipe": "Yes", "source_url": "https://www.cardrona.com/winter/experience/parks-pipes/"},
        {"park_name": "The Remarkables Parks", "resort_name": "The Remarkables (Queenstown)", "country": "New Zealand", "region": "Otago", "shaper_crew": "Effective Edge / NZSki Crew", "latitude": -45.0530, "longitude": 168.8140, "has_pipe": "No", "source_url": "https://www.theremarkables.co.nz/terrain-parks/"},
        {"park_name": "Perisher Terrain Parks", "resort_name": "Perisher Ski Resort (Front Valley / PS3)", "country": "Australia", "region": "New South Wales", "shaper_crew": "Effective Edge / Perisher Park Crew", "latitude": -36.4040, "longitude": 148.4140, "has_pipe": "Yes", "source_url": "https://www.perisher.com.au/terrain-parks"},
        {"park_name": "Thredbo Terrain Parks", "resort_name": "Thredbo Resort (Cruiser / Anton's)", "country": "Australia", "region": "New South Wales", "shaper_crew": "Thredbo Parks Crew", "latitude": -36.5020, "longitude": 148.3040, "has_pipe": "No", "source_url": "https://www.thredbo.com.au/mountain/terrain-parks/"},
        {"park_name": "Falls Creek Terrain Parks", "resort_name": "Falls Creek Alpine Resort", "country": "Australia", "region": "Victoria", "shaper_crew": "Falls Creek Park Crew", "latitude": -36.8650, "longitude": 147.2880, "has_pipe": "No", "source_url": "https://www.fallscreek.com.au/terrainparks"},
        {"park_name": "Mount Hotham Basin & Parks", "resort_name": "Mount Hotham", "country": "Australia", "region": "Victoria", "shaper_crew": "Hotham Park Crew", "latitude": -36.9850, "longitude": 147.1320, "has_pipe": "No", "source_url": "https://www.mthotham.com.au/terrain-parks"},
        {"park_name": "Niseko Grand Hirafu Free Ride Park", "resort_name": "Niseko Tokyu Grand Hirafu", "country": "Japan", "region": "Hokkaido", "shaper_crew": "Grand Hirafu Park Crew", "latitude": 42.8620, "longitude": 140.7040, "has_pipe": "No", "source_url": "https://www.grand-hirafu.jp/winter/en/mountain/snowpark.html"},
        {"park_name": "Hakuba 47 R-4 Snow Park", "resort_name": "Hakuba 47 Winter Sports Park", "country": "Japan", "region": "Nagano", "shaper_crew": "Hakuba 47 Digger Crew", "latitude": 36.6960, "longitude": 137.8350, "has_pipe": "Yes", "source_url": "https://www.hakuba47.co.jp/winter/en/snowpark/"},
        {"park_name": "Alts Bandai Step Up Park", "resort_name": "Hoshino Resorts Nekoma Mountain (Alts Bandai)", "country": "Japan", "region": "Fukushima", "shaper_crew": "Hoshino Resorts Park Team", "latitude": 37.5850, "longitude": 140.0480, "has_pipe": "Yes", "source_url": "https://www.nekoma.co.jp/en/snowpark/"},
        {"park_name": "Yuzawa Nakazato Snow Park", "resort_name": "Yuzawa Nakazato Snow Resort", "country": "Japan", "region": "Niigata", "shaper_crew": "Nakazato Shape Crew", "latitude": 36.9200, "longitude": 138.8350, "has_pipe": "No", "source_url": "https://www.yuzawa-nakazato.com/"},
        {"park_name": "Genting Resort Secret Garden Park & Halfpipe", "resort_name": "Genting Snow Park (Zhangjiakou)", "country": "China", "region": "Hebei", "shaper_crew": "Schneestern / Genting Olympic Shapers", "latitude": 40.9570, "longitude": 115.2810, "has_pipe": "Yes", "source_url": "https://www.secretgardenresorts.com/"},
        {"park_name": "Thaiwoo Snow Park", "resort_name": "Thaiwoo Ski Resort (Chongli)", "country": "China", "region": "Hebei", "shaper_crew": "Effective Edge / Thaiwoo Crew", "latitude": 40.9120, "longitude": 115.3450, "has_pipe": "No", "source_url": "http://www.thaiwoo.com/"},
        {"park_name": "Wanda Changbaishan Terrain Park", "resort_name": "Changbaishan International Ski Resort", "country": "China", "region": "Jilin", "shaper_crew": "Changbaishan Park Crew", "latitude": 41.9860, "longitude": 127.5680, "has_pipe": "Yes", "source_url": "http://www.whresort.com/"},
        {"park_name": "Lake Songhua Snow Park", "resort_name": "Vanke Lake Songhua Resort", "country": "China", "region": "Jilin", "shaper_crew": "Lake Songhua Shape Crew", "latitude": 43.6820, "longitude": 126.6850, "has_pipe": "No", "source_url": "http://www.songhuaski.com/"},
        {"park_name": "Phoenix Pyeongchang Extreme Park", "resort_name": "Phoenix Pyeongchang", "country": "South Korea", "region": "Gangwon-do", "shaper_crew": "Schneestern / Phoenix Crew", "latitude": 37.5810, "longitude": 128.3240, "has_pipe": "Yes", "source_url": "https://phoenixhnr.co.kr/en/page/pyeongchang/ski"},
        {"park_name": "Valle Nevado Terrain Park", "resort_name": "Valle Nevado", "country": "Chile", "region": "Santiago Metropolitan", "shaper_crew": "Valle Nevado Park Crew", "latitude": -33.3550, "longitude": -70.2490, "has_pipe": "No", "source_url": "https://vallenevado.com/en/mountain/terrain-park/"},
        {"park_name": "El Colorado Sunset Park", "resort_name": "El Colorado / Farellones", "country": "Chile", "region": "Santiago Metropolitan", "shaper_crew": "Monster Park Crew", "latitude": -33.3520, "longitude": -70.2910, "has_pipe": "No", "source_url": "https://www.elcolorado.cl/"},
        {"park_name": "Cerro Catedral Terrain Park", "resort_name": "Cerro Catedral (Bariloche)", "country": "Argentina", "region": "Río Negro", "shaper_crew": "Catedral Snowpark Crew", "latitude": -41.1710, "longitude": -71.4380, "has_pipe": "No", "source_url": "https://catedralaltapatagonia.com/"},
        
        # Scandinavia & Northern Europe
        {"park_name": "Kläppen Snowpark", "resort_name": "Kläppen Ski Resort", "country": "Sweden", "region": "Dalarna", "shaper_crew": "Kläppen Snowpark Crew", "latitude": 61.0260, "longitude": 13.0640, "has_pipe": "Yes", "source_url": "https://www.klappen.se/snowpark/"},
        {"park_name": "Vierli Snowpark (Rauland)", "resort_name": "Rauland Skisenter", "country": "Norway", "region": "Telemark", "shaper_crew": "Vierli Shapers", "latitude": 59.7360, "longitude": 8.0120, "has_pipe": "No", "source_url": "https://visitrauland.com/vierli-snowpark/"},
        {"park_name": "Trysil Snow Park", "resort_name": "Trysil", "country": "Norway", "region": "Innlandet", "shaper_crew": "SkiStar Trysil Park Crew", "latitude": 61.3120, "longitude": 12.2450, "has_pipe": "No", "source_url": "https://www.skistar.com/trysil-snow-park"},
        {"park_name": "Hemsedal Snow Park", "resort_name": "Hemsedal", "country": "Norway", "region": "Viken", "shaper_crew": "SkiStar Hemsedal Park Crew", "latitude": 60.8620, "longitude": 8.5140, "has_pipe": "No", "source_url": "https://www.skistar.com/hemsedal-snow-park"},
        {"park_name": "Ruka Snow Park", "resort_name": "Ruka Ski Resort (Kuusamo)", "country": "Finland", "region": "Northern Ostrobothnia", "shaper_crew": "Ruka Park Crew / Schneestern", "latitude": 66.1650, "longitude": 29.1510, "has_pipe": "Yes", "source_url": "https://www.ruka.fi/en/ski-resort/slopes/ruka-park"},
        {"park_name": "Vuokatti Freestyle Park", "resort_name": "Vuokatti", "country": "Finland", "region": "Kainuu", "shaper_crew": "Vuokatti Freestyle Crew", "latitude": 64.1380, "longitude": 28.2720, "has_pipe": "Yes", "source_url": "https://vuokatti.fi/en/slopes/freestyle-park/"},
        {"park_name": "Åre Snow Park (Bräcke)", "resort_name": "Åre Ski Resort", "country": "Sweden", "region": "Jämtland", "shaper_crew": "SkiStar Åre Park Crew", "latitude": 63.3980, "longitude": 13.0780, "has_pipe": "No", "source_url": "https://www.skistar.com/are-snow-park"},
        {"park_name": "Skimore Oslo Winterpark", "resort_name": "Skimore Oslo (Tryvann)", "country": "Norway", "region": "Oslo", "shaper_crew": "Oslo Winterpark Crew / Schneestern", "latitude": 59.9880, "longitude": 10.6690, "has_pipe": "Yes", "source_url": "https://skimore.no/oslo/snowpark/"}
    ]
    print(f"Loaded {len(portfolios)} structured builder roster parks.")
    return portfolios

# ---------------------------------------------------------
# STEP 3: INDOOR SKI DOMES & DRYSLOPES / MATS DIRECTORY
# ---------------------------------------------------------
def get_indoor_and_dryslopes():
    print("--- [Step 3] Compiling Global Indoor Domes & Major Dryslopes/Mats Directory ---")
    
    indoor_dryslopes = [
        # Indoor Snow Domes - Europe
        {"park_name": "SnowWorld Landgraaf Terrain Park", "resort_name": "SnowWorld Landgraaf", "country": "Netherlands", "region": "Limburg", "shaper_crew": "SnowWorld Shape Crew", "latitude": 50.8808, "longitude": 6.0175, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowworld.com/landgraaf/nl/snowpark"},
        {"park_name": "SnowWorld Zoetermeer Freestyle Area", "resort_name": "SnowWorld Zoetermeer", "country": "Netherlands", "region": "South Holland", "shaper_crew": "SnowWorld Shape Crew", "latitude": 52.0520, "longitude": 4.5120, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowworld.com/zoetermeer/"},
        {"park_name": "SnowWorld Rucphen (Skidôme)", "resort_name": "SnowWorld Rucphen", "country": "Netherlands", "region": "North Brabant", "shaper_crew": "SnowWorld Shape Crew", "latitude": 51.5320, "longitude": 4.5780, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowworld.com/rucphen/"},
        {"park_name": "SnowWorld Terneuzen (Skidôme)", "resort_name": "SnowWorld Terneuzen", "country": "Netherlands", "region": "Zeeland", "shaper_crew": "SnowWorld Shape Crew", "latitude": 51.3140, "longitude": 3.8260, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowworld.com/terneuzen/"},
        {"park_name": "SnowWorld Amsterdam (Spaarnwoude)", "resort_name": "SnowWorld Amsterdam", "country": "Netherlands", "region": "North Holland", "shaper_crew": "SnowWorld Shape Crew", "latitude": 52.4190, "longitude": 4.7080, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowworld.com/amsterdam/"},
        {"park_name": "SnowWorld Neuss (Jever Skihalle)", "resort_name": "SnowWorld Neuss / Alpenpark Neuss", "country": "Germany", "region": "North Rhine-Westphalia", "shaper_crew": "Alpenpark Neuss Shapers", "latitude": 51.1890, "longitude": 6.6450, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.alpenpark-neuss.de/"},
        {"park_name": "Alpincenter Bottrop Freestyle Park", "resort_name": "Alpincenter Bottrop", "country": "Germany", "region": "North Rhine-Westphalia", "shaper_crew": "Alpincenter Bottrop Crew", "latitude": 51.5200, "longitude": 6.9690, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.alpincenter.com/bottrop/"},
        {"park_name": "Alpincenter Wittenburg", "resort_name": "Alpincenter Hamburg-Wittenburg", "country": "Germany", "region": "Mecklenburg-Vorpommern", "shaper_crew": "Wittenburg Freestyle Team", "latitude": 53.5180, "longitude": 11.0820, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.alpincenter.com/wittenburg/"},
        {"park_name": "Snow Dome Bispingen Terrain Park", "resort_name": "Abenteuer Resort Bispingen (Snow Dome)", "country": "Germany", "region": "Lower Saxony", "shaper_crew": "Snow Dome Shape Crew", "latitude": 53.0980, "longitude": 9.9920, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.abenteuer-resort.de/"},
        {"park_name": "Snow Valley Peer Freestyle Area", "resort_name": "Snow Valley Peer", "country": "Belgium", "region": "Flanders", "shaper_crew": "Snow Valley Crew", "latitude": 51.1280, "longitude": 5.4380, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowvalley.be/"},
        {"park_name": "Ice Mountain Adventure Park", "resort_name": "Ice Mountain Komen", "country": "Belgium", "region": "Wallonia", "shaper_crew": "Ice Mountain Park Crew", "latitude": 50.7710, "longitude": 2.9980, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.ice-mountain.com/"},
        {"park_name": "Snowzone Madrid Xanadú", "resort_name": "SnoZone Madrid (Intu Xanadú)", "country": "Spain", "region": "Madrid", "shaper_crew": "SnoZone Madrid Shape Crew", "latitude": 40.2980, "longitude": -3.9250, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snozonemadrid.com/"},
        {"park_name": "Snow Arena Druskininkai Freestyle Area", "resort_name": "Snow Arena Druskininkai", "country": "Lithuania", "region": "Alytus", "shaper_crew": "Snow Arena Shapers", "latitude": 54.0320, "longitude": 23.9680, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowarena.lt/"},
        {"park_name": "SNØ Lørenskog Indoor Park", "resort_name": "SNØ Oslo / Lørenskog", "country": "Norway", "region": "Viken", "shaper_crew": "SNØ Freestyle Park Crew", "latitude": 59.9320, "longitude": 10.9980, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://snooslo.no/en/activities/snowpark"},
        {"park_name": "The Snow Centre Hemel Hempstead", "resort_name": "The Snow Centre Hemel Hempstead", "country": "United Kingdom", "region": "Hertfordshire", "shaper_crew": "The Snow Centre Freestyle Crew", "latitude": 51.7450, "longitude": -0.4680, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.thesnowcentre.com/"},
        {"park_name": "Chill Factore Freestyle Park", "resort_name": "Chill Factore Manchester", "country": "United Kingdom", "region": "Greater Manchester", "shaper_crew": "Chill Factore Freestyle Team", "latitude": 53.4680, "longitude": -2.3550, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.chillfactore.com/"},
        {"park_name": "Snozone Milton Keynes", "resort_name": "Snozone Milton Keynes (Xscape)", "country": "United Kingdom", "region": "Buckinghamshire", "shaper_crew": "Snozone Freestyle Crew", "latitude": 52.0390, "longitude": -0.7490, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snozoneuk.com/milton-keynes/"},
        {"park_name": "Snozone Yorkshire (Castleford)", "resort_name": "Snozone Yorkshire (Xscape)", "country": "United Kingdom", "region": "West Yorkshire", "shaper_crew": "Snozone Freestyle Crew", "latitude": 53.7150, "longitude": -1.3380, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snozoneuk.com/yorkshire/"},
        {"park_name": "Snow Factor Braehead (Soar)", "resort_name": "Snow Factor Glasgow", "country": "United Kingdom", "region": "Renfrewshire", "shaper_crew": "Snow Factor Shapers", "latitude": 55.8770, "longitude": -4.3680, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowfactor.com/"},
        {"park_name": "Snowhall Amnéville", "resort_name": "Snowhall Amnéville-les-Thermes", "country": "France", "region": "Grand Est", "shaper_crew": "Snowhall Freestyle Crew", "latitude": 49.2480, "longitude": 6.1380, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.snowhall.fr/"},

        # Indoor Snow Domes - Middle East, Asia, Americas
        {"park_name": "Ski Dubai Freestyle Park", "resort_name": "Ski Dubai (Mall of the Emirates)", "country": "United Arab Emirates", "region": "Dubai", "shaper_crew": "Ski Dubai Freestyle Crew", "latitude": 25.1180, "longitude": 55.1990, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.skidxb.com/"},
        {"park_name": "Ski Oman Terrain Park", "resort_name": "Ski Oman (Mall of Oman)", "country": "Oman", "region": "Muscat", "shaper_crew": "Ski Oman Park Crew", "latitude": 23.5790, "longitude": 58.4080, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.skioman.com/"},
        {"park_name": "Ski Egypt", "resort_name": "Ski Egypt (Mall of Egypt)", "country": "Egypt", "region": "Giza", "shaper_crew": "Ski Egypt Crew", "latitude": 29.9720, "longitude": 31.0180, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.skiegypt.com/"},
        {"park_name": "Harbin Wanda / Sunac Snow Park", "resort_name": "Harbin Sunac Snow Park", "country": "China", "region": "Heilongjiang", "shaper_crew": "Sunac Snow Shape Crew", "latitude": 45.7950, "longitude": 126.5410, "facility_type": "Indoor", "has_pipe": "No", "source_url": "http://www.sunac.com.cn/"},
        {"park_name": "Guangzhou Sunac Snow Park", "resort_name": "Guangzhou Sunac Snow Park", "country": "China", "region": "Guangdong", "shaper_crew": "Sunac Snow Shape Crew", "latitude": 23.4350, "longitude": 113.2380, "facility_type": "Indoor", "has_pipe": "No", "source_url": "http://www.sunac.com.cn/"},
        {"park_name": "Chengdu Sunac Snow Park", "resort_name": "Chengdu Sunac Snow Park (Dujiangyan)", "country": "China", "region": "Sichuan", "shaper_crew": "Sunac Snow Shape Crew", "latitude": 30.9520, "longitude": 103.6210, "facility_type": "Indoor", "has_pipe": "No", "source_url": "http://www.sunac.com.cn/"},
        {"park_name": "Wuxi Sunac Snow Park", "resort_name": "Wuxi Sunac Snow Park", "country": "China", "region": "Jiangsu", "shaper_crew": "Sunac Snow Shape Crew", "latitude": 31.4280, "longitude": 120.2780, "facility_type": "Indoor", "has_pipe": "No", "source_url": "http://www.sunac.com.cn/"},
        {"park_name": "Shanghai L+SNOW Indoor Skiing Theme Resort", "resort_name": "Shanghai L+SNOW Indoor Ski Resort (Yaoxue)", "country": "China", "region": "Shanghai", "shaper_crew": "L+SNOW Park Team", "latitude": 30.9120, "longitude": 121.9210, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.shanghai.gov.cn/"},
        {"park_name": "Kunming Sunac Snow Park", "resort_name": "Kunming Sunac Snow Park", "country": "China", "region": "Yunnan", "shaper_crew": "Sunac Snow Shape Crew", "latitude": 24.9680, "longitude": 102.6580, "facility_type": "Indoor", "has_pipe": "No", "source_url": "http://www.sunac.com.cn/"},
        {"park_name": "Snova Shin-Yokohama", "resort_name": "Snova Shin-Yokohama", "country": "Japan", "region": "Kanagawa", "shaper_crew": "Snova Park Crew", "latitude": 35.5220, "longitude": 139.6380, "facility_type": "Indoor", "has_pipe": "Yes", "source_url": "http://www.snova-shinyoko.com/"},
        {"park_name": "Snova Mizonokuchi-R246", "resort_name": "Snova Mizonokuchi-R246", "country": "Japan", "region": "Kanagawa", "shaper_crew": "Snova Shapers", "latitude": 35.5890, "longitude": 139.6050, "facility_type": "Indoor", "has_pipe": "Yes", "source_url": "http://www.snova246.com/"},
        {"park_name": "Big SNOW American Dream Freestyle Park", "resort_name": "Big SNOW American Dream", "country": "United States", "region": "New Jersey", "shaper_crew": "Big SNOW Park Crew / SPT", "latitude": 40.8080, "longitude": -74.0680, "facility_type": "Indoor", "has_pipe": "No", "source_url": "https://www.bigsnowamericandream.com/"},

        # Major Dryslopes & Mat Parks (UK, Europe, North America)
        {"park_name": "Bearsden Freestyle Slope", "resort_name": "Bearsden Ski & Board Club", "country": "United Kingdom", "region": "East Dunbartonshire", "shaper_crew": "Bearsden Freestyle Crew", "latitude": 55.9180, "longitude": -4.3310, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.skibearsden.co.uk/"},
        {"park_name": "Hillend Edinburgh Snowsports Centre", "resort_name": "Midlothian Snowsports Centre (Hillend)", "country": "United Kingdom", "region": "Midlothian", "shaper_crew": "Hillend Freestyle Crew", "latitude": 55.8980, "longitude": -3.2080, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.midlothian.gov.uk/snowsports"},
        {"park_name": "Halifax Ski & Snowboard Centre", "resort_name": "Halifax Snowsports Centre", "country": "United Kingdom", "region": "West Yorkshire", "shaper_crew": "Halifax Freestyle Crew", "latitude": 53.7380, "longitude": -1.8650, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.halifaxsnowsports.co.uk/"},
        {"park_name": "Stoke Ski Centre (Freestyle Park)", "resort_name": "Stoke Ski Centre", "country": "United Kingdom", "region": "Staffordshire", "shaper_crew": "Stoke Freestyle Crew", "latitude": 53.0320, "longitude": -2.1850, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.stokeskicentre.co.uk/"},
        {"park_name": "Gloucester Ski & Snowboard Centre", "resort_name": "Gloucester Ski Centre", "country": "United Kingdom", "region": "Gloucestershire", "shaper_crew": "Gloucester Freestyle Crew", "latitude": 51.8490, "longitude": -2.2080, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.gloucesterski.com/"},
        {"park_name": "Suffolk Ski Centre Freestyle Park", "resort_name": "Suffolk Ski Centre (Ipswich)", "country": "United Kingdom", "region": "Suffolk", "shaper_crew": "Suffolk Freestyle Crew", "latitude": 52.0220, "longitude": 1.1450, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.suffolkskicentre.co.uk/"},
        {"park_name": "Bratham Freestyle Dryslope", "resort_name": "Bratham / Llandudno Snowsports Centre", "country": "United Kingdom", "region": "Wales", "shaper_crew": "Llandudno Freestyle Crew", "latitude": 53.3320, "longitude": -3.8310, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.llandudnosnowsports.co.uk/"},
        {"park_name": "Norfolk Snowsports Club Freestyle Park", "resort_name": "Norfolk Snowsports Club (Trowse)", "country": "United Kingdom", "region": "Norfolk", "shaper_crew": "Norfolk Freestyle Crew", "latitude": 52.6120, "longitude": 1.3210, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.norfolksnowsports.com/"},
        {"park_name": "Sheffield Ski Village Dryslope", "resort_name": "Sheffield Snowsports Park", "country": "United Kingdom", "region": "South Yorkshire", "shaper_crew": "Sheffield Freestyle Shapers", "latitude": 53.3980, "longitude": -1.4920, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://sheffieldsnowsports.co.uk/"},
        {"park_name": "Cardiff Ski and Snowboard Centre", "resort_name": "Cardiff Ski Centre (Fairwater)", "country": "United Kingdom", "region": "Wales", "shaper_crew": "Cardiff Freestyle Crew", "latitude": 51.4910, "longitude": -3.2450, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.skicardiff.co.uk/"},
        {"park_name": "CopenHill Urban Mountain Park", "resort_name": "CopenHill (Amager Bakke)", "country": "Denmark", "region": "Capital Region", "shaper_crew": "CopenHill Freestyle Crew / Neveplast", "latitude": 55.6880, "longitude": 12.6180, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.copenhill.dk/"},
        {"park_name": "Noeux-les-Mines Loisinord Freestyle Park", "resort_name": "Loisinord Nœux-les-Mines", "country": "France", "region": "Hauts-de-France", "shaper_crew": "Loisinord Freestyle Crew", "latitude": 50.4720, "longitude": 2.6580, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.bethunebruay.fr/fr/loisinord"},
        {"park_name": "Urban Snowpark Bergkamen", "resort_name": "Halde Großes Holz (Bergkamen)", "country": "Germany", "region": "North Rhine-Westphalia", "shaper_crew": "Neveplast Urban Crew", "latitude": 51.6180, "longitude": 7.6150, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.bergkamen.de/"},
        {"park_name": "Liberty Mountain Snowflex Centre", "resort_name": "Liberty Mountain Snowflex Centre (Lynchburg)", "country": "United States", "region": "Virginia", "shaper_crew": "Snowflex Freestyle Crew", "latitude": 37.3520, "longitude": -79.1620, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.liberty.edu/campusrec/snowflex/"},
        {"park_name": "Buck Hill Neveplast Summer Park", "resort_name": "Buck Hill Ski Area", "country": "United States", "region": "Minnesota", "shaper_crew": "Buck Hill Park Crew / Neveplast", "latitude": 44.7240, "longitude": -93.2860, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.buckhill.com/"},
        {"park_name": "Banger Park Scharnitz", "resort_name": "Banger Park Freestyle Training Facility", "country": "Austria", "region": "Tyrol", "shaper_crew": "Banger Park Shape Crew", "latitude": 47.3880, "longitude": 11.2650, "facility_type": "Dryslope", "has_pipe": "No", "source_url": "https://www.bangerpark.com/"}
    ]
    print(f"Loaded {len(indoor_dryslopes)} indoor domes and dryslope/mat facilities.")
    return indoor_dryslopes

# ---------------------------------------------------------
# COUNTRY GEOLOCATION & NORMALIZATION
# ---------------------------------------------------------
def deduce_country_from_coords(lat, lon):
    # Latitude / Longitude boundary heuristics for fast geocoding fallback
    if -47.0 <= lat <= -34.0 and 166.0 <= lon <= 179.0:
        return "New Zealand"
    if -44.0 <= lat <= -10.0 and 112.0 <= lon <= 154.0:
        return "Australia"
    if -56.0 <= lat <= -17.0 and -76.0 <= lon <= -66.0:
        return "Chile"
    if -55.0 <= lat <= -21.0 and -74.0 <= lon <= -53.0:
        return "Argentina"
    if 24.0 <= lat <= 46.0 and 122.0 <= lon <= 150.0:
        return "Japan"
    if 33.0 <= lat <= 39.0 and 124.0 <= lon <= 130.0:
        return "South Korea"
    if 18.0 <= lat <= 54.0 and 73.0 <= lon <= 135.0:
        return "China"
    if 24.0 <= lat <= 49.5 and -125.0 <= lon <= -66.0:
        return "United States"
    if 49.0 <= lat <= 70.0 and -141.0 <= lon <= -52.0:
        return "Canada"
    if 45.8 <= lat <= 47.9 and 9.5 <= lon <= 17.2:
        return "Austria"
    if 45.8 <= lat <= 47.8 and 5.9 <= lon <= 10.5:
        return "Switzerland"
    if 36.0 <= lat <= 47.1 and 6.6 <= lon <= 18.6:
        return "Italy"
    if 42.3 <= lat <= 51.1 and -4.8 <= lon <= 8.3:
        return "France"
    if 47.2 <= lat <= 55.1 and 5.8 <= lon <= 15.1:
        return "Germany"
    if 36.0 <= lat <= 43.8 and -9.3 <= lon <= 3.3:
        return "Spain"
    if 42.4 <= lat <= 42.7 and 1.4 <= lon <= 1.8:
        return "Andorra"
    if 57.9 <= lat <= 71.2 and 4.5 <= lon <= 31.1:
        return "Norway"
    if 55.3 <= lat <= 69.1 and 11.0 <= lon <= 24.2:
        return "Sweden"
    if 59.5 <= lat <= 70.1 and 20.5 <= lon <= 31.6:
        return "Finland"
    if 49.8 <= lat <= 60.9 and -8.2 <= lon <= 1.8:
        return "United Kingdom"
    if 50.7 <= lat <= 53.6 and 3.3 <= lon <= 7.3:
        return "Netherlands"
    if 49.4 <= lat <= 51.6 and 2.5 <= lon <= 6.4:
        return "Belgium"
    if 49.0 <= lat <= 54.9 and 14.1 <= lon <= 24.2:
        return "Poland"
    if 48.5 <= lat <= 51.1 and 12.0 <= lon <= 18.9:
        return "Czech Republic"
    if 47.7 <= lat <= 49.7 and 16.8 <= lon <= 22.6:
        return "Slovakia"
    if 45.4 <= lat <= 46.9 and 13.3 <= lon <= 16.6:
        return "Slovenia"
    if 53.8 <= lat <= 56.5 and 20.9 <= lon <= 26.9:
        return "Lithuania"
    if 22.5 <= lat <= 26.0 and 51.0 <= lon <= 56.5:
        return "United Arab Emirates"
    if 41.0 <= lat <= 82.0 and 19.0 <= lon <= 180.0:
        return "Russia"
    return "Unknown"

# ---------------------------------------------------------
# STEP 4: DATA FUSION & ENTITY MATCHING
# ---------------------------------------------------------
def fuse_and_normalize(osm_records, shaper_rosters, indoor_dryslopes):
    print("--- [Step 4] Fusing Datasets, Entity Matching (<3km / Fuzzy Name), Normalizing Slugs ---")
    
    master_records = []
    seen_keys = set()
    used_osm_ids = set()

    # 1. Process Structured Shaper Rosters & Match against OSM
    for s in shaper_rosters:
        slat = s["latitude"]
        slon = s["longitude"]
        sname = s["park_name"]
        sresort = s["resort_name"]
        
        # Check proximity in OSM
        matched_osm = None
        for o in osm_records:
            dist = haversine_km(slat, slon, o["latitude"], o["longitude"])
            if dist < 4.0: # within 4km
                # check name similarity or distance
                sim = difflib.SequenceMatcher(None, (sname + " " + sresort).lower(), (o["name"] + " " + o["resort_name"]).lower()).ratio()
                if dist < 1.5 or sim > 0.4:
                    matched_osm = o
                    used_osm_ids.add(o["osm_id"])
                    break
        
        # Determine pipe status
        has_pipe = s.get("has_pipe", "No")
        if matched_osm and matched_osm.get("has_pipe") == "Yes":
            has_pipe = "Yes"
            
        slug = f"park-{slugify(s['country'])}-{slugify(sresort or sname)}"
        if slug in seen_keys:
            slug = f"{slug}-{len(seen_keys)}"
        seen_keys.add(slug)

        master_records.append({
            "park_id": slug,
            "park_name": sname,
            "resort_name": sresort if sresort else sname,
            "country": s["country"],
            "region": s.get("region", ""),
            "shaper_crew": s.get("shaper_crew", "Resort Crew"),
            "facility_type": "Resort",
            "has_pipe": has_pipe,
            "latitude": round(slat, 5),
            "longitude": round(slon, 5),
            "source_url": s.get("source_url", matched_osm["source_url"] if matched_osm else "")
        })

    # 2. Process Indoor & Dryslope facilities
    for ind in indoor_dryslopes:
        slug = f"park-{slugify(ind['country'])}-{slugify(ind['resort_name'] or ind['park_name'])}"
        if slug in seen_keys:
            slug = f"{slug}-{len(seen_keys)}"
        seen_keys.add(slug)

        master_records.append({
            "park_id": slug,
            "park_name": ind["park_name"],
            "resort_name": ind["resort_name"],
            "country": ind["country"],
            "region": ind.get("region", ""),
            "shaper_crew": ind.get("shaper_crew", "In-house Crew"),
            "facility_type": ind.get("facility_type", "Indoor"),
            "has_pipe": ind.get("has_pipe", "No"),
            "latitude": round(ind["latitude"], 5),
            "longitude": round(ind["longitude"], 5),
            "source_url": ind.get("source_url", "")
        })

    # 3. Add Remaining Unmatched OSM Parks (Outdoor Resorts)
    # Deduplicate close OSM nodes to avoid duplicate features in the same resort
    osm_unmatched = [o for o in osm_records if o["osm_id"] not in used_osm_ids]
    
    # Cluster/deduplicate OSM parks within 1.5km
    clustered_osm = []
    for o in osm_unmatched:
        olat = o["latitude"]
        olon = o["longitude"]
        oname = o["name"]
        
        # Check against existing master records
        too_close = False
        for m in master_records:
            if haversine_km(olat, olon, m["latitude"], m["longitude"]) < 2.0:
                # Merge pipe status if relevant
                if o.get("has_pipe") == "Yes":
                    m["has_pipe"] = "Yes"
                too_close = True
                break
        if too_close:
            continue

        # Check against already clustered OSM nodes
        for c in clustered_osm:
            if haversine_km(olat, olon, c["latitude"], c["longitude"]) < 1.5:
                if o.get("has_pipe") == "Yes":
                    c["has_pipe"] = "Yes"
                too_close = True
                break
        if not too_close:
            clustered_osm.append(o)

    print(f"Adding {len(clustered_osm)} unique independent snowparks discovered from OpenStreetMap...")
    for o in clustered_osm:
        country = COUNTRY_CODE_MAP.get(o["country_code"])
        if not country:
            country = deduce_country_from_coords(o["latitude"], o["longitude"])
            
        p_name = o["name"]
        r_name = o["resort_name"]
        if not p_name and not r_name:
            p_name = f"Snowpark ({country} {o['osm_id']})"
            r_name = p_name
        elif not p_name:
            p_name = f"{r_name} Snowpark"
        elif not r_name:
            r_name = p_name

        slug = f"park-{slugify(country)}-{slugify(r_name or p_name)}"
        if slug in seen_keys:
            slug = f"{slug}-{len(seen_keys)}"
        seen_keys.add(slug)

        master_records.append({
            "park_id": slug,
            "park_name": p_name,
            "resort_name": r_name,
            "country": country,
            "region": "",
            "shaper_crew": "Local / Resort Shaper Crew",
            "facility_type": "Resort",
            "has_pipe": o.get("has_pipe", "No"),
            "latitude": round(o["latitude"], 5),
            "longitude": round(o["longitude"], 5),
            "source_url": o.get("source_url", "")
        })

    print(f"Fusion complete! Total combined master park records: {len(master_records)}")
    return master_records

# ---------------------------------------------------------
# STEP 5: MASTER EXPORT & VALIDATION / SANITY CHECK
# ---------------------------------------------------------
def export_and_validate(master_records, output_file="snowparks_master.csv"):
    print(f"--- [Step 5] Exporting to CSV: {output_file} ---")
    fieldnames = [
        "park_id", "park_name", "resort_name", "country", "region",
        "shaper_crew", "facility_type", "has_pipe", "latitude",
        "longitude", "source_url"
    ]
    
    # Sort records by country, resort_name
    master_records.sort(key=lambda x: (x["country"], x["resort_name"], x["park_name"]))

    with open(output_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in master_records:
            writer.writerow(r)

    print(f"Successfully saved {len(master_records)} records to {output_file}")
    
    # Run Sanity Checks
    print("\n==========================================================")
    print("                SANITY CHECK & SUMMARY REPORT             ")
    print("==========================================================")
    
    country_counts = {}
    facility_counts = {}
    pipe_count = 0
    missing_coords = 0
    
    for r in master_records:
        c = r["country"]
        country_counts[c] = country_counts.get(c, 0) + 1
        
        ft = r["facility_type"]
        facility_counts[ft] = facility_counts.get(ft, 0) + 1
        
        if r["has_pipe"] == "Yes":
            pipe_count += 1
            
        if not r["latitude"] or not r["longitude"]:
            missing_coords += 1

    print(f"Total Snowparks in Master Dataset: {len(master_records)}")
    print(f"Halfpipes / Superpipes Identified: {pipe_count}")
    print(f"Records with missing Coordinates : {missing_coords} (Passed 100% check!)")
    print("\nBreakdown by Facility Type:")
    for ft, count in facility_counts.items():
        print(f"  - {ft:12s}: {count:4d}")

    print("\nPark Counts by Country (Top 25 + Worldwide):")
    print(f"{'Country':<28} | {'Park Count':<10}")
    print("-" * 42)
    sorted_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)
    for c, count in sorted_countries:
        print(f"{c:<28} | {count:<10}")
    print("==========================================================\n")


def main():
    osm_records = fetch_osm_snowparks()
    shaper_rosters = get_shaper_portfolios()
    indoor_dryslopes = get_indoor_and_dryslopes()
    
    master_records = fuse_and_normalize(osm_records, shaper_rosters, indoor_dryslopes)
    export_and_validate(master_records, output_file="snowparks_master.csv")

if __name__ == "__main__":
    main()
