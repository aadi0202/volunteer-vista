import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
from flask_socketio import SocketIO, join_room, emit


# Load environment variables from .env file
load_dotenv()

app = Flask("VolunteerVista")
secret_key = os.environ.get("SECRET_KEY")
if not secret_key:
    raise ValueError("No SECRET_KEY set for Flask application")
app.secret_key = secret_key
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Functions
def get_ngo_email_from_conversation(conversation_id):
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        return conversation.ngo_email
    return None

def get_volunteer_email_from_conversation(conversation_id):
    conversation = Conversation.query.get(conversation_id)
    if conversation:
        return conversation.volunteer_email
    return None

# Models
class NGO(db.Model):
    __tablename__ = 'ngos'
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    ngo_name = db.Column(db.String(120), nullable=False)
    ngo_summary = db.Column(db.Text, nullable=False)
    logo_filename = db.Column(db.String(200), nullable=False, default='images/image_spare.png')
    official_name = db.Column(db.String(120), nullable=False)
    registration_number = db.Column(db.String(100), nullable=False)
    registration_date = db.Column(db.Date, nullable=False)
    ngo_type = db.Column(db.String(100), nullable=False)
    pan_number = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    contact_number = db.Column(db.String(20), nullable=False)
    website = db.Column(db.String(200), nullable=True)
    volunteer_details = db.Column(db.Text, nullable=False)
    darpan_cert_filename = db.Column(db.String(200), nullable=True)

class Volunteer(db.Model):
    __tablename__ = 'volunteers'
    email = db.Column(db.String(120), primary_key=True)
    password = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(120), nullable=False)
    last_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    volunteer_experience = db.Column(db.Text, nullable=True)
    work_experience = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    areas_of_interest = db.Column(db.Text, nullable=True)
    certifications = db.Column(db.Text, nullable=True)
    availability = db.Column(db.String(50), nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    start_date = db.Column(db.String(50), nullable=True)
    profile_pic = db.Column(db.String(200), nullable=False, default='images/image_spare.png')
    status = db.Column(db.String(20), default='pending')

class JoinRequest(db.Model):
    __tablename__ = 'join_requests'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ngo_email = db.Column(db.String(120), db.ForeignKey('ngos.email'), nullable=False)
    volunteer_email = db.Column(db.String(120), db.ForeignKey('volunteers.email'), nullable=False)
    status = db.Column(db.String(50), nullable=False)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ngo_email = db.Column(db.String(120), db.ForeignKey('ngos.email'))
    volunteer_email = db.Column(db.String(120), db.ForeignKey('volunteers.email'))
    messages = db.relationship('Message', backref='conversation', lazy=True)
    ngo = db.relationship('NGO', foreign_keys=[ngo_email])
    volunteer = db.relationship('Volunteer', foreign_keys=[volunteer_email])
    messages = db.relationship('Message', backref='conversation', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'))
    sender_type = db.Column(db.String(10))  # "ngo" or "volunteer"
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    announcement = db.Column(db.String(500), nullable=True)
    maintenance_mode = db.Column(db.Boolean, default=False)

class Notification(db.Model):
     id = db.Column(db.Integer, primary_key=True)
     user_email = db.Column(db.String(120), nullable=False)  # email of NGO/volunteer
     type = db.Column(db.String(50))  # e.g., "application", "chat"
     content = db.Column(db.String(255))
     read = db.Column(db.Boolean, default=False)
     timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Create tables if they do not exist
with app.app_context():
    db.create_all()

# Helper to get a join request by its id
def get_join_request(app_id):
    return JoinRequest.query.get(app_id)

# ----------------------------
# Create tables and default admin
# ----------------------------
with app.app_context():
    db.create_all()
    # Create default admin account if it does not exist
    if not Admin.query.filter_by(email="admin123@mail.com").first():
        admin_account = Admin(email="admin123@mail.com", password="admin@123")
        db.session.add(admin_account)
        db.session.commit()
# ----------------------------
# Admin Routes
# ----------------------------
@app.route('/admin/')
def admin_home():
    return redirect(url_for('admin_login'))
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        admin = Admin.query.filter_by(email=email, password=password).first()
        if admin:
            session['user'] = email
            session['user_type'] = 'admin'
            return redirect(url_for('admin_dashboard'))
        else:
            error = "Invalid credentials."
            return render_template('admin_login.html', error=error)
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
def admin_users():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    ngos = NGO.query.all()
    volunteers = Volunteer.query.all()
    return render_template('admin_users.html', ngos=ngos, volunteers=volunteers)

@app.route('/admin/join_requests')
def admin_join_requests():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    join_requests = JoinRequest.query.all()
    return render_template('admin_join_requests.html', join_requests=join_requests)

@app.route('/admin/system_config', methods=['GET', 'POST'])
def admin_system_config():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    
    # Get the current system configuration; if none exists, create one.
    config = SystemConfig.query.first()
    if not config:
        config = SystemConfig()
        db.session.add(config)
    
    if request.method == 'POST':
        announcement = request.form.get('announcement')
        maintenance = request.form.get('maintenance')
        
        config.announcement = announcement if announcement.strip() != "" else None
        config.maintenance_mode = True if maintenance == 'on' else False
        
        db.session.commit()
        flash("System configuration updated.", "success")
    
    return render_template('admin_system_config.html', system_config=config)

@app.route('/admin/content_moderation')
def admin_content_moderation():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    # For demonstration, assume these are empty lists
    flagged_ngos = []
    flagged_volunteers = []
    flagged_listings = []
    return render_template('admin_content_moderation.html', flagged_ngos=flagged_ngos, flagged_volunteers=flagged_volunteers, flagged_listings=flagged_listings)

@app.route('/admin/chat_logs')
def admin_chat_logs():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    chat_logs = Message.query.order_by(Message.timestamp.desc()).all()
    return render_template('admin_chat_logs.html', chat_logs=chat_logs)

@app.route('/admin/edit_ngo', methods=['POST'])
def admin_edit_ngo():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    email = request.form.get('email')
    ngo = NGO.query.filter_by(email=email).first()
    if ngo:
        ngo.ngo_name = request.form.get('ngo_name')
        ngo.ngo_summary = request.form.get('ngo_summary')
        # Update password (admin can view and change it)
        ngo.password = request.form.get('password')
        
        # Update new fields
        ngo.official_name = request.form.get('official_name')
        ngo.registration_number = request.form.get('registration_number')
        registration_date_str = request.form.get('registration_date')
        try:
            ngo.registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d').date()
        except Exception:
            flash("Invalid registration date format.", "error")
            return redirect(url_for('admin_users'))
        ngo.ngo_type = request.form.get('ngo_type')
        ngo.pan_number = request.form.get('pan_number')
        ngo.address = request.form.get('address')
        ngo.contact_number = request.form.get('contact_number')
        ngo.website = request.form.get('website')
        ngo.volunteer_details = request.form.get('volunteer_details')
        
        # Handle logo update/deletion
        file = request.files.get('logo')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ngo.logo_filename = 'uploads/' + filename
        if request.form.get('delete_logo'):
            ngo.logo_filename = 'images/image_spare.png'
        
        # Handle DARPAN certification update (optional)
        darpan_file = request.files.get('darpan_cert')
        if darpan_file and darpan_file.filename:
            darpan_filename = secure_filename(darpan_file.filename)
            darpan_file.save(os.path.join(app.config['UPLOAD_FOLDER'], darpan_filename))
            ngo.darpan_cert_filename = 'uploads/' + darpan_filename
        
        db.session.commit()
        flash("NGO account updated successfully.", "success")
    else:
        flash("NGO not found.", "error")
    return redirect(url_for('admin_users'))

@app.route('/admin/edit_volunteer', methods=['POST'])
def admin_edit_volunteer():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    email = request.form.get('email')
    volunteer = Volunteer.query.filter_by(email=email).first()
    if volunteer:
        volunteer.first_name = request.form.get('first_name')
        volunteer.last_name = request.form.get('last_name')
        volunteer.username = request.form.get('username')
        # Update password (viewable and editable)
        volunteer.password = request.form.get('password')
        volunteer.phone = request.form.get('phone')
        volunteer.state = request.form.get('state')
        volunteer.city = request.form.get('city')
        volunteer.address = request.form.get('address')
        volunteer.age = request.form.get('age')
        volunteer.volunteer_experience = request.form.get('volunteer_experience')
        volunteer.work_experience = request.form.get('work_experience')
        volunteer.education = request.form.get('education')
        volunteer.skills = request.form.get('skills')
        volunteer.areas_of_interest = request.form.get('areas_of_interest')
        volunteer.certifications = request.form.get('certifications')
        volunteer.availability = request.form.get('availability')
        volunteer.duration = request.form.get('duration')
        volunteer.start_date = request.form.get('start_date')
        
        # Process profile picture update
        file = request.files.get('profile_pic')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            volunteer.profile_pic = 'uploads/' + filename
        # If delete checkbox is checked, set profile picture to default
        if request.form.get('delete_pic'):
            volunteer.profile_pic = 'images/image_spare.png'
        
        db.session.commit()
        flash("Volunteer account updated successfully.", "success")
    else:
        flash("Volunteer not found.", "error")
    return redirect(url_for('admin_users'))

@app.route('/admin/delete_announcement', methods=['POST'])
def delete_announcement():
    if session.get('user_type') != 'admin':
        return redirect(url_for('admin_login'))
    config = SystemConfig.query.first()
    if config:
        config.announcement = None
        db.session.commit()
        flash("Announcement deleted.", "success")
    else:
        flash("No announcement found.", "error")
    return redirect(url_for('admin_system_config'))

#########################
# Chat Routes and Setup
#########################
socketio = SocketIO(app)
@socketio.on('join')
def handle_join(data):
    room = str(data['conversation_id'])
    join_room(room)

from datetime import datetime

from datetime import datetime

@socketio.on('send_message')
def handle_send_message(data):
    conversation_id = data['conversation_id']
    sender_type = data['sender_type']
    message_text = data['message']
    
    # Save the message to the database
    new_message = Message(conversation_id=conversation_id, sender_type=sender_type, content=message_text)
    db.session.add(new_message)
    db.session.commit()
    
    # Retrieve the conversation once for both recipient and sender details
    conversation = Conversation.query.get(conversation_id)
    
    # Determine the recipient email and sender's name based on sender type
    if sender_type == 'ngo':
        recipient_email = conversation.volunteer_email
        sender_name = conversation.ngo.ngo_name if conversation.ngo else "NGO"
    else:
        recipient_email = conversation.ngo_email
        if conversation.volunteer:
            sender_name = f"{conversation.volunteer.first_name} {conversation.volunteer.last_name}"
        else:
            sender_name = "Volunteer"
    
    # Create a notification with the sender's actual name
    notification = Notification(
        user_email=recipient_email,
        type='chat',
        content=f"New message from **{sender_name}**.",
        read=False,
        timestamp=datetime.utcnow()
    )
    db.session.add(notification)
    db.session.commit()
    
    # Broadcast the message to everyone in the conversation room
    emit('receive_message', {
        'sender_type': sender_type,
        'message': message_text,
        'timestamp': new_message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    }, room=str(conversation_id))

@app.route('/chat/<partner_email>')
def chat(partner_email):
    user_role = session.get('user_type')  # 'ngo' or 'volunteer'
    
    if user_role == 'ngo':
        current_ngo = NGO.query.filter_by(email=session.get('user')).first()
        volunteer = Volunteer.query.filter_by(email=partner_email).first()
        if not current_ngo or not volunteer:
            flash("User not found.")
            return redirect(url_for('home'))
        conversation = Conversation.query.filter_by(
            ngo_email=current_ngo.email,
            volunteer_email=volunteer.email
        ).first()
        if not conversation:
            conversation = Conversation(ngo_email=current_ngo.email, volunteer_email=volunteer.email)
            db.session.add(conversation)
            db.session.commit()
        partner_info = volunteer  # Chat partner info for NGO user
    elif user_role == 'volunteer':
        current_volunteer = Volunteer.query.filter_by(email=session.get('user')).first()
        ngo = NGO.query.filter_by(email=partner_email).first()
        if not current_volunteer or not ngo:
            flash("User not found.")
            return redirect(url_for('home'))
        conversation = Conversation.query.filter_by(
            ngo_email=ngo.email,
            volunteer_email=current_volunteer.email
        ).first()
        if not conversation:
            conversation = Conversation(ngo_email=ngo.email, volunteer_email=current_volunteer.email)
            db.session.add(conversation)
            db.session.commit()
        partner_info = ngo  # Chat partner info for Volunteer user
    else:
        flash("Please log in first.")
        return redirect(url_for('home'))
    
    messages = Message.query.filter_by(conversation_id=conversation.id).order_by(Message.timestamp).all()
    return render_template('chat.html', conversation=conversation, messages=messages, partner_info=partner_info)
#########################
# NGO Routes
#########################

@app.route('/ngo/login', methods=['GET', 'POST'])
def ngo_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        ngo = NGO.query.filter_by(email=email).first()
        if ngo and ngo.password == password:
            session['user'] = email
            session['user_type'] = 'ngo'
            return redirect(url_for('ngo_dashboard'))
        else:
            error = "Invalid email or password."
            return render_template('ngo_login.html', error=error)
    return render_template('ngo_login.html')

@app.route('/ngo/signup', methods=['GET', 'POST'])
def ngo_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        # Check if the email is already registered
        if NGO.query.filter_by(email=email).first():
            error = "Email is already registered. Please use a different email."
            return render_template('ngo_signup.html', error=error)
        
        password = request.form.get('password')
        ngo_name = request.form.get('ngo_name')
        ngo_summary = request.form.get('ngo_summary')
        
        # New form fields
        official_name = request.form.get('official_name')
        registration_number = request.form.get('registration_number')
        registration_date_str = request.form.get('registration_date')
        ngo_type = request.form.get('ngo_type')
        pan_number = request.form.get('pan_number')
        address = request.form.get('address')
        contact_number = request.form.get('contact_number')
        website = request.form.get('website')
        volunteer_details = request.form.get('volunteer_details')
        
        # Process registration date (expects format YYYY-MM-DD)
        try:
            registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d').date()
        except Exception:
            flash("Invalid date format. Please use YYYY-MM-DD.", "error")
            return render_template('ngo_signup.html')
        
        # Handle file upload for NGO logo
        file = request.files.get('logo')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            logo_filename = 'uploads/' + filename  # Relative to static folder
        else:
            logo_filename = 'images/image_spare.png'
        
        # Handle file upload for optional DARPAN ID/Tax Exemption Certification
        darpan_file = request.files.get('darpan_cert')
        if darpan_file and darpan_file.filename != '':
            darpan_filename = secure_filename(darpan_file.filename)
            darpan_file.save(os.path.join(app.config['UPLOAD_FOLDER'], darpan_filename))
            darpan_cert_filename = 'uploads/' + darpan_filename
        else:
            darpan_cert_filename = None
        
        new_ngo = NGO(
            email=email,
            password=password,
            ngo_name=ngo_name,
            ngo_summary=ngo_summary,
            logo_filename=logo_filename,
            official_name=official_name,
            registration_number=registration_number,
            registration_date=registration_date,
            ngo_type=ngo_type,
            pan_number=pan_number,
            address=address,
            contact_number=contact_number,
            website=website,
            volunteer_details=volunteer_details,
            darpan_cert_filename=darpan_cert_filename
        )
        db.session.add(new_ngo)
        db.session.commit()
        session['user'] = email
        session['user_type'] = 'ngo'
        return redirect(url_for('ngo_dashboard'))
    return render_template('ngo_signup.html')

@app.route('/ngo/logout')
def ngo_logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

@app.route('/ngo/dashboard')
def ngo_dashboard():
    if session.get('user_type') != 'ngo':
        return redirect(url_for('ngo_login'))
    ngo_email = session.get('user')
    applications = JoinRequest.query.filter_by(ngo_email=ngo_email).all()
    joined_volunteers = []
    for req in applications:
        if req.status == 'accepted':
            vol = Volunteer.query.filter_by(email=req.volunteer_email).first()
            if vol:
                joined_volunteers.append(vol)
    ngo = NGO.query.filter_by(email=ngo_email).first()
    
    # Fetch unread notifications for the NGO
    notifications = Notification.query.filter_by(user_email=ngo.email, read=False).all()
    
    return render_template('ngo_dashboard.html', ngo=ngo,
                           applications=applications,
                           joined_volunteers=joined_volunteers,
                           notifications=notifications)

@app.route('/ngo/edit', methods=['POST'])
def ngo_edit():
    if session.get('user_type') != 'ngo':
        return redirect(url_for('ngo_login'))
    ngo_email = session.get('user')
    ngo = NGO.query.filter_by(email=ngo_email).first()
    if ngo:
        # Update existing fields
        ngo.ngo_name = request.form.get('ngo_name')
        ngo.ngo_summary = request.form.get('ngo_summary')
        
        # Update new fields
        ngo.official_name = request.form.get('official_name')
        ngo.registration_number = request.form.get('registration_number')
        registration_date_str = request.form.get('registration_date')
        try:
            ngo.registration_date = datetime.strptime(registration_date_str, '%Y-%m-%d').date()
        except Exception:
            flash("Invalid registration date format. Please use YYYY-MM-DD.")
            return redirect(url_for('ngo_dashboard', tab='profile'))
        ngo.ngo_type = request.form.get('ngo_type')
        ngo.pan_number = request.form.get('pan_number')
        ngo.address = request.form.get('address')
        ngo.contact_number = request.form.get('contact_number')
        ngo.website = request.form.get('website')
        ngo.volunteer_details = request.form.get('volunteer_details')
        
        # Handle logo update/deletion
        file = request.files.get('logo')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            ngo.logo_filename = 'uploads/' + filename
        elif request.form.get('delete_logo'):
            ngo.logo_filename = 'images/image_spare.png'
        
        # Handle DARPAN certificate update
        darpan_file = request.files.get('darpan_cert')
        if darpan_file and darpan_file.filename != '':
            darpan_filename = secure_filename(darpan_file.filename)
            darpan_file.save(os.path.join(app.config['UPLOAD_FOLDER'], darpan_filename))
            ngo.darpan_cert_filename = 'uploads/' + darpan_filename

        db.session.commit()
        flash("Profile updated successfully.")
    return redirect(url_for('ngo_dashboard', tab='profile'))

@app.route('/ngo/application/<int:app_id>', methods=['POST'])
def ngo_application_action(app_id):
    if session.get('user_type') != 'ngo':
        return redirect(url_for('ngo_login'))
    action = request.form.get('action')  # "accept" or "reject"
    app_req = get_join_request(app_id)
    if app_req:
        if action == 'accept':
            app_req.status = 'accepted'
        elif action == 'reject':
            app_req.status = 'rejected'
        db.session.commit()
    return redirect(url_for('ngo_dashboard'))

@app.route('/admin_delete_ngo', methods=['POST'])
def admin_delete_ngo():
    # Assume the admin authentication check is already in place.
    email = request.form.get('email')
    if not email:
        flash("Invalid NGO identifier.", "error")
        return redirect(url_for('admin_users'))

    # Query the NGO user (adjust query according to your ORM/model)
    ngo = NGO.query.filter_by(email=email).first()
    if ngo:
        # If there are associated files (like logos), delete them if needed.
        db.session.delete(ngo)
        db.session.commit()
        flash("NGO account deleted successfully.", "success")
    else:
        flash("NGO account not found.", "error")
    return redirect(url_for('admin_users'))

#########################
# Volunteer Routes
#########################

@app.route('/volunteer/login', methods=['GET', 'POST'])
def volunteer_login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        volunteer = Volunteer.query.filter_by(email=email).first()
        if volunteer and volunteer.password == password:
            session['user'] = email
            session['user_type'] = 'volunteer'
            return redirect(url_for('volunteer_dashboard'))
        else:
            error = "Invalid email or password."
            return render_template('volunteer_login.html', error=error)
    return render_template('volunteer_login.html')

@app.route('/volunteer/signup', methods=['GET', 'POST'])
def volunteer_signup():
    if request.method == 'POST':
        email = request.form.get('email')
        if Volunteer.query.filter_by(email=email).first():
            error = "Email is already registered. Please use a different email."
            return render_template('volunteer_signup.html', error=error)
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        # Handle file upload for volunteer profile picture
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_pic = 'uploads/' + filename
        else:
            profile_pic = 'images/image_spare.png'
        new_volunteer = Volunteer(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=request.form.get('username', ''),
            phone=request.form.get('phone', ''),
            state=request.form.get('state', ''),
            city=request.form.get('city', ''),
            address=request.form.get('address', ''),
            age=request.form.get('age') if request.form.get('age') else None,
            volunteer_experience=request.form.get('volunteer_experience', ''),
            work_experience=request.form.get('work_experience', ''),
            education=request.form.get('education', ''),
            skills=request.form.get('skills', ''),
            areas_of_interest=request.form.get('areas_of_interest', ''),
            certifications=request.form.get('certifications', ''),
            availability=request.form.get('availability', ''),
            duration=request.form.get('duration', ''),
            start_date=request.form.get('start_date', ''),
            profile_pic=profile_pic
        )
        db.session.add(new_volunteer)
        db.session.commit()
        session['user'] = email
        session['user_type'] = 'volunteer'
        return redirect(url_for('volunteer_dashboard'))
    return render_template('volunteer_signup.html')

@app.route('/volunteer/logout')
def volunteer_logout():
    session.pop('user', None)
    session.pop('user_type', None)
    return redirect(url_for('home'))

@app.route('/volunteer/dashboard', methods=['GET', 'POST'])
def volunteer_dashboard():
    if session.get('user_type') != 'volunteer':
        return redirect(url_for('volunteer_login'))
    volunteer_email = session.get('user')
    volunteer = Volunteer.query.filter_by(email=volunteer_email).first()
    if volunteer is None:
        flash("Volunteer record not found. Please sign up again.")
        return redirect(url_for('volunteer_signup'))
    
    if request.method == 'POST':
        # (Update volunteer profile logic)
        volunteer.email = request.form.get('email', volunteer.email)
        volunteer.first_name = request.form.get('first_name', volunteer.first_name)
        volunteer.last_name = request.form.get('last_name', volunteer.last_name)
        volunteer.username = request.form.get('username', volunteer.username)
        volunteer.phone = request.form.get('phone', volunteer.phone)
        volunteer.state = request.form.get('state', volunteer.state)
        volunteer.city = request.form.get('city', volunteer.city)
        volunteer.address = request.form.get('address', volunteer.address)
        volunteer.age = request.form.get('age', volunteer.age)
        volunteer.volunteer_experience = request.form.get('volunteer_experience', volunteer.volunteer_experience)
        volunteer.work_experience = request.form.get('work_experience', volunteer.work_experience)
        volunteer.education = request.form.get('education', volunteer.education)
        volunteer.skills = request.form.get('skills', volunteer.skills)
        volunteer.areas_of_interest = request.form.get('areas_of_interest', volunteer.areas_of_interest)
        volunteer.certifications = request.form.get('certifications', volunteer.certifications)
        volunteer.availability = request.form.get('availability', volunteer.availability)
        volunteer.duration = request.form.get('duration', volunteer.duration)
        volunteer.start_date = request.form.get('start_date', volunteer.start_date)
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            volunteer.profile_pic = 'uploads/' + filename
        elif request.form.get('delete_pic'):
            volunteer.profile_pic = 'images/image_spare.png'
        db.session.commit()
        flash("Profile updated successfully.")
        return redirect(url_for('volunteer_dashboard', tab='profile'))
    
    # Fetch unread notifications for the volunteer
    notifications = Notification.query.filter_by(user_email=volunteer.email, read=False).all()
    
    joined_ngos = []
    join_reqs = JoinRequest.query.filter_by(volunteer_email=volunteer_email).all()
    for req in join_reqs:
        ngo = NGO.query.filter_by(email=req.ngo_email).first()
        if ngo:
            # Attach the join request's status to the NGO object
            ngo.join_status = req.status
            joined_ngos.append(ngo)
    
    applications = JoinRequest.query.filter_by(volunteer_email=volunteer_email).all()
    return render_template('volunteer_dashboard.html', 
                           volunteer=volunteer,
                           applications=applications, 
                           joined_ngos=joined_ngos, 
                           notifications=notifications)

@app.route('/update_volunteer_status/<int:join_request_id>', methods=['POST'])
def update_volunteer_status(join_request_id):
    new_status = request.form.get('status')
    valid_statuses = ['pending', 'accepted', 'rejected']
    
    if new_status not in valid_statuses:
        flash('Invalid status provided.', 'error')
        return redirect(url_for('ngo_dashboard'))
    
    join_req = JoinRequest.query.get(join_request_id)
    if join_req:
        old_status = join_req.status
        join_req.status = new_status
        db.session.commit()
        
        # Create a notification if the status has changed
        # Create a notification if the status has changed
        if new_status != old_status:
            volunteer = Volunteer.query.filter_by(email=join_req.volunteer_email).first()
            ngo = NGO.query.filter_by(email=join_req.ngo_email).first()
            ngo_name = ngo.ngo_name if ngo else "NGO"
            if volunteer:
                notification = Notification(
                    user_email=volunteer.email,
                    type='application',
                    content=f"Your application status has been updated to **{new_status}** by **{ngo_name}**.",
                    read=False,
                    timestamp=datetime.utcnow()  # Ensure you import datetime from the datetime module
                )
                db.session.add(notification)
                db.session.commit()
        flash('Volunteer status updated successfully!', 'success')
    else:
        flash('Join request not found.', 'error')
    
    return redirect(url_for('ngo_dashboard'))

@app.route('/admin_delete_volunteer', methods=['POST'])
def admin_delete_volunteer():
    email = request.form.get('email')
    if not email:
        flash("Invalid volunteer identifier.", "error")
        return redirect(url_for('admin_users'))

    volunteer = Volunteer.query.filter_by(email=email).first()
    if volunteer:
        # Optionally, delete associated assets (e.g., profile picture)
        db.session.delete(volunteer)
        db.session.commit()
        flash("Volunteer account deleted successfully.", "success")
    else:
        flash("Volunteer account not found.", "error")
    return redirect(url_for('admin_users'))

@app.route('/join/<ngo_id>', methods=['POST'])
def join_ngo(ngo_id):
    if session.get('user_type') != 'volunteer':
        return redirect(url_for('volunteer_login'))
    volunteer_email = session.get('user')
    existing = JoinRequest.query.filter_by(ngo_email=ngo_id, volunteer_email=volunteer_email).first()
    if not existing:
        new_request = JoinRequest(ngo_email=ngo_id, volunteer_email=volunteer_email, status='pending')
        db.session.add(new_request)
        db.session.commit()
        
        # Create a notification for the NGO regarding the new join request
        notification = Notification(
            user_email=ngo_id,
            type='join',
            content="New volunteer application received.",
            read=False,
            timestamp=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
    return redirect(url_for('volunteer_dashboard'))
    

# Notification Routes
@app.route('/mark_notification_read/<int:notif_id>', methods=['POST'])
def mark_notification_read(notif_id):
    notif = Notification.query.get(notif_id)
    if notif:
        notif.read = True
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Notification not found'}), 404

@app.route('/')
def home():
    config = SystemConfig.query.first()  # Get the current configuration, if any.
    return render_template('home.html', system_config=config)

@app.route('/listings', methods=['GET', 'POST'])
def listings():
    search_query = request.form.get('search_query', '')
    results = NGO.query.filter(NGO.ngo_name.ilike(f"%{search_query}%")).all()
    return render_template('listings.html', results=results, search_query=search_query)

@app.context_processor
def inject_models():
    return dict(Volunteer=Volunteer)
if __name__ == '__main__':
    socketio.run(app, debug=True)
