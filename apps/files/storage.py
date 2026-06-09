from apps.common.supabase_client import get_supabase_client

def upload_file(bucket: str, path: str, file_obj):
    client = get_supabase_client()
    if not client:
        raise RuntimeError('Supabase client not configured')
    storage = client.storage()
    return storage.from_(bucket).upload(path, file_obj)
