/**
 * HeartGuard AI - Core Logic
 */

// State
let currentStep = 1;
const totalSteps = 3;

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Set date
    const dateOptions = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDate').innerText = new Date().toLocaleDateString('en-US', dateOptions);

    // Disable scroll if intro overlay is visible
    if (!document.getElementById('introOverlay').classList.contains('hidden')) {
        document.body.classList.add('no-scroll');
    }

    // Check auth status
    checkAuthStatus();
});

// Mobile Sidebar Toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    sidebar.classList.toggle('open');
    if (sidebar.classList.contains('open')) {
        overlay.classList.add('active');
    } else {
        overlay.classList.remove('active');
    };
}

// Landing Login Logic
function handleLandingLogin(e) {
    e.preventDefault();
    const user = document.getElementById('landingUser').value;
    const pass = document.getElementById('landingPass').value;

    // Using existing login API
    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
    }).then(r => r.json().then(data => ({ status: r.status, data: data })))
        .then(result => {
            if (result.status === 200) {
                // Success - close intro and update UI
                document.getElementById('introOverlay').classList.add('hidden');
                document.body.classList.remove('no-scroll');
                checkAuthStatus();
            } else {
                // Show actual error message from server
                alert(result.data.error || 'Login failed');
            }
        }).catch(err => {
            console.error('Login error:', err);
            alert('Network error during login. Please try again.');
        });
}

function enterAppAsGuest() {
    document.getElementById('introOverlay').classList.add('hidden');
    document.body.classList.remove('no-scroll');
}

function enterApp() {
    document.getElementById('introOverlay').classList.add('hidden');
    document.body.classList.remove('no-scroll');
}

// Navigation Functions
// Navigation Functions
function switchTab(event, tabId) {
    // 1. Update Navigation Bar State
    document.querySelectorAll('.nav-links li').forEach(li => {
        li.classList.remove('active');
        // Robust way to find the matching nav item
        if (li.getAttribute('onclick').includes(`'${tabId}'`)) {
            li.classList.add('active');
        }
    });

    // 2. Update View Section
    document.querySelectorAll('.view-section').forEach(view => view.classList.remove('active'));
    const targetView = document.getElementById(tabId);
    if (targetView) {
        targetView.classList.add('active');
    }

    // 3. Special Actions
    if (tabId === 'history') loadHistory();

    // 4. Scroll to top
    window.scrollTo(0, 0);
    const mainContent = document.querySelector('.main-content');
    if (mainContent) mainContent.scrollTop = 0;
}

// Stepper Logic
function nextStep(step) {
    // Validate current step
    if (!validateStep(currentStep)) return;

    // Update UI
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById(`step${step}`).classList.add('active');

    // Update Stepper Indicators
    const indicators = document.querySelectorAll('.step');
    indicators.forEach(ind => {
        const s = parseInt(ind.dataset.step);
        if (s < step) ind.classList.add('completed');
        if (s === step) ind.classList.add('active');
        if (s > step) ind.classList.remove('active', 'completed');
    });

    currentStep = step;
}

function prevStep(step) {
    document.getElementById(`step${currentStep}`).classList.remove('active');
    document.getElementById(`step${step}`).classList.add('active');

    const indicators = document.querySelectorAll('.step');
    indicators.forEach(ind => {
        const s = parseInt(ind.dataset.step);
        if (s === step) {
            ind.classList.add('active');
            ind.classList.remove('completed');
        }
        if (s > step) ind.classList.remove('active', 'completed');
    });

    currentStep = step;
}

function validateStep(step) {
    const container = document.getElementById(`step${step}`);
    const inputs = container.querySelectorAll('input, select');
    let valid = true;

    inputs.forEach(input => {
        if (!input.checkValidity()) {
            input.reportValidity();
            valid = false;
        }
    });

    return valid;
}

// Prediction Logic
function submitAssessment() {
    if (!validateStep(3)) return;

    // Collect Data
    const formData = {
        age: parseInt(document.getElementById('age').value),
        sex: parseInt(document.getElementById('sex').value),
        chest_pain_type: parseInt(document.getElementById('chest_pain_type').value),
        resting_blood_pressure: parseInt(document.getElementById('resting_blood_pressure').value),
        cholesterol: parseInt(document.getElementById('cholesterol').value),
        fasting_blood_sugar: parseInt(document.getElementById('fasting_blood_sugar').value),
        resting_ecg: parseInt(document.getElementById('resting_ecg').value),
        max_heart_rate: parseInt(document.getElementById('max_heart_rate').value),
        exercise_induced_angina: parseInt(document.getElementById('exercise_induced_angina').value),
        st_depression: parseFloat(document.getElementById('st_depression').value),
        st_slope: parseInt(document.getElementById('st_slope').value),
        major_vessels: parseInt(document.getElementById('major_vessels').value),
        thalassemia: parseInt(document.getElementById('thalassemia').value)
    };

    // Show Loading
    const loading = document.getElementById('loadingOverlay');
    loading.classList.remove('hidden');

    // API Call
    fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
    })
        .then(res => res.json())
        .then(data => {
            loading.classList.add('hidden');
            if (data.error) {
                alert(data.error);
                return;
            }
            showResults(data, formData);
        })
        .catch(err => {
            loading.classList.add('hidden');
            alert('Error connecting to server.');
            console.error(err);
        });
}

function showResults(data, inputData) {
    // Hide Form, Show Dashboard
    document.getElementById('assessmentForm').classList.add('hidden');
    document.querySelector('.stepper').classList.add('hidden');
    const dashboard = document.getElementById('resultsDashboard');
    dashboard.classList.remove('hidden');

    // Update Metrics
    document.getElementById('resBP').innerText = `${inputData.resting_blood_pressure} mmHg`;
    document.getElementById('resChol').innerText = `${inputData.cholesterol} mg/dl`;
    document.getElementById('resHR').innerText = `${inputData.max_heart_rate} bpm`;

    // Update Gauge
    const percent = data.risk_percentage;
    const circle = document.querySelector('.progress-ring__circle');
    const radius = circle.r.baseVal.value;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percent / 100) * circumference;

    circle.style.strokeDashoffset = offset;
    document.getElementById('riskPercentage').innerText = `${percent}%`;

    // Classes & Level Text
    let riskClass = 'low';
    let levelText = 'Low Risk';
    let color = '#34d399'; // Emerald

    if (percent >= 34) {
        riskClass = 'moderate';
        levelText = 'Moderate Risk';
        color = '#fbbf24'; // Amber
    }
    if (percent >= 67) {
        riskClass = 'high';
        levelText = 'High Risk';
        color = '#f87171'; // Red
    }

    circle.style.stroke = color;
    const riskBadge = document.getElementById('riskLevelText');

    // Clear old classes and add new one
    riskBadge.classList.remove('low', 'moderate', 'high');
    riskBadge.classList.add(riskClass);
    riskBadge.style.backgroundColor = ''; // Clear inline styles
    riskBadge.style.color = '';
    riskBadge.innerText = levelText;

    document.getElementById('riskMessage').innerText = data.message;

    // Precautions List
    const pList = document.getElementById('precautionsList');
    pList.innerHTML = '';
    data.precautions.precautions.forEach(p => {
        const li = document.createElement('li');
        li.innerText = p.replace(/^• /, '');
        pList.appendChild(li);
    });

    // Diet Lists
    const eatList = document.getElementById('dietEatList');
    const avoidList = document.getElementById('dietAvoidList');
    eatList.innerHTML = '';
    avoidList.innerHTML = '';

    data.diet_plan.foods_to_eat.forEach(f => {
        const li = document.createElement('li');
        li.innerHTML = f.replace('[OK] ', '<i class="fa-solid fa-check text-success"></i> ');
        eatList.appendChild(li);
    });

    data.diet_plan.foods_to_avoid.forEach(f => {
        const li = document.createElement('li');
        li.innerHTML = f.replace('[NO] ', '<i class="fa-solid fa-ban text-danger"></i> ');
        avoidList.appendChild(li);
    });
}

function resetAssessment() {
    document.getElementById('resultsDashboard').classList.add('hidden');
    document.getElementById('assessmentForm').classList.remove('hidden');
    document.querySelector('.stepper').classList.remove('hidden');
    document.getElementById('assessmentForm').reset();

    // Reset Stepper
    currentStep = 1;
    document.querySelectorAll('.step').forEach(s => {
        s.classList.remove('active', 'completed');
    });
    document.querySelector('.step[data-step="1"]').classList.add('active');

    // Reset Form Steps
    document.querySelectorAll('.form-step').forEach(fs => fs.classList.remove('active'));
    document.getElementById('step1').classList.add('active');

    // Reset gauge
    document.querySelector('.progress-ring__circle').style.strokeDashoffset = 440;
}

// History Functions
function loadHistory() {
    const tbody = document.getElementById('historyBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">Loading...</td></tr>';

    fetch('/api/history')
        .then(r => r.json())
        .then(data => {
            tbody.innerHTML = '';
            if (!data.history || data.history.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align:center">No records found.</td></tr>';
                return;
            }

            data.history.forEach(row => {
                const tr = document.createElement('tr');
                const rowDate = new Date(row.created_at);

                let badgeClass = 'bg-green-100 text-green-800'; // simplified styles
                let badgeStyle = 'background:#dcfce7; color:#166534; padding:4px 8px; border-radius:12px; font-weight:600; font-size:0.8rem';

                if (row.risk_level === 'MODERATE_RISK') badgeStyle = 'background:#fef3c7; color:#92400e; padding:4px 8px; border-radius:12px; font-weight:600; font-size:0.8rem';
                if (row.risk_level === 'HIGH_RISK') badgeStyle = 'background:#fee2e2; color:#991b1b; padding:4px 8px; border-radius:12px; font-weight:600; font-size:0.8rem';

                tr.innerHTML = `
                <td>${rowDate.toLocaleDateString()}</td>
                <td>${row.age}</td>
                <td>${row.resting_blood_pressure}</td>
                <td>${row.cholesterol}</td>
                <td><span style="${badgeStyle}">${row.risk_level.replace('_', ' ')}</span></td>
                <td><button class="btn btn-secondary" style="padding:4px 8px; font-size:0.8rem" onclick="alert('Details view coming soon!')">View</button></td>
            `;
                // Store raw date for filtering
                tr.dataset.date = rowDate.toISOString().split('T')[0];
                tbody.appendChild(tr);
            });

            // Apply filter if exists
            filterHistory();
        });
}

function filterHistory() {
    const filterValue = document.getElementById('historyDateFilter').value;
    const rows = document.querySelectorAll('#historyBody tr');

    rows.forEach(row => {
        if (!filterValue) {
            row.style.display = '';
            return;
        }

        if (row.dataset.date === filterValue) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}


function clearHistory() {
    if (!confirm('Are you sure you want to delete all history?')) return;

    fetch('/api/clear-history', { method: 'POST' })
        .then(r => {
            if (r.status === 401) {
                alert('Please login first to clear history.');
                openLoginModal();
                return;
            }
            return r.json();
        })
        .then(data => {
            if (data && data.message) {
                loadHistory(); // refresh
            }
        });
}

// Auth Mockup
function openLoginModal() {
    document.getElementById('loginModal').classList.add('active');
    document.body.classList.add('no-scroll');
}

function closeLoginModal() {
    document.getElementById('loginModal').classList.remove('active');
    document.body.classList.remove('no-scroll');
}

function handleLogin(e) {
    e.preventDefault();
    const user = document.getElementById('loginUser').value;
    const pass = document.getElementById('loginPass').value;

    fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password: pass })
    }).then(r => r.json().then(data => ({ status: r.status, data: data })))
        .then(result => {
            if (result.status === 200) {
                // Success - close modal and update UI
                closeLoginModal();
                checkAuthStatus();
            } else {
                // Show actual error message from server
                alert(result.data.error || 'Invalid credentials');
            }
        }).catch(err => {
            console.error('Login error:', err);
            alert('Network error during login. Please try again.');
        });
}

function checkAuthStatus() {
    fetch('/api/auth-status').then(r => r.json()).then(data => {
        const container = document.getElementById('userProfile');
        const welcomeHeader = document.getElementById('welcomeUser');

        if (data.logged_in) {
            // Update Header
            if (welcomeHeader) welcomeHeader.innerText = `Hello, ${data.user}!`;

            // Update Sidebar Profile
            container.innerHTML = `
                <div class="login-card-ref logged-in-state">
                    <div class="user-avatar-circle">
                        ${data.user.charAt(0).toUpperCase()}
                    </div>
                    <div class="user-info-text">
                        <p class="user-name">${data.user}</p>
                        <p class="user-role">Member</p>
                    </div>
                    <button class="btn-logout-icon" onclick="logout()" title="Logout">
                        <i class="fa-solid fa-power-off"></i>
                    </button>
                </div>
            `;
        } else {
            // Reset Header
            if (welcomeHeader) welcomeHeader.innerText = 'Hello, Guest!';

            // Revert Sidebar
            container.innerHTML = `
                <div class="login-card-ref">
                    <p class="login-text-ref">MEMBER LOGIN</p>
                    <button class="login-btn-ref" onclick="openLoginModal()">
                        <i class="fa-solid fa-user"></i> Sign In
                    </button>
                </div>
            `;
        }
    });
}

function logout() {
    fetch('/api/logout', { method: 'POST' }).then(() => {
        checkAuthStatus();
        alert('Logged out');
    });
}

// Close modal on outside click
window.onclick = function (event) {
    const modal = document.getElementById('loginModal');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}