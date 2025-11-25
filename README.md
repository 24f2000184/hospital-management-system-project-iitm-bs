# 🏥 Hospital Management System

A complete hospital management system built with Flask, SQLite, and Bootstrap.

## Features

- **Admin Dashboard**: Manage doctors, patients, and appointments
- **Doctor Portal**: View appointments, manage availability, add treatment records
- **Patient Portal**: Book appointments, view treatment history, manage profile

## Technologies Used

- **Backend**: Flask, SQLAlchemy
- **Frontend**: HTML, CSS, Bootstrap 5, Jinja2
- **Database**: SQLite

## Installation

1. Clone the repository:
```bash
git clone https://github.com/24f2000184-Maliha/hospital-management-system.git
cd hospital-management-system
```

2. Install dependencies:
```bash
pip install flask flask-sqlalchemy
```

3. Run the application:
```bash
python app.py
```

4. Open browser and go to: `http://127.0.0.1:5000/`

## Default Login

**Admin:**
- Email: admin@hospital.com
- Password: admin123

## Project Structure
```
hospital-management/
├── app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   └──
├── static/
│   └── css/
│       └── style.css
└── hospital.db
```

## License

MIT License