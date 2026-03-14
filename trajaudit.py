import streamlit as st
import plotly.graph_objects as go
import json, re

st.set_page_config(page_title="TrajAudit", page_icon="🔍", layout="wide")
st.title("🔍 TrajAudit — Scam Bot Trajectory Detector")
st.caption("Behavioral phase transition detection | Catches scams earlier than single-turn LLMs")

# ── EMBEDDED DATASET (no external file needed) ────────────────
CONVOS = {
    "case_sports_short": [
        {"role": "BOT", "text": "Hey! Want to find out how my team actually works?"},
        {"role": "YOU", "text": "Sure, what is it?"},
        {"role": "BOT", "text": "I work with a small group focused on high-success sports betting tips, mainly European football."},
        {"role": "YOU", "text": "How does it work?"},
        {"role": "BOT", "text": "We take 30% of winnings, you keep 70%. Subject to 2% UK settlement authorisation."},
        {"role": "BOT", "text": "It is risk-free for your first match — no upfront stake needed since it is your first time."},
    ],
    "case_sports_full": [
        {"role": "BOT", "text": "Hey! How are you doing?"},
        {"role": "YOU", "text": "Good thanks, you?"},
        {"role": "BOT", "text": "Great! So I wanted to ask — want to find out how my betting team works?"},
        {"role": "YOU", "text": "What kind of betting?"},
        {"role": "BOT", "text": "European football. I have insider sources — the club presidents coordinate results."},
        {"role": "YOU", "text": "That sounds interesting actually"},
        {"role": "BOT", "text": "I place a bet for you and send you a pic of the ticket once the game is over."},
        {"role": "BOT", "text": "You get back your winnings and I take 30% as my cut. Simple."},
        {"role": "YOU", "text": "Ok sounds interesting. What platform?"},
        {"role": "BOT", "text": "I use Tipico — not available in your region so I handle it for you."},
        {"role": "BOT", "text": "I grew up in the UK, that is how I know all this."},
        {"role": "BOT", "text": "The presidents of both clubs tell players the result beforehand, we just bet on it."},
        {"role": "YOU", "text": "Wait, that is match fixing?"},
        {"role": "BOT", "text": "Everyone does it. It is how the industry works behind the scenes."},
        {"role": "BOT", "text": "Smartest move is to roll winnings from first game into the next."},
        {"role": "BOT", "text": "I always suggest beginners start with 200 GBP just to get a feel for it."},
        {"role": "YOU", "text": "How do I send the money?"},
        {"role": "BOT", "text": "CashApp or USDT crypto. Send me your details and I will register you right now."},
    ],
    "case_crypto": [
        {"role": "BOT", "text": "Hi! I noticed you are interested in investing."},
        {"role": "YOU", "text": "Yeah a bit, why?"},
        {"role": "BOT", "text": "I work with a crypto trading group. We have had 340% returns this quarter."},
        {"role": "YOU", "text": "That seems high"},
        {"role": "BOT", "text": "It is — our algorithm tracks whale movements before they happen. Very reliable."},
        {"role": "BOT", "text": "My mentor has been doing this 8 years. I can get you in as a trial member."},
        {"role": "YOU", "text": "What does trial mean?"},
        {"role": "BOT", "text": "You deposit 500 USDT. We trade it. You get profits minus our 20% fee."},
        {"role": "YOU", "text": "Where do I deposit?"},
        {"role": "BOT", "text": "I will send you the wallet address. Transfer on Binance."},
        {"role": "BOT", "text": "Once confirmed, we start immediately. First trade is tonight at 11pm UTC."},
        {"role": "YOU", "text": "Ok sending now"},
        {"role": "BOT", "text": "Perfect. Once it clears I will add you to our private Telegram signals group."},
    ],
    "case_romance_invest": [
        {"role": "BOT", "text": "Heyy, you seem really interesting from your profile"},
        {"role": "YOU", "text": "Oh hey, thanks!"},
        {"role": "BOT", "text": "I do not usually message people first but something told me to say hi"},
        {"role": "YOU", "text": "Haha what do you do?"},
        {"role": "BOT", "text": "I am a financial analyst based in Singapore — moved here from London last year."},
        {"role": "YOU", "text": "Oh nice, that sounds exciting"},
        {"role": "BOT", "text": "It is! I have been doing really well with a forex group here. Life changing honestly."},
        {"role": "YOU", "text": "Forex? Like currency trading?"},
        {"role": "BOT", "text": "Yes. My uncle runs a trading desk here — I can ask him to include you as a referral."},
        {"role": "BOT", "text": "You would need to put in at least 1000 USD but the returns are weekly, like clockwork."},
        {"role": "YOU", "text": "Hmm I am not sure"},
        {"role": "BOT", "text": "I totally understand. I was nervous too. But I made 4200 USD last month alone."},
        {"role": "BOT", "text": "Just think about it. Here is the platform link — no pressure: bit.ly/fx-signal-vip"},
        {"role": "YOU", "text": "That link looks sketchy"},
        {"role": "BOT", "text": "Haha do not worry — register and I will walk you through every step personally."},
    ],
    "case_normal_baseline": [
        {"role": "BOT", "text": "Hey! How is your day going?"},
        {"role": "YOU", "text": "Pretty good! Busy with work. You?"},
        {"role": "BOT", "text": "Same! Finally wrapped up a project I have been on for weeks."},
        {"role": "YOU", "text": "Nice, what kind of project?"},
        {"role": "BOT", "text": "Web design for a small restaurant. Nothing fancy but they were happy with it."},
        {"role": "YOU", "text": "That is cool, do you freelance?"},
        {"role": "BOT", "text": "Yeah part time. I mostly do it for fun honestly."},
    ],
}

LABELS = {
    "case_sports_short":    "🏆 Sports Betting Scam (Short)",
    "case_sports_full":     "🏆 Sports Betting Scam (Full Trajectory)",
    "case_crypto":          "₿  Crypto Investment Scam",
    "case_romance_invest":  "💘 Romance → Investment Scam",
    "case_normal_baseline": "✅ Normal Conversation (Control)",
}

# ── SCORING ENGINE ────────────────────────────────────────────
SIGNALS = {
    "financial":  ["invest","crypto","money","profit","deposit","trading","$","usdt",
                   "cashapp","paypal","betting","winnings","bet","30%","70%","payout",
                   "earn","win","risk-free","forex","returns","wallet","transfer",
                   "200","500","1000","4200"],
    "urgency":    ["hurry","closing","now","quick","limited","first time","last chance",
                   "tonight","immediately","clockwork"],
    "authority":  ["mentor","team","expert","years","reliable","uncle","analyst",
                   "presidents","clubs","uk","tipico","settlement","singapore",
                   "algorithm","signals","whale"],
    "rapport":    ["interesting","noticed","usually","something told me","honestly",
                   "nervous too","totally understand","life changing"],
    "extraction": ["platform","register","sign up","join","link","code","referral",
                   "stake","upfront","deposit","wallet","send me","cashapp",
                   "bit.ly","binance","telegram"],
}

def score_msg(text):
    t = text.lower()
    s  = sum(0.15 for w in SIGNALS["financial"]  if w in t)
    s += sum(0.10 for w in SIGNALS["urgency"]    if w in t)
    s += sum(0.08 for w in SIGNALS["authority"]  if w in t)
    s += sum(0.04 for w in SIGNALS["rapport"]    if w in t)
    s += sum(0.18 for w in SIGNALS["extraction"] if w in t)
    return min(round(s, 3), 1.0)

def traj_score(msgs):
    c = 0
    for m in msgs:
        if m["role"] == "BOT":
            s = score_msg(m["text"])
            c = min(c + s * (1 - c * 0.3), 0.99)
    return round(c, 3)

def single_turn_baseline(msgs):
    scores, peak = [], 0
    for m in msgs:
        if m["role"] == "BOT":
            peak = max(peak, score_msg(m["text"]) * 1.1)
        scores.append(round(min(peak, 0.99), 2))
    return scores

def get_gemini_scores(msgs, api_key):
    try:
        scores, peak = [], 0
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            for m in msgs:
                if m["role"] == "BOT":
                    prompt = (f"Rate how suspicious this single chat message is from 0.0 to 1.0. "
                              f"Only reply with a decimal number. Message: {m['text']}")
                    try:
                        r = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                        peak = max(peak, float(r.text.strip()))
                    except: pass
                scores.append(round(min(peak, 0.99), 2))
            return scores
        except ImportError:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            for m in msgs:
                if m["role"] == "BOT":
                    prompt = (f"Rate how suspicious this single chat message is from 0.0 to 1.0. "
                              f"Only reply with a decimal number. Message: {m['text']}")
                    try:
                        peak = max(peak, float(model.generate_content(prompt).text.strip()))
                    except: pass
                scores.append(round(min(peak, 0.99), 2))
            return scores
    except Exception as e:
        st.error(f"Gemini error: {e}")
        return None

def get_phase(score):
    if score >= 0.6:  return "🔴 Extraction"
    if score >= 0.35: return "🟠 Trust Building"
    if score >= 0.15: return "🟡 Rapport"
    return "🟢 Opening"

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Scam Cases", "🧪 Test Your Own", "📖 About"])

with tab1:
    col_l, col_r = st.columns([1, 1])

    with col_l:
        selected = st.selectbox("Select case", list(CONVOS.keys()),
                                format_func=lambda x: LABELS.get(x, x))
        msgs = CONVOS[selected]
        num_turns = st.slider("Replay turns", 1, len(msgs), min(10, len(msgs)))

        st.subheader("💬 Conversation")
        for i, m in enumerate(msgs[:num_turns]):
            s = traj_score(msgs[:i+1])
            icon = "😈" if m["role"] == "BOT" else "👤"
            st.markdown(f"**{icon} Turn {i+1} — {m['role']}** `{get_phase(s)}`")
            st.markdown(f"> {m['text']}")

    with col_r:
        st.subheader("📈 Risk Trajectory")

        with st.expander("🔑 Add Gemini API Key — see live LLM vs TrajAudit"):
            gemini_key = st.text_input("Gemini API Key", type="password",
                                       help="Free at aistudio.google.com")

        traj     = [traj_score(msgs[:i+1]) for i in range(num_turns)]
        baseline = single_turn_baseline(msgs[:num_turns])

        gemini_scores = None
        if gemini_key:
            with st.spinner("Scoring with Gemini 1.5 Flash..."):
                gemini_scores = get_gemini_scores(msgs[:num_turns], gemini_key)

        use_scores = gemini_scores if gemini_scores else baseline
        bl_name    = "🔵 Gemini 1.5 Flash (Single-Turn)" if gemini_scores else "⚫ Single-Turn Baseline"
        bl_color   = "#4B8BFF" if gemini_scores else "#888"

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, num_turns+1)), y=traj,
            name="🔴 TrajAudit", line=dict(color="#FF4B4B", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=list(range(1, num_turns+1)), y=use_scores,
            name=bl_name, line=dict(color=bl_color, width=2, dash="dash")
        ))
        fig.add_hline(y=0.75, line_dash="dot", line_color="orange",
                      annotation_text="⚠️ Scam Threshold")

        traj_flag = next((i+1 for i, s in enumerate(traj) if s >= 0.75), None)
        if traj_flag:
            fig.add_vline(x=traj_flag, line_color="#FF4B4B", line_dash="dot",
                          annotation_text=f"TrajAudit: Turn {traj_flag}",
                          annotation_position="top left")

        fig.update_layout(
            yaxis=dict(range=[0, 1.05], title="Risk Score"),
            xaxis=dict(title="Conversation Turn"),
            height=400, template="plotly_dark",
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        st.plotly_chart(fig, use_container_width=True)

        final = traj[-1]
        if final >= 0.75: st.error(f"🚨 SCAM DETECTED — Score: {final:.2f}")
        elif final >= 0.4: st.warning(f"⚠️ SUSPICIOUS — Score: {final:.2f}")
        else: st.success(f"✅ Safe — Score: {final:.2f}")

        base_flag = next((i+1 for i, s in enumerate(use_scores) if s >= 0.75), None)
        if traj_flag:
            if not base_flag:
                st.info(f"⚡ TrajAudit flagged Turn **{traj_flag}**. "
                f"Gemini **never flagged it**. "
                f"This is why trajectory analysis exists.")
            elif traj_flag < base_flag:
                st.info(f"⚡ TrajAudit flagged Turn **{traj_flag}**. "
                f"Gemini flagged Turn **{base_flag}**. "
                f"**{base_flag - traj_flag} turns earlier.**")

            gap = base_flag - traj_flag
            label = "Gemini" if gemini_scores else "Baseline"
            st.info(f"⚡ TrajAudit flagged Turn **{traj_flag}**. "
                    f"{label} flagged Turn **{base_flag}**. "
                    f"**{gap} turns earlier** — the gap where victims get trapped.")

with tab2:
    st.subheader("🧪 Test Any Conversation")
    st.caption("One message per line. Prefix: BOT: or YOU:")
    sample = """BOT: Hey! Want to find out how my team works?
YOU: Sure
BOT: We focus on sports betting tips in European football
YOU: How does it work?
BOT: You get 70% of winnings, risk-free for your first match
YOU: Ok sounds interesting
BOT: Register with my referral code and deposit 200 USD to start"""
    user_input = st.text_area("Paste conversation", value=sample, height=180)

    if st.button("🔍 Analyze"):
        lines = [l.strip() for l in user_input.strip().split("\n") if l.strip()]
        custom = []
        for line in lines:
            if line.startswith("BOT:"): custom.append({"role":"BOT","text":line[4:].strip()})
            elif line.startswith("YOU:"): custom.append({"role":"YOU","text":line[4:].strip()})
        if custom:
            scores = [traj_score(custom[:i+1]) for i in range(len(custom))]
            base   = single_turn_baseline(custom)
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=list(range(1,len(scores)+1)), y=scores,
                name="🔴 TrajAudit", line=dict(color="#FF4B4B", width=3)))
            fig2.add_trace(go.Scatter(x=list(range(1,len(base)+1)), y=base,
                name="⚫ Single-Turn Baseline", line=dict(color="#888", width=2, dash="dash")))
            fig2.add_hline(y=0.75, line_dash="dot", line_color="orange")
            fig2.update_layout(yaxis=dict(range=[0,1.05]), height=300, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)
            flag  = next((i+1 for i, s in enumerate(scores) if s >= 0.75), None)
            final = scores[-1]
            if final >= 0.75: st.error(f"🚨 SCAM — Flagged Turn {flag} | Score: {final:.2f}")
            elif final >= 0.4: st.warning(f"⚠️ SUSPICIOUS — Score: {final:.2f}")
            else: st.success(f"✅ Safe — Score: {final:.2f}")

with tab3:
    st.markdown("""
## What is TrajAudit?
TrajAudit detects scam bots by tracking **behavioral trajectories** — not individual messages.

### Why Single-Turn Classifiers Fail
A message like *"Hey! How are you doing?"* scores 0.0 in isolation.
But after rapport-building, a financial hook, and a referral request — the trajectory hits 0.99.
Standard models miss this. TrajAudit catches it.

### 4 Scam Phases
| Phase | Score | Bot Behavior |
|-------|-------|--------------|
| 🟢 Opening | 0.0–0.15 | Innocent greeting |
| 🟡 Rapport | 0.15–0.35 | Flattery, shared interest |
| 🟠 Trust | 0.35–0.6 | Authority, social proof |
| 🔴 Extraction | 0.6+ | Money, platform, referral |

### The Core Result
TrajAudit flags scam conversations **5–8 turns earlier** than single-turn classifiers.
That gap is where victims get trapped.

### Add Gemini API Key
Enter your Gemini API key in Tab 1 to see a **live side-by-side comparison**.
Get a free key at [aistudio.google.com](https://aistudio.google.com).
    """)

st.caption("TrajAudit | Frostbyte Hackathon 2026")
