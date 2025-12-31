// DOM Elements
const queryInput = document.getElementById('queryInput');
const submitBtn = document.getElementById('submitBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const loadingStage = document.getElementById('loadingStage');
const resultsContainer = document.getElementById('resultsContainer');
const errorContainer = document.getElementById('errorContainer');
const errorMessage = document.getElementById('errorMessage');
const themeToggle = document.getElementById('themeToggle');
const refreshHealth = document.getElementById('refreshHealth');
const modelDashboard = document.getElementById('modelDashboard');

const stage1Content = document.getElementById('stage1Content');
const stage2Content = document.getElementById('stage2Content');
const stage3Content = document.getElementById('stage3Content');

// View containers
const sequentialView = document.getElementById('sequentialView');
const comparisonView = document.getElementById('comparisonView');
const tabbedView = document.getElementById('tabbedView');
const comparisonGrid = document.getElementById('comparisonGrid');
const tabNavigation = document.getElementById('tabNavigation');
const tabContent = document.getElementById('tabContent');

// State
let currentTheme = localStorage.getItem('theme') || 'dark';
let currentView = 'sequential';
let deliberationData = {
    stage1: [],
    stage2: [],
    stage3: null
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeTheme();
    loadHealthStatus();
    setupEventListeners();
    // Auto-refresh health every 30 seconds
    setInterval(loadHealthStatus, 30000);
});

// Theme Management
function initializeTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon();
}

function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', currentTheme);
    localStorage.setItem('theme', currentTheme);
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = themeToggle.querySelector('.theme-icon');
    icon.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
}

// Event Listeners
function setupEventListeners() {
    submitBtn.addEventListener('click', handleSubmit);
    themeToggle.addEventListener('click', toggleTheme);
    refreshHealth.addEventListener('click', () => {
        refreshHealth.style.animation = 'spin 0.5s ease-out';
        loadHealthStatus();
        setTimeout(() => {
            refreshHealth.style.animation = '';
        }, 500);
    });
    
    queryInput.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'Enter') {
            handleSubmit();
        }
    });
    
    // View mode switcher
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.dataset.view));
    });
    
    // Collapse buttons
    document.querySelectorAll('.collapse-btn').forEach(btn => {
        btn.addEventListener('click', () => toggleCollapse(btn));
    });
}

// Health Status
async function loadHealthStatus() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        displayHealthDashboard(data);
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

function displayHealthDashboard(healthData) {
    modelDashboard.innerHTML = '';
    
    Object.entries(healthData).forEach(([model, info]) => {
        const card = createModelCard(model, info);
        modelDashboard.appendChild(card);
    });
}

function createModelCard(model, info) {
    const card = document.createElement('div');
    card.className = 'model-card';
    card.style.setProperty('--model-color', info.color || '#00e5ff');
    
    const statusClass = `status-${info.status}`;
    const metrics = info.metrics || {};
    
    card.innerHTML = `
        <div class="model-card-header">
            <span class="model-name">${info.name || model}</span>
            <span class="status-badge ${statusClass}">${info.status}</span>
        </div>
        <div class="model-metrics">
            <div class="metric-item">
                <span class="metric-label">Avg Latency</span>
                <span class="metric-value">${metrics.avg_latency ? metrics.avg_latency.toFixed(2) + 's' : 'N/A'}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Requests</span>
                <span class="metric-value">${metrics.total_requests || 0}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Tokens</span>
                <span class="metric-value">${metrics.tokens_generated || 0}</span>
            </div>
            <div class="metric-item">
                <span class="metric-label">Errors</span>
                <span class="metric-value">${metrics.errors || 0}</span>
            </div>
        </div>
    `;
    
    return card;
}

// Main Submit Handler
async function handleSubmit() {
    const query = queryInput.value.trim();
    
    if (!query) {
        showError('Please enter a question');
        return;
    }
    
    // Reset
    hideError();
    resultsContainer.style.display = 'none';
    loadingIndicator.style.display = 'block';
    submitBtn.disabled = true;
    
    // Clear previous results
    stage1Content.innerHTML = '';
    stage2Content.innerHTML = '';
    stage3Content.innerHTML = '';
    comparisonGrid.innerHTML = '';
    tabNavigation.innerHTML = '';
    tabContent.innerHTML = '';
    
    deliberationData = { stage1: [], stage2: [], stage3: null };
    
    try {
        // Stage 1
        loadingStage.textContent = 'Stage 1: Collecting initial opinions...';
        await runStage('/api/council/stage1', query, 1);
        
        // Stage 2
        loadingStage.textContent = 'Stage 2: Reviewing and critiquing...';
        await runStage('/api/council/stage2', query, 2);
        
        // Stage 3
        loadingStage.textContent = 'Stage 3: Final synthesis...';
        await runStage('/api/council/stage3', query, 3);
        
        resultsContainer.style.display = 'block';
        loadingIndicator.style.display = 'none';
        
        // Refresh health after deliberation
        loadHealthStatus();
        
        // Switch to current view
        switchView(currentView);
        
        setTimeout(() => {
            resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 300);
        
    } catch (error) {
        console.error('Error:', error);
        showError(`Error during deliberation: ${error.message}`);
        loadingIndicator.style.display = 'none';
    } finally {
        submitBtn.disabled = false;
    }
}

// Run Stage
async function runStage(endpoint, query, stageNum) {
    const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
    }
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.error || 'Unknown error');
    }
    
    // Store data
    if (stageNum === 1) {
        deliberationData.stage1 = result.data;
        displayStage1(result.data);
    } else if (stageNum === 2) {
        deliberationData.stage2 = result.data;
        displayStage2(result.data);
    } else if (stageNum === 3) {
        deliberationData.stage3 = result.data;
        displayStage3(result.data);
    }
    
    // Show container after first stage
    if (stageNum === 1) {
        resultsContainer.style.display = 'block';
    }
}

// Display Functions
function displayStage1(data) {
    data.forEach((response, index) => {
        const card = createResponseCard(response, index);
        stage1Content.appendChild(card);
    });
}

function displayStage2(data) {
    data.forEach((review, index) => {
        const card = createReviewCard(review, index);
        stage2Content.appendChild(card);
    });
}

function displayStage3(data) {
    const card = createFinalCard(data);
    stage3Content.appendChild(card);
}

// Create Cards
function createResponseCard(response, index) {
    const card = document.createElement('div');
    card.className = 'response-card';
    card.style.setProperty('--card-color', response.color);
    card.style.animationDelay = `${index * 0.1}s`;
    
    const initial = response.author.charAt(0).toUpperCase();
    const time = formatTime(response.timestamp);
    
    card.innerHTML = `
        <div class="response-header">
            <div class="agent-icon" style="background: ${response.color}">${initial}</div>
            <span class="agent-name" style="color: ${response.color}">${escapeHtml(response.author)}</span>
            <div class="response-meta">
                <span class="meta-badge">⏱ ${response.latency}s</span>
                <span class="meta-badge">🎯 ${response.tokens} tokens</span>
                <span class="meta-badge">⏰ ${time}</span>
            </div>
        </div>
        <div class="response-content">${escapeHtml(response.content)}</div>
    `;
    
    return card;
}

function createReviewCard(review, index) {
    const card = document.createElement('div');
    card.className = 'response-card';
    card.style.setProperty('--card-color', review.color);
    card.style.animationDelay = `${index * 0.1}s`;
    
    const initial = review.reviewer.charAt(0).toUpperCase();
    const time = formatTime(review.timestamp);
    
    card.innerHTML = `
        <div class="response-header">
            <div class="agent-icon" style="background: ${review.color}">${initial}</div>
            <span class="agent-name" style="color: ${review.color}">${escapeHtml(review.reviewer)}</span>
            <div class="response-meta">
                <span class="meta-badge">⏱ ${review.latency}s</span>
                <span class="meta-badge">🎯 ${review.tokens} tokens</span>
                <span class="meta-badge">⏰ ${time}</span>
            </div>
        </div>
        <div class="response-content">${escapeHtml(review.review)}</div>
    `;
    
    return card;
}

function createFinalCard(data) {
    const card = document.createElement('div');
    card.className = 'response-card final-answer';
    card.style.setProperty('--card-color', data.color);
    
    const initial = data.chairman.charAt(0).toUpperCase();
    const time = formatTime(data.timestamp);
    
    card.innerHTML = `
        <div class="response-header">
            <div class="agent-icon" style="background: ${data.color}">${initial}</div>
            <span class="agent-name" style="color: ${data.color}">${escapeHtml(data.chairman)}</span>
            <div class="response-meta">
                <span class="meta-badge">⏱ ${data.latency}s</span>
                <span class="meta-badge">🎯 ${data.tokens} tokens</span>
                <span class="meta-badge">⏰ ${time}</span>
            </div>
        </div>
        <div class="response-content">${escapeHtml(data.final_answer)}</div>
    `;
    
    return card;
}

// View Switching
function switchView(view) {
    currentView = view;
    
    // Update buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });
    
    // Hide all views
    sequentialView.classList.remove('active');
    comparisonView.classList.remove('active');
    tabbedView.classList.remove('active');
    
    // Show selected view
    if (view === 'sequential') {
        sequentialView.classList.add('active');
    } else if (view === 'comparison') {
        comparisonView.classList.add('active');
        buildComparisonView();
    } else if (view === 'tabbed') {
        tabbedView.classList.add('active');
        buildTabbedView();
    }
}

// Comparison View
function buildComparisonView() {
    comparisonGrid.innerHTML = '';
    
    // Stage 1 comparison
    if (deliberationData.stage1.length > 0) {
        deliberationData.stage1.forEach((response, index) => {
            const card = createResponseCard(response, index);
            comparisonGrid.appendChild(card);
        });
    }
}

// Tabbed View
function buildTabbedView() {
    tabNavigation.innerHTML = '';
    tabContent.innerHTML = '';
    
    // Create tabs for each agent
    const allResponses = [
        ...deliberationData.stage1,
        ...deliberationData.stage2
    ];
    
    const agentMap = new Map();
    
    allResponses.forEach(item => {
        const name = item.author || item.reviewer;
        if (!agentMap.has(name)) {
            agentMap.set(name, []);
        }
        agentMap.get(name).push(item);
    });
    
    // Add chairman if exists
    if (deliberationData.stage3) {
        agentMap.set(deliberationData.stage3.chairman, [deliberationData.stage3]);
    }
    
    let firstTab = true;
    agentMap.forEach((responses, agentName) => {
        const color = responses[0].color;
        
        // Create tab button
        const tabBtn = document.createElement('button');
        tabBtn.className = `tab-btn ${firstTab ? 'active' : ''}`;
        tabBtn.style.setProperty('--tab-color', color);
        tabBtn.textContent = agentName;
        tabBtn.onclick = () => activateTab(agentName);
        tabNavigation.appendChild(tabBtn);
        
        // Create tab panel
        const panel = document.createElement('div');
        panel.className = `tab-panel ${firstTab ? 'active' : ''}`;
        panel.id = `tab-${agentName.replace(/\s+/g, '-')}`;
        
        responses.forEach((resp, idx) => {
            const card = resp.final_answer 
                ? createFinalCard(resp)
                : (resp.review ? createReviewCard(resp, idx) : createResponseCard(resp, idx));
            panel.appendChild(card);
        });
        
        tabContent.appendChild(panel);
        firstTab = false;
    });
}

function activateTab(agentName) {
    const tabId = `tab-${agentName.replace(/\s+/g, '-')}`;
    
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent === agentName);
    });
    
    // Update panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.toggle('active', panel.id === tabId);
    });
}

// Collapse functionality
function toggleCollapse(button) {
    const targetId = button.dataset.target;
    const content = document.getElementById(targetId);
    
    if (content) {
        content.classList.toggle('collapsed');
        button.classList.toggle('collapsed');
    }
}

// Utilities
function formatTime(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    errorMessage.textContent = message;
    errorContainer.style.display = 'block';
    setTimeout(() => hideError(), 5000);
}

function hideError() {
    errorContainer.style.display = 'none';
}

// Console
console.log('%c🤖 LLM Council System - Enhanced', 'font-size: 20px; font-weight: bold; color: #00e5ff;');
console.log('%cAdvanced monitoring and comparison features enabled', 'color: #00ffa3;');
