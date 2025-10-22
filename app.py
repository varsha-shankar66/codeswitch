import json
import textwrap
from datetime import datetime
from typing import Dict, Tuple

import streamlit as st
import streamlit.components.v1 as components


# ---------- Page setup ----------
st.set_page_config(
    page_title="Code Converter",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------- Session state initialization ----------
def init_session_state() -> None:
    defaults = {
        "from_lang": "Python",
        "to_lang": "JavaScript",
        "prompt": "",
        "input_code": "",
        "output_code": "",
        "history": [],  # List[Dict]
        "history_limit": 10,
        "ai_open": False,
        "ai_messages": [],
        "theme": "Light",  # Light | Dark | Auto
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()


# ---------- Constants & helpers ----------
LANGUAGES = ["Python", "Java", "C++", "JavaScript"]


def language_to_ext_and_highlight(lang: str) -> Tuple[str, str, str]:
    mapping: Dict[str, Tuple[str, str, str]] = {
        "Python": (".py", "python", "text/x-python"),
        "Java": (".java", "java", "text/x-java-source"),
        "C++": (".cpp", "cpp", "text/x-c++src"),
        "JavaScript": (".js", "javascript", "application/javascript"),
    }
    return mapping.get(lang, (".txt", "text", "text/plain"))


def convert_code_placeholder(from_lang: str, to_lang: str, prompt: str, code: str) -> str:
    banner = f"// Conversion from {from_lang} to {to_lang} completed!\n"
    comment_prefix = {
        "Python": "# ",
        "Java": "// ",
        "C++": "// ",
        "JavaScript": "// ",
    }.get(to_lang, "// ")
    prompt_block = (
        f"{comment_prefix}Prompt: {prompt.strip()}\n" if prompt.strip() else ""
    )
    note = (
        f"{comment_prefix}This is a placeholder. Replace with real conversion output.\n\n"
    )
    original_header = f"{comment_prefix}Original {from_lang} code below for reference:\n"
    original = textwrap.indent(code, prefix=comment_prefix)
    return banner + prompt_block + note + original_header + original


def add_to_history(from_lang: str, to_lang: str, prompt: str, code: str) -> None:
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "from": from_lang,
        "to": to_lang,
        "prompt": prompt.strip(),
        "code_preview": (code[:120] + "…") if len(code) > 120 else code,
    }
    st.session_state.history.insert(0, entry)
    # Trim history
    st.session_state.history = st.session_state.history[: st.session_state.history_limit]


def inject_css(theme: str) -> None:
    is_dark = theme == "Dark"
    primary = "#2563eb"  # blue-600
    bg_light = "#f7f9fc"
    card_light = "#ffffff"
    text_light = "#0f172a"  # slate-900

    bg_dark = "#0b1220"
    card_dark = "#121a2a"
    text_dark = "#e5e7eb"

    bg = bg_dark if is_dark else bg_light
    card = card_dark if is_dark else card_light
    text = text_dark if is_dark else text_light

    st.markdown(
        f"""
        <style>
        :root {{
          --primary: {primary};
          --bg: {bg};
          --card: {card};
          --text: {text};
        }}

        .stApp {{
          background: var(--bg);
          color: var(--text);
        }}

        /* Cards */
        .cc-card {{
          background: var(--card);
          border-radius: 14px;
          padding: 1rem 1.25rem;
          box-shadow: 0 8px 24px rgba(2, 6, 23, 0.08);
          border: 1px solid rgba(2, 6, 23, 0.06);
        }}

        /* Buttons */
        .stButton > button {{
          background: var(--primary);
          color: white;
          border: none;
          border-radius: 12px;
          padding: 0.6rem 1rem;
          font-weight: 600;
          box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
          transition: transform 0.06s ease, box-shadow 0.2s ease;
        }}
        .stButton > button:hover {{
          transform: translateY(-1px);
          box-shadow: 0 10px 24px rgba(37, 99, 235, 0.45);
        }}

        /* File uploader dropzone */
        [data-testid="stFileUploaderDropzone"] {{
          background: var(--card);
          border-radius: 12px;
          border: 1px dashed rgba(2, 6, 23, 0.18);
          box-shadow: inset 0 0 0 1px rgba(2, 6, 23, 0.04);
        }}

        textarea, .stTextArea textarea {{
          border-radius: 12px !important;
          border: 1px solid rgba(2, 6, 23, 0.1);
          box-shadow: 0 4px 12px rgba(2, 6, 23, 0.05);
        }}

        /* Code block */
        pre, code {{
          border-radius: 12px !important;
        }}

        /* Copy button inside components.html */
        .copy-btn {{
          background: var(--card);
          color: var(--text);
          border: 1px solid rgba(2, 6, 23, 0.12);
          border-radius: 12px;
          padding: 0.5rem 0.75rem;
          cursor: pointer;
          font-weight: 600;
          transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.06s ease;
          box-shadow: 0 4px 12px rgba(2,6,23,0.06);
        }}
        .copy-btn:hover {{
          transform: translateY(-1px);
          box-shadow: 0 8px 18px rgba(2,6,23,0.10);
        }}

        /* Section titles */
        .cc-title {{
          font-weight: 800; letter-spacing: -0.01em;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_copy_button(code: str) -> None:
    # Use components.html to trigger clipboard copy via JS
    code_js = json.dumps(code)  # safely escape
    components.html(
        f"""
        <div style="display:flex;align-items:center;gap:0.5rem;">
          <button class="copy-btn" onclick='navigator.clipboard.writeText({code_js}).then(() => {{ window.parent.postMessage({{"type":"copy-success"}}, "*"); }});'>📋 Copy Code</button>
        </div>
        """,
        height=50,
    )


def main():
    # Sidebar - settings and info
    with st.sidebar:
        st.subheader("Settings")
        st.session_state.theme = st.selectbox("Theme", ["Light", "Dark"], index=(0 if st.session_state.theme == "Light" else 1))
        st.session_state.history_limit = st.slider("History size", 3, 30, st.session_state.history_limit)
        st.markdown("---")
        st.subheader("About")
        st.markdown("Built with Streamlit · by Your Name")
        st.caption("This app simulates code conversion; connect to a backend to enable real translations.")

    inject_css(st.session_state.theme)

    # Header row with title and Ask AI button on the right
    title_col, ai_col = st.columns([0.8, 0.2])
    with title_col:
        st.markdown("## 💻 Code Converter")
        st.caption("Convert code between languages with AI (placeholder)")
    with ai_col:
        if st.button("🧠 Ask AI", use_container_width=True):
            st.session_state.ai_open = True

    # Language selectors
    with st.container():
        st.markdown(" ")
        lang_col1, lang_col2 = st.columns(2)
        with lang_col1:
            st.session_state.from_lang = st.selectbox("From Language", LANGUAGES, index=LANGUAGES.index(st.session_state.from_lang))
        with lang_col2:
            st.session_state.to_lang = st.selectbox("To Language", LANGUAGES, index=LANGUAGES.index(st.session_state.to_lang))

    st.markdown("---")

    # Prompt input
    with st.container():
        st.text_input(
            "Prompt",
            key="prompt",
            placeholder="Describe what you want the code to do...",
            help="Optional guidance for conversion",
        )

    # File uploader and input code area
    with st.container():
        up_col, _ = st.columns([1, 0.0001])  # keep uploader full width
        with up_col:
            uploaded = st.file_uploader(
                "Upload source code file",
                type=["py", "java", "cpp", "js", "txt"],
                accept_multiple_files=False,
                help="Drag & drop or browse a single file",
            )
            if uploaded is not None:
                try:
                    content_bytes = uploaded.read()
                    try:
                        content = content_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        content = content_bytes.decode("latin-1", errors="replace")

                    if st.session_state.input_code.strip():
                        # Append to avoid overwriting user's manual input
                        st.session_state.input_code = st.session_state.input_code.rstrip() + "\n\n" + content
                        st.info("Uploaded file content appended to existing input.")
                    else:
                        st.session_state.input_code = content
                        st.success(f"Loaded '{uploaded.name}' into input code.")
                except Exception as e:
                    st.error(f"Failed to read uploaded file: {e}")

        st.markdown(" ")
        st.markdown("Input Code")
        st.text_area(
            label="Input Code",
            key="input_code",
            height=260,
            placeholder="Write or paste your code here...",
            label_visibility="collapsed",
        )

    # Convert button centered
    st.markdown(" ")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        do_convert = st.button("Convert", use_container_width=True)

    # Handle conversion
    if do_convert:
        if not st.session_state.input_code.strip():
            st.warning("Please provide code or upload a file.")
        else:
            from_lang = st.session_state.from_lang
            to_lang = st.session_state.to_lang
            with st.spinner("Converting…"):
                # Simulate conversion
                result = convert_code_placeholder(
                    from_lang=from_lang,
                    to_lang=to_lang,
                    prompt=st.session_state.prompt,
                    code=st.session_state.input_code,
                )
                st.session_state.output_code = result
            st.success(f"Conversion from {from_lang} to {to_lang} completed!")
            add_to_history(from_lang, to_lang, st.session_state.prompt, st.session_state.input_code)

    st.markdown("---")

    # Output area and actions
    out_ext, out_lang, mime = language_to_ext_and_highlight(st.session_state.to_lang)
    st.markdown("#### Output Code")
    if st.session_state.output_code:
        st.code(st.session_state.output_code, language=out_lang)

        # Actions row
        ac1, ac2, ac3 = st.columns([0.18, 0.2, 0.62])
        with ac1:
            render_copy_button(st.session_state.output_code)
        with ac2:
            st.download_button(
                label="⬇️ Download Code",
                data=st.session_state.output_code.encode("utf-8"),
                file_name=f"converted{out_ext}",
                mime=mime,
                use_container_width=True,
            )
    else:
        st.info("Your converted code will appear here after conversion.")

    # Ask AI expander (chat-like area)
    with st.expander("🧠 Ask AI", expanded=st.session_state.ai_open):
        st.caption("Get help or explanations about your code. (Placeholder)")
        # Show conversation
        for msg in st.session_state.ai_messages:
            with st.chat_message(msg.get("role", "assistant")):
                st.markdown(msg.get("content", ""))

        user_q = st.chat_input("Ask a question about the code…")
        if user_q:
            st.session_state.ai_messages.append({"role": "user", "content": user_q})
            # Placeholder assistant response
            assistant_reply = (
                "I'm here to help! This AI helper will explain or refactor your code once connected to a backend."
            )
            st.session_state.ai_messages.append({"role": "assistant", "content": assistant_reply})
            st.session_state.ai_open = True
            try:
                st.rerun()
            except Exception:
                # Fallback for older Streamlit versions
                st.experimental_rerun()

    # History section at the bottom
    with st.expander("History", expanded=False):
        if st.session_state.history:
            for item in st.session_state.history:
                st.markdown(
                    f"**{item['from']} → {item['to']}** · {item['time']}  \n"
                    f"Prompt: {item['prompt'] or '—'}  \n"
                    f"Snippet: {item['code_preview'] or '—'}"
                )
                st.markdown("---")
            if st.button("Clear History"):
                st.session_state.history = []
                st.info("History cleared.")
        else:
            st.write("No conversions yet.")


# Listen to copy success message from iframe and show a toast
components.html(
    """
    <script>
      window.addEventListener('message', (event) => {
        if (event.data && event.data.type === 'copy-success') {
          const streamlitMsg = {isStreamlitMessage: true, type: 'streamlit:setComponentValue', value: 'copied'};
          window.parent.postMessage(streamlitMsg, '*');
        }
      });
    </script>
    """,
    height=0,
)


if __name__ == "__main__":
    main()
