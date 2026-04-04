/**
 * MSME Credit Risk Intelligence — Frontend Logic
 * With GST Amnesty Scheme Management (Twist 2)
 */

const API_BASE = '';

// ── State ──────────────────────────────────────────────────────────────────────
let currentResult = null;

// ── DOM Elements ───────────────────────────────────────────────────────────────
const form = document.getElementById('analyze-form');
const gstinInput = document.getElementById('gstin-input');
const analyzeBtn = document.getElementById('analyze-btn');
const formSection = document.getElementById('form-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const serverStatus = document.getElementById('server-status');

// ── Initialize ─────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    checkServerHealth();
    loadAmnestyWindows();

    // Auto-uppercase GSTIN
    gstinInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
    });

    form.addEventListener('submit', handleSubmit);
});

// ── Server Health ──────────────────────────────────────────────────────────────
async function checkServerHealth() {
    try {
        const res = await fetch(`${API_BASE}/api/health`);
        const data = await res.json();
        if (data.models_trained) {
            serverStatus.className = 'header-status ready';
            serverStatus.querySelector('.status-text').textContent =
                `Models Ready (${data.training_time}s)`;
            // Update amnesty badge from health
            updateAmnestyBadge(data.amnesty_active);
        } else {
            serverStatus.querySelector('.status-text').textContent = 'Training models...';
            setTimeout(checkServerHealth, 2000);
        }
    } catch {
        serverStatus.className = 'header-status error';
        serverStatus.querySelector('.status-text').textContent = 'Server offline';
        setTimeout(checkServerHealth, 5000);
    }
}

// ── Amnesty Management ─────────────────────────────────────────────────────────
function updateAmnestyBadge(active) {
    const badge = document.getElementById('amnesty-badge');
    const badgeText = document.getElementById('amnesty-badge-text');
    if (active) {
        badge.classList.add('active');
        badgeText.textContent = 'Amnesty Active';
    } else {
        badge.classList.remove('active');
        badgeText.textContent = 'No Amnesty Active';
    }
}

async function loadAmnestyWindows() {
    try {
        const res = await fetch(`${API_BASE}/api/amnesty`);
        const data = await res.json();
        updateAmnestyBadge(data.amnesty_active);
        renderAmnestyWindows(data.windows || []);
    } catch {
        // Server may not be ready yet
    }
}

function renderAmnestyWindows(windows) {
    const list = document.getElementById('amnesty-windows-list');
    list.innerHTML = '';

    if (windows.length === 0) {
        list.innerHTML = '<p class="amnesty-empty">No amnesty windows registered. Use the form above to register one.</p>';
        return;
    }

    windows.forEach(w => {
        const card = document.createElement('div');
        card.className = `amnesty-window-card ${w.active ? 'active' : 'inactive'}`;
        card.innerHTML = `
            <div class="aw-info">
                <div class="aw-quarter">${w.quarter}</div>
                <div class="aw-dates">${w.start} → ${w.end}</div>
                <div class="aw-desc">${w.description}</div>
            </div>
            <div class="aw-status">
                <span class="aw-status-badge ${w.active ? 'active' : 'inactive'}">${w.active ? 'ACTIVE' : 'INACTIVE'}</span>
                ${w.active
                    ? `<button class="btn-aw-action deactivate" onclick="toggleAmnesty('${w.quarter}', false)">Deactivate</button>`
                    : `<button class="btn-aw-action activate" onclick="toggleAmnesty('${w.quarter}', true)">Activate</button>`
                }
            </div>
        `;
        list.appendChild(card);
    });
}

async function registerAmnesty() {
    const quarter = document.getElementById('amnesty-quarter').value.trim();
    const start = document.getElementById('amnesty-start').value;
    const end = document.getElementById('amnesty-end').value;

    if (!quarter || !start || !end) {
        showToast('Please fill all amnesty fields', 'error');
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/api/amnesty`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quarter, start_date: start, end_date: end }),
        });
        const data = await res.json();
        if (data.success) {
            showToast(`Amnesty '${quarter}' registered — late-filing penalties suppressed`, 'success');
            document.getElementById('amnesty-quarter').value = '';
            document.getElementById('amnesty-start').value = '';
            document.getElementById('amnesty-end').value = '';
            loadAmnestyWindows();
        } else {
            showToast('Failed to register amnesty', 'error');
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

async function toggleAmnesty(quarter, activate) {
    try {
        let res;
        if (activate) {
            res = await fetch(`${API_BASE}/api/amnesty/${encodeURIComponent(quarter)}/activate`, { method: 'PUT' });
        } else {
            res = await fetch(`${API_BASE}/api/amnesty/${encodeURIComponent(quarter)}`, { method: 'DELETE' });
        }
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            loadAmnestyWindows();
        }
    } catch (err) {
        showToast(err.message, 'error');
    }
}

// ── Form Submit ────────────────────────────────────────────────────────────────
async function handleSubmit(e) {
    e.preventDefault();

    const gstin = gstinInput.value.trim();
    if (gstin.length !== 15) {
        showToast('GSTIN must be exactly 15 characters', 'error');
        gstinInput.focus();
        return;
    }

    // Only GSTIN — everything else is auto-generated by the ML pipeline
    const payload = { gstin: gstin };

    showLoading();

    try {
        const res = await fetch(`${API_BASE}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Analysis failed');
        }

        const data = await res.json();
        currentResult = data;
        renderResults(data);
        showToast('Analysis complete!', 'success');
    } catch (err) {
        showToast(err.message, 'error');
        hideLoading();
    }
}

// ── Loading Animation ──────────────────────────────────────────────────────────
function showLoading() {
    formSection.style.display = 'none';
    resultsSection.style.display = 'none';
    loadingSection.style.display = 'block';
    analyzeBtn.disabled = true;

    // Animate steps
    const steps = document.querySelectorAll('#loading-steps .step');
    steps.forEach(s => { s.className = 'step'; });

    let current = 0;
    const interval = setInterval(() => {
        if (current > 0) steps[current - 1].classList.replace('active', 'done');
        if (current < steps.length) {
            steps[current].classList.add('active');
            current++;
        } else {
            clearInterval(interval);
        }
    }, 500);
}

function hideLoading() {
    loadingSection.style.display = 'none';
    formSection.style.display = 'block';
    analyzeBtn.disabled = false;
}

// ── Render Results ─────────────────────────────────────────────────────────────
function renderResults(data) {
    loadingSection.style.display = 'none';
    formSection.style.display = 'none';
    resultsSection.style.display = 'block';
    
    // Default to 'all' view when newly generated
    switchTab('all');

    // ── Amnesty Banner ─────────────────────────────────────────────────────
    const banner = document.getElementById('amnesty-banner');
    const amnestyStatus = data.amnesty_status || {};
    if (amnestyStatus.amnesty_active) {
        banner.style.display = 'flex';
        document.getElementById('amnesty-banner-title').textContent = 'GST Amnesty Scheme Active';
        document.getElementById('amnesty-banner-detail').textContent = amnestyStatus.message || '';

        const adjDiv = document.getElementById('amnesty-adjustments');
        adjDiv.innerHTML = '';
        (amnestyStatus.adjusted_fields || []).forEach(adj => {
            const row = document.createElement('div');
            row.className = 'adj-row';
            row.innerHTML = `
                <span class="adj-field">${adj.field}</span>
                <span class="adj-original">${adj.original_value}</span>
                <span class="adj-arrow">→</span>
                <span class="adj-adjusted">${adj.adjusted_value}</span>
                <span class="adj-reason">${adj.reason}</span>
            `;
            adjDiv.appendChild(row);
        });
    } else {
        banner.style.display = 'none';
    }

    // Summary cards
    document.getElementById('val-score').textContent = data.credit_score;
    document.getElementById('val-risk-band').textContent = data.risk_band;
    const scorePct = ((data.credit_score - 300) / 600) * 100;
    setTimeout(() => {
        document.getElementById('score-fill').style.width = scorePct + '%';
    }, 100);

    // Score card color
    const cardScore = document.getElementById('card-score');
    if (data.credit_score >= 700) {
        cardScore.querySelector('.card-value').style.color = 'var(--accent-green)';
    } else if (data.credit_score < 500) {
        cardScore.querySelector('.card-value').style.color = 'var(--accent-red)';
    }

    // Fraud
    document.getElementById('val-fraud').textContent = (data.fraud_probability * 100).toFixed(1) + '%';
    document.getElementById('val-fraud-level').textContent = data.fraud_risk_level + ' RISK';
    const cardFraud = document.getElementById('card-fraud');
    cardFraud.className = 'summary-card card-fraud ' + data.fraud_risk_level.toLowerCase();

    // Decision
    document.getElementById('val-decision').textContent = data.decision;
    document.getElementById('val-loan-amt').textContent = 'Rs. ' + data.recommended_loan_amount.toLocaleString('en-IN');
    const cardDec = document.getElementById('card-decision');
    cardDec.className = 'summary-card card-decision ' + data.decision.toLowerCase();

    // Time
    document.getElementById('val-time').textContent = 'Processed in ' + data.elapsed_seconds.toFixed(1) + 's';

    // Business Headers added in new UI
    const bNameElt = document.getElementById('b-name');
    if(bNameElt) bNameElt.textContent = data.business_name;
    const bGstinElt = document.getElementById('b-gstin');
    if(bGstinElt) bGstinElt.textContent = 'GSTIN: ' + data.gstin;
    const bSectorElt = document.getElementById('b-sector');
    if(bSectorElt) bSectorElt.textContent = data.sector;

    // Profile grid
    const profileGrid = document.getElementById('profile-grid');
    profileGrid.innerHTML = '';
    const profileItems = [
        ['GSTIN', data.gstin],
        ['Business Name', data.business_name],
        ['Trade Name', data.trade_name],
        ['Sector', data.sector],
        ['Constitution', data.constitution],
        ['Location', data.location],
        ['Business Age', data.business_age + ' years'],
        ['Registration Date', data.registration_date],
        ['Sector Risk', data.risk_sector_score + '/10'],
        ['Annual Turnover', 'Rs. ' + Math.round(data.sales_summary.estimated_turnover).toLocaleString('en-IN')],
        ['Sales Volatility', (data.sales_summary.sales_volatility * 100).toFixed(1) + '%'],
        ['P/S Ratio', data.purchase_summary.purchase_to_sales_ratio.toFixed(2)],
        ['Vendors', data.network_summary.vendor_count],
        ['Customers', data.network_summary.customer_count],
        ['Late GST Filings', data.gst_behavior.late_filings_count + (amnestyStatus.amnesty_active ? ' (amnesty applied)' : '')],
        ['Loan Defaults', data.loan_history.loan_defaults],
    ];
    profileItems.forEach(([label, value]) => {
        const div = document.createElement('div');
        div.className = 'flex flex-col p-3 border border-outline-variant bg-white';
        div.innerHTML = `<span class="text-[9px] font-black uppercase tracking-widest text-outline mb-1">${label}</span>
                         <span class="text-xs font-bold text-on-surface">${value}</span>`;
        profileGrid.appendChild(div);
    });

    // PDF download
    const pdfBtn = document.getElementById('btn-download-pdf-app');
    if(pdfBtn) {
        pdfBtn.onclick = () => {
            window.open(data.pdf_url + "?t=" + new Date().getTime(), '_blank');
        };
    }

    // Decision reasons
    const reasonsDiv = document.getElementById('decision-reasons');
    reasonsDiv.innerHTML = '';
    data.decision_reasons.forEach(reason => {
        const div = document.createElement('div');
        let cls = 'border-l-4 border-outline-variant text-outline';
        let icon = 'info';
        if (reason.toLowerCase().includes('strong') || reason.toLowerCase().includes('low fraud') || reason.toLowerCase().includes('stable')) {
            cls = 'border-l-4 border-primary text-primary bg-primary-container/10';
            icon = 'check_circle';
        } else if (reason.toLowerCase().includes('below') || reason.toLowerCase().includes('exceed') || reason.toLowerCase().includes('poor') || reason.toLowerCase().includes('high') || reason.toLowerCase().includes('unstable') || reason.toLowerCase().includes('default')) {
            cls = 'border-l-4 border-error text-error bg-error-container/20';
            icon = 'warning';
        }
        div.className = `p-3 flex gap-2 items-start bg-white ${cls}`;
        div.innerHTML = `<span class="material-symbols-outlined text-sm pt-0.5">${icon}</span><span>${reason}</span>`;
        reasonsDiv.appendChild(div);
    });

    // Charts (Plotly Interactive)
    const config = { responsive: true, displayModeBar: false };
    if(data.charts.gauge) Plotly.newPlot('chart-gauge', data.charts.gauge.data, data.charts.gauge.layout, config);
    if(data.charts.radar) Plotly.newPlot('chart-radar', data.charts.radar.data, data.charts.radar.layout, config);
    if(data.charts.sales) Plotly.newPlot('chart-sales', data.charts.sales.data, data.charts.sales.layout, config);
    if(data.charts.turnover) Plotly.newPlot('chart-turnover', data.charts.turnover.data, data.charts.turnover.layout, config);
    if(data.charts.network) Plotly.newPlot('chart-network', data.charts.network.data, data.charts.network.layout, config);

    // Fraud Detection Info for Network Topology
    const circCount = data.network_summary.circular_trades_count || 0;
    const fraudText = circCount > 0 
        ? `The automated topology scan detected <b>${circCount} circular funding loops</b> within the immediate vendor-customer ecosystem. The underlying nodes and interconnects highlighted in red reveal closed-loop transactions where identical capital is shifted sequentially between entities. This structure is a mathematical hallmark of artificial invoice inflation and requires strict manual compliance review.`
        : `The automated topology scan verifies a healthy, linear supply chain distribution. No closed-loop circular capital flows were detected among vendor and client pairs. The network spread supports the reported financial metrics organically without cyclic friction.`;
    const netFraudTxtEl = document.getElementById('network-fraud-text');
    if(netFraudTxtEl) netFraudTxtEl.innerHTML = fraudText;

    // Explanations Translation into Narrative Paragraphs
    const explDiv = document.getElementById('explanations-list');
    explDiv.innerHTML = '';
    
    let mitigants = [];
    let risks = [];
    
    data.explanations.forEach(exp => {
        let text = exp.trim();
        if(text.startsWith('+') || text.startsWith('  +')) {
            mitigants.push(text.replace('+ ', '').replace('  +', '').trim());
        } else if(text.startsWith('[!]') || text.startsWith('  [!]')) {
            risks.push(text.replace('[!]', '').replace('  [!]', '').trim());
        } else if(text.length > 5 && text !== '---' && !text.toLowerCase().includes('score') && !text.toLowerCase().includes('probability')) {
             risks.push(text.replace('-', '').trim());
        }
    });
    
    // Build Narrative HTML
    explDiv.className = 'grid grid-cols-2 gap-8 text-sm mt-4';
    
    let riskHtml = `<div class="p-6 border border-error/20 bg-error-container/5 border-l-4 border-l-error rounded-sm print-shadow">
        <h4 class="font-extrabold text-error mb-3 tracking-tight flex items-center gap-2"><span class="material-symbols-outlined text-base">warning</span> Critical Risk Factors</h4>
        <p class="text-on-surface-variant leading-relaxed text-xs font-medium">Our neural risk evaluation model has identified specific vulnerabilities in the business profile. ${risks.join('. ')}. These statistical patterns strongly suggest that closer monitoring is necessary during manual underwriting.</p>
    </div>`;
    
    let mitHtml = `<div class="p-6 border border-primary/20 bg-primary-container/10 border-l-4 border-l-primary rounded-sm print-shadow">
        <h4 class="font-extrabold text-primary mb-3 tracking-tight flex items-center gap-2"><span class="material-symbols-outlined text-base">check_circle</span> Mitigating Strengths</h4>
        <p class="text-on-surface-variant leading-relaxed text-xs font-medium">Despite identified weaknesses, the enterprise exhibits structural strengths. ${mitigants.join('. ')}. Such indicators contribute positively to the final credit rating baseline.</p>
    </div>`;
    
    if(risks.length === 0) riskHtml = '';
    if(mitigants.length === 0) mitHtml = '';
    
    explDiv.innerHTML = riskHtml + mitHtml;

    // Fraud indicators
    const fiSection = document.getElementById('fraud-indicators-section');
    const fiList = document.getElementById('fraud-indicators-list');
    fiList.innerHTML = '';
    if (data.fraud_indicators && data.fraud_indicators.length > 0) {
        fiSection.style.display = 'block';
        data.fraud_indicators.forEach(ind => {
            const div = document.createElement('div');
            div.className = 'fraud-indicator';
            div.innerHTML = `
                <span class="fi-severity ${ind.severity}">${ind.severity}</span>
                <span class="fi-desc">${ind.description}</span>
            `;
            fiList.appendChild(div);
        });
    } else {
        fiSection.style.display = 'none';
    }

    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Reset Form ─────────────────────────────────────────────────────────────────
function resetForm() {
    resultsSection.style.display = 'none';
    formSection.style.display = 'block';
    analyzeBtn.disabled = false;
    document.getElementById('score-fill').style.width = '0%';
    gstinInput.focus();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ── Tab Management ─────────────────────────────────────────────────────────────
function switchTab(tabId) {
    const sections = document.querySelectorAll('.report-section');
    if(sections.length === 0) return;
    
    const profileSection = document.getElementById('view-profile');
    
    if(tabId === 'all') {
        sections.forEach(s => s.style.display = 'block');
        if(profileSection) profileSection.style.display = 'block';
    } else {
        sections.forEach(s => s.style.display = 'none');
        if(profileSection) profileSection.style.display = (tabId === 'dashboard') ? 'block' : 'none';
        const target = document.getElementById('view-' + tabId);
        if(target) target.style.display = 'block';
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Trigger window resize to force Plotly charts to adapt to container constraints
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
    }, 50);
}

// ── Toast Notifications ────────────────────────────────────────────────────────
function showToast(message, type = 'error') {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}
