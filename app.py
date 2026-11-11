import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv
from services.ai_service import generate_interview_questions, evaluate_interview_session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "super_secret_key_2026")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        session['user_id'] = 1
        session['user_name'] = name if name else "Candidate"
        session['user_email'] = email
        flash('Welcome to InterviewAce!', 'success')
        return redirect(url_for('dashboard'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        
        session['user_id'] = 1
        session['user_name'] = email.split('@')[0].capitalize() if email else "Candidate"
        session['user_email'] = email
        return redirect(url_for('dashboard'))
        
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    user_name = session.get('user_name', 'Candidate')
    history_list = session.get('history_list', [])
    
    total_interviews = len(history_list)
    if total_interviews > 0:
        avg_score = round(sum(item['score'] for item in history_list) / total_interviews / 10, 1)
        best_score = round(max(item['score'] for item in history_list) / 10, 1)
    else:
        avg_score = 0.0
        best_score = 0.0

    return render_template(
        'dashboard.html',
        user_name=user_name,
        total_interviews=total_interviews,
        avg_score=avg_score,
        best_score=best_score,
        history_list=history_list
    )

@app.route('/setup')
def setup():
    return render_template('setup.html')

@app.route('/start-interview', methods=['POST'])
def start_interview():
    selected_role = request.form.get('job_role_select')
    custom_role = request.form.get('custom_job_role')
    
    job_role = custom_role if (selected_role == 'Custom' and custom_role) else selected_role
    if not job_role:
        job_role = "Software Developer"

    difficulty = request.form.get('difficulty', 'Intermediate')
    interview_type = request.form.get('interview_type', 'Technical')
    experience = request.form.get('experience', 'Fresher')
    total_questions = int(request.form.get('total_questions', 5))
    
    questions = generate_interview_questions(job_role, difficulty, interview_type, experience, total_questions)
    
    session['interview_config'] = {
        'job_role': job_role,
        'difficulty': difficulty,
        'interview_type': interview_type,
        'experience': experience,
        'total_questions': total_questions
    }
    session['questions'] = questions
    session['current_index'] = 0
    session['user_answers'] = []
    
    return redirect(url_for('interview'))

@app.route('/interview')
def interview():
    questions = session.get('questions', [])
    current_index = session.get('current_index', 0)
    config = session.get('interview_config', {})
    
    if not questions or current_index >= len(questions):
        return redirect(url_for('feedback'))
    
    current_question = questions[current_index]
    total = len(questions)
    progress_percentage = int(((current_index + 1) / total) * 100)
    
    return render_template(
        'interview.html',
        question=current_question,
        current_num=current_index + 1,
        total_questions=total,
        progress=progress_percentage,
        config=config
    )

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    question_text = request.form.get('question_text')
    user_answer = request.form.get('user_answer')
    
    user_answers = session.get('user_answers', [])
    user_answers.append({
        'question': question_text,
        'answer': user_answer
    })
    session['user_answers'] = user_answers
    
    session['current_index'] = session.get('current_index', 0) + 1
    
    questions = session.get('questions', [])
    if session['current_index'] >= len(questions):
        return redirect(url_for('feedback'))
    
    return redirect(url_for('interview'))

@app.route('/feedback')
def feedback():
    report_id = request.args.get('id', type=int)
    history_list = session.get('history_list', [])
    
    # If clicking from dashboard/history table
    if report_id is not None and 0 <= report_id < len(history_list):
        saved_attempt = history_list[report_id]
        return render_template('feedback.html', report=saved_attempt['report'], config=saved_attempt['config'])
    
    # Standard flow: evaluate live session answers
    user_answers = session.get('user_answers', [])
    config = session.get('interview_config', {'job_role': 'Software Developer', 'difficulty': 'Intermediate'})
    
    report = evaluate_interview_session(config.get('job_role', 'Developer'), user_answers)
    
    # Save this evaluation so View Report links work
    history_entry = {
        'job_role': config.get('job_role', 'Developer'),
        'difficulty': config.get('difficulty', 'Intermediate'),
        'interview_type': config.get('interview_type', 'Technical'),
        'total_questions': config.get('total_questions', 5),
        'score': report.get('overall_score', 0),
        'report': report,
        'config': config
    }
    
    history_list.append(history_entry)
    session['history_list'] = history_list
    
    return render_template('feedback.html', report=report, config=config)

@app.route('/history')
def history():
    history_list = session.get('history_list', [])
    return render_template('history.html', history_list=history_list)

if __name__ == '__main__':
    app.run(debug=True)