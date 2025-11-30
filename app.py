from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ===================== DATABASE MODELS =====================

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    doctors = db.relationship('Doctor', backref='department', lazy=True)

class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    experience = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    availability = db.relationship('DoctorAvailability', backref='doctor', lazy=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)

class DoctorAvailability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='Booked')  # Booked, Completed, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    treatment = db.relationship('Treatment', backref='appointment', uselist=False, lazy=True)

class Treatment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=False)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ===================== DECORATORS FOR LOGIN REQUIRED =====================

def login_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session or session.get('role') != role:
                flash('Please login first', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ===================== INITIALIZE DATABASE & ADMIN =====================

def init_db():
    with app.app_context():
        db.create_all()
        
        # Create admin if doesn't exist
        if not Admin.query.first():
            admin = Admin(
                username='admin',
                email='admin@hospital.com',
                password=generate_password_hash('admin123')
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin created - Username: admin, Password: admin123")
        
        # Create sample departments if none exist
        if not Department.query.first():
            departments = [
                Department(name='Cardiology', description='Heart and cardiovascular system'),
                Department(name='Neurology', description='Brain and nervous system'),
                Department(name='Orthopedics', description='Bones and joints'),
                Department(name='Pediatrics', description='Children health'),
                Department(name='Dermatology', description='Skin conditions')
            ]
            db.session.add_all(departments)
            db.session.commit()
            print("Sample departments created")

# ===================== HOME & AUTH ROUTES =====================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
@app.route('/login/<role_type>', methods=['GET', 'POST'])
def login(role_type=None):
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role') or role_type
        
        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['role'] = 'admin'
                session['name'] = user.username
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
        
        elif role == 'doctor':
            user = Doctor.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                if user.is_active:
                    session['user_id'] = user.id
                    session['role'] = 'doctor'
                    session['name'] = user.name
                    flash('Login successful!', 'success')
                    return redirect(url_for('doctor_dashboard'))
                else:
                    flash('Your account has been deactivated', 'danger')
        
        elif role == 'patient':
            user = Patient.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                if user.is_active:
                    session['user_id'] = user.id
                    session['role'] = 'patient'
                    session['name'] = user.name
                    flash('Login successful!', 'success')
                    return redirect(url_for('patient_dashboard'))
                else:
                    flash('Your account has been deactivated', 'danger')
        
        flash('Invalid credentials', 'danger')
    
    return render_template('login.html', role_type=role_type)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        age = request.form.get('age')
        gender = request.form.get('gender')
        address = request.form.get('address')
        
        if Patient.query.filter_by(email=email).first():
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        patient = Patient(
            name=name,
            email=email,
            password=generate_password_hash(password),
            phone=phone,
            age=age,
            gender=gender,
            address=address
        )
        db.session.add(patient)
        db.session.commit()
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

# ===================== ADMIN ROUTES =====================

@app.route('/admin/dashboard')
@login_required('admin')
def admin_dashboard():
    total_doctors = Doctor.query.filter_by(is_active=True).count()
    total_patients = Patient.query.filter_by(is_active=True).count()
    total_appointments = Appointment.query.count()
    upcoming_appointments = Appointment.query.filter(
        Appointment.date >= datetime.now().date(),
        Appointment.status == 'Booked'
    ).count()
    
    return render_template('admin_dashboard.html',
                         total_doctors=total_doctors,
                         total_patients=total_patients,
                         total_appointments=total_appointments,
                         upcoming_appointments=upcoming_appointments)

@app.route('/admin/doctors')
@login_required('admin')
def admin_doctors():
    search = request.args.get('search', '')
    if search:
        doctors = Doctor.query.filter(
            (Doctor.name.contains(search)) | 
            (Doctor.email.contains(search))
        ).all()
    else:
        doctors = Doctor.query.all()
    
    departments = Department.query.all()
    return render_template('admin_doctors.html', doctors=doctors, departments=departments)

@app.route('/admin/add_doctor', methods=['POST'])
@login_required('admin')
def add_doctor():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    department_id = request.form.get('department_id')
    experience = request.form.get('experience')
    
    if Doctor.query.filter_by(email=email).first():
        flash('Email already exists', 'danger')
        return redirect(url_for('admin_doctors'))
    
    doctor = Doctor(
        name=name,
        email=email,
        password=generate_password_hash(password),
        phone=phone,
        department_id=department_id,
        experience=experience
    )
    db.session.add(doctor)
    db.session.commit()
    
    flash('Doctor added successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/edit_doctor/<int:id>', methods=['POST'])
@login_required('admin')
def edit_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.name = request.form.get('name')
    doctor.phone = request.form.get('phone')
    doctor.department_id = request.form.get('department_id')
    doctor.experience = request.form.get('experience')
    
    db.session.commit()
    flash('Doctor updated successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/delete_doctor/<int:id>')
@login_required('admin')
def delete_doctor(id):
    doctor = Doctor.query.get_or_404(id)
    doctor.is_active = False
    db.session.commit()
    flash('Doctor deactivated successfully', 'success')
    return redirect(url_for('admin_doctors'))

@app.route('/admin/patients')
@login_required('admin')
def admin_patients():
    search = request.args.get('search', '')
    if search:
        patients = Patient.query.filter(
            (Patient.name.contains(search)) | 
            (Patient.email.contains(search)) |
            (Patient.phone.contains(search))
        ).all()
    else:
        patients = Patient.query.all()
    
    return render_template('admin_patients.html', patients=patients)

@app.route('/admin/delete_patient/<int:id>')
@login_required('admin')
def delete_patient(id):
    patient = Patient.query.get_or_404(id)
    patient.is_active = False
    db.session.commit()
    flash('Patient deactivated successfully', 'success')
    return redirect(url_for('admin_patients'))

@app.route('/admin/appointments')
@login_required('admin')
def admin_appointments():
    appointments = Appointment.query.order_by(Appointment.date.desc(), Appointment.time.desc()).all()
    return render_template('admin_appointments.html', appointments=appointments)

@app.route('/admin/upcoming_appointments')
@login_required('admin')
def admin_upcoming_appointments():
    today = datetime.now().date()
    
    # Get only future appointments with Booked status
    appointments = Appointment.query.filter(
        Appointment.date >= today,
        Appointment.status == 'Booked'
    ).order_by(Appointment.date.asc(), Appointment.time.asc()).all()
    
    return render_template('admin_upcoming_appointments.html', 
                         appointments=appointments, 
                         today=today)  

# ===================== DOCTOR ROUTES =====================

@app.route('/doctor/dashboard')
@login_required('doctor')
def doctor_dashboard():
    doctor_id = session['user_id']
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    
    # Get upcoming appointments for next 7 days
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor_id,
        Appointment.date.between(today, week_later),
        Appointment.status == 'Booked'
    ).order_by(Appointment.date, Appointment.time).all()
    
    # Get list of unique patients assigned to this doctor
    patients = db.session.query(Patient).join(Appointment).filter(
        Appointment.doctor_id == doctor_id
    ).distinct().all()
    
    total_patients = len(patients)
    
    return render_template('doctor_dashboard.html',
                         appointments=upcoming_appointments,
                         patients=patients,
                         total_patients=total_patients,
                         today=today)

@app.route('/doctor/availability', methods=['GET', 'POST'])
@login_required('doctor')
def doctor_availability():
    doctor_id = session['user_id']
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
        
        # Check if availability already exists
        existing = DoctorAvailability.query.filter_by(
            doctor_id=doctor_id,
            date=date
        ).first()
        
        if existing:
            existing.start_time = start_time
            existing.end_time = end_time
            existing.is_available = True
        else:
            availability = DoctorAvailability(
                doctor_id=doctor_id,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            db.session.add(availability)
        
        db.session.commit()
        flash('Availability updated successfully', 'success')
        return redirect(url_for('doctor_availability'))
    
    # Get next 7 days availability
    today = datetime.now().date()
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date >= today
    ).order_by(DoctorAvailability.date).all()
    
    return render_template('doctor_availability.html', availabilities=availabilities)

@app.route('/doctor/appointments')
@login_required('doctor')
def doctor_appointments():
    doctor_id = session['user_id']
    appointments = Appointment.query.filter_by(doctor_id=doctor_id).order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).all()
    
    return render_template('doctor_appointments.html', appointments=appointments)

@app.route('/doctor/complete_appointment/<int:id>', methods=['GET', 'POST'])
@login_required('doctor')
def complete_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    # Check if appointment belongs to this doctor
    if appointment.doctor_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('doctor_appointments'))
    
    # Check if appointment is already completed or cancelled
    if appointment.status != 'Booked':
        flash(f'This appointment is already {appointment.status}', 'warning')
        return redirect(url_for('doctor_appointments'))
    
    # Check if today is the appointment date
    today = datetime.now().date()
    if appointment.date != today:
        if appointment.date > today:
            flash(f'Cannot complete appointment scheduled for future date ({appointment.date.strftime("%Y-%m-%d")}). Please wait until the appointment date.', 'warning')
        else:
            flash(f'This appointment was scheduled for {appointment.date.strftime("%Y-%m-%d")}. You can still complete it as a past appointment.', 'info')
            # Allow completing past appointments, but show info message
    
    if request.method == 'POST':
        # Double-check on submission
        if appointment.date > today:
            flash('Cannot complete future appointments', 'danger')
            return redirect(url_for('doctor_appointments'))
        
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        if not diagnosis or not prescription:
            flash('Diagnosis and prescription are required', 'danger')
            return redirect(url_for('complete_appointment', id=id))
        
        appointment.status = 'Completed'
        
        treatment = Treatment(
            appointment_id=appointment.id,
            diagnosis=diagnosis,
            prescription=prescription,
            notes=notes
        )
        db.session.add(treatment)
        db.session.commit()
        
        flash('Appointment completed successfully', 'success')
        return redirect(url_for('doctor_appointments'))
    
    return render_template('complete_appointment.html', 
                         appointment=appointment,
                         now=datetime.now())

@app.route('/doctor/patient_history/<int:patient_id>')
@login_required('doctor')
def patient_history(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        status='Completed'
    ).order_by(Appointment.date.desc()).all()
    
    return render_template('patient_history.html', patient=patient, appointments=appointments)

@app.route('/doctor/cancel_appointment/<int:id>')
@login_required('doctor')
def cancel_appointment_doctor(id):
    appointment = Appointment.query.get_or_404(id)
    
    # Check if appointment belongs to this doctor
    if appointment.doctor_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('doctor_dashboard'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('doctor_dashboard'))

# ===================== PATIENT ROUTES =====================

@app.route('/patient/dashboard')
@login_required('patient')
def patient_dashboard():
    departments = Department.query.all()
    patient_id = session['user_id']
    
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient_id,
        Appointment.date >= datetime.now().date(),
        Appointment.status == 'Booked'
    ).order_by(Appointment.date, Appointment.time).all()
    
    return render_template('patient_dashboard.html',
                         departments=departments,
                         appointments=upcoming_appointments)

@app.route('/patient/doctors')
@login_required('patient')
def patient_doctors():
    search = request.args.get('search', '')
    department_id = request.args.get('department_id', '')
    
    query = Doctor.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(Doctor.name.contains(search))
    
    if department_id:
        query = query.filter_by(department_id=department_id)
    
    doctors = query.all()
    departments = Department.query.all()
    
    # Get availability for next 7 days
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    
    return render_template('patient_doctors.html',
                         doctors=doctors,
                         departments=departments,
                         today=today,
                         week_later=week_later)

@app.route('/patient/book_appointment/<int:doctor_id>', methods=['GET', 'POST'])
@login_required('patient')
def book_appointment(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    
    if request.method == 'POST':
        date_str = request.form.get('date')
        time_str = request.form.get('time')
        
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
        
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            date=date,
            time=time,
            status='Booked'
        ).first()
        
        if existing:
            flash('This time slot is already booked', 'danger')
            return redirect(url_for('book_appointment', doctor_id=doctor_id))
        
        appointment = Appointment(
            patient_id=session['user_id'],
            doctor_id=doctor_id,
            date=date,
            time=time,
            reason=request.form.get('reason')
        )
        db.session.add(appointment)
        db.session.commit()
        
        flash('Appointment booked successfully', 'success')
        return redirect(url_for('patient_dashboard'))
    
    today = datetime.now().date()
    week_later = today + timedelta(days=7)
    
    availabilities = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == doctor_id,
        DoctorAvailability.date.between(today, week_later),
        DoctorAvailability.is_available == True
    ).all()
    
    return render_template('book_appointment.html', doctor=doctor, availabilities=availabilities, today=today, week_later=week_later)

@app.route('/patient/cancel_appointment/<int:id>')
@login_required('patient')
def cancel_appointment(id):
    appointment = Appointment.query.get_or_404(id)
    
    if appointment.patient_id != session['user_id']:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('patient_dashboard'))
    
    appointment.status = 'Cancelled'
    db.session.commit()
    
    flash('Appointment cancelled successfully', 'success')
    return redirect(url_for('patient_appointments'))

@app.route('/patient/appointments')
@login_required('patient')
def patient_appointments():
    patient_id = session['user_id']
    appointments = Appointment.query.filter_by(patient_id=patient_id).order_by(
        Appointment.date.desc(), Appointment.time.desc()
    ).all()
    
    return render_template('patient_appointments.html', appointments=appointments)

@app.route('/patient/treatment_history')
@login_required('patient')
def treatment_history():
    patient_id = session['user_id']
    appointments = Appointment.query.filter_by(
        patient_id=patient_id,
        status='Completed'
    ).order_by(Appointment.date.desc()).all()
    
    return render_template('treatment_history.html', appointments=appointments)

@app.route('/patient/profile', methods=['GET', 'POST'])
@login_required('patient')
def patient_profile():
    patient = Patient.query.get_or_404(session['user_id'])
    
    if request.method == 'POST':
        patient.name = request.form.get('name')
        patient.phone = request.form.get('phone')
        patient.age = request.form.get('age')
        patient.gender = request.form.get('gender')
        patient.address = request.form.get('address')
        
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('patient_profile'))
    
    return render_template('patient_profile.html', patient=patient)

# ===================== RUN APP =====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True)