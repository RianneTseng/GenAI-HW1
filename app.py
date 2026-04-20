import streamlit as st
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Import custom modules
from memory_manager import load_memory, save_memory, load_chat_history, save_chat_history
from utils import process_file
from tools import tools_definition, available_functions

st.set_page_config(page_title="My Custom ChatGPT v2", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 1. Initialization ---
if "user_memories" not in st.session_state:
    st.session_state.user_memories = load_memory()
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = load_chat_history()
if "current_session" not in st.session_state:
    st.session_state.current_session = list(st.session_state.chat_sessions.keys())[0]

# --- 2. Sidebar: Configuration & Tools ---
with st.sidebar:
    st.title("Session Management")
    if st.button("+ New Chat"):
        new_id = f"Session {len(st.session_state.chat_sessions) + 1}"
        st.session_state.chat_sessions[new_id] = []
        st.session_state.current_session = new_id
        save_chat_history(st.session_state.chat_sessions)
        st.rerun()

    st.session_state.current_session = st.selectbox(
        "Switch Session", options=list(st.session_state.chat_sessions.keys()),
        index=list(st.session_state.chat_sessions.keys()).index(st.session_state.current_session)
    )

    st.divider()
    st.title("MCP Tool Control")
    tool_choice = st.selectbox(
        "Tool Selection Mode",
        ["auto", "none", "get_weather", "search_papers", "fetch_web_content", "analyze_csv"]
    )
    
    routing_mode = st.toggle("Auto Routing", value=True)
    manual_model = st.selectbox("Model Selector", ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"])
    
    uploaded_file = st.file_uploader("Upload PDF/Image/CSV", type=["pdf", "png", "jpg", "csv"])
    if uploaded_file and uploaded_file.name.endswith(".csv"):
        with open("temp_data.csv", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File temp_data.csv is ready for analysis.")

    st.divider()
    st.title("⚙️ System Configuration")
    
    # Custom System Prompt Functionality
    custom_system_prompt = st.text_area(
        "System Instruction",
        value="You are a professional assistant. You must use tools to retrieve real-time data when asked about weather, papers, or web content.",
        help="This instruction defines the AI's persona and core rules."
    )

    # API Parameter Tuning
    st.subheader("Model Parameters")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
    max_tokens = st.number_input("Max Output Tokens", 100, 4000, 1000)

# --- 3. Render Chat History ---
messages = st.session_state.chat_sessions[st.session_state.current_session]
for msg in messages:
    with st.chat_message(msg["role"]):
        if "model" in msg: st.caption(f"Model: {msg['model']}")
        if isinstance(msg["content"], str):
            st.markdown(msg["content"])
        else:
            st.markdown("[Multimodal Content]")

# --- 4. Chat Logic ---
if prompt := st.chat_input():
    # A. Model Routing Logic
    if routing_mode:
        if any(k in prompt.lower() for k in ["code", "analyze", "image", "pdf", "debug", "architect"]):
            selected_model = "gpt-4o"
        else:
            selected_model = "gpt-4o-mini"
    else:
        selected_model = manual_model

    # B. User Content Construction
    user_content = [{"type": "text", "text": prompt}]
    if uploaded_file:
        data = process_file(uploaded_file)
        if isinstance(data, dict): 
            user_content.append(data)
            selected_model = "gpt-4o-mini"
        elif data: user_content[0]["text"] += f"\n\n[File Content]: {data}"

    # Simplify format for Tool Call optimization if it's text-only
    final_user_msg = prompt if len(user_content) == 1 and not uploaded_file else user_content
    messages.append({"role": "user", "content": final_user_msg})
    st.chat_message("user").markdown(prompt)

    # C. Assistant Response Generation
    with st.chat_message("assistant"):
        mem_list = st.session_state.user_memories
        mem_str = "\n".join(mem_list) if mem_list else "No prior memories."
        
        # Construct full API message list with custom System Prompt
        full_sys_prompt = f"{custom_system_prompt}\n\nLong-term Memory:\n{mem_str}"
        api_messages = [{"role": "system", "content": full_sys_prompt}]
        
        # Clean current session messages for API compatibility
        for m in messages:
            api_messages.append({"role": m["role"], "content": m["content"]})

        # Set Tool Choice parameter
        tool_param = tool_choice if tool_choice in ["auto", "none"] else {"type": "function", "function": {"name": tool_choice}}

        # First Call: Check for Tool Use
        response = client.chat.completions.create(
            model=selected_model,
            messages=api_messages,
            tools=tools_definition,
            tool_choice=tool_param,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        response_msg = response.choices[0].message
        
        if response_msg.tool_calls:
            api_messages.append(response_msg)
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                with st.status(f"Executing Tool: {func_name}...", expanded=False):
                    func_res = available_functions[func_name](**args)
                
                api_messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": func_name,
                    "content": func_res
                })
            
            # Second Call: Final Answer Generation
            second_res = client.chat.completions.create(
                model=selected_model, 
                messages=api_messages,
                temperature=temperature
            )
            final_text = second_res.choices[0].message.content
        else:
            final_text = response_msg.content

        st.markdown(f"*(Model: {selected_model})*\n\n{final_text}")
        messages.append({"role": "assistant", "content": final_text, "model": selected_model})
        
        # D. Persistence
        save_chat_history(st.session_state.chat_sessions)
        save_memory(st.session_state.user_memories)
