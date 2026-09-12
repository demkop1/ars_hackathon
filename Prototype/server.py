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
    match_percent: int = 0  # <--- New field

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
def get_recommendations(user_vector: np.ndarray, seen_ids: set, pinned_id: str = None, limit: int = 5):
    """Computes cosine similarity and returns a list of (id, match_percentage) tuples."""
    scores = np.dot(norm_matrix, user_vector)
    
    # --- Z-SCORE CALIBRATION ---
    # Calculate the mean and standard deviation of all events BEFORE masking
    mean_s = np.mean(scores)
    std_s = np.std(scores)
    
    def to_percent(raw_score):
        # Calculate how many standard deviations this score is above average
        z_score = (raw_score - mean_s) / (std_s + 1e-9)
        # Map it: Center at 60%, add 14% per standard deviation. 
        # (Top matches usually hit Z = 2.0 to 2.8, mapping them perfectly into the 85-99% range)
        pct = 60 + (z_score * 14)
        return int(max(0, min(100, pct)))

    new_deck = []
    
    # 1. Grab pinned card and calculate its Z-score percentage
    if pinned_id:
        pinned_idx = db_ids.index(pinned_id)
        new_deck.append((pinned_id, to_percent(scores[pinned_idx])))
        
    # 2. Mask out seen events and pinned event
    for idx, eid in enumerate(db_ids):
        if eid in seen_ids or eid == pinned_id:
            scores[idx] = -np.inf
            
    # 3. Calculate refill amount
    num_needed = limit if pinned_id is None else limit - 1
    num_available = np.count_nonzero(scores > -np.inf)
    k = min(num_needed, num_available)
    
    # 4. Grab top remaining cards and calculate their Z-score percentages
    if k > 0:
        top_indices = np.argpartition(scores, -k)[-k:]
        top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]
        new_deck.extend([(db_ids[i], to_percent(scores[i])) for i in top_indices])
        
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
    
    # Get initial 5 cards with their raw cosine similarity scores
    deck_with_scores = get_recommendations(user_vec, seen_ids=set(), limit=5)
    
    # Build the deck with the match percentage
# Build the deck (the math is already done in get_recommendations!)
    final_deck = []
    for eid, percent in deck_with_scores:
        card = db_cards[eid].copy()
        card["match_percent"] = percent
        final_deck.append(card)
    
    # Store session state using just the IDs
    SESSIONS[session_id] = {
        "user_vector": user_vec,
        "seen_ids": set([eid for eid, score in deck_with_scores]),
        "liked_ids": [],
        "current_deck": [eid for eid, score in deck_with_scores]
    }
    
    return {
        "session_id": session_id,
        "deck": final_deck
    }


# --- Updated Swipe Endpoint ---
@app.post("/api/swipe", response_model=SwipeResponse)
def swipe_card(req: SwipeRequest):
    session = SESSIONS.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session["seen_ids"].add(req.card_id)
    
    # Handle Right Swipe Mathematics
    if req.direction == "right":
        session["liked_ids"].append(req.card_id)
        try:
            liked_idx = db_ids.index(req.card_id)
            liked_vec = norm_matrix[liked_idx]
            
            # Rocchio-style update and re-normalize
            new_vec = 0.95 * session["user_vector"] + 0.05 * liked_vec
            session["user_vector"] = new_vec / np.linalg.norm(new_vec)
        except ValueError:
            pass
    
    # Buffer & Anti-Jank Maintenance
    current_deck = session["current_deck"]
    if req.card_id in current_deck:
        current_deck.remove(req.card_id)
        
    # The new top card is whatever shifted into index 0
    pinned_id = current_deck[0] if current_deck else None
    
    # Refill deck
    deck_with_scores = get_recommendations(
        user_vector=session["user_vector"],
        seen_ids=session["seen_ids"],
        pinned_id=pinned_id,
        limit=5
    )
    
    # Build the deck (the Z-score math is already done in get_recommendations!)
    final_deck = []
    for eid, percent in deck_with_scores:
        card = db_cards[eid].copy()
        card["match_percent"] = percent
        final_deck.append(card)
        
    # Update internal state tracking
    session["current_deck"] = [eid for eid, percent in deck_with_scores]
    session["seen_ids"].update(session["current_deck"])
    
    return {
        "deck": final_deck,
        "has_more": len(final_deck) > 0
    }

@app.get("/api/session/{session_id}/likes", response_model=list[Card])
def get_likes(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return [db_cards[eid] for eid in session["liked_ids"]]

@app.get("/api/3d/events")
def get_all_events_3d():
    # Return the pre-computed 3D coordinates instantly
    return {"events": events_3d}

@app.get("/api/session/{session_id}/3d-state")
def get_user_state_3d(session_id: str):
    session = SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Grab the user's current vector
    user_vec = session["user_vector"]
    
    # Transform this single vector into our pre-existing 3D space
    # .reshape(1, -1) is needed because sklearn expects a 2D array
    user_3d = pca_model.transform(user_vec.reshape(1, -1))[0]
    
    return {
        "x": float(user_3d[0]),
        "y": float(user_3d[1]),
        "z": float(user_3d[2])
    }

