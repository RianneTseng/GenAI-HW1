import streamlit as st
from openai import OpenAI
import PyPDF2
import io
import base64

# 設定網頁標題
st.set_page_config(page_title="My Custom ChatGPT", layout="wide")

# 初始化 OpenAI 客戶端
client = OpenAI()

# 初始化 Session State
if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = {"Default": []}
if "current_session" not in st.session_state:
    st.session_state.current_session = "Default"
if "user_memories" not in st.session_state:
    st.session_state.user_memories = []
if "selected_tone" not in st.session_state:
    st.session_state.selected_tone = "標準"

# 語氣定義
tone_options = {
    "標準": "請用中性、專業的語氣回答。",
    "幽默": "請用風趣、幽默的語氣回答，讓對話更有趣。",
    "簡潔": "請用極度簡潔的方式回答，直接切入重點，不要有冗詞贅句。",
    "溫柔": "請用溫柔、體貼且充滿鼓勵的口吻回答。",
    "嚴謹": "請用學術、嚴謹且邏輯縝密的語氣回答。"
}

# 定義使用者記憶對話框
@st.dialog("使用者記憶管理")
def manage_memories():
    st.write("在這裡儲存關於您的資訊，模型將會在後續對話中參考。")
    
    # 語氣選擇
    st.session_state.selected_tone = st.selectbox(
        "選擇預設語氣",
        options=list(tone_options.keys()),
        index=list(tone_options.keys()).index(st.session_state.selected_tone)
    )
    
    # 新增記憶
    new_memory = st.text_input("新增記憶條目 (例如：我是一名學生)", key="new_mem_input")
    if st.button("儲存新記憶"):
        if new_memory and new_memory not in st.session_state.user_memories:
            st.session_state.user_memories.append(new_memory)
            st.rerun()
    
    st.divider()
    
    # 顯示與刪除記憶
    if st.session_state.user_memories:
        st.write("目前的記憶列表：")
        for i, m in enumerate(st.session_state.user_memories):
            col1, col2 = st.columns([0.8, 0.2])
            col1.text(f"- {m}")
            if col2.button("刪除", key=f"del_mem_{i}"):
                st.session_state.user_memories.pop(i)
                st.rerun()
    
    if st.button("關閉"):
        st.rerun()

# 側邊欄：對話設定
with st.sidebar:
    st.title("對話設定")
    
    # 1. 記憶管理入口
    if st.button("開啟使用者記憶設定"):
        manage_memories()
    
    st.divider()
    
    # 2. 對話管理
    new_session_name = st.text_input("新增對話名稱", key="new_session_input")
    if st.button("新增對話"):
        if new_session_name and new_session_name not in st.session_state.chat_sessions:
            st.session_state.chat_sessions[new_session_name] = []
            st.session_state.current_session = new_session_name
    
    session_list = list(st.session_state.chat_sessions.keys())
    st.session_state.current_session = st.selectbox(
        "選擇對話", 
        session_list, 
        index=session_list.index(st.session_state.current_session)
    )

    st.divider()

    # 3. 模型與參數
    model_option = st.selectbox(
        "選擇模型",
        ["gpt-5-nano", "gpt-4o-mini", "gpt-4.1-nano"]
    )
    
    system_prompt_base = st.text_area("基礎 System Prompt", value="你是一個專業的助手")
    temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)

    if st.button("清除當前對話歷史"):
        st.session_state.chat_sessions[st.session_state.current_session] = []
        st.rerun()

# 檔案處理函數
def process_file(uploaded_file):
    if uploaded_file is not None:
        file_type = uploaded_file.type
        if "image" in file_type:
            base64_image = base64.b64encode(uploaded_file.read()).decode('utf-8')
            return {"type": "image_url", "image_url": {"url": f"data:{file_type};base64,{base64_image}"}}
        elif file_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = "".join([page.extract_text() for page in pdf_reader.pages])
            return {"type": "text", "text": f"[PDF 檔案內容]:\n{text}"}
    return None

# 主畫面
st.title(f"當前對話: {st.session_state.current_session}")

current_messages = st.session_state.chat_sessions[st.session_state.current_session]

# 顯示歷史紀錄
for msg in current_messages:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            for item in msg["content"]:
                if item["type"] == "text":
                    st.markdown(item["text"])
                elif item["type"] == "image_url":
                    st.image(item["image_url"]["url"])
        else:
            st.markdown(msg["content"])

uploaded_file = st.file_uploader("上傳照片或 PDF", type=["png", "jpg", "jpeg", "pdf"])

if prompt := st.chat_input("請輸入訊息"):
    content_list = [{"type": "text", "text": prompt}]
    file_data = process_file(uploaded_file)
    if file_data:
        content_list.append(file_data)

    current_messages.append({"role": "user", "content": content_list})
    
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_file:
            st.write(f"已附加檔案: {uploaded_file.name}")

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # 動態組合記憶與語氣進入 System Prompt
        memories_text = "\n".join([f"- {m}" for m in st.session_state.user_memories])
        final_system_content = f"""{system_prompt_base}

使用者長期記憶：
{memories_text if memories_text else "無特定記憶"}

指定語氣：
{tone_options[st.session_state.selected_tone]}
"""
        
        api_messages = [{"role": "system", "content": final_system_content}] + [
            {"role": m["role"], "content": m["content"]} for m in current_messages
        ]

        try:
            stream = client.chat.completions.create(
                model=model_option,
                messages=api_messages,
                #temperature=temperature,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "|")
            
            message_placeholder.markdown(full_response)
            current_messages.append({"role": "assistant", "content": full_response})
        except Exception as e:
            st.error(f"錯誤: {str(e)}")