import streamlit as st
import os
import requests
import json
from datetime import date
from dotenv import load_dotenv
from groq import Groq
from openai import OpenAI
from pinecone_utils import query_pinecone

load_dotenv()

st.set_page_config(page_title="astrology AI · AstroVed", page_icon="🪐", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;1,400&family=Nunito:wght@300;400;500;600;700&display=swap');

/* ── AstroVed Chat UI Palette (from astroved.com chat screenshot) ────────────
   page-bg      : #E8E8F5   lavender page background
   chat-header  : #7B00FF   deep violet header bar
   bubble-bot   : #D4D8F0   blue-grey left bubbles (astrologer/AI)
   bubble-user  : #F0EAD6   cream/beige right bubbles (user)
   send-btn     : #4A5BE8   blue send button
   end-btn      : #E53935   red End Chat button
   blue-logo    : #6B6FE0   AstroVed periwinkle brand
   orange-logo  : #E8720C   AstroVed orange gem accent
   text-dark    : #1A1A4E   deep text
   text-muted   : #7678C8   muted labels
   border       : #D8D9F8   soft border
   ──────────────────────────────────────────────────────────────────────── */

html, body, [class*="css"] {
  font-family: 'Nunito', sans-serif;
  background: #E8E8F5 !important;
  color: #1A1A4E;
}
.stApp { background: #E8E8F5 !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container {
  padding: 0 !important;
  max-width: 860px !important;
  margin: 0 auto;
}

/* ── Top nav bar mimicking AstroVed ── */
.av-navbar {
  background: #ffffff;
  border-bottom: 3px solid #7B00FF;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.7rem 1.6rem;
  box-shadow: 0 2px 12px rgba(107,111,224,0.10);
  margin-bottom: 1.6rem;
}
.av-logo {
  font-family: 'Nunito', sans-serif;
  font-size: 1.35rem;
  font-weight: 700;
  color: #6B6FE0;
}
.av-nav-links {
  font-size: 0.75rem;
  color: #7678C8;
  display: flex;
  gap: 1.2rem;
}
.av-nav-link {
  font-size: 0.75rem;
  color: #1A1A4E;
  text-decoration: none;
  font-weight: 500;
}
.av-nav-link:hover { color: #7B00FF; }

/* ── Chat card wrapper ── */
.chat-card {
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 32px rgba(107,111,224,0.14);
  overflow: hidden;
  margin: 0 1rem 1.2rem 1rem;
}

/* ── Chat header bar ── */
.chat-header {
  background: #7B00FF;
  padding: 1rem 1.4rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.chat-header-name   { font-size: 1.05rem; font-weight: 700; color: #fff; }
.chat-header-status { font-size: 0.72rem; color: rgba(255,255,255,0.72); margin-top: 2px; }
.btn-end-chat {
  background: #E53935;
  color: #fff;
  border: none;
  border-radius: 7px;
  padding: 6px 16px;
  font-family: 'Nunito', sans-serif;
  font-weight: 700;
  font-size: 0.78rem;
  cursor: pointer;
}

/* ── Counter strip ── */
.counter-strip {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.45rem 1.4rem;
  background: #f8f7ff;
  border-bottom: 1px solid #E8E8F5;
  font-size: 0.68rem;
  color: #7678C8;
}

/* ── Messages area with zodiac watermark ── */
.chat-messages {
  padding: 1.2rem 1.4rem;
  min-height: 360px;
  background-color: #ffffff;
  background-image:
    radial-gradient(circle at 15% 20%, rgba(107,111,224,0.04) 70px, transparent 70px),
    radial-gradient(circle at 80% 65%, rgba(107,111,224,0.04) 90px, transparent 90px),
    radial-gradient(circle at 50% 50%, rgba(232,114,12,0.025) 110px, transparent 110px);
  position: relative;
  overflow: hidden;
}
/* zodiac symbol watermark */
.chat-messages::before {
  content: '♈  ♉  ♊  ♋  ♌  ♍  ♎  ♏  ♐  ♑  ♒  ♓  ★  ☽  ☀  ♄  ♃  ♂  ♀  ☿';
  position: absolute;
  inset: 0;
  font-size: 2rem;
  color: rgba(107,111,224,0.055);
  word-break: break-all;
  letter-spacing: 1.4rem;
  line-height: 4rem;
  pointer-events: none;
  padding: 1rem;
}

/* ── Individual message rows ── */
.msg-row { position: relative; z-index: 1; margin-bottom: 0.9rem; }

/* Bot (left) */
.msg-bot  { display: flex; flex-direction: column; align-items: flex-start; }
.msg-user { display: flex; flex-direction: column; align-items: flex-end; }

.bubble-bot {
  background: #D4D8F0;
  border-radius: 4px 18px 18px 18px;
  padding: 10px 14px;
  max-width: 68%;
  font-size: 0.87rem;
  line-height: 1.62;
  color: #1A1A4E;
}
.bubble-user {
  background: #F0EAD6;
  border-radius: 18px 4px 18px 18px;
  padding: 10px 14px;
  max-width: 68%;
  font-size: 0.87rem;
  line-height: 1.62;
  color: #1A1A4E;
}
.msg-time {
  font-size: 0.61rem;
  color: #aaa;
  margin-top: 3px;
  padding: 0 4px;
}

/* sources */
.sources { margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(107,111,224,0.15); display: flex; flex-wrap: wrap; gap: 4px; }
.src-tag {
  background: rgba(107,111,224,0.10);
  border: 1px solid #D8D9F8;
  border-radius: 20px;
  padding: 2px 8px;
  font-size: 0.62rem;
  color: #6B6FE0;
}

/* ── Input area ── */
.chat-input-wrap {
  border-top: 1px solid #eee;
  padding: 0.9rem 1.4rem;
  background: #fff;
}
.stTextInput > div > div > input {
  background: #ffffff !important;
  border: 1.5px solid #D8D9F8 !important;
  border-radius: 10px !important;
  color: #1A1A4E !important;
  font-family: 'Nunito', sans-serif !important;
  font-size: 0.88rem !important;
  padding: 10px 14px !important;
}
.stTextInput > div > div > input:focus {
  border-color: #6B6FE0 !important;
  box-shadow: 0 0 0 3px rgba(107,111,224,0.12) !important;
}
.stTextInput > div > div > input::placeholder { color: #bbb !important; }

/* ── Ask / Send button — blue ── */
.stButton > button {
  background: #4A5BE8 !important;
  color: #fff !important;
  border: none !important;
  border-radius: 10px !important;
  font-family: 'Nunito', sans-serif !important;
  font-weight: 700 !important;
  padding: 10px 20px !important;
  transition: all 0.2s !important;
  font-size: 0.88rem !important;
}
.stButton > button:hover {
  background: #6B6FE0 !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 16px rgba(74,91,232,0.35) !important;
}
/* End Chat button — red override */
[data-testid="stHorizontalBlock"] div:last-child .stButton > button,
button[kind="secondary"] { background: #E53935 !important; }
div[data-testid="column"]:last-child .stButton > button {
  background: #E53935 !important;
  font-size: 0.78rem !important;
  padding: 8px 14px !important;
  border-radius: 7px !important;
  width: auto !important;
}
div[data-testid="column"]:last-child .stButton > button:hover {
  background: #C62828 !important;
  box-shadow: 0 4px 12px rgba(229,57,53,0.4) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: #f0effc !important;
  border-right: 1px solid #D8D9F8 !important;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] div { color: #4E52C8 !important; }
[data-testid="stSidebar"] .stTextInput > div > div > input {
  background: #fff !important;
  border: 1px solid #B0B3F0 !important;
  color: #1A1A4E !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
  background: #fff !important;
  border: 1px solid #B0B3F0 !important;
  color: #1A1A4E !important;
}
/* Sidebar generate button — orange gem style */
[data-testid="stSidebar"] .stButton > button {
  background: linear-gradient(135deg, #FFA040, #E8720C) !important;
  color: #fff !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: linear-gradient(135deg, #FFB560, #FFA040) !important;
  box-shadow: 0 4px 16px rgba(232,114,12,0.4) !important;
}

/* ── Redirect / session-end box ── */
.redirect-box {
  background: linear-gradient(135deg, #f4f4fd, #eeeffe);
  border: 1px solid #B0B3F0;
  border-radius: 16px;
  padding: 1.8rem;
  text-align: center;
  margin: 1rem;
}
.redirect-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: 1.4rem;
  color: #7B00FF;
  margin-bottom: 0.6rem;
}
.redirect-link {
  display: inline-block;
  background: linear-gradient(135deg, #FFA040, #E8720C);
  color: #fff !important;
  border-radius: 10px;
  padding: 11px 30px;
  font-weight: 700;
  font-size: 0.92rem;
  text-decoration: none;
  margin: 0.8rem 0;
  letter-spacing: 0.04em;
  box-shadow: 0 4px 18px rgba(232,114,12,0.40);
  text-transform: uppercase;
}

/* ── Welcome chips ── */
.chips { margin-top: 1rem; display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; }
.chip {
  background: #fff;
  border: 1px solid #B0B3F0;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 0.75rem;
  color: #6B6FE0;
}

/* ── Consult banner ── */
.consult-banner {
  background: linear-gradient(135deg, #6B6FE0, #7B00FF);
  border-radius: 14px;
  padding: 1.1rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 1rem 1.5rem 1rem;
  box-shadow: 0 4px 20px rgba(107,111,224,0.25);
  color: #fff;
  font-size: 0.82rem;
  line-height: 1.5;
}
.consult-banner a {
  background: linear-gradient(135deg, #FFA040, #E8720C);
  color: #fff !important;
  border-radius: 9px;
  padding: 9px 18px;
  font-weight: 700;
  font-size: 0.8rem;
  text-decoration: none;
  white-space: nowrap;
  margin-left: 1rem;
  box-shadow: 0 3px 12px rgba(232,114,12,0.4);
  flex-shrink: 0;
}

.stSpinner > div { border-top-color: #7B00FF !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #E8E8F5; }
::-webkit-scrollbar-thumb { background: #B0B3F0; border-radius: 2px; }

/* footer divider */
.av-footer-divider {
  border: none;
  height: 2px;
  background: linear-gradient(90deg, transparent, #6B6FE0, #E8720C, #6B6FE0, transparent);
  margin: 0.5rem 1rem;
}
</style>
""", unsafe_allow_html=True)

# ── Clients ───────────────────────────────────────────────────────────────────
@st.cache_resource
def get_clients():
    return (
        Groq(api_key=os.getenv("GROQ_API_KEY")),
        OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    )

groq_client, openai_client = get_clients()

ASTROVED_URL       = "https://qa.astroved.com/new/api/gnpt/astro-insight"
ASTROVED_CLIENT_ID = os.getenv("ASTROVED_CLIENT_ID")
MAX_QUESTIONS      = 5
CONSULTATION_LINK  = "\n\n💬 **Want deeper insights?** [Talk to an Expert Astrologer](https://www.astroved.com/astrovedspeaks/talk-to-astrologer?promo=SL_MM_Talk_to_Astrologer)"

SIGN_ORDER = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo",
              "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

# ── Session state ─────────────────────────────────────────────────────────────
for k, v in {"birth_submitted": False, "chart_data": None,
              "messages": [], "chat_count": 0, "user_name": ""}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Helpers ───────────────────────────────────────────────────────────────────
def compute_whole_sign_houses(chart_data):
    asc_sign  = chart_data["natalChart"]["ascendant"]["sign"]
    asc_index = SIGN_ORDER.index(asc_sign)
    return {SIGN_ORDER[(asc_index + i) % 12]: i + 1 for i in range(12)}

def enrich_planets_with_houses(chart_data):
    house_map = compute_whole_sign_houses(chart_data)
    for p in chart_data.get("natalPlanets", []):
        p["house"] = house_map.get(p["sign"])

@st.cache_data(ttl=3600)
def get_lat_lon(place):
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": place, "format": "json", "limit": 1},
                     headers={"User-Agent": "astroved-ai"}, timeout=10)
    data = r.json()
    if not data:
        raise ValueError("Location not found")
    return float(data[0]["lat"]), float(data[0]["lon"])

@st.cache_data(ttl=3600)
def call_astroved(dob, tob, place, lat, lon):
    r = requests.post(ASTROVED_URL,
        json={"dateOfBirth": dob, "timeOfBirth": tob, "placeOfBirth": place,
              "latitude": lat, "longitude": lon, "timezone": "Asia/Kolkata",
              "ayanamsa": "lahiri", "language": "en"},
        headers={"Content-Type": "application/json", "X-Client-ID": ASTROVED_CLIENT_ID},
        timeout=20)
    if r.status_code != 200:
        raise Exception(r.text)
    return r.json()

def is_astrology_question(q):
    keywords = [
        "career","job","work","profession","business","love","relationship",
        "marriage","partner","spouse","health","wealth","money","finance",
        "income","family","children","parents","education","future","prediction",
        "planet","sign","house","chart","horoscope","birth chart","natal","zodiac",
        "sun","moon","mercury","venus","mars","jupiter","saturn","rahu","ketu",
        "ascendant","lagna","dasha","transit","when will","will i","should i",
        "yoga","rajayoga","yogakaraka","parivartana","trikona","kendra"
    ]
    return any(kw in q.lower() for kw in keywords)

def generate_answer(question, chart_data, name):
    classical_context = ""
    source_namespaces = []
    try:
        results = query_pinecone(query=question, top_k=3, openai_client=openai_client)
        chunks = []
        for m in results:
            text = m.get("metadata", {}).get("text", "")
            ns   = m.get("namespace", "")
            if text:
                chunks.append(f"[{ns}]: {text}")
                if ns not in source_namespaces:
                    source_namespaces.append(ns)
        classical_context = "\n\n".join(chunks[:6])
    except Exception:
        pass

    enrich_planets_with_houses(chart_data)
    chart_summary = json.dumps(chart_data, indent=2)

    system = """You are a Vedic astrology expert powered by AstroVed and trained on classical texts.
RULES:
1. Keep response to 8-10 lines (120-150 words).
2. Answer the SPECIFIC question asked.
3. Blend classical principles with the person's actual chart.
4. Use Sanskrit terms sparingly, with brief English meaning.
5. Be warm, practical, and actionable.
6. Do NOT answer non-astrology questions.
"""
    prompt = f"""User: {name}
Question: {question}

CLASSICAL TEXT CONTEXT:
{classical_context if classical_context else "No specific classical reference found."}

PERSONAL BIRTH CHART:
{chart_summary}

Answer in 120-150 words. Be personal and practical.
"""
    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": system},
                  {"role": "user",   "content": prompt}],
        temperature=0.3,
        max_tokens=200,
    )
    return resp.choices[0].message.content + CONSULTATION_LINK, source_namespaces

# ── Navbar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="av-navbar">
  <div class="av-logo">🔺 AstroVed</div>
  <div class="av-nav-links">
    <a class="av-nav-link" href="https://qa.astroved.com/astrovedspeaks/talk-to-astrologer?promo=SL_MM_Talk_to_Astrologer" target="_blank">📞 Talk to Astrologer</a>
    <a class="av-nav-link" href="https://www.astroved.com/astrovedspeaks/chat-with-astrologer?promo=SL_MM_Chat_to_Astrologer" target="_blank">💬 Chat with Astrologer</a>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div style='font-family:Cormorant Garamond,serif;font-size:1.1rem;color:#4E52C8;margin-bottom:1rem;'>📘 Your Birth Details</div>", unsafe_allow_html=True)

    name  = st.text_input("Full Name", placeholder="Your name")
    dob   = st.date_input("Date of Birth", min_value=date(1900, 1, 1))
    col_h, col_m = st.columns(2)
    with col_h: hour   = st.selectbox("Hour",   range(24))
    with col_m: minute = st.selectbox("Minute", range(60))
    place = st.text_input("Birth Place", placeholder="City, Country")

    if st.button("✨ Generate My Chart"):
        if not name or not place:
            st.error("Please fill in your name and birth place.")
        else:
            with st.spinner("Reading the cosmos..."):
                try:
                    lat, lon = get_lat_lon(place)
                    chart = call_astroved(
                        dob.strftime("%Y-%m-%d"),
                        f"{hour:02d}:{minute:02d}",
                        place, lat, lon
                    )
                    enrich_planets_with_houses(chart)
                    st.session_state.update({
                        "birth_submitted": True,
                        "chart_data": chart,
                        "messages": [],
                        "chat_count": 0,
                        "user_name": name,
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"✨ Namaste {name}! Your birth chart is ready. Ask me anything about your career, relationships, health, yogas, or spiritual path — I'll answer using both your personal chart and classical Vedic texts.",
                        "sources": []
                    })
                    st.success("✅ Chart ready!")
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.birth_submitted:
        st.markdown("---")
        used      = st.session_state.chat_count
        remaining = MAX_QUESTIONS - used
        filled    = "🟠" * used
        empty     = "⚫" * remaining
        st.markdown(
            f"<div style='font-size:0.8rem;color:#4E52C8;margin-bottom:4px;'>Questions used</div>"
            f"{filled}{empty}"
            f"<div style='font-size:0.75rem;color:#7678C8;margin-top:4px;'>{remaining} remaining</div>",
            unsafe_allow_html=True
        )

# ── Main area ─────────────────────────────────────────────────────────────────
if not st.session_state.birth_submitted:
    # ── Welcome screen ──
    st.markdown("""
    <div class="chat-card">
      <div class="chat-header">
        <div>
          <div class="chat-header-name">🪐 astrology AI · AstroVed</div>
          <div class="chat-header-status">Enter birth details in sidebar to begin</div>
        </div>
      </div>
      <div class="chat-messages" style="display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:300px;">
        <div style="position:relative;z-index:1;text-align:center;padding:2rem 1rem;">
          <div style="font-family:'Cormorant Garamond',serif;font-size:1.3rem;color:#4E52C8;font-style:italic;margin-bottom:0.7rem;">
            Enter your birth details to begin
          </div>
          <div style="font-size:0.8rem;color:#7678C8;line-height:1.8;margin-bottom:1rem;">
            Combines your personal chart with wisdom from<br>
            Laghu Parashari · Saravali · Prasna Marga
          </div>
          <div class="chips">
            <span class="chip">🪐 Personal birth chart</span>
            <span class="chip">📚 54 classical texts</span>
            <span class="chip">🤖 AI-synthesized answers</span>
            <span class="chip">💬 5 free questions</span>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

elif st.session_state.chat_count >= MAX_QUESTIONS:
    # ── Session complete ──
    used = MAX_QUESTIONS
    # render all messages
    msgs_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            msgs_html += f"""
            <div class="msg-row msg-user">
              <div class="bubble-user">{msg["content"]}</div>
              <div class="msg-time">You</div>
            </div>"""
        else:
            srcs = msg.get("sources", [])
            src_html = ""
            if srcs:
                tags = "".join([f"<span class='src-tag'>📚 {s}</span>" for s in srcs[:4]])
                src_html = f"<div class='sources'>{tags}</div>"
            msgs_html += f"""
            <div class="msg-row msg-bot">
              <div class="bubble-bot">{msg["content"]}{src_html}</div>
              <div class="msg-time">🪐 astrology AI</div>
            </div>"""

    st.markdown(f"""
    <div class="chat-card">
      <div class="chat-header">
        <div>
          <div class="chat-header-name">🪐 astrology AI · AstroVed</div>
          <div class="chat-header-status">Session complete — {st.session_state.user_name}</div>
        </div>
        <button class="btn-end-chat">End Chat</button>
      </div>
      <div class="counter-strip">
        <span>Questions used: {"🟠" * used}</span>
        <span>0 remaining</span>
      </div>
      <div class="chat-messages">{msgs_html}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="redirect-box">
      <div class="redirect-title">🪐 Your free session is complete</div>
      <div style="font-size:0.85rem;color:#7678C8;line-height:1.7;margin-bottom:0.8rem;">
        You've used all 5 free questions. For a deeper personalised consultation<br>with a human expert astrologer:
      </div>
      <a class="redirect-link" href="https://qa.astroved.com/astrovedspeaks/talk-to-astrologer?promo=SL_MM_Talk_to_Astrologer" target="_blank">
        Book Consultation →
      </a>
      <div style="font-size:0.75rem;color:#7678C8;margin-top:0.6rem;">
        Career · Relationships · Health · Spiritual Growth · Timing
      </div>
    </div>
    """, unsafe_allow_html=True)

else:
    # ── Active chat ──
    used      = st.session_state.chat_count
    remaining = MAX_QUESTIONS - used
    filled    = "🟠" * used
    empty     = "⚫" * remaining

    # Build messages HTML
    msgs_html = ""
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            msgs_html += f"""
            <div class="msg-row msg-user">
              <div class="bubble-user">{msg["content"]}</div>
              <div class="msg-time">You</div>
            </div>"""
        else:
            srcs = msg.get("sources", [])
            src_html = ""
            if srcs:
                tags = "".join([f"<span class='src-tag'>📚 {s}</span>" for s in srcs[:4]])
                src_html = f"<div class='sources'>{tags}</div>"
            msgs_html += f"""
            <div class="msg-row msg-bot">
              <div class="bubble-bot">{msg["content"]}{src_html}</div>
              <div class="msg-time">🪐 astrology AI</div>
            </div>"""

    # ── Chat header with real End Chat button ──
    hcol1, hcol2 = st.columns([5, 1])
    with hcol1:
        st.markdown(f"""
        <div style="background:#7B00FF;padding:1rem 1.4rem;border-radius:16px 0 0 0;display:flex;flex-direction:column;">
          <div class="chat-header-name" style="color:#fff;font-weight:700;font-size:1.05rem;">🪐 Jyotish AI · AstroVed</div>
          <div class="chat-header-status" style="color:rgba(255,255,255,0.72);font-size:0.72rem;margin-top:2px;">Chat In Progress · {st.session_state.user_name}</div>
        </div>
        """, unsafe_allow_html=True)
    with hcol2:
        st.markdown('<div style="background:#7B00FF;padding:0.6rem 0.4rem 0 0;border-radius:0 16px 0 0;height:100%;display:flex;align-items:center;justify-content:center;">', unsafe_allow_html=True)
        if st.button("🔴 End Chat", key="end_chat"):
            for k, v in {"birth_submitted": False, "chart_data": None,
                         "messages": [], "chat_count": 0, "user_name": ""}.items():
                st.session_state[k] = v
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div class="chat-card" style="border-radius:0 0 16px 16px;margin-top:0;">
      <div class="counter-strip">
        <span>Questions used: {filled}{empty}</span>
        <span>{remaining} remaining</span>
      </div>
      <div class="chat-messages">{msgs_html}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Input form ──
    with st.form("chat", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "q",
                placeholder="Write message...",
                label_visibility="collapsed"
            )
        with col2:
            send = st.form_submit_button("➤ Send")

    if send and user_input.strip():
        if not is_astrology_question(user_input):
            st.session_state.messages.append({"role": "user", "content": user_input})
            st.session_state.messages.append({
                "role": "assistant",
                "content": "I can only answer astrology and life-guidance questions. Try asking about career, relationships, health, planetary yogas, or your dashas!",
                "sources": []
            })
        else:
            st.session_state.chat_count += 1
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.spinner("Consulting classical texts & your chart..."):
                answer, sources = generate_answer(
                    user_input,
                    st.session_state.chart_data,
                    st.session_state.user_name
                )
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })
        st.rerun()

    # ── Consult banner ──
    st.markdown("""
    <div class="consult-banner">
      <div>
        <strong style="font-size:0.9rem;">💬 Want deeper insights?</strong><br>
        Talk to a real expert astrologer for a personalised in-depth consultation
      </div>
      <div style="display:flex;flex-direction:column;gap:6px;margin-left:1rem;flex-shrink:0;">
        <a href="https://qa.astroved.com/astrovedspeaks/talk-to-astrologer?promo=SL_MM_Talk_to_Astrologer" target="_blank" style="background:linear-gradient(135deg,#FFA040,#E8720C);color:#fff;border-radius:8px;padding:7px 14px;font-weight:700;font-size:0.75rem;text-decoration:none;text-align:center;white-space:nowrap;">📞 Talk to Astrologer</a>
        <a href="https://www.astroved.com/astrovedspeaks/chat-with-astrologer?promo=SL_MM_Chat_to_Astrologer" target="_blank" style="background:rgba(255,255,255,0.18);color:#fff;border-radius:8px;padding:7px 14px;font-weight:700;font-size:0.75rem;text-decoration:none;text-align:center;white-space:nowrap;border:1px solid rgba(255,255,255,0.35);">💬 Chat with Astrologer</a>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("<div class='av-footer-divider'></div>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;font-size:0.7rem;color:#7678C8;padding:0.5rem 0 1rem;'>"
    "Powered by AstroVed · Classical Vedic Texts · AI · "
    "<a href='https://www.astroved.com' style='color:#6B6FE0;font-weight:600;'>www.astroved.com</a>"
    "</div>",
    unsafe_allow_html=True
)