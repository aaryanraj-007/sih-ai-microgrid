import pymongo

uri = "mongodb+srv://aaryanrajschooling_db_user:FkbeB8WC3ggGDs87@cluster0.kgcufqo.mongodb.net/"
print(f"Attempting to connect to: {uri.split('@')[1]}")

try:
    client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=10000)
    
    # 1. Get all databases
    db_names = client.list_database_names()
    print("\n--- Found Databases ---")
    print(db_names)
    
    # 2. Loop through databases and find collections/sample data
    for db_name in db_names:
        if db_name in ['admin', 'local']:
            continue
            
        print(f"\n--- Exploring Database: '{db_name}' ---")
        db = client[db_name]
        collections = db.list_collection_names()
        print(f"Collections: {collections}")
        
        for coll in collections:
            sample = db[coll].find_one()
            print(f"\nSample document from '{db_name}.{coll}':")
            print(sample)

except Exception as e:
    print(f"\n[ERROR] Failed to connect or query MongoDB: {e}")
