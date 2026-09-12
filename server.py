import uuid
import json
import numpy as np
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

# --- Global State ---
model = None
db_cards = {}       # id -> Card dict (without vectors)
db_vectors = []     # Raw vectors corresponding to db_ids
db_ids = []         # List of event IDs to map matrix row index back to ID
norm_matrix = None  # 2D NumPy array of normalized event vectors
pca_model = None    
events_3d = []
SESSIONS = {}       # session_id -> dict of session state

# --- Pydantic Models ---
class Card(BaseModel):
    id: str
    title: str
    category: str
    description: str

class StartRequest(BaseModel):
    interests: str

class StartResponse(BaseModel):
    session_id: str
    deck: list[Card]

class SwipeRequest(BaseModel):
    session_id: str
    card_id: str
    direction: str  # "right" | "left"

class SwipeResponse(BaseModel):
    deck: list[Card]
    has_more: bool

# --- Lifespan / Startup ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global model, db_cards, db_vectors, db_ids, norm_matrix
    
    print("Loading SentenceTransformer model...")
    model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")
    
    print("Loading vector_database.json...")
    with open("vector_database.json", "r", encoding="utf-8") as f:
        events = json.load(f)
        
    for event in events:
        eid = event["id"]
        db_ids.append(eid)
        db_vectors.append(event["vector"])
        # Strip the 896-dimension vector for frontend payload
        db_cards[eid] = {
            "id": eid,
            "title": event["title"],
            "category": event["category"],
            "description": event["description"]
        }
        
    # Construct 2D array and pre-normalize rows for fast cosine similarity
    matrix = np.array(db_vectors, dtype=np.float32)
    norm_matrix = matrix / np.linalg.norm(matrix, axis=1, keepdims=True)

    pca = PCA(n_components=3)
    pca.fit_transform(norm_matrix)
        
    print(f"Startup complete. Loaded {len(db_ids)} events.")
    yield
    # Teardown logic can go here

# --- Application Init ---
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper Functions ---
def get_recommendations(user_vector: np.ndarray, seen_ids: set, pinned_id: str = None, limit: int = 5) -> list[str]:
    """Computes cosine similarity and returns top un-seen IDs, preserving a pinned card if provided."""
    # Dot product broadcasts across all pre-normalized event vectors
    scores = np.dot(norm_matrix, user_vector)
    
    # Mask out seen events and the pinned event so they aren't re-recommended
    for idx, eid in enumerate(db_ids):
        if eid in seen_ids or eid == pinned_id:
            scores[idx] = -np.inf
            
    # Calculate how many cards we actually need to fetch
    num_needed = limit if pinned_id is None else limit - 1
    num_available = np.count_nonzero(scores > -np.inf)
    k = min(num_needed, num_available)
    
    new_deck = []
    if pinned_id:
        new_deck.append(pinned_id)
        
    if k > 0:
        # Get top k indices efficiently
        top_indices = np.argpartition(scores, -k)[-k:]
        # Sort them descending
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        new_deck.extend([db_ids[i] for i in top_indices])
        
    return new_deck

# --- Endpoints ---
@app.get("/api/health")
def health_check():
    return {
        "status": "ok", 
        "model_loaded": model is not None, 
        "database_size": len(db_ids)
    }

@app.post("/api/session/start", response_model=StartResponse)
def start_session(req: StartRequest):
    # Encode initial query and normalize
    raw_vec = model.encode(req.interests, prompt_name="query").flatten()
    user_vec = raw_vec / np.linalg.norm(raw_vec)
    
    session_id = str(uuid.uuid4())
    
    # Get initial 5 cards
    deck_ids = get_recommendations(user_vec, seen_ids=set(), limit=5)
    
    SESSIONS[session_id] = {
        "user_vector": user_vec,
        "seen_ids": set(deck_ids),
        "liked_ids": [],
        "current_deck": deck_ids
    }
    
    return {
        "session_id": session_id,
        "deck": [db_cards[eid] for eid in deck_ids]
    }

@app.post("/api/swipe", response_model=SwipeResponse)
def swipe_card(req: SwipeRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session["seen_ids"].add(req.card_id)
    
    # Handle Right Swipe Mathematics
    if req.direction == "right":
        session["liked_ids"].append(req.card_id)
        # Find index of liked card to get its vector
        try:
            liked_idx = db_ids.index(req.card_id)
            liked_vec = norm_matrix[liked_idx]
            
            # Rocchio-style update
            new_vec = 0.8 * session["user_vector"] + 0.2 * liked_vec
            session["user_vector"] = new_vec / np.linalg.norm(new_vec)
        except ValueError:
            pass # Failsafe if card ID somehow doesn't exist
            
    # Buffer & Anti-Jank Maintenance
    current_deck = session["current_deck"]
    if req.card_id in current_deck:
        current_deck.remove(req.card_id)
        
    # The new top card is whatever shifted into index 0
    pinned_id = current_deck[0] if current_deck else None
    
    # Refill deck
    new_deck_ids = get_recommendations(
        user_vector=session["user_vector"],
        seen_ids=session["seen_ids"],
        pinned_id=pinned_id,
        limit=5
    )
    
    session["current_deck"] = new_deck_ids
    session["seen_ids"].update(new_deck_ids)
    
    return {
        "deck": [db_cards[eid] for eid in new_deck_ids],
        "has_more": len(new_deck_ids) > 0
    }

@app.get("/api/session/{session_id}/likes", response_model=list[Card])
def get_likes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return [db_cards[eid] for eid in session["liked_ids"]]

