from math import radians, cos, sin, asin, sqrt
import requests
import time
import logging

logger = logging.getLogger(__name__)


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 6371
    return c * r


class OSMDataFetcher:
    def __init__(self):
        self.overpass_url = "https://overpass-api.de/api/interpreter"

    def get_area_data(self, north, west, south, east):
        query = f"""
        [out:json];
        (
          way["highway"]({south},{west},{north},{east});
          way["leisure"="park"]({south},{west},{north},{east});
          way["natural"="wood"]({south},{west},{north},{east});
          way["landuse"="forest"]({south},{west},{north},{east});
          way["landuse"="meadow"]({south},{west},{north},{east});
          way["landuse"="grass"]({south},{west},{north},{east});
          way["natural"="water"]({south},{west},{north},{east});
          way["waterway"]({south},{west},{north},{east});
          node["public_transport"]({south},{west},{north},{east});
          node["highway"="bus_stop"]({south},{west},{north},{east});
          node["railway"="station"]({south},{west},{north},{east});
          node["railway"="tram_stop"]({south},{west},{north},{east});
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = requests.post(self.overpass_url, data=query)

            if response.status_code == 429:
                logger.warning("Rate limited by Overpass API, waiting 5 seconds")
                time.sleep(5)
                return self.get_area_data(north, west, south, east)

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching OSM data: {e}")
            return {"elements": []}