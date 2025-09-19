# Smart Timetable Management System

A production-ready, constraint-based timetable scheduling system built with Flask and SQLAlchemy. This system automatically generates optimized academic timetables while respecting complex scheduling constraints.

## 🌟 Features

### Core Functionality
- **Automatic Timetable Generation**: Advanced constraint satisfaction algorithm with backtracking
- **Multiple View Types**: Master, per-teacher, per-section, and per-student timetables
- **Role-Based Access Control**: Admin, Teacher, and Student roles with appropriate permissions
- **Manual Editing**: Admin can manually adjust generated timetables with conflict detection
- **Export Capabilities**: CSV and PDF export for all timetable views

### Scheduling Features
- **Hard Constraints**: No double-booking, room type matching, lab session requirements
- **Soft Constraints**: Balanced teacher loads, limited consecutive periods, optimal scheduling
- **Lab Session Support**: 2-period consecutive lab blocks with lab room requirements
- **Elective Handling**: Shared slots across sections for student choice
- **Configurable Settings**: Flexible time slots, working days, and scheduling parameters

### User Management
- **Multi-Role Support**: Comprehensive user management for admins, teachers, and students
- **Authentication**: Secure bcrypt password hashing with session management
- **Dashboard Views**: Role-specific dashboards with relevant information and actions

## 🏗️ Architecture

### Backend (Python/Flask)
- **Flask**: Web framework with modular blueprint structure
- **SQLAlchemy**: ORM for database operations with relationship management
- **Constraint Scheduler**: Custom algorithm implementing backtracking with heuristics
- **REST API**: JSON-based API for frontend communication

### Frontend (HTML/CSS/JavaScript)
- **Responsive Design**: Bootstrap-based UI that works on all devices
- **Role-Based UI**: Different interfaces for Admin, Teacher, and Student roles
- **Interactive Grids**: Dynamic timetable visualization with conflict highlighting
- **AJAX Operations**: Seamless user experience with asynchronous operations

### Database Design
- **Users & Roles**: User management with teacher/student relationships
- **Academic Structure**: Departments, sections, subjects, and classrooms
- **Scheduling**: Time slots, timetable entries, and generation reports
- **Constraints**: Teacher-subject eligibility and system settings

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sih
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database and seed data**
   ```bash
   python seed_data.py
   ```

5. **Start the application**
   ```bash
   python app.py
   ```

6. **Access the application**
   - Open your web browser and go to: http://localhost:5000
   - Use the default admin credentials: `admin` / `admin123`

## 📖 Usage Guide

### Initial Setup

1. **Login as Admin**
   - Username: `admin`
   - Password: `admin123`

2. **Configure Time Slots**
   - Go to "Timetable" → "Generate"
   - Click "Configure" to set up working days, times, and break periods
   - Generate time slots based on your institution's schedule

3. **Manage Academic Data**
   - Add/edit teachers, students, sections, subjects, and classrooms
   - Assign teachers to subjects they can teach
   - Create subject instances for each section

4. **Generate Timetable**
   - Navigate to "Timetable" → "Generate"
   - Click "Generate Timetable" to create optimized schedules
   - View results and handle any conflicts

### Daily Operations

#### For Administrators
- **Dashboard**: View system statistics and quick actions
- **Management**: CRUD operations for all entities
- **Timetable Generation**: Create and regenerate schedules
- **Manual Editing**: Fine-tune generated timetables
- **Export**: Generate PDF/CSV reports

#### For Teachers
- **Personal Timetable**: View teaching schedule
- **Dashboard**: See today's classes and weekly overview
- **Export**: Download personal timetable

#### For Students
- **Section Timetable**: View class schedule
- **Dashboard**: See today's classes and upcoming sessions
- **Export**: Download section timetable

## 🔧 Configuration

### Environment Variables
```bash
FLASK_DEBUG=True              # Enable debug mode
FLASK_HOST=127.0.0.1         # Server host
FLASK_PORT=5000              # Server port
DATABASE_URL=sqlite:///timetable.db  # Database URL
SECRET_KEY=your-secret-key   # Session secret (change in production)
```

### System Settings
Configurable through admin interface:
- Scheduler iterations and timeout
- Maximum consecutive periods for teachers
- Working days and default timings
- Semester length and academic calendar

### Database Configuration
Default: SQLite for development
Production: Update `config.py` for PostgreSQL/MySQL:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@localhost/timetable'
```

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Model tests
pytest tests/test_models.py -v

# API tests
pytest tests/test_api.py -v

# Scheduler tests
pytest tests/test_scheduler.py -v
```

### Test Coverage
```bash
pytest --cov=app tests/
```

## 📊 API Documentation

### Authentication Endpoints
```
POST /api/login          # User login
POST /api/logout         # User logout
GET  /api/current-user   # Get current user info
```

### Admin Endpoints
```
GET    /api/teachers      # List teachers
POST   /api/teachers      # Create teacher
PUT    /api/teachers/{id} # Update teacher
DELETE /api/teachers/{id} # Delete teacher

GET    /api/sections      # List sections
POST   /api/sections      # Create section
PUT    /api/sections/{id} # Update section
DELETE /api/sections/{id} # Delete section

# Similar patterns for subjects, classrooms, students
```

### Timetable Endpoints
```
POST /api/generate                    # Generate timetable
GET  /api/timetable/master           # Master timetable
GET  /api/timetable/section/{id}     # Section timetable
GET  /api/timetable/teacher/{id}     # Teacher timetable
GET  /api/timetable/export           # Export timetable
```

### Example API Usage
```javascript
// Login
const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'admin', password: 'admin123' })
});

// Generate timetable
const generate = await fetch('/api/generate', { method: 'POST' });
const result = await generate.json();

// Export timetable
window.open('/api/timetable/export?format=pdf&target=master', '_blank');
```

## 🧠 Scheduler Algorithm

### Algorithm Overview
The system uses a **constraint satisfaction approach** with **backtracking**:

1. **Environment Preparation**
   - Load available time slots, teachers, and classrooms
   - Build constraint mappings (teacher-subject eligibility)

2. **Demand Generation**
   - Create scheduling demands from subject instances
   - Handle regular lectures and lab blocks separately

3. **Difficulty-Based Ordering**
   - Sort demands by scheduling difficulty
   - Prioritize lab blocks, electives, and constrained subjects

4. **Backtracking Search**
   - Try assignments for each demand in order
   - Validate hard constraints before assignment
   - Backtrack on conflicts and try alternatives

5. **Optimization**
   - Apply soft constraint penalties
   - Use heuristics for pruning search space
   - Timeout protection for complex scenarios

### Constraint Types

**Hard Constraints (Must Never Violate)**
- No teacher double-booking
- No classroom double-booking
- Lab sessions use lab rooms only
- Lab sessions are 2 consecutive periods
- Section scheduling conflicts
- Required period counts

**Soft Constraints (Preferences)**
- Limit consecutive periods for teachers
- Balance teacher workloads
- Avoid labs at day start/end
- Distribute subjects across week

## 🔒 Security Features

- **Password Security**: bcrypt hashing with salt
- **Session Management**: Secure session handling
- **Role-Based Access**: Endpoint-level authorization
- **Input Validation**: Server-side validation for all inputs
- **CORS Protection**: Configurable cross-origin policies

## 📱 Browser Compatibility

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🐛 Troubleshooting

### Common Issues

**Database Connection Errors**
```bash
# Reset database
rm timetable.db
python seed_data.py
```

**Import Errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Scheduler Timeout**
- Reduce complexity by limiting subjects or increasing time slots
- Adjust timeout settings in admin panel
- Check for insufficient teachers or classrooms

**Generation Failures**
- Verify all subjects have assigned teachers
- Ensure sufficient lab rooms for lab subjects
- Check time slot configuration

### Debug Mode
Enable detailed logging:
```bash
export FLASK_DEBUG=True
python app.py
```

### Performance Optimization
- Increase `scheduler_max_iterations` for complex schedules
- Add more time slots if utilization is too high
- Ensure adequate teacher-subject assignments

## 🚀 Production Deployment

### Database Migration
```bash
# For production, use proper database
pip install psycopg2-binary  # for PostgreSQL
# Update config.py with production database URL
```

### Security Hardening
1. Change default admin password
2. Set strong `SECRET_KEY` in environment
3. Use HTTPS in production
4. Configure proper CORS settings
5. Enable logging and monitoring

### Docker Deployment
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install pytest pytest-cov pytest-flask

# Run tests before committing
pytest tests/ -v --cov=app

# Code style
pip install black flake8
black . && flake8 .
```

## 📄 License

MIT License - see LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with details
4. For security issues, contact maintainers directly

## 🔄 Version History

### v1.0.0 (Current)
- Initial release with core functionality
- Constraint-based scheduling algorithm
- Role-based access control
- Export capabilities
- Comprehensive test suite

---

**Built with ❤️ for Smart India Hackathon 2024**

Ready to revolutionize academic scheduling! 🎓