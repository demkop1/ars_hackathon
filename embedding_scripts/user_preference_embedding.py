import json
import numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")

example_tags = input("Example tag string: ") # <== rewritte how the users initial query gets picked up 

def compute_cos_similarity(document_matrix, query_vector):
    norm_matrix = document_matrix / np.linalg.norm(document_matrix, axis=1, keepdims=True)
    norm_embedding = query_vector/np.linalg.norm(query_vector)

    return np.dot(norm_matrix, norm_embedding)

def update_query(query_vector, like_vector, fac=0.9):
   new_query_vector = fac * query_vector + (1-fac) * like_vector
   return new_query_vector / np.linalg.norm(new_query_vector)


embedding = model.encode(example_tags, prompt_name="query").flatten()

print("Opening Vector_Database.json...")
with open("Vector database/vector_database.json", "r", encoding="utf-8") as file:
    event_list = json.load(file)

matrix_list = []
for event in event_list:
    matrix_list.append(event["vector"])

matrix = np.array(matrix_list)

cos_sim = compute_cos_similarity(matrix, embedding)
top_indices = np.argsort(cos_sim)[::-1][:3]

for idx in top_indices:
    print(f"Match: {cos_sim[idx]:.4f} | {event_list[idx]['title']}")