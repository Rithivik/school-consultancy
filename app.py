import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'edu_consultancy_secure_key'

# ==========================================
# REAL EMAIL SMTP FUNCTION
# ==========================================
def send_real_email(recipient_email, subject, message_body):
    # ⚠️ Replace these with your actual Gmail address and your 16-character Google App Password
    sender_email = "rithuolive@gmail.com"
    sender_password = "kvszsupxgmsogdsa"
    
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message_body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print(f"Real email successfully sent to {recipient_email}")
    except Exception as e:
        print(f"Failed to send real email: {e}")


# In-memory database holding consultancy client records, revenue, and notification logs
consultancy_db = [
    {
        "id": "CS-101",
        "student": "Rahul Sharma",
        "email": "rahul@gmail.com",
        "interest": "Artificial Intelligence & Data Science",
        "cutoff": 185.5,
        "fee_paid": 2000,
        "status": "Completed",
        "notifications": [
            "📧 [Email Sent to rahul@gmail.com]: Your consultation request CS-101 was successfully submitted and is In Review.",
            "📧 [Email Sent to rahul@gmail.com]: Good news! Your consultation CS-101 status has been updated to Completed."
        ],
        "roadmap": [
            "Target Stream: B.Sc/B.Tech Artificial Intelligence & Data Science",
            "Institutional Band: Tier-1 Premier Autonomous Institutions",
            "Action Plan: Python/Flask portfolio development, mathematics prep, and scholarship filing."
        ]
    },
    {
        "id": "CS-102",
        "student": "Priya V.",
        "email": "priya@gmail.com",
        "interest": "Computer Science & Engineering",
        "cutoff": 174.0,
        "fee_paid": 2000,
        "status": "In Review",
        "notifications": [
            "📧 [Email Sent to priya@gmail.com]: Your consultation request CS-102 was successfully submitted and is In Review."
        ],
        "roadmap": None
    }
]

# ==========================================
# PUBLIC LANDING PAGE
# ==========================================
@app.route('/')
def home():
    total_revenue = sum(c['fee_paid'] for c in consultancy_db)
    total_clients = len(consultancy_db)
    return render_template('index.html', revenue=total_revenue, clients=total_clients)


# ==========================================
# CLIENT / STUDENT PORTAL
# ==========================================
@app.route('/client/login', methods=['GET', 'POST'])
def client_login():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        
        session['client_name'] = name
        session['client_email'] = email
        return redirect(url_for('client_dashboard'))
    return render_template('client_login.html')

@app.route('/client/dashboard', methods=['GET', 'POST'])
def client_dashboard():
    if 'client_email' not in session:
        return redirect(url_for('client_login'))
        
    client_name = session['client_name']
    client_email = session['client_email']
    
    if request.method == 'POST':
        interest = request.form.get('interest')
        cutoff = float(request.form.get('cutoff', 0))
        
        tier = "Tier-1 Premier Autonomous Institutions" if cutoff >= 180 else "Tier-2 Reputed Regional Colleges"
        roadmap = [
            f"Recommended Major: {interest}",
            f"Target Institution Category: {tier}",
            "Strategic Guidance: Complete technical certification courses and apply before priority deadlines."
        ]
        
        new_id = f"CS-{101 + len(consultancy_db)}"
        
        # Create submission notification log for the dashboard UI inbox
        init_notification = f"📧 [Email Sent to {client_email}]: Your consultation request {new_id} was successfully submitted and is In Review."
        
        consultancy_db.append({
            "id": new_id,
            "student": client_name,
            "email": client_email,
            "interest": interest,
            "cutoff": cutoff,
            "fee_paid": 2000,
            "status": "In Review",
            "notifications": [init_notification],
            "roadmap": roadmap
        })
        
        # 🚀 Dispatches a REAL email to the entered client email address
        subject = f"EduPathway AI - Consultation Request Received ({new_id})"
        body = f"Hello {client_name},\n\nYour consultation request for {interest} has been successfully submitted and is currently In Review.\n\nSession ID: {new_id}\nRetainer Fee Paid: ₹2,000\n\nThank you for choosing EduPathway AI!"
        send_real_email(client_email, subject, body)
        
        return redirect(url_for('client_dashboard'))
        
    client_records = [c for c in consultancy_db if c['email'] == client_email]
    return render_template('client_dashboard.html', name=client_name, email=client_email, records=client_records)


# ==========================================
# CONSULTANCY COMPANY STAFF PORTAL
# ==========================================
@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == 'admin' and password == 'admin123':
            session['staff_logged'] = True
            return redirect(url_for('staff_dashboard'))
        else:
            error = "Invalid credentials. Use staff ID: admin / admin123"
            
    return render_template('staff_login.html', error=error)

@app.route('/staff/dashboard')
def staff_dashboard():
    if not session.get('staff_logged'):
        return redirect(url_for('staff_login'))
        
    total_revenue = sum(c['fee_paid'] for c in consultancy_db)
    completed = sum(1 for c in consultancy_db if c['status'] == 'Completed')
    pending = sum(1 for c in consultancy_db if c['status'] == 'In Review')
    
    return render_template('staff_dashboard.html', 
                           clients=consultancy_db, 
                           revenue=total_revenue, 
                           total=len(consultancy_db),
                           completed=completed, 
                           pending=pending)

@app.route('/staff/update/<session_id>', methods=['POST'])
def staff_update(session_id):
    if not session.get('staff_logged'):
        return redirect(url_for('staff_login'))
        
    new_status = request.form.get('status')
    for c in consultancy_db:
        if c['id'] == session_id:
            c['status'] = new_status
            status_note = f"📧 [Email Sent to {c['email']}]: Your consultation {session_id} status has been updated to {new_status} by staff."
            c['notifications'].append(status_note)
            
            # 🚀 Dispatches a REAL email to the client when staff updates their status
            subject = f"EduPathway AI - Status Update ({session_id})"
            body = f"Hello {c['student']},\n\nYour consultation session {session_id} status has been updated to: {new_status}.\n\nLog into your client portal dashboard to view your updated details.\n\nThank you,\nEduPathway AI Team"
            send_real_email(c['email'], subject, body)
            break
            
    return redirect(url_for('staff_dashboard'))


# ==========================================
# LOGOUT
# ==========================================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)