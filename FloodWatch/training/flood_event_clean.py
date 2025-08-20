import pandas as pd
import os

def clean_flood_events_strict(input_path, output_path):
    print(f"Loading events from {input_path}...")
    df = pd.read_csv(input_path)

    # Ensure date column is datetime
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])  # drop invalid dates

    # Step 1: Deduplicate (city + date)
    before = len(df)
    df = df.drop_duplicates(subset=["city", "date"])
    after = len(df)
    print(f"Deduplicated: {before} → {after} unique city-date entries")

    # Step 2: Stricter keyword filter (drop waterlogging noise)
    if "title" in df.columns:
        keywords = ["flood", "inundated", "dam release", "overflow", "breach"]
        mask = df["title"].str.lower().str.contains("|".join(keywords), na=False)
        df = df[mask]
        print(f"Filtered with stricter keywords → {len(df)} rows left")

    # Step 3: Severity filter (keep only High / Critical if column exists)
    if "severity" in df.columns:
        df = df[df["severity"].isin(["High", "Critical"])]
        print(f"After severity filter → {len(df)} rows left")

    # Step 4: Collapse multiple days into single weekly event
    df["year_week"] = df["date"].dt.strftime("%Y-%U")
    df = df.drop_duplicates(subset=["city", "year_week"])
    print(f"After weekly grouping → {len(df)} unique events left")

    # Step 5: Keep essential columns
    keep_cols = [c for c in ["city", "district", "date", "year_week", "source_url", "severity", "title"] if c in df.columns]
    df = df[keep_cols].sort_values(by="date")

    # Save cleaned dataset
    df.to_csv(output_path, index=False)
    print(f"Saved cleaned events to {output_path}")
    print(f"Final dataset size: {len(df)} events")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(script_dir)
    input_file = os.path.join(project_root, "data", "flood_events.csv")  # raw scraped file
    output_file = os.path.join(project_root, "data", "flood_events_clean.csv")

    clean_flood_events_strict(input_file, output_file)
