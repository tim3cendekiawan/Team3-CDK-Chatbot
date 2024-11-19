from openai import OpenAI
import tiktoken
import requests
import os
import streamlit as st
import fitz  # PyMuPDF for PDF handling

# Default settings
DEFAULT_API_KEY = "your api key"
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = "meta-llama/Llama-Vision-Free"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOKEN_BUDGET = 4096

# Sidebar Temperature, Max Tokens, and Token Budget
st.sidebar.header("Configuration Settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, 0.05)
max_tokens = st.sidebar.number_input("Max Tokens", min_value=1, max_value=4096, value=DEFAULT_MAX_TOKENS, step=1)
token_budget = st.sidebar.number_input("Token Budget", min_value=1, max_value=4096, value=DEFAULT_TOKEN_BUDGET, step=1)

class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None):
        # Initialization
        if not api_key:
            api_key = DEFAULT_API_KEY
        if not base_url:
            base_url = DEFAULT_BASE_URL
            
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model if model else DEFAULT_MODEL
        self.temperature = temperature if temperature else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens else DEFAULT_MAX_TOKENS
        self.token_budget = token_budget if token_budget else DEFAULT_TOKEN_BUDGET
        self.system_message = "You are an interviewer, asking insightful questions based on the provided document. Ask the question one at a time as to not overwhelm the user."
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    def count_tokens(self, text):
        try:
            encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
        tokens = encoding.encode(text)
        return len(tokens)

    def total_tokens_used(self):
        try:
            return sum(self.count_tokens(message['content']) for message in self.conversation_history)
        except Exception as e:
            print(f"Error calculating total tokens used: {e}")
            return None
    
    def enforce_token_budget(self):
        try:
            while self.total_tokens_used() > self.token_budget:
                if len(self.conversation_history) <= 1:
                    break
                self.conversation_history.pop(1)
        except Exception as e:
            print(f"Error enforcing token budget: {e}")

    def chat_completion(self, prompt, temperature=None, max_tokens=None, model=None):
        temperature = temperature if temperature is not None else self.temperature
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        model = model if model is not None else self.model

        self.conversation_history.append({"role": "user", "content": prompt})
        self.enforce_token_budget()

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=self.conversation_history,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except Exception as e:
            print(f"Error generating response: {e}")
            return None

        ai_response = response.choices[0].message.content
        self.conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response
    
    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]

def get_instance_id():
    """Retrieve the EC2 instance ID from AWS metadata using IMDSv2."""
    try:
        # Step 1: Get the token
        token = requests.put(
            "http://169.254.169.254/latest/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=1
        ).text

        # Step 2: Use the token to get the instance ID
        instance_id = requests.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            headers={"X-aws-ec2-metadata-token": token},
            timeout=1
        ).text
        return instance_id
    except requests.exceptions.RequestException:
        return "Instance ID not available (running locally or error in retrieval)"
    
# PDF Parsing Function
def parse_pdf(file):
    """Extract text from a PDF file using PyMuPDF."""
    content = ""
    with fitz.open(stream=file.read(), filetype="pdf") as pdf:
        for page_num in range(len(pdf)):
            content += pdf[page_num].get_text("text")
    return content

### Streamlit code ###
st.title("AI Interview Chatbot")

# Display EC2 Instance ID
instance_id = get_instance_id()
st.write(f"**EC2 Instance ID**: {instance_id}")

# Initialize the ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager()

chat_manager = st.session_state['chat_manager']

# Initialize conversation history in session state
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = chat_manager.conversation_history

# st.sidebar.title("Interview Details")
# Update the sidebar with a dropdown for interview type
interview_type = st.sidebar.selectbox(
    "Jenis Interview", 
    options=["Custom", "HR Interview", "Technical Interview", "Technical Skill"],
    index=0  # Default to "Custom"
)

# If the interview type is "Custom", allow the user to input their own type
if interview_type == "Custom":
    interview_type = st.sidebar.text_input("Masukkan Jenis Interview", placeholder="Misalnya: Coding Test")

# Display the selected interview type
st.sidebar.write(f"Selected Interview Type: {interview_type}")

# # Jenis interview
# interview_type = st.sidebar.text_input("Jenis Interview", placeholder="e.g., Technical Interview, HR Interview")

# Job yang dilamar
job_applied = st.sidebar.text_input("Job yang Dilamar", placeholder="e.g., Software Engineer")

# Deskripsi kualifikasi yang dibutuhkan
job_qualifications = st.sidebar.text_area("Deskripsi Kualifikasi", placeholder="Tuliskan kualifikasi yang diperlukan untuk posisi ini")

# PDF Upload
uploaded_file = st.file_uploader("Upload a PDF for interview content", type="pdf")
if uploaded_file:
    pdf_content = parse_pdf(uploaded_file)
    # Add PDF content to conversation history without displaying it
    chat_manager.conversation_history.append({
        "role": "user", "content": f"The interview type is '{interview_type}', for the job position '{job_applied}', "
                   f"with the required qualifications as follows: {job_qualifications}. "
                  f"and additional content from the PDF: {pdf_content}"
    })
    st.write("PDF content loaded. The chatbot is now ready to ask questions based on this document.")

# Chat input
user_input = st.chat_input("Write a message")

if user_input:
    response = chat_manager.chat_completion(user_input)
    st.session_state['conversation_history'] = chat_manager.conversation_history
# if st.button("Mulai Interview"):
#     # Send the prompt to the chatbot to start the interview
#     prompt = "Ayo kita mulai interviewnya"
#     response = chat_manager.chat_completion(prompt)
#     st.session_state['conversation_history'] = chat_manager.conversation_history
if st.button("Mulai Interview"):
    # Send the prompt to the chatbot to start the interview
    prompt = f"Ayo kita mulai interviewnya! Jenis interview: {interview_type}"
    response = chat_manager.chat_completion(prompt)
    st.session_state['conversation_history'] = chat_manager.conversation_history

# Display conversation history, excluding the system message
# for message in st.session_state['conversation_history']:
#     if message["role"] != "system" and not message["content"]:
#         with st.chat_message(message["role"]):
#             st.write(message["content"])

for message in st.session_state['conversation_history']:
    # Menyembunyikan pesan konteks awal
    if message["role"] != "system" and "The interview type is" not in message["content"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
