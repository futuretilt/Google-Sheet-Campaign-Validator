import pandas as pd
from klaviyo_handler import get_all_resources

client_id = "invigor8"

segments = get_all_resources(client_id, "segments")

# Convert pulled segments into rows
rows = []
for s in segments:
    rows.append({
        "id": s.id,
        "name": s.attributes.name
    })

df_segments = pd.DataFrame(rows)
df_segments.to_csv("segments_output.csv", index=False)

# Load your existing CSV
df_existing = pd.read_csv("EXAMPLE_Invigor8 _ Campaign Calendar - Segments(1).csv")

# Extract names (column is "name", not "Segment")
existing_names = set(df_existing["name"].dropna())
klaviyo_names = set(df_segments["name"].dropna())

# Compare
matches = existing_names.intersection(klaviyo_names)

print(f"Found {len(matches)} matches")
for m in matches:
    print(f"- {m}")
