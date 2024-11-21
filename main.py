from openai import OpenAI
import tiktoken
import requests
import os
import streamlit as st
import fitz
from dotenv import load_dotenv

load_dotenv()

# Default settings
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
CODING_API_KEY = os.getenv("OPENAI_CODING_API_KEY")
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = "meta-llama/Llama-Vision-Free"
CODING_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOKEN_BUDGET = 4096

# Sidebar Temperature, Max Tokens, and Token Budget
st.sidebar.header("Configuration Settings")
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, 0.05)
max_tokens = st.sidebar.number_input("Max Tokens", min_value=1, max_value=4096, value=DEFAULT_MAX_TOKENS, step=1)
token_budget = st.sidebar.number_input("Token Budget", min_value=1, max_value=4096, value=DEFAULT_TOKEN_BUDGET, step=1)

# Language Selection Dropdown
languages = {"English": "en", "Spanish": "es", "French": "fr", "German": "de", "Japanese": "ja", "Indonesian": "id"}
selected_language = st.sidebar.selectbox("Select Language", options=list(languages.keys()), index=0)

class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None, language="en"):
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
        self.language = language
        self.system_message = f"You are an interviewer, asking insightful questions based on the provided document. Ask the question one at a time as to not overwhelm the user. All responses should be in {self.get_language_name()}."
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    def get_language_name(self):
        """Retrieve the language name from its code."""
        for name, code in languages.items():
            if code == self.language:
                return name
        return "English"

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

        # Add language-specific instruction to the prompt
        prompt += f" Respond in {self.get_language_name()}."

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

### Streamlit Code ###
st.title("AI Interview Chatbot")

# Display EC2 Instance ID
instance_id = get_instance_id()
st.write(f"**EC2 Instance ID**: {instance_id}")

# Initialize the ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager(language=languages[selected_language])

chat_manager = st.session_state['chat_manager']

# Update language setting if changed
if chat_manager.language != languages[selected_language]:
    chat_manager.language = languages[selected_language]
    chat_manager.reset_conversation_history()

# Initialize conversation history in session state
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = chat_manager.conversation_history

# Sidebar for Interview Configuration
st.sidebar.header("Interview Configuration")
interview_type = st.sidebar.selectbox(
    "Interview Type",
    options=["", "Custom", "HR Interview", "Technical Interview", "Practical Coding"],
    index=0
)

if interview_type == "Custom":
    interview_type = st.sidebar.text_input("Enter Interview Type", placeholder="e.g., Coding Test")

job_applied = st.sidebar.text_input("Apply Position", placeholder="e.g., Software Engineer")
job_qualifications = st.sidebar.text_area("Job Qualification", placeholder="Enter qualifications needed for the job (optional)")

# PDF Upload
uploaded_file = st.file_uploader("Upload your CV in PDF format", type="pdf")
if uploaded_file:
    pdf_content = parse_pdf(uploaded_file)
    st.session_state['pdf_loaded'] = True
    st.write("✅ PDF uploaded successfully!")
else:
    st.session_state['pdf_loaded'] = False

# Initialize button state
if 'interview_started' not in st.session_state:
    st.session_state['interview_started'] = False

# Button to Start Interview
if st.button("Start Interview"):
    if not uploaded_file:
        st.warning("⚠️ Please upload your CV.")
    elif not interview_type:
        st.warning("⚠️ Please select or input interview type.")
    elif not job_applied:
        st.warning("⚠️ Please enter position you want to apply.")
    else:
        # Determine model and API key based on the interview type
        if interview_type == "Practical Coding":
            chat_manager.model = CODING_MODEL
            chat_manager.client = OpenAI(api_key=CODING_API_KEY, base_url=DEFAULT_BASE_URL)
            coding_prompt = (
                f"Let's start the Practical Coding interview. "
                f"You are an experienced coding interviewer. Ask the user coding problems based on these information: "
                f"apply position: {job_applied}, job requirements: {job_qualifications}, "
                f"CV content: {pdf_content}. "
                f"Use {selected_language} when asking and ask the questions one by one. "
                f"Do not ask more than 5 questions. At the end, give the user your judgement about their interview performance "
                f"and recommendations for improvement."
            )
            chat_manager.system_message = coding_prompt
        else:
            # Use default settings for other interview types
            chat_manager.model = DEFAULT_MODEL
            chat_manager.client = OpenAI(api_key=DEFAULT_API_KEY, base_url=DEFAULT_BASE_URL)
            general_prompt = (
                f"Let's start the interview. "
                f"Ask questions based on these information: interview type: {interview_type}, "
                f"apply position: {job_applied}, job requirements: {job_qualifications}, "
                f"CV content: {pdf_content}. "
                f"Use {selected_language} when asking and ask the questions one by one. "
                f"Do not ask more than 5 questions. At the end, give the user your judgement about their interview performance "
                f"and recommendations for improvement."
            )
            chat_manager.system_message = general_prompt

        # Reset conversation history with the updated system message
        chat_manager.reset_conversation_history()
        st.session_state['conversation_history'] = chat_manager.conversation_history

        # Start the interview
        st.session_state['interview_started'] = True
        response = chat_manager.chat_completion(chat_manager.system_message)
        st.session_state['conversation_history'] = chat_manager.conversation_history

# Display conversation history only if the interview has started
if st.session_state['interview_started']:
    user_input = st.chat_input("Write a message")
    if user_input:
        response = chat_manager.chat_completion(user_input)
        st.session_state['conversation_history'] = chat_manager.conversation_history

    # Render conversation history (skip the initial user prompt)
    for i, message in enumerate(st.session_state['conversation_history']):
        if message["role"] != "system" and not (
            i == 1 and message["role"] == "user"
        ):  # Skip the first user message (initial prompt)
            with st.chat_message(message["role"]):
                st.write(message["content"])
else:
    st.write("🔒 Chatbot can only be accessed after you start the interview.")
