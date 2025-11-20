"""View routes for rendering HTML pages."""
from flask import render_template, Blueprint, session

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Main landing page."""
    return render_template('index.html')

@views_bp.route('/editor')
def task_editor():
    """Interactive task editor with live schedulability analysis."""
    return render_template('task_editor.html')

@views_bp.route('/dashboard_view')
def dashboard_view():
    """Dashboard view for verification metrics."""
    return render_template('dashboard.html')

@views_bp.route('/results/enhanced')
def enhanced_results():
    """Enhanced verification results view with all analysis features."""
    # Get latest verification results from session or default
    results = session.get('latest_verification', {})
    return render_template('enhanced_results.html', results=results)

@views_bp.route('/pattern-library')
def pattern_library_view():
    """View the property pattern library."""
    return render_template('pattern_library.html')

@views_bp.route('/autonomous')
def autonomous_view():
    """Autonomous formal verification pipeline interface."""
    return render_template('autonomous.html')
