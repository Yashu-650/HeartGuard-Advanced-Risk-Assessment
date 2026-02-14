
from flask import Flask, render_template, request, jsonify, session
import json
import sqlite3
import joblib
import numpy as np
from datetime import datetime
import os
from pathlib import Path

# Print environment info for debugging
import sklearn
import numpy
print(f"[DEBUG] Python version: {os.sys.version}")
print(f"[DEBUG] Scikit-learn version: {sklearn.__version__}")
print(f"[DEBUG] Numpy version: {numpy.__version__}")

# ==================== FLASK APP INITIALIZATION ====================

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)

app.config['JSON_SORT_KEYS'] = False
# Simple session secret for login - in production use a secure secret and env var
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'change-this-secret')
# Session configuration
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# ==================== PATHS ====================
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / 'models'
DATABASE_PATH = BASE_DIR / 'database' / 'heart_disease.db'

# Create database directory if it doesn't exist
DATABASE_PATH.parent.mkdir(exist_ok=True)

# ==================== DATABASE INITIALIZATION ====================

def init_database():
    """Initialize SQLite database"""
    if not DATABASE_PATH.exists():
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age INTEGER,
                sex INTEGER,
                chest_pain_type INTEGER,
                resting_blood_pressure INTEGER,
                cholesterol INTEGER,
                fasting_blood_sugar INTEGER,
                resting_ecg INTEGER,
                max_heart_rate INTEGER,
                exercise_induced_angina INTEGER,
                st_depression REAL,
                st_slope INTEGER,
                major_vessels INTEGER,
                thalassemia INTEGER,
                risk_percentage REAL,
                risk_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("[OK] Database initialized successfully")

# Initialize database at startup
init_database()

# ==================== MODEL LOADING ====================

def load_models():
    """Load all trained ML models"""
    try:
        models = {}
        
        # Check which models exist and load them
        model_files = {
            'knn': 'knn.pkl',
            'decision_tree': 'decision_tree.pkl',
            'naive_bayes': 'naive_bayes.pkl',
            'svm': 'svm.pkl',
            'logistic_regression': 'logistic_regression.pkl',
            'mlp': 'mlp.pkl'
        }
        
        # Track loaded models
        loaded_count = 0
        
        for model_name, filename in model_files.items():
            filepath = MODELS_DIR / filename
            if filepath.exists():
                models[model_name] = joblib.load(filepath)
                print(f"[OK] Loaded {model_name}: {filename}")
                loaded_count += 1
            else:
                print(f"[WARNING] Warning: {filename} not found")
        
        # Try to load scaler
        scaler_path = MODELS_DIR / 'scaler.pkl'
        if scaler_path.exists():
            models['scaler'] = joblib.load(scaler_path)
            print(f"[OK] Loaded scaler: scaler.pkl")
        else:
            print("[WARNING] Warning: scaler.pkl not found - using standard scaling")
            from sklearn.preprocessing import StandardScaler
            models['scaler'] = StandardScaler()
        
        # Try to load feature names
        feature_names_path = MODELS_DIR / 'feature_names.pkl'
        if feature_names_path.exists():
            models['feature_names'] = joblib.load(feature_names_path)
            print(f"[OK] Loaded feature names: feature_names.pkl")
        else:
            print("[WARNING] Warning: feature_names.pkl not found")
        
        if loaded_count == 0:
            print("[ERROR] Error: No models found!")
            return None
        
        print(f"[OK] Successfully loaded {loaded_count} models!")
        return models
    
    except Exception as e:
        print(f"[ERROR] Error loading models: {e}")
        return None

# Load models at startup
MODELS = load_models()

# ==================== HEALTH RECOMMENDATIONS ====================

def get_precautions(risk_level):
    """Get precautions based on risk level"""
    
    precautions = {
        'LOW_RISK': {
            'title': '[LOW RISK] - Maintain Good Health',
            'precautions': [
                '• Continue regular exercise (30 mins daily)',
                '• Maintain healthy weight',
                '• Keep blood pressure under control',
                '• Regular health check-ups (yearly)',
                '• Avoid smoking and excessive alcohol',
                '• Manage stress through meditation',
                '• Sleep 7-8 hours daily',
                '• Monitor cholesterol levels'
            ]
        },
        'MODERATE_RISK': {
            'title': '[MODERATE RISK] - Take Preventive Measures',
            'precautions': [
                '• Increase exercise to 45 mins daily',
                '• Reduce sodium intake significantly',
                '• Control weight strictly',
                '• Monitor blood pressure daily',
                '• Check cholesterol every 3-6 months',
                '• Avoid stress and take breaks',
                '• Limit alcohol consumption',
                '• Consult with cardiologist',
                '• Take prescribed medications on time',
                '• Monitor blood sugar if diabetic'
            ]
        },
        'HIGH_RISK': {
            'title': '[HIGH RISK] - Immediate Medical Attention Required',
            'precautions': [
                '• CONSULT CARDIOLOGIST IMMEDIATELY',
                '• Get ECG and stress test done',
                '• Daily blood pressure monitoring',
                '• Strict salt restriction (< 1500mg/day)',
                '• Exercise only with doctor\'s guidance',
                '• Regular medication as prescribed',
                '• Monitor any chest pain or discomfort',
                '• Keep emergency contact ready',
                '• Avoid stressful activities',
                '• Weekly health check-ups recommended',
                '• Maintain food diary',
                '• Regular follow-ups with specialist'
            ]
        }
    }
    
    return precautions.get(risk_level, precautions['MODERATE_RISK'])

def get_diet_plan(risk_level):
    """Get diet plan based on risk level"""
    
    diet_plans = {
        'LOW_RISK': {
            'title': '[DIET] BALANCED DIET PLAN',
            'foods_to_eat': [
                '[OK] Fatty fish (salmon, mackerel) - 2x weekly',
                '[OK] Whole grains and oats daily',
                '[OK] Fresh fruits - 2-3 servings daily',
                '[OK] Vegetables - 3-4 servings daily',
                '[OK] Nuts and seeds - 1 handful daily',
                '[OK] Legumes and beans - 3x weekly',
                '[OK] Low-fat dairy products',
                '[OK] Olive oil for cooking',
                '[OK] Lean poultry without skin'
            ],
            'foods_to_avoid': [
                '[NO] Minimal red meat (1-2 times/month)',
                '[NO] Limit processed foods',
                '[NO] Avoid sugary drinks and desserts',
                '[NO] Reduce saturated fats',
                '[NO] Minimize salt intake',
                '[NO] Avoid fried foods',
                '[NO] No trans fats',
                '[NO] Limit alcohol'
            ]
        },
        'MODERATE_RISK': {
            'title': '[DIET] HEART-HEALTHY DIET PLAN',
            'foods_to_eat': [
                '[OK] Oily fish daily (salmon, sardines, tuna)',
                '[OK] Whole grains at every meal',
                '[OK] Leafy greens (spinach, kale) daily',
                '[OK] Colorful vegetables 4+ servings/day',
                '[OK] Berries and citrus fruits daily',
                '[OK] Nuts and seeds 1-2 servings/day',
                '[OK] Legumes and beans daily',
                '[OK] Extra virgin olive oil only',
                '[OK] Garlic and onions (beneficial for heart)',
                '[OK] Green tea 2-3 cups daily'
            ],
            'foods_to_avoid': [
                '[NO] NO red meat',
                '[NO] Eliminate processed foods',
                '[NO] NO sugary items',
                '[NO] NO trans fats or saturated fats',
                '[NO] VERY LOW salt (< 2g/day)',
                '[NO] NO fried or fatty foods',
                '[NO] Minimize dairy (only low-fat)',
                '[NO] NO alcohol or very minimal',
                '[NO] NO refined carbohydrates',
                '[NO] NO fast food or takeouts'
            ]
        },
        'HIGH_RISK': {
            'title': '[DIET] STRICT THERAPEUTIC DIET PLAN (Follow Strictly)',
            'foods_to_eat': [
                '[OK] Fatty fish 3-4x weekly (doctor approved)',
                '[OK] Whole grains & brown rice at every meal',
                '[OK] Spinach, kale, broccoli daily',
                '[OK] Red/orange/yellow vegetables (5+ servings)',
                '[OK] Citrus fruits, berries (3+ servings/day)',
                '[OK] Legumes & beans with every lunch/dinner',
                '[OK] Garlic & onions in every meal',
                '[OK] Extra virgin olive oil for cooking',
                '[OK] Herbs instead of salt for flavoring',
                '[OK] Green/herbal tea 3-4 cups daily',
                '[OK] Water - 8-10 glasses daily',
                '[OK] Low-sodium broth & soups'
            ],
            'foods_to_avoid': [
                '[NO] COMPLETELY NO red meat',
                '[NO] NO processed foods whatsoever',
                '[NO] NO sugar, sweets, or desserts',
                '[NO] ZERO salt or minimal salt',
                '[NO] NO fried, oily, or fatty foods',
                '[NO] NO saturated fats or trans fats',
                '[NO] NO butter or cream',
                '[NO] NO full-fat dairy products',
                '[NO] NO refined carbohydrates',
                '[NO] NO alcohol',
                '[NO] NO fast food, takeouts, or eating out',
                '[NO] NO canned foods (high sodium)',
                '[NO] NO coffee or caffeine',
                '[WARNING] CONSULT DIETITIAN FOR DETAILED PLAN'
            ]
        }
    }
    
    return diet_plans.get(risk_level, diet_plans['MODERATE_RISK'])

def calculate_risk_level(disease_votes, total_models):
    """Calculate risk level based on voting"""
    
    percentage = (disease_votes / total_models) * 100
    
    if percentage < 33:
        risk_level = 'LOW_RISK'
    elif percentage < 67:
        risk_level = 'MODERATE_RISK'
    else:
        risk_level = 'HIGH_RISK'
    
    return risk_level, percentage

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the main index page"""
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    """
    Make a prediction based on patient data
    Returns: Risk percentage, precautions, and diet plan
    """
    try:
        if not MODELS or len(MODELS) < 6:
            return jsonify({'error': 'Models not loaded. Please check models folder.'}), 500
        
        data = request.json
        
        # Validate input
        required_fields = [
            'age', 'sex', 'chest_pain_type', 'resting_blood_pressure',
            'cholesterol', 'fasting_blood_sugar', 'resting_ecg',
            'max_heart_rate', 'exercise_induced_angina', 'st_depression',
            'st_slope', 'major_vessels', 'thalassemia'
        ]
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Prepare feature array
        input_data = [
            data['age'],
            data['sex'],
            data['chest_pain_type'],
            data['resting_blood_pressure'],
            data['cholesterol'],
            data['fasting_blood_sugar'],
            data['resting_ecg'],
            data['max_heart_rate'],
            data['exercise_induced_angina'],
            data['st_depression'],
            data['st_slope'],
            data['major_vessels'],
            data['thalassemia']
        ]
        
        # Use pandas DataFrame to include feature names and avoid scikit-learn warnings
        import pandas as pd
        feature_names = MODELS.get('feature_names')
        if feature_names:
            features = pd.DataFrame([input_data], columns=feature_names)
        else:
            features = np.array([input_data])
        
        # Scale features if scaler available
        try:
            if 'scaler' in MODELS:
                scaled_features = MODELS['scaler'].transform(features)
                # Keep as DataFrame if original was DataFrame
                if feature_names:
                    scaled_features = pd.DataFrame(scaled_features, columns=feature_names)
            else:
                scaled_features = features
        except Exception as e:
            print(f"[WARNING] Scaling failed: {e}")
            scaled_features = features
        
        # Get predictions from all available models
        predictions = {}
        
        if 'knn' in MODELS:
            predictions['knn'] = int(MODELS['knn'].predict(scaled_features)[0])
        
        if 'decision_tree' in MODELS:
            predictions['decision_tree'] = int(MODELS['decision_tree'].predict(scaled_features)[0])
        
        if 'naive_bayes' in MODELS:
            predictions['naive_bayes'] = int(MODELS['naive_bayes'].predict(scaled_features)[0])
        
        if 'svm' in MODELS:
            predictions['svm'] = int(MODELS['svm'].predict(scaled_features)[0])
        
        if 'logistic_regression' in MODELS:
            predictions['logistic_regression'] = int(MODELS['logistic_regression'].predict(scaled_features)[0])
        
        if 'mlp' in MODELS:
            predictions['mlp'] = int(MODELS['mlp'].predict(scaled_features)[0])
        
        # If no models loaded, return error
        if not predictions:
            return jsonify({'error': 'No models available for prediction'}), 500
        
        # Ensemble voting
        num_models = len(predictions)
        disease_votes = sum(predictions.values())
        
        # Calculate risk level and percentage
        risk_level, risk_percentage = calculate_risk_level(disease_votes, num_models)
        
        # Get precautions and diet plan
        precautions = get_precautions(risk_level)
        diet_plan = get_diet_plan(risk_level)
        
        # Save to database
        save_prediction(data, risk_percentage, risk_level)
        
        # Prepare response
        response = {
            'timestamp': datetime.now().isoformat(),
            'risk_percentage': round(risk_percentage, 1),
            'risk_level': risk_level,
            'diagnosis': 'Heart Disease Risk Detected' if risk_percentage >= 50 else 'Low Heart Disease Risk',
            'precautions': precautions,
            'diet_plan': diet_plan,
            'message': f'Risk of Heart Disease: {risk_percentage:.1f}%'
        }
        
        return jsonify(response), 200
    
    except Exception as e:
        print(f"Error in prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-content', methods=['GET'])
def get_content():
    """Get precautions and diet plan for a specific risk level"""
    risk_level = request.args.get('risk_level')
    if not risk_level:
        return jsonify({'error': 'Risk level required'}), 400
    
    return jsonify({
        'precautions': get_precautions(risk_level),
        'diet_plan': get_diet_plan(risk_level)
    }), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get prediction history from database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM predictions ORDER BY created_at DESC LIMIT 100')
        rows = cursor.fetchall()
        
        history = [dict(row) for row in rows]
        
        conn.close()
        
        return jsonify({'history': history}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    """Public access login - accepts any valid username/password."""
    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Validate input - require minimum length only
        if not username or len(username) < 3:
            print(f"[LOGIN] Failed - Username must be at least 3 characters")
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if not password or len(password) < 3:
            print(f"[LOGIN] Failed - Password must be at least 3 characters")
            return jsonify({'error': 'Password must be at least 3 characters'}), 400

        # PUBLIC ACCESS MODE - Accept any valid username/password
        # This allows all public users to access the health assessment system
        session['logged_in'] = True
        session['user'] = username
        print(f"[LOGIN] Success - User '{username}' logged in (Public Access)")
        return jsonify({'message': 'Login successful', 'user': username}), 200

    except Exception as e:
        print(f"[LOGIN] Error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500


@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'message': 'Logged out'}), 200


@app.route('/api/auth-status', methods=['GET'])
def api_auth_status():
    return jsonify({'logged_in': bool(session.get('logged_in')), 'user': session.get('user')}), 200

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear all prediction history"""
    try:
        # Require login to clear history
        if not session.get('logged_in'):
            return jsonify({'error': 'Unauthorized'}), 401

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM predictions')
        conn.commit()

        count = cursor.rowcount

        conn.close()

        return jsonify({'message': f'Cleared {count} predictions'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== DATABASE HELPER FUNCTIONS ====================

def save_prediction(data, risk_percentage, risk_level):
    """Save prediction to database"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions (
                age, sex, chest_pain_type, resting_blood_pressure,
                cholesterol, fasting_blood_sugar, resting_ecg,
                max_heart_rate, exercise_induced_angina, st_depression,
                st_slope, major_vessels, thalassemia,
                risk_percentage, risk_level, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['age'], data['sex'], data['chest_pain_type'],
            data['resting_blood_pressure'], data['cholesterol'],
            data['fasting_blood_sugar'], data['resting_ecg'],
            data['max_heart_rate'], data['exercise_induced_angina'],
            data['st_depression'], data['st_slope'],
            data['major_vessels'], data['thalassemia'],
            risk_percentage, risk_level, datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"[OK] Prediction saved: Risk Level = {risk_level}, Risk % = {risk_percentage}%")
        
    except Exception as e:
        print(f"Error saving prediction: {str(e)}")

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Check models loaded
    if not MODELS:
        print("[WARNING]  WARNING: No models loaded!")
        print("[ERROR] Check that your models are in the 'models/' folder")
    
    # Run Flask app
    print("=" * 60)
    print("HEARTGUARD")
    print("=" * 60)
    print("[SERVER] Server running on http://localhost:5000")
    print("Press CTRL+C to stop")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
