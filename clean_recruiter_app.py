import streamlit as st
import time
import random
import io
import PyPDF2 
import pandas as pd 

# --- 1. CORE CHATBOT LOGIC CLASS ---

class RecruiterBot:
    def __init__(self, master_data, candidate_tier, time_limit_minutes=20):
        self.master_questions = master_data
        self.time_limit = time_limit_minutes * 60
        self.start_time = time.time()
        self.current_q_index = 0
        self.score = {'generic': 0, 'technical': 0, 'total': 0}
        self.recorded_answers = []
        self.candidate_tier = candidate_tier
        
        # Dynamically select 10 questions based on the tier
        self.questions = self._select_questions() 
        self.total_questions = len(self.questions)

    def _select_questions(self):
        """Dynamically selects 10 questions (5 Base + 5 Technical) based on the candidate's tier."""
        
        base_qs = [q for q in self.master_questions if q['difficulty'] == 'BASE']
        basic_qs = [q for q in self.master_questions if q['difficulty'] == 'BASIC']
        intermediate_qs = [q for q in self.master_questions if q['difficulty'] == 'INTERMEDIATE']
        advanced_qs = [q for q in self.master_questions if q['difficulty'] == 'ADVANCED']

        selected_questions = random.sample(base_qs, 5)

        if self.candidate_tier == 'Junior':
            tech_selection = random.sample(basic_qs, 5)
        elif self.candidate_tier == 'Mid-Level':
            tech_selection = random.sample(intermediate_qs, 3) + random.sample(basic_qs, 2)
        elif self.candidate_tier == 'Senior':
            tech_selection = random.sample(advanced_qs, 3) + random.sample(intermediate_qs, 2)
        else:
            tech_selection = random.sample(basic_qs, 5)

        selected_questions.extend(tech_selection)
        random.shuffle(selected_questions)
        return selected_questions

    def _check_time(self):
        """Checks if the 20-minute limit has been reached."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.time_limit:
            return False
        return True

    def _process_answer(self, q_data, response):
        """Processes the answer for scoring and prepares the detailed analysis record."""
        response_lower = response.lower()
        score_gain = 0
        analysis_detail = ""
        
        # --- Rule-Based Scoring Logic ---
        if q_data['type'] == 'T': 
            keywords = q_data.get('keywords', [])
            is_correct = all(keyword in response_lower for keyword in keywords)
            
            if is_correct:
                score_gain = 1
                analysis_detail = "✅ **Full Credit.** Correctly identified all key concepts."
            elif any(keyword in response_lower for keyword in keywords):
                score_gain = 0.5
                analysis_detail = "💡 **Partial Credit.** Identified some key concepts but lacked complete detail."
            else:
                score_gain = 0
                analysis_detail = "❌ **No Credit.** Did not address the core technical concept required."
        
        elif q_data['type'] == 'G': 
            if len(response) > 30:
                score_gain = 1
                analysis_detail = "⭐ **Full Credit.** Provided a thoughtful and substantial response."
            else:
                score_gain = 0.5
                analysis_detail = "🟡 **Partial Credit.** Response was too brief or lacked depth."
        
        if q_data['type'] == 'G':
            self.score['generic'] += score_gain
        else:
            self.score['technical'] += score_gain
            
        self.score['total'] = self.score['generic'] + self.score['technical']
        
        self.recorded_answers.append({
            'Q': q_data['Q'],
            'User_Response': response,
            'Model_Answer': q_data['Model_Answer'],
            'Score_Earned': score_gain,
            'Analysis': analysis_detail
        })
        return None

# --- 2. MASTER QUESTION ROSTER (20 Questions) ---

MASTER_QUESTION_ROSTER = [
    # 5 GENERIC QUESTIONS (Difficulty: BASE)
    {'id': 'G1', 'type': 'G', 'difficulty': 'BASE', 'Q': "1/20 (Generic): What excites you most about this role, and what Python projects have you enjoyed working on recently?", 'keywords': ['project', 'library', 'framework'], 'Model_Answer': "Focus on enthusiasm and technical specificity."},
    {'id': 'G2', 'type': 'G', 'difficulty': 'BASE', 'Q': "2/20 (Generic): Describe a situation where you encountered a major coding bug in a project. How did you debug it?", 'keywords': ['debugger', 'logging', 'isolation'], 'Model_Answer': "Focus on systematic process, isolation, and use of debugging tools."},
    {'id': 'G3', 'type': 'G', 'difficulty': 'BASE', 'Q': "3/20 (Generic): How do you prioritize learning a new Python library or framework on a tight deadline?", 'keywords': ['documentation', 'examples'], 'Model_Answer': "Focus on efficiency: quickstart guides and minimal working examples."},
    {'id': 'G4', 'type': 'G', 'difficulty': 'BASE', 'Q': "4/20 (Generic): What do you consider your greatest weakness in a technical team environment?", 'keywords': ['mitigation', 'action', 'plan'], 'Model_Answer': "Focus on self-awareness and describing concrete action taken to mitigate the weakness."},
    {'id': 'G5', 'type': 'G', 'difficulty': 'BASE', 'Q': "5/20 (Generic): If you could only use one built-in Python data type for the rest of your career, which would it be and why?", 'keywords': ['versatility', 'key-value'], 'Model_Answer': "Focus on versatility, choosing Dictionary or List and justifying its wide application."},
    
    # 5 BASIC TECHNICAL QUESTIONS (Difficulty: BASIC)
    {'id': 'T1', 'type': 'T', 'difficulty': 'BASIC', 'Q': "6/20 (Basic): What is the difference between a list and a tuple in Python?", 'keywords': ['mutable', 'immutable'], 'Model_Answer': "List is mutable, tuple is immutable."},
    {'id': 'T2', 'type': 'T', 'difficulty': 'BASIC', 'Q': "7/20 (Basic): How would you reverse the string 'Python' using a single line of code?", 'keywords': ['[::-1]'], 'Model_Answer': "Using slicing: `s[::-1]`."},
    {'id': 'T3', 'type': 'T', 'difficulty': 'BASIC', 'Q': "8/20 (Basic): Write a simple `for` loop that prints all numbers from 0 up to, but not including, 5.", 'keywords': ['range(5)', 'print', 'for'], 'Model_Answer': "Code: `for i in range(5): print(i)`."},
    {'id': 'T4', 'type': 'T', 'difficulty': 'BASIC', 'Q': "9/20 (Basic): What is a dictionary used for, and how is it structured?", 'keywords': ['key', 'value', 'pair'], 'Model_Answer': "Stores data in key-value pairs."},
    {'id': 'T5', 'type': 'T', 'difficulty': 'BASIC', 'Q': "10/20 (Basic): Write a simple function named `add_two` that takes one argument, `x`, and returns `x + 2`.", 'keywords': ['def', 'return', 'x + 2'], 'Model_Answer': "Code: `def add_two(x): return x + 2`."},

    # 5 INTERMEDIATE TECHNICAL QUESTIONS (Difficulty: INTERMEDIATE)
    {'id': 'T6', 'type': 'T', 'difficulty': 'INTERMEDIATE', 'Q': "11/20 (Intermediate): Explain the purpose of `__init__` in Python classes.", 'keywords': ['constructor', 'initialize', 'self'], 'Model_Answer': "A constructor method called when a new instance is created to initialize attributes."},
    {'id': 'T7', 'type': 'T', 'difficulty': 'INTERMEDIATE', 'Q': "12/20 (Intermediate): What is the Global Interpreter Lock (GIL) and how does it affect multi-threading?", 'keywords': ['GIL', 'thread', 'multiprocessing', 'concurrent'], 'Model_Answer': "Ensures only one native thread executes Python bytecode at a time, limiting concurrency on multi-core systems."},
    {'id': 'T8', 'type': 'T', 'difficulty': 'INTERMEDIATE', 'Q': "13/20 (Intermediate): How do you handle exceptions and guarantee clean-up in a file operation?", 'keywords': ['try', 'except', 'finally', 'with open'], 'Model_Answer': "Use a `with open` statement or `try...finally` block to ensure the resource is closed."},
    {'id': 'T9', 'type': 'T', 'difficulty': 'INTERMEDIATE', 'Q': "14/20 (Intermediate): Give an example of using a list comprehension to transform a list of strings to uppercase.", 'keywords': ['[s.upper()', 'for s in list]'], 'Model_Answer': "Code: `[s.upper() for s in my_list]`"},
    {'id': 'T10', 'type': 'T', 'difficulty': 'INTERMEDIATE', 'Q': "15/20 (Intermediate): Explain the difference between `==` and `is` in Python.", 'keywords': ['equality', 'identity', 'value', 'memory address'], 'Model_Answer': "`==` checks for value equality; `is` checks for object identity (same memory address)."},

    # 5 ADVANCED TECHNICAL QUESTIONS (Difficulty: ADVANCED)
    {'id': 'T11', 'type': 'T', 'difficulty': 'ADVANCED', 'Q': "16/20 (Advanced): What is a Python decorator? Provide a conceptual use case.", 'keywords': ['@', 'wrap', 'modify', 'function'], 'Model_Answer': "A function that `wraps` another function to `modify` its behavior (e.g., logging, timing)."},
    {'id': 'T12', 'type': 'T', 'difficulty': 'ADVANCED', 'Q': "17/20 (Advanced): Explain the concept of dependency injection in a Python framework.", 'keywords': ['decoupling', 'IoC', 'class', 'external'], 'Model_Answer': "Passing required services (dependencies) into a `class` instead of having the class create them internally, promoting `decoupling`."},
    {'id': 'T13', 'type': 'T', 'difficulty': 'ADVANCED', 'Q': "18/20 (Advanced): Describe a scenario where you would use a generator instead of a standard list.", 'keywords': ['yield', 'memory', 'large data', 'iteration'], 'Model_Answer': "When dealing with `large data` streams or infinite sequences to save `memory` by using `yield`."},
    {'id': 'T14', 'type': 'T', 'difficulty': 'ADVANCED', 'Q': "19/20 (Advanced): What are *args and **kwargs, and when would you use them together?", 'keywords': ['arbitrary', '*args', '**kwargs', 'dictionary'], 'Model_Answer': "Allow passing an `arbitrary` number of positional (`*args`) and `dictionary` keyword arguments (`**kwargs`) to a function."},
    {'id': 'T15', 'type': 'T', 'difficulty': 'ADVANCED', 'Q': "20/20 (Advanced): Explain how Python's garbage collector works.", 'keywords': ['reference counting', 'generational', 'collect'], 'Model_Answer': "Uses `reference counting` primarily, supplemented by a `generational` collector to break reference cycles and reclaim memory."},
]

# --- 3. HELPER FUNCTIONS FOR FILE UPLOAD AND ANALYSIS ---

def parse_resume_text(uploaded_file):
    """Reads text content from an uploaded file (supports PDF and TXT)."""
    if uploaded_file.name.endswith('.pdf'):
        try:
            reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text() if page.extract_text() else ""
            return text.lower()
        except Exception as e:
            return f"Error parsing PDF: {e}"
    
    return uploaded_file.getvalue().decode("utf-8", errors='ignore').lower()


def analyze_and_rank_resume(resume_text, file_name):
    """Calculates a seniority score based on weighted keywords (simulating LLM/NLP)."""
    if "error" in resume_text:
        return {'tier': 'Junior', 'Total_Score': 0, 'YoE': 'N/A', 'Keyword_Score': 0}

    senior_keywords = ['tensorflow', 'pytorch', 'architecture', 'kubernetes', 'cloud', 'design patterns']
    mid_keywords = ['flask', 'django', 'api', 'sql', 'unit testing', 'data analysis']
    
    senior_count = sum(1 for keyword in senior_keywords if keyword in resume_text)
    mid_count = sum(1 for keyword in mid_keywords if keyword in resume_text)
    
    total_score = 0
    yoe = "2-5"
    
    # 1. Technical Relevance (Max ~50 points)
    tech_score = (senior_count * 15) + (mid_count * 5)
    total_score += min(50, tech_score)

    # 2. Seniority Keywords (Max ~30 points)
    if 'senior' in resume_text or 'lead' in resume_text:
        total_score += 25
        yoe = "5+"
    elif 'mid-level' in resume_text or 'developer' in resume_text:
        total_score += 15
    
    # 3. Education (Max 20 points)
    if 'm.s.' in resume_text or 'phd' in resume_text or 'master' in resume_text:
        total_score += 20
    elif 'b.s.' in resume_text or 'bachelor' in resume_text:
        total_score += 10

    # Determine tier based on total score (0-100+)
    if total_score >= 80:
        tier = 'Senior'
    elif total_score >= 50:
        tier = 'Mid-Level'
    else:
        tier = 'Junior'
        
    return {
        'Candidate Name': file_name,
        'Tier Rank': tier,
        'Score': total_score,
        'YoE (Est.)': yoe,
        'Keyword Match': tech_score
    }


# --- 4. STREAMLIT INTERFACE SETUP AND EXECUTION ---

st.set_page_config(
    page_title="AI Python Recruiter Screening",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@aipythonrecruiter.com',
        'About': 'Automated Python candidate screening tool by AI Python Recruiter.'
    }
)

# Initialize the bot and state in Streamlit's session state
if 'bot' not in st.session_state:
    st.session_state.bot = None 
    st.session_state.interview_started = False
    st.session_state.messages = []
    st.session_state.is_finished = False
    st.session_state.input_key = 0 
    st.session_state.analysis_ready = False 
    st.session_state.candidate_tier = 'N/A' 
    st.session_state.ranking_data = []
    st.session_state.uploaded_files_list = [] # Storage for uploaded files

def start_interview_logic():
    st.session_state.interview_started = True
    st.session_state.bot.start_time = time.time()
    st.session_state.messages = [] 
    st.session_state.bot.recorded_answers = [] 
    
    st.session_state.messages.append({"role": "bot", "content": f"Hello! I'm your **AI Python Recruiter**. Your resume categorized you as a **{st.session_state.candidate_tier}** candidate. This interview is dynamically tailored to your profile and will take exactly **20 minutes**. Good luck!"})
    
    st.session_state.current_q_data = st.session_state.bot.questions[0]
    st.session_state.messages.append({"role": "bot", "content": st.session_state.current_q_data['Q']})
    st.session_state.bot.current_q_index = 1

def handle_user_input(user_input):
    bot_instance = st.session_state.bot
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    bot_instance._process_answer(st.session_state.current_q_data, user_input)
    
    st.session_state.input_key += 1
    
    if bot_instance._check_time() and bot_instance.current_q_index < bot_instance.total_questions:
        
        next_q_data = bot_instance.questions[bot_instance.current_q_index]
        st.session_state.current_q_data = next_q_data
        
        current_time_str = time.strftime("%M:%S", time.gmtime(time.time() - bot_instance.start_time))
        st.session_state.messages.append({"role": "bot", "content": f"**[Elapsed Time: {current_time_str}]** Thank you for your response. Next Question is..."})
        st.session_state.messages.append({"role": "bot", "content": next_q_data['Q']})
        
        bot_instance.current_q_index += 1
    
    elif bot_instance.current_q_index >= bot_instance.total_questions:
        st.session_state.is_finished = True
        st.session_state.interview_started = False
        final_message = "✅ **All questions answered!**"
        st.session_state.messages.append({"role": "bot", "content": f"**Interview Session Concluded.** {final_message} Your complete performance analysis is now available below."})
    
    elif not bot_instance._check_time():
        st.session_state.is_finished = True
        st.session_state.interview_started = False
        final_message = "🚨 **Time's up!**"
        st.session_state.messages.append({"role": "bot", "content": f"**Interview Session Concluded.** {final_message} Your complete performance analysis is now available below."})
        
    st.rerun() 

def display_final_analysis():
    st.header("📊 Final Candidate Performance Analysis")
    bot_instance = st.session_state.bot
    
    st.markdown("---")
    st.subheader("I. Summary Results")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Score", f"{bot_instance.score['total']:.1f} / {bot_instance.total_questions}")
    col2.metric("Technical Score", f"{bot_instance.score['technical']:.1f} / 5.0")
    col3.metric("Generic/Behavioral Score", f"{bot_instance.score['generic']:.1f} / 5.0")
    
    st.markdown("---")
    st.subheader("II. Question-by-Question Breakdown")
    
    for i, record in enumerate(bot_instance.recorded_answers):
        st.markdown(f"#### Q{i + 1}: {record['Q']}")
        st.markdown(f"**Score Earned:** {record['Score_Earned']:.1f} point(s) | **Analysis:** {record['Analysis']}")
        
        with st.expander("Show User Response and Model Key"):
            st.markdown(f"**Candidate Response:**\n\n`{record['User_Response']}`")
            st.markdown(f"**Model Answer Key:**\n\n`{record['Model_Answer']}`")
        st.markdown("---")
        
def reset_session():
    keys_to_delete = ['bot', 'interview_started', 'is_finished', 'messages', 'current_q_data', 'input_key', 'analysis_ready', 'candidate_tier', 'ranking_data', 'uploaded_files_list']
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

# --- MAIN EXECUTION BLOCK ---

st.markdown(
    """
    <h1 style='text-align: center; color: #1e88e5; background-color: #262730; padding: 10px; border-radius: 10px;'>
        🤖 AI Python Recruiter
    </h1>
    <p style='text-align: center; font-size: 1.1em;'>
        Automated Technical Screening Interface
    </p>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# 2. Sidebar Logic (Handles File Upload and Interview Setup)
with st.sidebar:
    st.header("Interview Status")
    
    if st.button("🔴 Reset Interview & Clear State"):
        reset_session()
        
    st.markdown("---") 

    # --- NEW FILE UPLOAD AND RANKING LOGIC ---
    if not st.session_state.interview_started and not st.session_state.is_finished:
        st.header("Stage 1: Resume Analysis")
        # Multi-file uploader
        uploaded_files = st.file_uploader("Upload Multiple PDF or TXT Resumes", 
                                          type=['pdf', 'txt'], 
                                          accept_multiple_files=True)
        
        # 1. Store uploaded files in session state (crucial for stability)
        if uploaded_files:
            st.session_state.uploaded_files_list = uploaded_files
            st.info(f"Loaded {len(uploaded_files)} file(s).")

        # 2. Analysis Button Logic (Triggers ranking)
        if st.session_state.uploaded_files_list and not st.session_state.analysis_ready:
            if st.button("🚀 Analyze & Rank Candidates"):
                
                st.session_state.ranking_data = [] 
                
                # Analyze all uploaded files
                for file in st.session_state.uploaded_files_list:
                    resume_text = parse_resume_text(file)
                    analysis = analyze_and_rank_resume(resume_text, file.name)
                    st.session_state.ranking_data.append(analysis)
                
                st.session_state.analysis_ready = True
                st.success(f"Ranking Complete for {len(st.session_state.uploaded_files_list)} candidate(s).")
                st.rerun() 

        elif st.session_state.analysis_ready:
            
            st.header("Stage 2: Candidate Ranking")
            
            # Use pandas to display and allow sorting
            df_rank = pd.DataFrame(st.session_state.ranking_data)
            df_rank_sorted = df_rank.sort_values(by='Score', ascending=False)

            st.dataframe(df_rank_sorted, height=200, use_container_width=True)
            
            # Selection for interview
            selected_name = st.selectbox("Select Candidate to Interview:", df_rank_sorted['Candidate Name'])
            
            if selected_name:
                # Retrieve the tier for the selected candidate
                selected_candidate_data = df_rank_sorted[df_rank_sorted['Candidate Name'] == selected_name].iloc[0]
                selected_tier = selected_candidate_data['Tier Rank']
                
                if st.button(f"Start Interview for {selected_name} ({selected_tier})"):
                    st.session_state.bot = RecruiterBot(MASTER_QUESTION_ROSTER, selected_tier)
                    st.session_state.candidate_tier = selected_tier 
                    start_interview_logic()
        
    # --- END NEW LOGIC ---

    if st.session_state.interview_started and not st.session_state.is_finished:
        st.success(f"🟢 LIVE: Tier: {st.session_state.candidate_tier}")
    elif st.session_state.is_finished:
        st.error("🔴 FINISHED: Results Available")
    else:
        st.warning(f"🟡 READY: Upload resume to begin.")

    st.markdown("---") 

    if st.session_state.interview_started or st.session_state.is_finished:
        elapsed = time.time() - st.session_state.bot.start_time
        time_display = time.strftime("%M:%S", time.gmtime(elapsed))
        st.metric(label="Elapsed Time (Max 20:00)", value=time_display)

        if st.session_state.bot:
            q_completed = st.session_state.bot.current_q_index - 1
            st.metric(label="Questions Completed", value=q_completed if q_completed >= 0 else 0, delta=st.session_state.bot.total_questions)
            if st.session_state.is_finished:
                st.subheader("Final Score")
                st.info(f"Total: **{st.session_state.bot.score['total']:.1f} / {st.session_state.bot.total_questions}**")
        else:
            st.caption("Awaiting interview start...")


# 3. Main Chat Window
chat_container = st.container()

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
    # Input box and Start Button logic
    if st.session_state.interview_started and not st.session_state.is_finished:
        if user_input := st.chat_input("Type your answer here...", key=st.session_state.input_key):
            handle_user_input(user_input)
    elif not st.session_state.interview_started and not st.session_state.is_finished and st.session_state.analysis_ready:
        st.info("Ranking complete. Select a candidate from the sidebar table to start the interview.")
    elif st.session_state.is_finished:
        display_final_analysis()