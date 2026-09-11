import streamlit as st
import time

# --- SETUP & SESSION STATE ---
st.set_page_config(page_title="Third Space Collider", page_icon="⚡", layout="centered")

# We use session state to remember which card we are on during re-runs
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "matches" not in st.session_state:
    st.session_state.matches = []
if "llm_explanation" not in st.session_state:
    st.session_state.llm_explanation = ""

# --- MOCK DATA (Output from your Core Engine) ---
local_events = [
    {
        "id": 1,
        "title": "Repair Café Urfahr",
        "desc_german": "Gemeinsames Reparieren von Haushaltsgeräten mit Kaffee und Kuchen.",
        "distance": "12 min (Tram 1)",
        "venue": "Stadtwerkstatt"
    },
    {
        "id": 2,
        "title": "Open Mic / Poetry Slam",
        "desc_german": "Lokale Poeten lesen Texte über das Leben in der Stahlstadt.",
        "distance": "8 min (Walk)",
        "venue": "Kapu"
    },
    {
        "id": 3,
        "title": "Seniorentanz & Frühschoppen",
        "desc_german": "Traditionelle Blasmusik und Tanz für alle Generationen.",
        "distance": "15 min (Bus 45)",
        "venue": "Volkshaus Bindermichl"
    }
]


# --- THE CLAUDE LLM WRAPPER ---
def get_vibe_match(user_interests, event):
    # In production, this uses the Anthropic API you set up earlier.
    # We simulate a 1.5-second API call here for the UI effect.
    time.sleep(1.5)

    # Mocking the Claude response based on the event
    if event["id"] == 1:
        return f"**Vibe Match: Analog Engineering.** You just attended '{user_interests}'. Why not step away from high-end AI and watch local Linzers hack and solder their broken toasters back to life? It's hardware sustainability in its purest form."
    elif event["id"] == 2:
        return f"**Vibe Match: Human Algorithms.** After filling your brain with '{user_interests}', cleanse your palate with raw human emotion. A local poetry slam offers unstructured, un-computable storytelling."
    else:
        return f"**Vibe Match: Complete Contrast.** You've been in the dark rooms of POSTCITY learning about '{user_interests}'. It's time to drink beer, eat pretzels, and watch Austrian grandmothers dance to brass music. You need this."


# --- SIDEBAR: USER INPUT ---
with st.sidebar:
    st.header("👤 Your Profile")
    st.write("What did you just attend at Ars Electronica?")
    user_interest = st.selectbox(
        "Recent Panel:",
        ["The Ethics of Autonomous Systems", "Generative Bio-Art", "Quantum Computing Futures"]
    )
    st.write("---")
    st.write(f"💚 **Matches found:** {len(st.session_state.matches)}")
    for match in st.session_state.matches:
        st.caption(f"- {match}")

# --- MAIN UI: THE TINDER-STYLE CARD ---
st.title("⚡ Third Space Collider")
st.write("You have 2 hours until your next panel. Step outside the bubble.")

# Check if we have run out of events
if st.session_state.current_index >= len(local_events):
    st.success("You've seen all nearby events! Head to your matches in the sidebar, or go back to the festival.")
    if st.button("Start Over"):
        st.session_state.current_index = 0
        st.session_state.matches = []
        st.rerun()
else:
    current_event = local_events[st.session_state.current_index]

    # Generate LLM text only once per card
    if not st.session_state.llm_explanation:
        with st.spinner("Claude is translating and checking the vibe..."):
            st.session_state.llm_explanation = get_vibe_match(user_interest, current_event)

    # UI DESIGN: The Card
    st.markdown("""
        <style>
        .event-card {
            background-color: #1e1e2e;
            padding: 25px;
            border-radius: 15px;
            border: 1px solid #333;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="event-card">', unsafe_allow_html=True)
    st.subheader(current_event["title"])
    st.caption(f"📍 {current_event['venue']} | 🚆 {current_event['distance']}")
    st.write(f"_{current_event['desc_german']}_")

    st.info(st.session_state.llm_explanation, icon="🤖")
    st.markdown('</div>', unsafe_allow_html=True)
    st.write("")  # Spacer

    # UI DESIGN: The Swipe Buttons
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])

    with col2:
        if st.button("❌ Nope", use_container_width=True):
            st.session_state.current_index += 1
            st.session_state.llm_explanation = ""  # Reset for the next card
            st.rerun()

    with col3:
        # We use a primary type button to highlight the 'Swipe Right' action
        if st.button("💚 Let's Go!", type="primary", use_container_width=True):
            st.session_state.matches.append(current_event["title"])
            st.session_state.current_index += 1
            st.session_state.llm_explanation = ""  # Reset for the next card
            st.rerun()