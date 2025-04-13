import streamlit as st
import os
from PIL import Image
import io
import base64
import openai
from dotenv import load_dotenv
import datetime
import time
import json
import random

# Load environment variables
load_dotenv()

# Set page config for mobile-friendly display
st.set_page_config(
    page_title="Found IT, Mate!",
    page_icon="🏠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 初始化兼容OpenAI的第三方API客户端
# openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_base = os.getenv("OPENAI_API_BASE")
openai.api_key = st.secrets["OPENAI_API_KEY"]
openai.api_base = st.secrets["OPENAI_API_BASE"]

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []

if "selected_image" not in st.session_state:
    st.session_state.selected_image = None

# Function to handle image selection
def select_image(index, img_data, is_selected):
    if is_selected:
        st.session_state.selected_image = None
    else:
        st.session_state.selected_image = img_data

# Function to delete image
def delete_image(index):
    # Find the image in the uploaded_images list
    for i, img in enumerate(st.session_state.uploaded_images):
        if img["id"] == index:
            # If the deleted image was selected, clear selection
            if st.session_state.selected_image and st.session_state.selected_image["id"] == index:
                st.session_state.selected_image = None
            # Remove the image from the list
            st.session_state.uploaded_images.pop(i)
            break

# Function to create thumbnail
def create_thumbnail(image, size=(45, 45)):
    img_copy = image.copy()
    img_copy.thumbnail(size)
    return img_copy

# Function to encode image to base64
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode == 'RGBA':
        image_rgb = Image.new('RGB', image.size, (255, 255, 255))
        image_rgb.paste(image, mask=image.split()[3])
        image_rgb.save(buffered, format="JPEG")
    else:
        image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# Function to get AI response
def get_ai_response(prompt, image_base64=None, context=None):
    try:
        system_message = """You are Found IT, Mate! - a helpful assistant that helps users manage household items. 
        You can help with:
        1. Finding items in the home
        2. Tracking expiry dates of drugs and food
        3. Managing books and creating sharing platforms
        4. Providing clothing tips based on weather and occasion
        
        Be concise, practical and helpful in your responses.
        """
        
        if context:
            system_message += f"\nCurrent context: {context}"
        
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add chat history for context (last 5 messages)
        for msg in st.session_state.chat_history[-5:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        if image_base64:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})
        
        response = openai.ChatCompletion.create(
            model="claude-3-7-sonnet",
            messages=messages,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    /* Global styles */
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #333;
        background-color: #f5f5f5;
        margin: 0;
        padding: 0;
    }
    
    /* Header styles */
    .app-header {
        background-color: #FF6B35;
        color: white;
        padding: 15px;
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 20px;
        border-radius: 0 0 15px 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #f0f0f0;
        border-radius: 15px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 10px;
        padding: 0 10px;
        font-size: 0.8rem;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF6B35 !important;
        color: white !important;
    }
    
    /* Thumbnail grid styles */
    .thumbnail-container {
        margin-bottom: 10px;
        border-radius: 8px;
        overflow: hidden;
        border: 2px solid transparent;
        transition: all 0.2s;
        height: 60px;
        width: 60px;
        display: inline-block;
        margin-right: 8px;
        position: relative;
    }
    
    .selected-thumbnail {
        margin-bottom: 10px;
        border-radius: 8px;
        overflow: hidden;
        border: 2px solid #FF6B35;
        box-shadow: 0 0 8px rgba(255, 107, 53, 0.7);
        transition: all 0.2s;
        height: 60px;
        width: 60px;
        display: inline-block;
        margin-right: 8px;
        transform: scale(1.05);
        position: relative;
        z-index: 10;
    }
    
    .thumbnail-container img, .selected-thumbnail img {
        width: 100%;
        height: 100%;
        border-radius: 6px;
        object-fit: cover;
    }
    
    .thumbnail-actions {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        display: flex;
        justify-content: space-between;
        padding: 2px;
        background-color: rgba(0,0,0,0.5);
        opacity: 0;
        transition: opacity 0.2s;
    }
    
    .thumbnail-container:hover .thumbnail-actions,
    .selected-thumbnail:hover .thumbnail-actions {
        opacity: 1;
    }
    
    .thumbnail-action-btn {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        font-size: 12px;
        color: white;
    }
    
    .select-btn {
        background-color: rgba(76, 175, 80, 0.8);
    }
    
    .delete-btn {
        background-color: rgba(244, 67, 54, 0.8);
    }
    
    .selected-icon {
        position: absolute;
        top: -5px;
        right: -5px;
        background-color: #FF6B35;
        color: white;
        border-radius: 50%;
        width: 20px;
        height: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        box-shadow: 0 0 5px rgba(0,0,0,0.3);
    }
    
    .thumbnail-container img, .selected-thumbnail img {
        width: 100%;
        height: 100%;
        border-radius: 6px;
        object-fit: cover;
    }
    
    /* Selected image display */
    .selected-image-container {
        border: 2px solid #FF6B35;
        border-radius: 15px;
        padding: 10px;
        margin: 15px 0;
        box-shadow: 0 5px 15px rgba(255, 107, 53, 0.3);
        animation: float 3s ease-in-out infinite;
    }
    
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-5px); }
        100% { transform: translateY(0px); }
    }
    
    /* Chat styling */
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-user"] {
        background-color: #4CAF50 !important;
    }
    
    .stChatMessage [data-testid="chatAvatarIcon-assistant"] {
        background-color: #2196F3 !important;
    }
    
    /* Button styling */
    button[kind="primary"] {
        background-color: #FF6B35 !important;
        border-radius: 20px !important;
    }
    
    button[kind="secondary"] {
        border-color: #FF6B35 !important;
        color: #FF6B35 !important;
        border-radius: 20px !important;
    }
    
    /* Input styling */
    .stTextInput input, .stSelectbox select {
        border-radius: 20px;
    }
    
    /* File uploader */
    .stFileUploader {
        padding: 10px;
        border-radius: 20px;
        border: 2px dashed #FF6B35;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Hide specific elements */
    button[key^="select_btn_"], button[key^="delete_btn_"] {
        display: none !important;
        position: absolute;
        opacity: 0;
        pointer-events: none;
    }
    
    /* Bottom spacing for chat input */
    .bottom-spacer {
        height: 80px;
    }
    
    /* Feature card */
    .feature-card {
        background-color: white;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .feature-card:hover {
        transform: translateY(-2px);
    }
    
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 10px;
        color: #FF6B35;
    }
</style>
""", unsafe_allow_html=True)

# App header
st.markdown('<div class="app-header">Found IT, Mate!</div>', unsafe_allow_html=True)

# Tabs for navigation
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Home", "🔍 Find", "⏱️ Expiry", "📚 Books", "👕 Clothing"])

# Home tab
with tab1:
    st.markdown("""
    <div class="feature-card" onclick="document.querySelector('[data-baseweb=\\\"tab\\\"]').click()">
        <div class="feature-icon">🔍</div>
        <h3>Find Items</h3>
        <p>AI identifies items via user description, provides location.</p>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">⏱️</div>
        <h3>Drug & Food Expiry</h3>
        <p>Track quantity/shelf life, remind expiry.</p>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">📚</div>
        <h3>Book Management</h3>
        <p>Manage books, create sharing platform for friends.</p>
    </div>
    
    <div class="feature-card">
        <div class="feature-icon">👕</div>
        <h3>Clothing Tips</h3>
        <p>Recommend outfits based on weather, occasion.</p>
    </div>
    """, unsafe_allow_html=True)

# Find Items tab
with tab2:
    st.subheader("Find Items")
    st.write("Upload a photo or describe an item to find its location.")
    
    # Image gallery
    if st.session_state.uploaded_images:
        st.write("Recent images:")
        
        # Create a container for thumbnails with flex layout
        st.markdown("""
        <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
        """, unsafe_allow_html=True)
        
        # Display thumbnails in a flexible grid
        for i, img_data in enumerate(st.session_state.uploaded_images[-10:]):
            is_selected = st.session_state.selected_image and st.session_state.selected_image["id"] == img_data["id"]
            
            # Add CSS class based on selection state
            container_class = "selected-thumbnail" if is_selected else "thumbnail-container"
            
            # Create thumbnail with action buttons
            st.markdown(
                f"""
                <div class="{container_class}">
                    <img src="data:image/jpeg;base64,{img_data['image']}" alt="Thumbnail {i}">
                    <div class="thumbnail-actions">
                        <div class="thumbnail-action-btn select-btn" onclick="selectImage({img_data['id']})">✓</div>
                        <div class="thumbnail-action-btn delete-btn" onclick="deleteImage({img_data['id']})">×</div>
                    </div>
                    {f'<div class="selected-icon">✓</div>' if is_selected else ''}
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Hidden buttons to handle image selection and deletion
        for img_data in st.session_state.uploaded_images:
            # Select button
            if st.button("Select", key=f"select_btn_{img_data['id']}", help="Hidden button for image selection"):
                if st.session_state.selected_image and st.session_state.selected_image["id"] == img_data["id"]:
                    st.session_state.selected_image = None
                else:
                    st.session_state.selected_image = img_data
                # st.experimental_rerun()
            
            # Delete button
            if st.button("Delete", key=f"delete_btn_{img_data['id']}", help="Hidden button for image deletion"):
                delete_image(img_data["id"])
                # st.experimental_rerun()

    
    # Upload section
    uploaded_file = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
    
    # Process uploaded image
    if uploaded_file:
        image = Image.open(uploaded_file)
        # Create thumbnail and encode
        img_str = encode_image(image)
        # Save to session state
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        img_data = {
            "image": img_str,
            "timestamp": timestamp,
            "id": len(st.session_state.uploaded_images)
        }
        st.session_state.uploaded_images.append(img_data)
        st.session_state.selected_image = img_data
        # st.experimental_rerun()
        st.session_state.selected_image = img_data

    
    # Process camera input
    # Camera functionality removed as requested
    
    # Display selected image
    if st.session_state.selected_image:
        st.markdown('<div class="selected-image-container">', unsafe_allow_html=True)
        st.image(Image.open(io.BytesIO(base64.b64decode(st.session_state.selected_image["image"]))), 
                 width=250)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick actions for selected image
        if st.button("Find this item", key="find_item_btn"):
            prompt = "What is this item and where might it be stored in a home?"
            response = get_ai_response(prompt, st.session_state.selected_image["image"], "find_items")
            
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            # Show response
            st.success("Analysis complete!")
            st.write(response)

# Expiry tab
with tab3:
    st.subheader("Drug & Food Expiry")
    st.write("Track expiry dates of medications and food items.")
    
    # Simple form for adding items with expiry dates
    with st.form("expiry_form"):
        item_name = st.text_input("Item name")
        category = st.selectbox("Category", ["Medication", "Food", "Other"])
        expiry_date = st.date_input("Expiry date")
        quantity = st.number_input("Quantity", min_value=1, value=1)
        
        submit_button = st.form_submit_button("Add Item")
        
        if submit_button:
            st.success(f"Added {item_name} with expiry date {expiry_date}")
    
    # Option to upload an image of the product
    st.write("Or upload an image of the product:")
    expiry_image = st.file_uploader("Upload product image", type=["jpg", "jpeg", "png"], key="expiry_uploader")
    
    if expiry_image:
        image = Image.open(expiry_image)
        st.image(image, width=200)
        
        if st.button("Analyze Expiry Date"):
            st.write("Analyzing expiry date from image...")
            # Here you would integrate with AI to extract expiry information

# Books tab
with tab4:
    st.subheader("Book Management")
    st.write("Manage your books and share with friends.")
    
    # Book management interface
    with st.form("book_form"):
        book_title = st.text_input("Book title")
        book_author = st.text_input("Author")
        book_category = st.selectbox("Category", ["Fiction", "Non-fiction", "Reference", "Textbook", "Other"])
        book_location = st.text_input("Location at home")
        
        submit_button = st.form_submit_button("Add Book")
        
        if submit_button:
            st.success(f"Added {book_title} by {book_author}")
    
    # Option to scan book cover
    st.write("Or scan a book cover:")
    book_image = st.file_uploader("Upload book cover", type=["jpg", "jpeg", "png"], key="book_uploader")
    
    if book_image:
        image = Image.open(book_image)
        st.image(image, width=200)
        
        if st.button("Identify Book"):
            st.write("Identifying book from cover...")
            # Here you would integrate with AI to extract book information

# Clothing tab
with tab5:
    st.subheader("Clothing Tips")
    st.write("Get outfit recommendations based on weather and occasion.")
    
    # Clothing recommendation interface
    col1, col2 = st.columns(2)
    
    with col1:
        occasion = st.selectbox("Occasion", ["Casual", "Work", "Formal", "Sport", "Party"])
    
    with col2:
        weather = st.selectbox("Weather", ["Sunny", "Rainy", "Cold", "Hot", "Windy"])
    
    if st.button("Get Recommendations"):
        prompt = f"Suggest an outfit for a {weather.lower()} day for a {occasion.lower()} occasion."
        response = get_ai_response(prompt, context="clothing_tips")
        
        st.write(response)
    
    # Option to upload clothing item
    st.write("Or upload a clothing item to get styling tips:")
    clothing_image = st.file_uploader("Upload clothing item", type=["jpg", "jpeg", "png"], key="clothing_uploader")
    
    if clothing_image:
        image = Image.open(clothing_image)
        st.image(image, width=200)
        
        if st.button("Get Styling Tips"):
            img_str = encode_image(image)
            prompt = "What is this clothing item and how can I style it for different occasions?"
            response = get_ai_response(prompt, img_str, "clothing_tips")
            
            st.write(response)

# Chat interface at the bottom of all tabs
st.markdown("---")
st.subheader("Chat with Found IT, Mate!")

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
user_input = st.chat_input("Ask about your home items...")

if user_input:
    # Add user message to chat history
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.write(user_input)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if st.session_state.selected_image:
                response = get_ai_response(user_input, st.session_state.selected_image["image"])
            else:
                response = get_ai_response(user_input)
            
            st.write(response)
            
            # Add AI response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

# JavaScript for image selection and deletion
st.markdown("""
<script>
function selectImage(index) {
    // Find the corresponding hidden button and click it
    document.getElementById(`select_btn_${index}`).click();
}

function deleteImage(index) {
    // Find the corresponding hidden button and click it
    document.getElementById(`delete_btn_${index}`).click();
}
</script>
""", unsafe_allow_html=True)

# Add bottom spacer for mobile
st.markdown('<div class="bottom-spacer"></div>', unsafe_allow_html=True)
