import csv
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup

def fetch_flood_events_for_city(city, start_year=2019, end_year=2025):
    """
    Fetch flood-related news headlines for a given city using Google News RSS
    """
    events = []
    for year in range(start_year, end_year + 1):
        query = f"{city} Maharashtra flood {year}"
        url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
        
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.content, "lxml-xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.title.text
                link = item.link.text
                pub_date = item.pubDate.text if item.pubDate else None
                
                # Try to parse date
                try:
                    date_obj = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %Z")
                    date_str = date_obj.strftime("%Y-%m-%d")
                except:
                    date_str = ""
                
                events.append({
                    "city": city,
                    "district": "",  # can be filled later via mapping
                    "date": date_str,
                    "source_url": link,
                    "severity": "High" if "severe" in title.lower() or "heavy" in title.lower() else "Medium"
                })
        except Exception as e:
            print(f"Error fetching news for {city} {year}: {e}")
            continue
    return events


def main():
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    cities_path = os.path.join(project_root, "data", "cities.csv")
    output_path = os.path.join(project_root, "data", "flood_events.csv")
    
    # Load cities
    cities = []
    with open(cities_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cities.append(row["city"])
    
    all_events = []
    for city in cities:
        print(f"Fetching flood events for {city}...")
        city_events = fetch_flood_events_for_city(city)
        all_events.extend(city_events)
    
    # Save CSV
    headers = ["city", "district", "date", "source_url", "severity"]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_events)
    
    print(f"Saved {len(all_events)} flood events to {output_path}")


if __name__ == "__main__":
    main()
