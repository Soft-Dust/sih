import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///timetable.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Scheduler configuration
    SCHEDULER_MAX_ITERATIONS = 10000
    SCHEDULER_TIMEOUT_SECONDS = 30
    MAX_CONSECUTIVE_PERIODS = 3

    # Working days (0=Monday, 6=Sunday)
    DEFAULT_WORKING_DAYS = [0, 1, 2, 3, 4]  # Mon-Fri

    # Default class timings
    DEFAULT_START_TIME = "08:00"
    DEFAULT_END_TIME = "15:00"
    DEFAULT_PERIOD_DURATION = 60  # minutes
    DEFAULT_BREAK_DURATION = 15   # minutes

    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size