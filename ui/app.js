/**
 * Job Aggregator - Dashboard JavaScript
 * Handles job loading, filtering, and display
 */

// State
let allJobs = [];
let filteredJobs = [];
let stats = {};

// DOM Elements
const jobsGrid = document.getElementById('jobs-grid');
const emptyState = document.getElementById('empty-state');
const searchInput = document.getElementById('search-input');
const sourceFilter = document.getElementById('source-filter');
const timeFilter = document.getElementById('time-filter');
const newOnlyFilter = document.getElementById('new-only-filter');
const totalJobsEl = document.getElementById('total-jobs');
const newJobsEl = document.getElementById('new-jobs');
const sourcesCountEl = document.getElementById('sources-count');
const visibleJobsCountEl = document.getElementById('visible-jobs-count');
const lastUpdatedEl = document.getElementById('last-updated');
const modal = document.getElementById('job-modal');
const modalBody = document.getElementById('modal-body');

// API URL (for local development)
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : '/api';

/**
 * Load jobs from API or local JSON file
 */
async function loadJobs() {
    showLoading();
    
    try {
        // Try API first
        let data;
        try {
            const response = await fetch(`${API_BASE}/jobs`);
            if (response.ok) {
                data = await response.json();
            }
        } catch (e) {
            console.log('API not available, trying local file...');
        }
        
        // Fallback to local JSON file
        if (!data) {
            const response = await fetch('jobs_data.json');
            if (!response.ok) throw new Error('No data available');
            data = await response.json();
        }
        
        allJobs = data.jobs || [];
        stats = data.stats || {};
        
        updateStats();
        applyFilters();
        updateLastUpdated(data.generated_at);
        
    } catch (error) {
        console.error('Error loading jobs:', error);
        showEmptyState('Unable to load jobs. Run the aggregator first.');
    }
}

/**
 * Update statistics display
 */
function updateStats() {
    totalJobsEl.textContent = stats.total_jobs || allJobs.length;
    newJobsEl.textContent = stats.new_jobs_last_24h || allJobs.filter(j => j.is_new).length;
    
    const sources = stats.by_source ? Object.keys(stats.by_source).length : 
        [...new Set(allJobs.map(j => j.source))].length;
    sourcesCountEl.textContent = sources;
}

/**
 * Update last updated timestamp
 */
function updateLastUpdated(timestamp) {
    if (timestamp) {
        const date = new Date(timestamp);
        lastUpdatedEl.textContent = `Updated: ${date.toLocaleString()}`;
    } else {
        lastUpdatedEl.textContent = 'Updated: Just now';
    }
}

/**
 * Apply all filters
 */
function applyFilters() {
    const searchTerm = searchInput.value.toLowerCase();
    const sourceValue = sourceFilter.value;
    const timeValue = timeFilter.value;
    const newOnly = newOnlyFilter.checked;
    
    filteredJobs = allJobs.filter(job => {
        // Search filter
        if (searchTerm) {
            const searchable = `${job.title} ${job.company} ${job.location} ${(job.keywords || []).join(' ')}`.toLowerCase();
            if (!searchable.includes(searchTerm)) return false;
        }
        
        // Source filter
        if (sourceValue && job.source !== sourceValue) return false;
        
        // New only filter
        if (newOnly && !job.is_new) return false;
        
        // Time filter would require posted_date comparison
        // For now, all jobs are within 24-48h from fetch
        
        return true;
    });
    
    renderJobs();
}

/**
 * Render jobs to grid
 */
function renderJobs() {
    if (filteredJobs.length === 0) {
        showEmptyState();
        return;
    }
    
    emptyState.style.display = 'none';
    
    jobsGrid.innerHTML = filteredJobs.map(job => createJobCard(job)).join('');
    visibleJobsCountEl.textContent = `${filteredJobs.length} jobs`;
}

/**
 * Create job card HTML
 */
function createJobCard(job) {
    const keywords = (job.keywords || []).slice(0, 3);
    const logo = job.logo ? `<img src="${job.logo}" alt="${job.company}" onerror="this.parentElement.innerHTML='<span class=\\'job-logo-placeholder\\'>🏢</span>'">` : '<span class="job-logo-placeholder">🏢</span>';
    
    return `
        <div class="job-card ${job.is_new ? 'is-new' : ''}" onclick="openJobModal('${encodeURIComponent(JSON.stringify(job))}')">
            ${job.is_new ? '<span class="new-badge">New</span>' : ''}
            <div class="job-header">
                <div>
                    <h3 class="job-title">${escapeHtml(job.title)}</h3>
                    <div class="job-company">${escapeHtml(job.company || 'Company not specified')}</div>
                </div>
                <div class="job-logo">${logo}</div>
            </div>
            
            <div class="job-meta">
                <span class="job-meta-item">
                    <span>📍</span>
                    ${escapeHtml(job.location || 'Location not specified')}
                </span>
                ${job.posted_date ? `
                <span class="job-meta-item">
                    <span>📅</span>
                    ${escapeHtml(job.posted_date)}
                </span>
                ` : ''}
            </div>
            
            ${keywords.length > 0 ? `
            <div class="job-keywords">
                ${keywords.map(kw => `<span class="keyword-badge">${escapeHtml(kw)}</span>`).join('')}
            </div>
            ` : ''}
            
            <div class="job-footer">
                <span class="source-badge">${escapeHtml(job.source)}</span>
                <a href="${escapeHtml(job.url)}" target="_blank" class="apply-btn" onclick="event.stopPropagation()">
                    Apply →
                </a>
            </div>
        </div>
    `;
}

/**
 * Show loading state
 */
function showLoading() {
    jobsGrid.innerHTML = `
        <div class="loading-state">
            <div class="spinner"></div>
            <p>Loading jobs...</p>
        </div>
    `;
    emptyState.style.display = 'none';
}

/**
 * Show empty state
 */
function showEmptyState(message) {
    jobsGrid.innerHTML = '';
    emptyState.style.display = 'block';
    if (message) {
        emptyState.querySelector('p').textContent = message;
    }
    visibleJobsCountEl.textContent = '0 jobs';
}

/**
 * Open job detail modal
 */
function openJobModal(encodedJob) {
    const job = JSON.parse(decodeURIComponent(encodedJob));
    
    modalBody.innerHTML = `
        <h2 style="font-size: 24px; margin-bottom: 16px;">${escapeHtml(job.title)}</h2>
        <div style="color: var(--accent-primary); font-size: 18px; margin-bottom: 24px;">
            ${escapeHtml(job.company || 'Company not specified')}
        </div>
        
        <div style="display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 24px; color: var(--text-secondary);">
            <span>📍 ${escapeHtml(job.location || 'Not specified')}</span>
            <span>🏷️ ${escapeHtml(job.source)}</span>
            ${job.posted_date ? `<span>📅 ${escapeHtml(job.posted_date)}</span>` : ''}
        </div>
        
        ${(job.keywords || []).length > 0 ? `
        <div style="margin-bottom: 24px;">
            <strong style="display: block; margin-bottom: 8px;">Matched Keywords:</strong>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                ${job.keywords.map(kw => `<span class="keyword-badge">${escapeHtml(kw)}</span>`).join('')}
            </div>
        </div>
        ` : ''}
        
        <a href="${escapeHtml(job.url)}" target="_blank" class="apply-btn" style="display: inline-flex; font-size: 16px; padding: 12px 24px;">
            Apply for this position →
        </a>
    `;
    
    modal.classList.add('active');
}

/**
 * Close modal
 */
function closeModal() {
    modal.classList.remove('active');
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Event Listeners
searchInput.addEventListener('input', debounce(applyFilters, 300));
sourceFilter.addEventListener('change', applyFilters);
timeFilter.addEventListener('change', applyFilters);
newOnlyFilter.addEventListener('change', applyFilters);

// Close modal on escape or background click
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
});

modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
});

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initial load
document.addEventListener('DOMContentLoaded', loadJobs);




