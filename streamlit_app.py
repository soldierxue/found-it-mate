import streamlit as st
import os
from PIL import Image
import io
import base64
import openai
from dotenv import load_dotenv
from gtts import gTTS
import tempfile
import time

# 加载环境变量
load_dotenv()

# 设置页面配置
st.set_page_config(
    page_title="家居物品定位助手",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed",  # 在移动端默认收起侧边栏
    menu_items={
        'About': "家居物品定位助手 - 帮助您找到家中物品的最佳位置"
    }
)

# 加载自定义CSS
with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# 文字转语音函数
def text_to_speech(text, lang='zh-cn'):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(fp.name)
        return fp.name

# 初始化兼容OpenAI的第三方API客户端
# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.api_base = st.secrets["OPENAI_API_BASE"]

# 应用标题和介绍
st.markdown("<h1 style='text-align: center;'>家居物品定位助手 🏠</h1>", unsafe_allow_html=True)
st.markdown("""
<p style='text-align: center; padding: 0 10px;'>
上传一张物品的照片，AI将帮助您找到它在家中可能的位置！
</p>
""", unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("关于")
    st.info("""
    这个应用使用Claude AI Vision模型来分析您上传的物品图片，
    并提供关于该物品在家中可能存放位置的建议。
    """)
    
    st.header("使用说明")
    st.markdown("""
    1. 上传一张物品的照片
    2. 等待AI分析图片
    3. 查看AI给出的建议位置
    4. 可以通过聊天框或语音进一步询问详情
    """)
    
    # 语音设置
    st.header("语音设置")
    enable_voice = st.checkbox("启用语音功能", value=True)

# 创建两列布局用于图片上传
col1, col2, col3 = st.columns([1, 10, 1])

with col2:
    # 图片上传功能
    st.markdown("<div class='upload-header'>上传物品照片</div>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("上传物品照片", type=["jpg", "jpeg", "png"], label_visibility="collapsed")

# 处理上传的图片
if uploaded_file is not None:
    # 显示上传的图片
    image = Image.open(uploaded_file)
    
    # 调整图片大小以适应移动屏幕
    max_width = 300
    if image.width > max_width:
        ratio = max_width / image.width
        new_height = int(image.height * ratio)
        image = image.resize((max_width, new_height), Image.LANCZOS)
    
    # 居中显示图片
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(image, caption="上传的图片", use_column_width=True)
    
    # 转换图片为base64格式
    buffered = io.BytesIO()
    # 如果图像有透明通道(RGBA)，转换为RGB模式
    if image.mode == 'RGBA':
        image_rgb = Image.new('RGB', image.size, (255, 255, 255))
        image_rgb.paste(image, mask=image.split()[3])  # 使用alpha通道作为mask
        image_rgb.save(buffered, format="JPEG")
    else:
        image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # 添加一个按钮来触发分析
    if st.button("分析物品", key="analyze_button"):
        with st.spinner("AI正在分析图片..."):
            try:
                # 调用API进行图像分析
                response = openai.ChatCompletion.create(
                    model="claude-3-7-sonnet",  # 使用兼容的模型名称
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个专业的家居物品定位助手。用户会上传一张物品的照片，你需要：1. 识别这个物品是什么；2. 详细描述这个物品在家中可能的存放位置；3. 给出3-5个最可能的具体位置建议，并解释原因。请用中文回答，语气友好专业。"
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "这是什么物品？它在家里通常会放在哪里？请给我一些具体的位置建议。"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                
                # 显示AI的回答
                st.markdown("<div class='result-header'>AI分析结果</div>", unsafe_allow_html=True)
                ai_response = response.choices[0].message.content
                
                # 格式化AI回答，使其更易于阅读
                formatted_response = ai_response.replace('**', '__')  # 替换粗体标记为下划线标记
                st.markdown(formatted_response)
                
                # 如果启用了语音，将AI回答转换为语音
                if 'enable_voice' in locals() and enable_voice:
                    with st.spinner("正在生成语音..."):
                        speech_file = text_to_speech(ai_response)
                        
                        # 添加语音播放控件
                        st.markdown("<div class='audio-player'>", unsafe_allow_html=True)
                        st.audio(speech_file, format='audio/mp3')
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # 保存会话状态
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                
                # 添加系统消息和用户上传图片的消息到会话
                if not st.session_state.messages:
                    st.session_state.messages.append({"role": "system", "content": "你是一个专业的家居物品定位助手。请继续用中文回答用户关于这个物品的问题。"})
                    st.session_state.messages.append({"role": "user", "content": "我上传了一张物品的照片"})
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 聊天功能
st.markdown("<div class='chat-header'>有更多问题？直接问我！</div>", unsafe_allow_html=True)

# 初始化聊天历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示聊天历史
for message in st.session_state.messages:
    if message["role"] != "system":  # 不显示系统消息
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# 聊天输入
if prompt := st.chat_input("输入您的问题"):
    # 添加用户消息到聊天历史
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # 显示用户消息
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # 生成助手回复
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 调用API
                response = openai.ChatCompletion.create(
                    model="claude-3-7-sonnet",  # 使用兼容的模型名称
                    messages=st.session_state.messages,
                    max_tokens=1000
                )
                
                assistant_response = response.choices[0].message.content
                st.markdown(assistant_response)
                
                # 如果启用了语音，将AI回答转换为语音
                if 'enable_voice' in locals() and enable_voice:
                    with st.spinner("正在生成语音..."):
                        speech_file = text_to_speech(assistant_response)
                        st.audio(speech_file, format='audio/mp3')
                
                # 添加助手回复到聊天历史
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})
                
            except Exception as e:
                st.error(f"发生错误: {str(e)}")

# 添加页脚
st.markdown("---")
st.markdown("<footer>© 2025 家居物品定位助手 | 由Streamlit和Claude AI提供技术支持</footer>", unsafe_allow_html=True)
