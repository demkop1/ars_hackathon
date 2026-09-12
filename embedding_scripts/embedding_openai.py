import json
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
import numpy as np

# 1. Load the free local embedding model
model = OpenAIEmbeddings()

# 2. Access the JSON file
print("Opening notion_export.json...")
with open("data/prepared_cards.json", "r", encoding="utf-8") as file:
    event_list = json.load(file)

dataset = {block["id"]: block for block in event_list}

# 3. Extract the data you want to embed
# Let's pull out the public projects and create a descriptive string for each

docs_to_embed = []
for event in event_list:
    embeddings_string = event["title"] + "|" + event["full_desc"]
    # embeddings_string = event.get("embedding_input") or ""

    docs_to_embed.append( embeddings_string )

# 4. Generate the mathematical vectors
print(f"Generating embeddings for {len(docs_to_embed)} events. This takes a few seconds...")
embeddings = np.array( model.embed_documents( docs_to_embed ) ) # This returns a NumPy array

# 5. Attach the vectors back to your event data
final_database = []
for i, event in enumerate(event_list):
    # We only keep the fields we actually need for the frontend card
    card = {
        "id": event.get("id"),
        "title": event.get("title"),
        "category": event.get("category"),
        "description": event.get("full_desc"),
        "vector": embeddings[i].tolist() # Convert NumPy array to standard Python list
    }
    final_database.append(card)

# 6. Save your new, intelligent database
with open("vector_database.json", "w", encoding="utf-8") as out_file:
    json.dump(final_database, out_file, indent=2)

print("Success! vector_database.json is ready for your swipe app backend.")
