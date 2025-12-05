from clients import get_klaviyo_client
from urllib.parse import unquote

def get_all_resources(client_id, resource_type):
    """
    Get all resources (tags or segments) with proper pagination and error handling
    
    Args:
        client_id: The client identifier
        resource_type: Either 'tags' or 'segments'
    
    Returns:
        List of all resources
    """
    client = get_klaviyo_client(client_id)
    
    # Map resource type to the correct API client
    resource_map = {
        'tags': client.Tags.get_tags,
        'segments': client.Segments.get_segments
    }
    
    if resource_type not in resource_map:
        raise ValueError(f"Invalid resource_type. Must be 'tags' or 'segments', got '{resource_type}'")
    
    api_method = resource_map[resource_type]
    all_resources = []
    page_count = 0
    
    try:
        # First call without cursor
        response = api_method()
        all_resources.extend(response.data)
        page_count += 1
        print(f"Page {page_count}: Got {len(response.data)} {resource_type}")
        
        # Continue fetching while there's a next link
        while hasattr(response.links, 'next') and response.links.next:
            # URL decode the next link first
            next_url = unquote(response.links.next)
            
            if 'page[cursor]=' in next_url:
                cursor = next_url.split('page[cursor]=')[1].split('&')[0]
                print(f"Fetching next page with cursor: {cursor[:20]}...")
                
                # Make the next request with just the cursor string
                response = api_method(page_cursor=cursor)
                all_resources.extend(response.data)
                page_count += 1
                print(f"Page {page_count}: Got {len(response.data)} {resource_type}")
            else:
                break
                
    except Exception as e:
        print(f"Error getting {resource_type}: {e}")
        import traceback
        traceback.print_exc()
        
    return all_resources

# Usage
if __name__ == "__main__":
    client_id = "invigor8"
    
    # Get all tags
    print("Fetching tags...")
    tags = get_all_resources(client_id, 'tags')
    print(f"\nFound {len(tags)} total tags\n")
    
    # Get all segments
    print("Fetching segments...")
    segments = get_all_resources(client_id, 'segments')
    print(f"\nFound {len(segments)} total segments\n")
    
    # Print details
    print("=== TAGS ===")
    for tag in tags:
        print(f"- {tag.attributes.name} (ID: {tag.id})")
    
    print("\n=== SEGMENTS ===")
    for segment in segments:
        print(f"- {segment.attributes.name} (ID: {segment.id})")