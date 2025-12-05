from klaviyo_handler import get_all_resources

client_id = "invigor8"

segments = get_all_resources(client_id, 'segments')


print("\n=== SEGMENTS ===")
for segment in segments:
    print(f"- {segment.attributes.name} (ID: {segment.id})")