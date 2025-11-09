// Healthcare Analytics - Frontend JavaScript

// Global variables
let currentPatientsPage = 1;
let currentVisitsPage = 1;
let charts = {};
let metadataOptions = null;
let activeFilters = {
    patient_state: '',
    hospital_state: '',
    disease: '',
    specialization: '',
    hospital_id: '',
    visit_type: '',
    start_date: '',
    end_date: ''
};

// Authentication functions
let authToken = null;
let currentUser = null;

// Initialize authentication
function initAuth() {
    authToken = localStorage.getItem('auth_token');
    const userInfo = localStorage.getItem('user_info');
    
    if (userInfo) {
        currentUser = JSON.parse(userInfo);
        updateUIForUser();
    }
    
    // Check if token is valid
    if (authToken) {
        checkAuth();
    } else {
        // Redirect to login if no token
        if (window.location.pathname !== '/login' && !window.location.pathname.includes('login.html')) {
            window.location.href = '/login';
        }
    }
}

// Check authentication status
async function checkAuth() {
    try {
        const response = await fetch('/api/auth/me', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            },
            credentials: 'include'
        });
        
        if (!response.ok) {
            // Token invalid, redirect to login
            logout();
            return;
        }
        
        const user = await response.json();
        currentUser = user;
        localStorage.setItem('user_info', JSON.stringify(user));
        updateUIForUser();
    } catch (error) {
        console.error('Auth check failed:', error);
        logout();
    }
}

// Update UI based on user role
function updateUIForUser() {
    if (!currentUser) return;
    
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.getElementById('logoutBtn');
    
    if (userInfo) {
        const roleDisplay = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
        userInfo.textContent = `${currentUser.full_name || currentUser.username} (${roleDisplay})`;
        userInfo.style.display = 'inline-block';
    }
    
    if (logoutBtn) {
        logoutBtn.style.display = 'flex';
    }
    
    // Hide/show features based on role
    const role = currentUser.role;
    
    // Hide export all for doctors
    if (role === 'doctor') {
        const exportAllBtn = document.querySelector('button[onclick="exportAllData()"]');
        if (exportAllBtn) {
            exportAllBtn.style.display = 'none';
        }
    }
}

// Logout function
async function logout() {
    try {
        if (authToken) {
            await fetch('/api/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                },
                credentials: 'include'
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        authToken = null;
        currentUser = null;
        window.location.href = '/login';
    }
}

// Add auth token to all fetch requests
const originalFetch = window.fetch;
window.fetch = function(...args) {
    const [url, options = {}] = args;
    
    // Skip auth for login endpoint
    if (url.includes('/api/auth/login')) {
        return originalFetch.apply(this, args);
    }
    
    // Add auth token to headers
    if (!options.headers) {
        options.headers = {};
    }
    
    if (authToken) {
        options.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    options.credentials = 'include';
    
    return originalFetch.apply(this, [url, options]);
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initAuth();
    
    // Only load app if authenticated
    if (authToken && currentUser) {
        loadMetadataOptions();
        initializeNavigation();
        initializeFilters();
        loadDashboard();
        loadAnalytics('diseases');
        loadPatients();
        loadVisits();
        loadDropdowns();
        setupForms();
        setupIngestion();
        setupPredictionForm();
    }
});

// Navigation
function initializeNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            
            // Show target section
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.getElementById(target).classList.add('active');
            
            // Load section data
            if (target === 'dashboard') {
                loadDashboard();
            } else if (target === 'analytics') {
                loadAnalytics('diseases');
            } else if (target === 'patients') {
                loadPatients();
            } else if (target === 'visits') {
                loadVisits();
            }
        });
    });
}

// Show loading overlay
function showLoading() {
    document.getElementById('loadingOverlay').classList.add('active');
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('active');
}

// Toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// API calls
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`/api/${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call error:', error);
        showToast('Error: ' + error.message, 'error');
        throw error;
    }
}

// Dashboard
async function loadDashboard() {
    showLoading();
    try {
        const stats = await apiCall('dashboard/stats');
        
        // Update stats cards
        document.getElementById('total-patients').textContent = formatNumber(stats.total_patients);
        document.getElementById('total-hospitals').textContent = formatNumber(stats.total_hospitals);
        document.getElementById('total-doctors').textContent = formatNumber(stats.total_doctors);
        document.getElementById('total-visits').textContent = formatNumber(stats.total_visits);
        document.getElementById('total-revenue').textContent = formatCurrency(stats.total_revenue);
        document.getElementById('avg-visit-cost').textContent = formatCurrency(stats.avg_visit_cost);
        
        // Charts
        createVisitsTypeChart(stats.visits_by_type);
        createPaymentMethodChart(stats.revenue_by_payment);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    } finally {
        hideLoading();
    }
}

// Charts
function createVisitsTypeChart(data) {
    const ctx = document.getElementById('visitsTypeChart').getContext('2d');
    
    if (charts.visitsType) {
        charts.visitsType.destroy();
    }
    
    charts.visitsType = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data),
            datasets: [{
                data: Object.values(data),
                backgroundColor: [
                    '#667eea',
                    '#f093fb',
                    '#4facfe',
                    '#43e97b'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function createPaymentMethodChart(data) {
    const ctx = document.getElementById('paymentMethodChart').getContext('2d');
    
    if (charts.paymentMethod) {
        charts.paymentMethod.destroy();
    }
    
    charts.paymentMethod = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(data),
            datasets: [{
                label: 'Revenue (₹)',
                data: Object.values(data),
                backgroundColor: '#667eea'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}



// Analytics
function showAnalyticsTab(tab, evt) {
    const eventObj = evt || window.event;
    document.querySelectorAll('.analytics-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (eventObj && eventObj.target) {
        eventObj.target.classList.add('active');
    } else {
        const button = Array.from(document.querySelectorAll('.analytics-tabs .tab-btn'))
            .find(btn => btn.textContent.trim().toLowerCase() === tab);
        if (button) button.classList.add('active');
    }

    document.querySelectorAll('.analytics-content').forEach(content => {
        content.classList.remove('active');
    });
    const section = document.getElementById(`${tab}-analytics`);
    if (section) section.classList.add('active');

    if (tab !== 'predictions') {
        loadAnalytics(tab);
    }
}

async function loadAnalytics(type) {
    showLoading();
    try {
        const query = buildQueryParams();
        switch(type) {
            case 'diseases':
                await loadDiseasesAnalytics(query);
                break;
            case 'hospitals':
                await loadHospitalsAnalytics(query);
                break;
            case 'geographic':
                await loadGeographicAnalytics(query);
                break;
            case 'temporal':
                await loadTemporalAnalytics(query);
                break;
            case 'specializations':
                await loadSpecializationsAnalytics(query);
                break;
            case 'predictions':
                break;
        }
    } catch (error) {
        console.error(`Error loading ${type} analytics:`, error);
    } finally {
        hideLoading();
    }
}

async function loadDiseasesAnalytics(query = '') {
    // Get category filter
    const categoryFilter = document.getElementById('filterDiseaseCategory');
    const category = categoryFilter ? categoryFilter.value : '';
    const noteElement = document.getElementById('cancerFilterNote');
    
    // Update note for cancer filter
    if (category === 'Oncology' && noteElement) {
        noteElement.textContent = '(Showing Top 3 Cancers)';
        noteElement.style.color = '#e74c3c';
    } else if (noteElement) {
        noteElement.textContent = '';
    }
    
    let qs = query ? `?${query}` : '';
    if (category) {
        qs += qs ? `&category=${encodeURIComponent(category)}` : `?category=${encodeURIComponent(category)}`;
    }
    
    const diseases = await apiCall(`analytics/diseases${qs}`);
    
    // Chart - show top 3 for Oncology, top 15 for others
    const chartData = category === 'Oncology' ? diseases.slice(0, 3) : diseases.slice(0, 15);
    const ctx = document.getElementById('diseasesChart').getContext('2d');
    if (charts.diseases) {
        charts.diseases.destroy();
    }
    
    // Use consistent color for all diseases
    charts.diseases = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.map(d => d.name),
            datasets: [{
                label: 'Occurrences',
                data: chartData.map(d => d.occurrence),
                backgroundColor: '#667eea' // Consistent blue for all diseases
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
    
    // Table - show only top 3 for Oncology, all others for general view
    const tableData = category === 'Oncology' ? diseases.slice(0, 3) : diseases;
    const tbody = document.getElementById('diseasesTableBody');
    tbody.innerHTML = tableData.map(d => {
        return `
        <tr>
            <td><strong>${d.name}</strong></td>
            <td>${d.category}</td>
            <td><span class="badge badge-${d.severity.toLowerCase()}">${d.severity}</span></td>
            <td>${formatNumber(d.occurrence)}</td>
            <td>${formatCurrency(d.avg_cost)}</td>
        </tr>
    `;
    }).join('');
}

async function loadHospitalsAnalytics(query = '') {
    const qs = query ? `?${query}` : '';
    const hospitals = await apiCall(`analytics/hospitals${qs}`);
    
    // Chart
    const ctx = document.getElementById('hospitalsChart').getContext('2d');
    if (charts.hospitals) {
        charts.hospitals.destroy();
    }
    
    const top10 = hospitals.slice(0, 10);
    charts.hospitals = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: top10.map(h => h.name.substring(0, 20)),
            datasets: [{
                label: 'Revenue (₹)',
                data: top10.map(h => h.total_revenue),
                backgroundColor: '#f093fb'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + formatNumber(value);
                        }
                    }
                }
            }
        }
    });
    
    // Table
    const tbody = document.getElementById('hospitalsTableBody');
    tbody.innerHTML = hospitals.map(h => `
        <tr>
            <td>${h.name}</td>
            <td>${h.type}</td>
            <td>${h.city}</td>
            <td>${formatNumber(h.patient_count)}</td>
            <td>${formatNumber(h.visit_count)}</td>
            <td>${formatCurrency(h.total_revenue)}</td>
        </tr>
    `).join('');
}

async function loadGeographicAnalytics(query = '') {
    const qs = query ? `?${query}` : '';
    const geo = await apiCall(`analytics/geographic${qs}`);
    
    // State chart
    const stateCtx = document.getElementById('stateChart').getContext('2d');
    if (charts.state) {
        charts.state.destroy();
    }
    
    charts.state = new Chart(stateCtx, {
        type: 'pie',
        data: {
            labels: geo.states.map(s => s.state),
            datasets: [{
                data: geo.states.map(s => s.visit_count),
                backgroundColor: generateColors(geo.states.length)
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
    
    // City chart
    const cityCtx = document.getElementById('cityChart').getContext('2d');
    if (charts.city) {
        charts.city.destroy();
    }
    
    const top10Cities = geo.cities.slice(0, 10);
    charts.city = new Chart(cityCtx, {
        type: 'bar',
        data: {
            labels: top10Cities.map(c => c.city),
            datasets: [{
                label: 'Visits',
                data: top10Cities.map(c => c.visit_count),
                backgroundColor: '#4facfe'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            scales: {
                x: {
                    beginAtZero: true
                }
            }
        }
    });
}

async function loadTemporalAnalytics(query = '') {
    const qs = query ? `?${query}` : '';
    const temporal = await apiCall(`analytics/temporal${qs}`);
    
    // Monthly chart
    const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    if (charts.monthly) {
        charts.monthly.destroy();
    }
    
    charts.monthly = new Chart(monthlyCtx, {
        type: 'line',
        data: {
            labels: temporal.monthly.map(m => `${m.month_name} ${m.year}`),
            datasets: [{
                label: 'Visits',
                data: temporal.monthly.map(m => m.visit_count),
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }, {
                label: 'Revenue (₹)',
                data: temporal.monthly.map(m => m.revenue),
                borderColor: '#f093fb',
                backgroundColor: 'rgba(240, 147, 251, 0.1)',
                tension: 0.4,
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + formatNumber(value);
                        }
                    }
                }
            }
        }
    });
    
    // Quarterly chart
    const quarterlyCtx = document.getElementById('quarterlyChart').getContext('2d');
    if (charts.quarterly) {
        charts.quarterly.destroy();
    }
    
    charts.quarterly = new Chart(quarterlyCtx, {
        type: 'bar',
        data: {
            labels: temporal.quarterly.map(q => `Q${q.quarter} ${q.year}`),
            datasets: [{
                label: 'Visits',
                data: temporal.quarterly.map(q => q.visit_count),
                backgroundColor: '#43e97b'
            }, {
                label: 'Revenue (₹)',
                data: temporal.quarterly.map(q => q.revenue),
                backgroundColor: '#4facfe',
                yAxisID: 'y1'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '₹' + formatNumber(value);
                        }
                    }
                }
            }
        }
    });
}

async function loadSpecializationsAnalytics(query = '') {
    const qs = query ? `?${query}` : '';
    const specializations = await apiCall(`analytics/specializations${qs}`);
    
    const ctx = document.getElementById('specializationsChart').getContext('2d');
    if (charts.specializations) {
        charts.specializations.destroy();
    }
    
    charts.specializations = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: specializations.map(s => s.specialization),
            datasets: [{
                label: 'Visits',
                data: specializations.map(s => s.visit_count),
                backgroundColor: '#667eea'
            }, {
                label: 'Doctors',
                data: specializations.map(s => s.doctor_count),
                backgroundColor: '#f093fb'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    // Load the heatmap data
    
}

// Patients
async function loadPatients(page = 1) {
    showLoading();
    try {
        const data = await apiCall(`patients?page=${page}&per_page=20`);
        currentPatientsPage = page;
        
        const tbody = document.getElementById('patientsTableBody');
        tbody.innerHTML = data.patients.map(p => `
            <tr>
                <td>${p.patient_id}</td>
                <td>${p.patient_name}</td>
                <td>${p.age}</td>
                <td>${p.gender}</td>
                <td>${p.city || '-'}</td>
                <td>${p.state || '-'}</td>
                <td>${p.phone || '-'}</td>
                <td>${p.email || '-'}</td>
            </tr>
        `).join('');
        
        // Pagination
        updatePagination('patientsPagination', page, data.pages, loadPatients);
    } catch (error) {
        console.error('Error loading patients:', error);
    } finally {
        hideLoading();
    }
}

// Visits
async function loadVisits(page = 1) {
    showLoading();
    try {
        const query = buildQueryParams({ page, per_page: 20 });
        const data = await apiCall(`visits?${query}`);
        currentVisitsPage = page;
        
        const tbody = document.getElementById('visitsTableBody');
        tbody.innerHTML = data.visits.map(v => `
            <tr>
                <td>${v.visit_id}</td>
                <td>${v.patient_name}</td>
                <td>${v.doctor_name}</td>
                <td>${v.hospital_name}</td>
                <td>${v.disease_name || '-'}</td>
                <td>${v.visit_type}</td>
                <td>${v.visit_date}</td>
                <td>${formatCurrency(v.total_cost)}</td>
                <td>${v.payment_method}</td>
                <td>${v.status}</td>
            </tr>
        `).join('');
        
        // Pagination
        updatePagination('visitsPagination', page, data.pages, loadVisits);
    } catch (error) {
        console.error('Error loading visits:', error);
    } finally {
        hideLoading();
    }
}

// Data Entry
function showDataEntryTab(tab, evt) {
    const eventObj = evt || window.event;
    document.querySelectorAll('.data-entry-tabs .tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    if (eventObj && eventObj.target) {
        eventObj.target.classList.add('active');
    }

    document.querySelectorAll('.data-entry-content').forEach(content => {
        content.classList.remove('active');
    });
    const section = document.getElementById(`${tab}-entry`);
    if (section) section.classList.add('active');
}

async function loadDropdowns() {
    try {
        const [patients, doctors, hospitals, diseases] = await Promise.all([
            apiCall('patients?per_page=1000'),
            apiCall('doctors'),
            apiCall('hospitals'),
            apiCall('diseases')
        ]);
        
        // Patient dropdown
        const patientSelect = document.getElementById('visitPatientSelect');
        patientSelect.innerHTML = '<option value="">Select Patient</option>' +
            patients.patients.map(p => 
                `<option value="${p.patient_id}">${p.patient_name} (ID: ${p.patient_id})</option>`
            ).join('');
        
        // Doctor dropdown
        const doctorSelect = document.getElementById('visitDoctorSelect');
        doctorSelect.innerHTML = '<option value="">Select Doctor</option>' +
            doctors.map(d => 
                `<option value="${d.doctor_id}">${d.doctor_name} - ${d.specialization}</option>`
            ).join('');
        
        // Hospital dropdown
        const hospitalSelect = document.getElementById('visitHospitalSelect');
        hospitalSelect.innerHTML = '<option value="">Select Hospital</option>' +
            hospitals.map(h => 
                `<option value="${h.hospital_id}">${h.hospital_name} - ${h.city}</option>`
            ).join('');
        
        // Disease dropdown
        const diseaseSelect = document.getElementById('visitDiseaseSelect');
        diseaseSelect.innerHTML = '<option value="">None</option>' +
            diseases.map(d => 
                `<option value="${d.disease_id}">${d.disease_name}</option>`
            ).join('');
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

function setupForms() {
    // Patient form
    document.getElementById('patientForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        showLoading();
        try {
            await apiCall('patients', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('Patient added successfully!');
            this.reset();
            loadPatients();
        } catch (error) {
            showToast('Error adding patient', 'error');
        } finally {
            hideLoading();
        }
    });
    
    // Visit form
    document.getElementById('visitForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const data = Object.fromEntries(formData);
        
        // Convert empty strings to null
        Object.keys(data).forEach(key => {
            if (data[key] === '') {
                data[key] = null;
            }
        });
        
        // Convert numeric fields
        if (data.total_cost) data.total_cost = parseFloat(data.total_cost);
        if (data.visit_duration_minutes) data.visit_duration_minutes = parseInt(data.visit_duration_minutes);
        if (data.medication_quantity) data.medication_quantity = parseInt(data.medication_quantity);
        
        showLoading();
        try {
            await apiCall('visits', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            showToast('Visit added successfully!');
            this.reset();
            loadVisits();
            loadDashboard();
        } catch (error) {
            showToast('Error adding visit', 'error');
        } finally {
            hideLoading();
        }
    });
}

// Pagination
function updatePagination(containerId, currentPage, totalPages, callback) {
    const container = document.getElementById(containerId);
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    if (currentPage > 1) {
        html += `<button onclick="${callback.name}(${currentPage - 1})">Previous</button>`;
    }
    
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="${i === currentPage ? 'active' : ''}" onclick="${callback.name}(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += `<button disabled>...</button>`;
        }
    }
    
    if (currentPage < totalPages) {
        html += `<button onclick="${callback.name}(${currentPage + 1})">Next</button>`;
    }
    
    container.innerHTML = html;
}

// Utility functions
function formatNumber(num) {
    return new Intl.NumberFormat('en-IN').format(num);
}

function formatCurrency(num) {
    return '₹' + formatNumber(Math.round(num));
}

function generateColors(count) {
    const colors = [
        '#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a',
        '#fee140', '#30cfd0', '#764ba2', '#f5576c', '#38f9d7'
    ];
    const result = [];
    for (let i = 0; i < count; i++) {
        result.push(colors[i % colors.length]);
    }
    return result;
}

function loadMetadataOptions() {
    apiCall('metadata/options')
        .then(data => {
            metadataOptions = data;
            populateFilterOptions();
        })
        .catch(error => console.error('Metadata load error:', error));
}

function populateFilterOptions() {
    if (!metadataOptions) return;

    const stateSelects = [
        document.getElementById('filterPatientState'),
        document.getElementById('filterHospitalState'),
        document.getElementById('predictionPatientState'),
        document.getElementById('predictionHospitalState')
    ];

    stateSelects.forEach(select => {
        if (!select) return;
        const options = metadataOptions.patient_states || [];
        if (select.id === 'filterHospitalState' || select.id === 'predictionHospitalState') {
            select.innerHTML = '<option value="">All</option>';
            (metadataOptions.hospital_states || []).forEach(state => {
                select.innerHTML += `<option value="${state}">${state}</option>`;
            });
        } else {
            select.innerHTML = '<option value="">All</option>';
            options.forEach(state => {
                select.innerHTML += `<option value="${state}">${state}</option>`;
            });
        }
    });

    const diseaseSelect = document.getElementById('filterDisease');
    if (diseaseSelect) {
        diseaseSelect.innerHTML = '<option value="">All</option>';
        (metadataOptions.diseases || []).forEach(disease => {
            diseaseSelect.innerHTML += `<option value="${disease}">${disease}</option>`;
        });
    }
    
    // Add event listener for disease category filter
    const diseaseCategoryFilter = document.getElementById('filterDiseaseCategory');
    if (diseaseCategoryFilter) {
        diseaseCategoryFilter.addEventListener('change', () => {
            loadDiseasesAnalytics();
        });
    }

    const specializationSelects = [
        document.getElementById('filterSpecialization'),
        document.getElementById('predictionSpecialization')
    ];
    specializationSelects.forEach(select => {
        if (!select) return;
        select.innerHTML = select.id === 'filterSpecialization' ? '<option value="">All</option>' : '';
        (metadataOptions.specializations || []).forEach(spec => {
            select.innerHTML += `<option value="${spec}">${spec}</option>`;
        });
    });

    const hospitalSelect = document.getElementById('filterHospital');
    if (hospitalSelect) {
        hospitalSelect.innerHTML = '<option value="">All</option>';
        (metadataOptions.hospitals || []).forEach(hospital => {
            hospitalSelect.innerHTML += `<option value="${hospital.hospital_id}">${hospital.hospital_name}</option>`;
        });
    }
}

function initializeFilters() {
    document.querySelectorAll('.filters-panel select, .filters-panel input[type="date"]').forEach(elem => {
        elem.addEventListener('change', () => {
            const key = elem.id.replace('filter', '').replace(/^[A-Z]/, c => c.toLowerCase());
            switch (elem.id) {
                case 'filterPatientState':
                    activeFilters.patient_state = elem.value;
                    break;
                case 'filterHospitalState':
                    activeFilters.hospital_state = elem.value;
                    break;
                case 'filterDisease':
                    activeFilters.disease = elem.value;
                    break;
                case 'filterSpecialization':
                    activeFilters.specialization = elem.value;
                    break;
                case 'filterHospital':
                    activeFilters.hospital_id = elem.value;
                    break;
                case 'filterVisitType':
                    activeFilters.visit_type = elem.value;
                    break;
                case 'filterStartDate':
                    activeFilters.start_date = elem.value;
                    break;
                case 'filterEndDate':
                    activeFilters.end_date = elem.value;
                    break;
            }
        });
    });
}

function applyFilters() {
    loadAnalytics('diseases');
    loadAnalytics('hospitals');
    loadAnalytics('geographic');
    loadAnalytics('temporal');
    loadAnalytics('specializations');
    loadVisits();
}

function resetFilters() {
    activeFilters = {
        patient_state: '',
        hospital_state: '',
        disease: '',
        specialization: '',
        hospital_id: '',
        visit_type: '',
        start_date: '',
        end_date: ''
    };
    document.querySelectorAll('.filters-panel select').forEach(el => el.value = '');
    document.querySelectorAll('.filters-panel input[type="date"]').forEach(el => el.value = '');
    applyFilters();
}

function buildQueryParams(params = {}) {
    const query = new URLSearchParams();
    Object.entries(activeFilters).forEach(([key, value]) => {
        if (value) query.append(key, value);
    });
    Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
            query.append(key, value);
        }
    });
    return query.toString();
}

function exportCurrentView() {
    const activeSection = document.querySelector('.analytics-tabs .tab-btn.active');
    if (!activeSection) return;
    const sectionId = activeSection.textContent.trim().toLowerCase();
    let endpoint = '';
    switch (sectionId) {
        case 'diseases':
            endpoint = 'analytics/diseases?format=csv';
            break;
        case 'hospitals':
            endpoint = 'analytics/hospitals?format=csv';
            break;
        case 'geographic':
            endpoint = 'analytics/geographic?format=csv';
            break;
        case 'temporal':
            endpoint = 'analytics/temporal?format=csv';
            break;
        case 'specializations':
            endpoint = 'analytics/specializations?format=csv';
            break;
        default:
            showToast('Export not available for this section', 'error');
            return;
    }
    const query = buildQueryParams();
    window.open(`/api/${endpoint}${query ? '&' + query : ''}`, '_blank');
}

function setupIngestion() {
    const form = document.getElementById('ingestionForm');
    if (!form) return;
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const fileInput = document.getElementById('ingestionFile');
        if (!fileInput.files.length) {
            showToast('Please select a file to upload', 'error');
            return;
        }
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        showLoading();
        try {
            const response = await fetch('/api/ingestion/patient-visits', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Upload failed');
            showToast('Ingestion job submitted successfully');
            form.reset();
            loadIngestionJobs();
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            hideLoading();
        }
    });
    loadIngestionJobs();
}

async function loadIngestionJobs() {
    try {
        const jobs = await apiCall('ingestion/jobs');
        const tbody = document.getElementById('ingestionJobsBody');
        if (!tbody) return;
        tbody.innerHTML = jobs.map(job => `
            <tr>
                <td>${job.job_id}</td>
                <td>${job.source_file || '-'}</td>
                <td>${job.total_records}</td>
                <td>${job.success_count}</td>
                <td>${job.failure_count}</td>
                <td>${job.status}</td>
                <td>${formatDateTime(job.started_at)}</td>
                <td>${formatDateTime(job.completed_at)}</td>
                <td><button class="btn-link" onclick="loadIngestionErrors(${job.job_id})">View</button></td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load ingestion jobs:', error);
    }
}

async function loadIngestionErrors(jobId) {
    try {
        const errors = await apiCall(`ingestion/jobs/${jobId}/errors`);
        const container = document.getElementById('ingestionErrorsContainer');
        const tbody = document.getElementById('ingestionErrorsBody');
        if (!container || !tbody) return;
        container.style.display = errors.length ? 'block' : 'none';
        tbody.innerHTML = errors.map(error => `
            <tr>
                <td>${error.staging_id}</td>
                <td>${error.error_message || '-'}</td>
                <td><pre>${JSON.stringify(error.raw_payload, null, 2)}</pre></td>
                <td>${formatDateTime(error.processed_at)}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load ingestion errors:', error);
    }
}

function formatDateTime(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString('en-IN');
}

function downloadTemplate(event) {
    event.preventDefault();
    window.open('/api/ingestion/template', '_blank');
}

function setupPredictionForm() {
    const form = document.getElementById('predictionForm');
    if (!form) return;
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        const formData = new FormData(form);
        const payload = Object.fromEntries(formData.entries());
        payload.age = parseInt(payload.age, 10);
        payload.consultation_fee = parseFloat(payload.consultation_fee);
        payload.visit_duration_minutes = parseInt(payload.visit_duration_minutes, 10);

        showLoading();
        try {
            const response = await fetch('/api/ml/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.error || 'Prediction failed');
            const result = document.getElementById('predictionResult');
            result.innerHTML = `
                <div class="prediction-card ${data.risk_level === 'High' ? 'high' : 'low'}">
                    <h4>Risk Level: ${data.risk_level}</h4>
                    <p>Probability of high cost: ${(data.probability * 100).toFixed(2)}%</p>
                </div>
            `;
        } catch (error) {
            showToast(error.message, 'error');
        } finally {
            hideLoading();
        }
    });
}

async function trainModel() {
    const button = document.getElementById('trainModelBtn');
    if (!button) return;
    button.disabled = true;
    showLoading();
    try {
        const response = await fetch('/api/ml/train', { method: 'POST' });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Training failed');
        const metrics = data.metrics || {};
        const metricsContainer = document.getElementById('modelMetrics');
        metricsContainer.innerHTML = `
            <div class="metrics-grid">
                <div class="metric">
                    <span class="label">Precision</span>
                    <span class="value">${(metrics.precision * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span class="label">Recall</span>
                    <span class="value">${(metrics.recall * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span class="label">F1 Score</span>
                    <span class="value">${(metrics.f1_score * 100).toFixed(1)}%</span>
                </div>
                <div class="metric">
                    <span class="label">Cost Threshold</span>
                    <span class="value">₹${formatNumber(metrics.threshold || 0)}</span>
                </div>
            </div>
        `;
        showToast('Model trained successfully');
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        hideLoading();
        button.disabled = false;
    }
}

// Refresh Data
function refreshData() {
    const refreshBtn = event.target.closest('button');
    const icon = refreshBtn.querySelector('i');
    
    // Add spinning animation
    icon.classList.add('fa-spin');
    refreshBtn.disabled = true;
    
    // Reload current section
    const activeSection = document.querySelector('.section.active');
    if (activeSection) {
        const sectionId = activeSection.id;
        if (sectionId === 'dashboard') {
            loadDashboard();
        } else if (sectionId === 'analytics') {
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) {
                const tabType = activeTab.dataset.tab;
                loadAnalytics(tabType);
            }
        } else if (sectionId === 'patients') {
            loadPatients();
        } else if (sectionId === 'visits') {
            loadVisits();
        }
    }
    
    // Remove spinning animation after a delay
    setTimeout(() => {
        icon.classList.remove('fa-spin');
        refreshBtn.disabled = false;
        showToast('Data refreshed successfully', 'success');
    }, 1000);
}

// Export All Data (ignoring filters)
async function exportAllData() {
    try {
        showLoading();
        const response = await fetch('/api/visits/export?all=true');
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `all_patient_visits_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        showToast('All data exported successfully', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showToast('Failed to export data: ' + error.message, 'error');
    } finally {
        hideLoading();
    }
}

// Export Chart as Image
function exportChart(canvasId, filename) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        showToast('Chart not found', 'error');
        return;
    }
    
    // Try to find Chart.js instance by matching canvas ID
    let chartInstance = null;
    
    // Map canvas IDs to chart keys
    const chartMap = {
        'diseasesChart': 'diseases',
        'hospitalsChart': 'hospitals',
        'stateChart': 'state',
        'cityChart': 'city',
        'monthlyChart': 'monthly',
        'quarterlyChart': 'quarterly',
        'specializationsChart': 'specializations',
        'visitsTypeChart': 'visitstype',
        'paymentMethodChart': 'paymentmethod'
    };
    
    const chartKey = chartMap[canvasId];
    if (chartKey && charts[chartKey]) {
        chartInstance = charts[chartKey];
    }
    
    // Export using Chart.js if available, otherwise use canvas directly
    let url;
    if (chartInstance && typeof chartInstance.toBase64Image === 'function') {
        url = chartInstance.toBase64Image('image/png', 1);
    } else {
        url = canvas.toDataURL('image/png');
    }
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${new Date().toISOString().split('T')[0]}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    showToast('Chart exported successfully', 'success');
}

