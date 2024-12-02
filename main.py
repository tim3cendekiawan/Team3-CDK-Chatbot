from openai import OpenAI
import tiktoken
import requests
import os
import streamlit as st
import fitz
from dotenv import load_dotenv

load_dotenv()
from datetime import datetime
import json
import csv
import io
import re

# Initialize conversation history if it doesn't exist
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []

TRANSLATIONS = {
    "English": {
        "system_message": "You are an interviewer, asking insightful questions based on the provided document. Ask the question one at a time as to not overwhelm the user.",
        "interview_type": "Interview Type",
        "job_applied": "Job Position",
        "qualifications": "Required Qualifications",
        "upload_pdf": "Upload a PDF for interview content",
        "start_interview": "Start Interview",
        "chat_placeholder": "Write a message",
        "custom_input": "Enter Interview Type",
        "custom_placeholder": "e.g., Coding Test",
        "selected_type": "Selected Interview Type",
        "job_placeholder": "e.g., Software Engineer",
        "qual_placeholder": "Enter the qualifications required for this position",
        "pdf_loaded": "PDF content loaded. The chatbot is now ready to ask questions based on this document.",
        "lets_start": "Let's start the interview! Interview type: ",
        "instance_id": "EC2 Instance ID",
        "search_options": "Search Options",
        "case_sensitive": "Case Sensitive",
        "match_whole_words": "Match Whole Words",
        "search_in_conversation": "Search in conversation",
        "export_options": "Export Options",
        "choose_export_format": "Choose export format",
        "export_conversation": "Export Conversation",
        "no_conversation": "No conversation to export!",
        "clear_conversation": "Clear Conversation",
        "clear_confirm": "Are you sure you want to clear the conversation?",
        "yes": "Yes",
        "no": "No",
        "save_conversation": "Save Conversation",
        "load_saved": "Load Saved Conversation",
        "load": "Load",
        "generate_summary": "Generate Conversation Summary",
        "conversation_summary": "Conversation Summary",
        "no_summary": "No conversation to summarize yet!",
        "response_settings": "Response Settings",
        "word_limit": "User's Message Word Limit",
        "word_limit_help": "Adjust the maximum number of words in the user's input",
        "input_exceeds": "⚠️ Input exceeds word limit!"
    },
    "Bahasa Indonesia": {
        "system_message": "Anda adalah pewawancara, mengajukan pertanyaan berdasarkan dokumen yang diberikan. Tanyakan pertanyaan satu per satu agar tidak membebani pengguna.",
        "interview_type": "Jenis Interview",
        "job_applied": "Posisi Pekerjaan", 
        "qualifications": "Kualifikasi yang Dibutuhkan",
        "upload_pdf": "Unggah PDF untuk konten interview",
        "start_interview": "Mulai Interview",
        "chat_placeholder": "Tulis pesan",
        "custom_input": "Masukkan Jenis Interview",
        "custom_placeholder": "Misalnya: Coding Test", 
        "selected_type": "Jenis Interview yang Dipilih",
        "job_placeholder": "Misalnya: Software Engineer",
        "qual_placeholder": "Tuliskan kualifikasi yang diperlukan untuk posisi ini",
        "pdf_loaded": "Konten PDF dimuat. Chatbot siap mengajukan pertanyaan berdasarkan dokumen ini.",
        "lets_start": "Ayo kita mulai interviewnya! Jenis interview: ",
        "instance_id": "ID Instance EC2",
        "search_options": "Opsi Pencarian",
        "case_sensitive": "Sesuai Huruf Besar/Kecil", 
        "match_whole_words": "Cocokkan Kata Lengkap",
        "search_in_conversation": "Cari dalam percakapan",
        "export_options": "Opsi Ekspor",
        "choose_export_format": "Pilih format ekspor",
        "export_conversation": "Ekspor Percakapan", 
        "no_conversation": "Belum ada percakapan untuk diekspor!",
        "clear_conversation": "Hapus Percakapan",
        "clear_confirm": "Apakah Anda yakin ingin menghapus percakapan?",
        "yes": "Ya",
        "no": "Tidak",
        "save_conversation": "Simpan Percakapan",
        "load_saved": "Muat Percakapan Tersimpan",
        "load": "Muat",
        "generate_summary": "Buat Ringkasan Percakapan",
        "conversation_summary": "Ringkasan Percakapan",
        "no_summary": "Belum ada percakapan untuk diringkas!",
        "response_settings": "Pengaturan Respons",
        "word_limit": "Batas Kata Respons",
        "word_limit_help": "Sesuaikan jumlah maksimum kata dalam respons AI",
        "input_exceeds": "⚠️ Input melebihi batas kata!"
    },
    "French": {
        "system_message": "Vous êtes un intervieweur, posant des questions pertinentes basées sur le document fourni. Posez les questions une à la fois pour ne pas submerger l'utilisateur.",
        "interview_type": "Type d'entretien",
        "job_applied": "Poste",
        "qualifications": "Qualifications requises",
        "upload_pdf": "Télécharger un PDF pour le contenu de l'entretien",
        "start_interview": "Commencer l'entretien",
        "chat_placeholder": "Écrire un message",
        "custom_input": "Entrer le type d'entretien",
        "custom_placeholder": "ex: Test de codage",
        "selected_type": "Type d'entretien sélectionné",
        "job_placeholder": "ex: Ingénieur logiciel",
        "qual_placeholder": "Entrez les qualifications requises pour ce poste",
        "pdf_loaded": "Contenu PDF chargé. Le chatbot est maintenant prêt à poser des questions basées sur ce document.",
        "lets_start": "Commençons l'entretien! Type d'entretien: ",
        "instance_id": "ID d'instance EC2",
        "search_options": "Options de recherche",
        "case_sensitive": "Sensible à la casse",
        "match_whole_words": "Correspondance mot entier",
        "search_in_conversation": "Rechercher dans la conversation",
        "export_options": "Options d'exportation",
        "choose_export_format": "Choisir le format d'exportation",
        "export_conversation": "Exporter la conversation",
        "no_conversation": "Pas de conversation à exporter!",
        "clear_conversation": "Effacer la conversation",
        "clear_confirm": "Êtes-vous sûr de vouloir effacer la conversation?",
        "yes": "Oui",
        "no": "Non", 
        "save_conversation": "Sauvegarder la conversation",
        "load_saved": "Charger une conversation sauvegardée",
        "load": "Charger",
        "generate_summary": "Générer un résumé de la conversation",
        "conversation_summary": "Résumé de la conversation",
        "no_summary": "Pas encore de conversation à résumer!",
        "response_settings": "Paramètres de réponse",
        "word_limit": "Limite de mots pour la réponse",
        "word_limit_help": "Ajuster le nombre maximum de mots dans les réponses de l'IA",
        "input_exceeds": "⚠️ La saisie dépasse la limite de mots!"
    },
    "Spanish": {
        "system_message": "Eres un entrevistador, haciendo preguntas perspicaces basadas en el documento proporcionado. Haz las preguntas una a la vez para no abrumar al usuario.",
        "interview_type": "Tipo de entrevista",
        "job_applied": "Puesto de trabajo",
        "qualifications": "Cualificaciones requeridas",
        "upload_pdf": "Subir un PDF para el contenido de la entrevista",
        "start_interview": "Comenzar entrevista",
        "chat_placeholder": "Escribir un mensaje",
        "custom_input": "Introducir tipo de entrevista",
        "custom_placeholder": "ej: Prueba de código",
        "selected_type": "Tipo de entrevista seleccionado",
        "job_placeholder": "ej: Ingeniero de software",
        "qual_placeholder": "Introduce las cualificaciones requeridas para este puesto",
        "pdf_loaded": "Contenido PDF cargado. El chatbot está ahora listo para hacer preguntas basadas en este documento.",
        "lets_start": "¡Comencemos la entrevista! Tipo de entrevista: ",
        "instance_id": "ID de instancia EC2",
        "search_options": "Opciones de búsqueda",
        "case_sensitive": "Distinguir mayúsculas y minúsculas",
        "match_whole_words": "Coincidir palabras completas",
        "search_in_conversation": "Buscar en la conversación",
        "export_options": "Opciones de exportación",
        "choose_export_format": "Elegir formato de exportación",
        "export_conversation": "Exportar conversación",
        "no_conversation": "¡No hay conversación para exportar!",
        "clear_conversation": "Borrar conversación",
        "clear_confirm": "¿Estás seguro de que quieres borrar la conversación?",
        "yes": "Sí",
        "no": "No",
        "save_conversation": "Guardar conversación",
        "load_saved": "Cargar conversación guardada",
        "load": "Cargar",
        "generate_summary": "Generar resumen de la conversación",
        "conversation_summary": "Resumen de la conversación",
        "no_summary": "¡Aún no hay conversación para resumir!",
        "response_settings": "Configuración de respuesta",
        "word_limit": "Límite de palabras de respuesta",
        "word_limit_help": "Ajustar el número máximo de palabras en las respuestas de la IA",
        "input_exceeds": "⚠️ ¡La entrada excede el límite de palabras!"
    },
    "Dutch": {
        "system_message": "U bent een interviewer die inzichtelijke vragen stelt op basis van het verstrekte document. Stel de vragen één voor één om de gebruiker niet te overweldigen.",
        "interview_type": "Type interview",
        "job_applied": "Functie",
        "qualifications": "Vereiste kwalificaties",
        "upload_pdf": "Upload een PDF voor interview inhoud",
        "start_interview": "Start interview",
        "chat_placeholder": "Schrijf een bericht",
        "custom_input": "Voer type interview in",
        "custom_placeholder": "bijv: Coding Test",
        "selected_type": "Geselecteerd type interview",
        "job_placeholder": "bijv: Software Engineer",
        "qual_placeholder": "Voer de vereiste kwalificaties in voor deze functie",
        "pdf_loaded": "PDF-inhoud geladen. De chatbot is nu klaar om vragen te stellen op basis van dit document.",
        "lets_start": "Laten we het interview beginnen! Type interview: ",
        "instance_id": "EC2 Instance ID",
        "search_options": "Zoekopties",
        "case_sensitive": "Hoofdlettergevoelig",
        "match_whole_words": "Hele woorden matchen",
        "search_in_conversation": "Zoeken in gesprek",
        "export_options": "Exportopties",
        "choose_export_format": "Kies exportformaat",
        "export_conversation": "Gesprek exporteren",
        "no_conversation": "Geen gesprek om te exporteren!",
        "clear_conversation": "Gesprek wissen",
        "clear_confirm": "Weet je zeker dat je het gesprek wilt wissen?",
        "yes": "Ja",
        "no": "Nee",
        "save_conversation": "Gesprek opslaan",
        "load_saved": "Opgeslagen gesprek laden",
        "load": "Laden",
        "generate_summary": "Gespreksamenvatting genereren",
        "conversation_summary": "Gespreksamenvatting",
        "no_summary": "Nog geen gesprek om samen te vatten!",
        "response_settings": "Antwoordinstellingen",
        "word_limit": "Woordlimiet antwoord",
        "word_limit_help": "Pas het maximale aantal woorden in AI-antwoorden aan",
        "input_exceeds": "⚠️ Invoer overschrijdt woordlimiet!"
    },
    "Chinese": {
        "system_message": "您是一位面试官，根据提供的文档提出富有洞察力的问题。一次只问一个问题，以免让用户应接不暇。",
        "interview_type": "面试类型",
        "job_applied": "应聘职位",
        "qualifications": "所需资格",
        "upload_pdf": "上传PDF面试内容",
        "start_interview": "开始面试",
        "chat_placeholder": "输入消息",
        "custom_input": "输入面试类型",
        "custom_placeholder": "例如：编程测试",
        "selected_type": "已选择的面试类型",
        "job_placeholder": "例如：软件工程师",
        "qual_placeholder": "输入此职位所需的资格条件",
        "pdf_loaded": "PDF内容已加载。聊天机器人现在准备根据此文档提问。",
        "lets_start": "让我们开始面试！面试类型：",
        "instance_id": "EC2实例ID",
        "search_options": "搜索选项",
        "case_sensitive": "区分大小写",
        "match_whole_words": "匹配整词",
        "search_in_conversation": "在对话中搜索",
        "export_options": "导出选项",
        "choose_export_format": "选择导出格式",
        "export_conversation": "导出对话",
        "no_conversation": "没有对话可导出！",
        "clear_conversation": "清除对话",
        "clear_confirm": "您确定要清除对话吗？",
        "yes": "是",
        "no": "否",
        "save_conversation": "保存对话",
        "load_saved": "加载已保存的对话",
        "load": "加载",
        "generate_summary": "生成对话摘要",
        "conversation_summary": "对话摘要",
        "no_summary": "还没有对话可以总结！",
        "response_settings": "回复设置",
        "word_limit": "回复字数限制",
        "word_limit_help": "调整AI回复的最大字数",
        "input_exceeds": "⚠️ 输入超过字数限制！"
    }
}

# word counter
def count_words(text):
    """Count the number of words in a text string"""
    return len(text.split())


# Default settings
DEFAULT_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_BASE_URL = "https://api.together.xyz/v1"
DEFAULT_MODEL = "meta-llama/Llama-Vision-Free"
CODING_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 512
DEFAULT_TOKEN_BUDGET = 4096
DEFAULT_WORD_LIMIT = 150


class ConversationManager:
    def __init__(self, api_key=None, base_url=None, model=None, temperature=None, max_tokens=None, token_budget=None, word_limit=None):
        if not api_key:
            api_key = DEFAULT_API_KEY
        if not base_url:
            base_url = DEFAULT_BASE_URL
            
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model if model else DEFAULT_MODEL
        self.temperature = temperature if temperature else DEFAULT_TEMPERATURE
        self.max_tokens = max_tokens if max_tokens else DEFAULT_MAX_TOKENS
        self.token_budget = token_budget if token_budget else DEFAULT_TOKEN_BUDGET
        self.word_limit = word_limit if word_limit else DEFAULT_WORD_LIMIT  # Add this line
        self.system_message = f"You are an interviewer, asking insightful questions based on the provided document. Ask the question one at a time as to not overwhelm the user."
        self.conversation_history = [{"role": "system", "content": self.system_message}]

    def update_word_limit(self, new_limit):
        """Update the word limit for responses"""
        self.word_limit = new_limit

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
        """Generate a chat completion with word limit consideration"""
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
            ai_response = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_response})
            return ai_response
        except Exception as e:
            print(f"Error generating response: {e}")
            return None
    
    def reset_conversation_history(self):
        self.conversation_history = [{"role": "system", "content": self.system_message}]
    
    def update_system_message(self, system_message):
        try:
            if self.conversation_history[0]["role"] == "system":
                self.conversation_history[0]["content"] = system_message
            else:
                self.conversation_history.insert(0, {
                    "role": "system",
                    "content": system_message
                })
        except IndexError:
            # If conversation history is empty
            self.conversation_history.append({
                "role": "system",
                "content": system_message
            })

    
    def reset_conversation(self):
        self.conversation_history = []

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

# Filter actual messages
def filter_messages(messages):
    actual_messages = [
        msg for msg in messages
        if msg["role"] in ["user", "assistant"] 
        and not any(skip_text in msg["content"].lower() for skip_text in [
            "interview_type",
            "job_applied",
            "pdf content",
            "qualifications"
        ])
    ]
    return actual_messages

actual_messages = filter_messages(st.session_state['conversation_history'])

# Add language selector in the sidebar (place this at the top of the sidebar)
if 'language' not in st.session_state:
    st.session_state['language'] = 'English'

language = st.sidebar.selectbox(
    "Select Language / Pilih Bahasa / 选择语言",
    options=list(TRANSLATIONS.keys()),
    index=list(TRANSLATIONS.keys()).index(st.session_state['language']),
    key='language'
)

# Get current language translations
trans = TRANSLATIONS[language]

# Update the interview type selection
interview_type = st.sidebar.selectbox(
    trans["interview_type"],
    options=["Custom", "HR Interview", "Technical Interview", "Technical Skill"],
    index=0
)

# If the interview type is "Custom", allow the user to input their own type
if interview_type == "Custom":
    interview_type = st.sidebar.text_input(
        trans["custom_input"],
        placeholder=trans["custom_placeholder"]
    )

# Display the selected interview type
st.sidebar.write(f"{trans['selected_type']}: {interview_type}")

# Job yang dilamar
job_applied = st.sidebar.text_input(
    trans["job_applied"],
    placeholder=trans["job_placeholder"]
)

# Deskripsi kualifikasi yang dibutuhkan
job_qualifications = st.sidebar.text_area(
    trans["qualifications"],
    placeholder=trans["qual_placeholder"]
)

# Add word limit slider in sidebar
st.sidebar.markdown(f"### {trans['response_settings']}")
word_limit = st.sidebar.slider(
    trans["word_limit"],
    min_value=50,
    max_value=500,
    value=DEFAULT_WORD_LIMIT,
    step=50,
    help=trans["word_limit_help"]
)

# Add a container for word count warning in sidebar
word_count_container = st.sidebar.container()



# Initialize the ConversationManager object
if 'chat_manager' not in st.session_state:
    st.session_state['chat_manager'] = ConversationManager(word_limit=word_limit)
else:
    st.session_state['chat_manager'].update_word_limit(word_limit)

chat_manager = st.session_state['chat_manager']
chat_manager.update_system_message(trans["system_message"])

# Initialize conversation history in session state
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = chat_manager.conversation_history

# Conversation export feature
st.sidebar.markdown(f"### {trans['export_options']}")

# Export format selector
export_format = st.sidebar.selectbox(
    trans["choose_export_format"],
    ["TXT", "CSV", "JSON"]
)

def create_export_content():
    if 'conversation_history' not in st.session_state:
        return None
    
    # For TXT format
    if export_format == "TXT":
        content = "Chat History\n"
        content += f"Export Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 50 + "\n\n"
        
        for msg in actual_messages:
            content += f"{msg['role'].upper()}: {msg['content']}\n\n"
        
        return content
        
    # For CSV format
    elif export_format == "CSV":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Role", "Content", "Timestamp"])
        
        for msg in actual_messages:
            writer.writerow([
                msg["role"],
                msg["content"],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
                
        return output.getvalue()
        
    # For JSON format
    elif export_format == "JSON":
        chat_data = []
        for msg in actual_messages:
            chat_data.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        return json.dumps(chat_data, indent=2)

    return None

# Export button
if st.sidebar.button(trans["export_conversation"]):
    if 'conversation_history' in st.session_state and len(st.session_state['conversation_history']) > 1:
        export_content = create_export_content()
        
        if export_content:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create download button based on format
            if export_format == "TXT":
                st.sidebar.download_button(
                    label="Download TXT",
                    data=export_content,
                    file_name=f"chat_history_{timestamp}.txt",
                    mime="text/plain"
                )
            elif export_format == "CSV":
                st.sidebar.download_button(
                    label="Download CSV",
                    data=export_content,
                    file_name=f"chat_history_{timestamp}.csv",
                    mime="text/csv"
                )
            elif export_format == "JSON":
                st.sidebar.download_button(
                    label="Download JSON",
                    data=export_content,
                    file_name=f"chat_history_{timestamp}.json",
                    mime="application/json"
                )
    else:
        st.sidebar.warning(trans["no_conversation"])

# Session management with confirmation
if 'confirm_clear' not in st.session_state:
    st.session_state.confirm_clear = False

if st.sidebar.button(trans["clear_conversation"]):
    st.session_state.confirm_clear = True

if st.session_state.confirm_clear:
    st.sidebar.warning(trans["clear_confirm"])
    col1, col2 = st.sidebar.columns([0.02, 0.06])  # Smaller columns and narrow gap

    with col1:
        if st.button("Yes"):
            st.session_state['conversation_history'] = []
            chat_manager.reset_conversation()
            st.session_state.confirm_clear = False
            st.rerun()

    with col2:
        if st.button("No"):
            st.session_state.confirm_clear = False
            st.rerun()



# Save conversation with dynamic naming
if st.sidebar.button(trans["save_conversation"]):
    if "conversation_history" in st.session_state and st.session_state["conversation_history"]:
        # Generate the name dynamically
        interview_type = st.session_state.get("interview_type", "UnknownType")
        job_applied = st.session_state.get("job_applied", "UnknownPosition")
        save_name = f"{interview_type}-{job_applied}".replace(" ", "_")

        # Ensure uniqueness by adding a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_key = f"saved_conversation_{save_name}_{timestamp}"

        # Save conversation in session state
        st.session_state[unique_key] = st.session_state["conversation_history"].copy()
        st.success(f"Conversation saved as: {save_name}")
    else:
        st.warning("No conversation available to save!")


# Display and load saved conversations
saved_conversations = [key for key in st.session_state.keys() 
                      if key.startswith('saved_conversation_')]
if saved_conversations:
    selected_conversation = st.sidebar.selectbox(
        trans["load_saved"],
        saved_conversations
    )
    if st.sidebar.button(trans["load"]):
        st.session_state['conversation_history'] = \
            st.session_state[selected_conversation].copy()
        st.rerun()  # Using st.rerun() instead of st.experimental_rerun()


# Initialize button state
if 'interview_started' not in st.session_state:
    st.session_state['interview_started'] = False


# Tabs for different sections
tabs = st.tabs(["Chatbot", "Summary"])

# Chatbot tab: Contains the chatbot UI
with tabs[0]:
    ### Streamlit code ###
    st.title("HireHelp")

    # Display EC2 Instance ID
    instance_id = get_instance_id()
    st.write(f"**{trans['instance_id']}**: {instance_id}")

    # PDF Upload
    uploaded_file = st.file_uploader("Upload your CV in PDF format", type="pdf")
    if uploaded_file:
        pdf_content = parse_pdf(uploaded_file)
        st.session_state['pdf_loaded'] = True
        st.write("✅ PDF uploaded successfully!")
    else:
        st.session_state['pdf_loaded'] = False

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
            if "coding" in interview_type.lower() or interview_type == "Technical Skill":
                chat_manager.model = CODING_MODEL
                chat_manager.client = OpenAI(api_key=DEFAULT_API_KEY, base_url=DEFAULT_BASE_URL)
                chat_manager.max_tokens=1024
                chat_manager.token_budget=8192
                coding_prompt = (
                    f"Let's start the Practical Coding interview. Ask question one by one. "
                    f"You are an experienced coding interviewer. You can generate a code relevant to these information and ask the user the output "
                    f"Or you can ask the user to make a code for task relevant to these information: "
                    f"apply position: {job_applied}, job requirements: {job_qualifications}, "
                    f"CV content: {pdf_content}. "
                    f"Use {language} when asking and ask the questions one by one, don't ask all 5 questions at once. "
                    f"Do not ask more than 5 questions. At the end, give the user your judgement about their interview performance "
                    f"and recommendations for improvement. Also, give a score in the scale of 1 to 10. Also, you don't have to explain the answer, just focus on asking. "
                )
                chat_manager.system_message = coding_prompt
            else:
                # Use default settings for other interview types
                chat_manager.model = DEFAULT_MODEL
                chat_manager.client = OpenAI(api_key=DEFAULT_API_KEY, base_url=DEFAULT_BASE_URL)
                general_prompt = (
                    f"Let's start the interview. Ask question one by one. "
                    f"Ask questions based on these information: interview type: {interview_type}, "
                    f"apply position: {job_applied}, job requirements: {job_qualifications}, "
                    f"CV content: {pdf_content}. "
                    f"Use {language} when asking and ask the questions one by one, don't ask all 5 questions at once. "
                    f"Do not ask more than 5 questions. At the end, give the user your judgement about their interview performance "
                    f"and recommendations for improvement. Also, give a score in the scale of 1 to 10. "
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
        # Chat input with word limit check
        # Chat history container
        chat_history_container = st.container()

        # User input container
        user_input_container = st.container()

        with chat_history_container:
            # Render conversation history (skip the initial user prompt)
            for i, message in enumerate(st.session_state['conversation_history']):
                if message["role"] != "system" and not (
                    i == 1 and message["role"] == "user"
                ):  # Skip the first user message (initial prompt)
                    with st.chat_message(message["role"]):
                        st.write(message["content"])

        with user_input_container:
            # Chat input with word limit check
            if user_input := st.chat_input(trans["chat_placeholder"], key="main_chat_input"):
                word_count = count_words(user_input)

                # Check if input exceeds word limit
                if word_count > word_limit:
                    st.warning(f"{trans['input_exceeds']} ({word_count}/{word_limit} words)")
                else:
                    # Add language instruction before each interaction if not already added
                    if not any(
                        msg["role"] == "system" and "Please respond in" in msg["content"]
                        for msg in st.session_state['conversation_history']
                    ):
                        st.session_state['conversation_history'].append({
                            "role": "system",
                            "content": f"Please respond in {language}."
                        })

                    # Generate and update AI response
                    response = chat_manager.chat_completion(user_input)
                    st.session_state['conversation_history'] = chat_manager.conversation_history
                    st.rerun()
    else:
        st.write("🔒 Chatbot can only be accessed after you start the interview.")
    

# Summary tab: Contains the conversation summary
with tabs[1]:
    st.header(trans["conversation_summary"])
    
    # Button to generate the summary
    if st.button(trans["generate_summary"]):
        if actual_messages:  # Check if there is a conversation to summarize
            conversation_text = "\n".join(
                [f"{msg['role'].upper()}: {msg['content']}" for msg in actual_messages]
            )
            try:
                summary_response = chat_manager.client.chat.completions.create(
                    model=chat_manager.model,
                    messages=[{
                        "role": "system",
                        "content": "You are a helpful assistant. Please provide a concise summary of the following conversation."
                    },
                    {
                        "role": "user",
                        "content": f"Please summarize this conversation:\n{conversation_text}. Please respond in {language}."
                    }],
                    temperature=0.7,
                    max_tokens=250
                )
                st.markdown(summary_response.choices[0].message.content)
            except Exception as e:
                st.warning("⚠️ Failed to generate summary. Please try again.")
        else:
            st.warning("⚠️ No conversation to summarize yet!")
