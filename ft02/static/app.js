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

    // Score card color — use the score fill bar color instead of a missing .card-value
    const scoreEl = document.getElementById('val-score');
    if (scoreEl) {
        if (data.credit_score >= 700) scoreEl.style.color = 'var(--accent-green, #16a34a)';
        else if (data.credit_score < 500) scoreEl.style.color = 'var(--accent-red, #dc2626)';
    }

    // Fraud
    document.getElementById('val-fraud').textContent = (data.fraud_probability * 100).toFixed(1) + '%';
    const valFraudLevel = document.getElementById('val-fraud-level');
    if (valFraudLevel) {
        valFraudLevel.textContent = data.fraud_risk_level + ' RISK';
        // Tint the badge without wiping Tailwind classes
        const riskColors = { high: '#b91c1c', medium: '#d97706', low: '#15803d' };
        valFraudLevel.style.background = riskColors[data.fraud_risk_level.toLowerCase()] || '#006d4e';
    }

    // Decision
    document.getElementById('val-decision').textContent = data.decision;
    document.getElementById('val-loan-amt').textContent = 'Rs. ' + data.recommended_loan_amount.toLocaleString('en-IN');
    // Tint decision text without overwriting Tailwind classes
    const valDecEl = document.getElementById('val-decision');
    if (valDecEl) {
        const decColors = { APPROVE: '#15803d', REJECT: '#b91c1c', REVIEW: '#d97706' };
        valDecEl.style.color = decColors[data.decision] || '';
    }

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

    // Fraud indicators — inject into card-fraud widget
    const fiList = document.getElementById('fraud-indicators-list');
    if (fiList) {
        fiList.innerHTML = '';
        if (data.fraud_indicators && data.fraud_indicators.length > 0) {
            const sevColor = { critical: '#b91c1c', high: '#ea580c', medium: '#d97706', low: '#15803d' };
            data.fraud_indicators.forEach(ind => {
                const div = document.createElement('div');
                div.className = 'flex gap-1 items-start mt-1';
                div.innerHTML = `<span style="color:${sevColor[ind.severity]||'#333'};font-weight:700;font-size:10px;text-transform:uppercase;">${ind.severity}</span>
                    <span style="font-size:10px;">${ind.description}</span>`;
                fiList.appendChild(div);
            });
        }
    }

    // Load trend data + render new panels
    loadTrendData(data.gstin);
    renderAIAnalyst(data);
    renderDecisionEngine(data);
    if(data.bankruptcy_probability !== undefined) renderBankruptcyCard(data.bankruptcy_probability);

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

    // Highlight active nav item
    document.querySelectorAll('.nav-item').forEach(el => {
        el.classList.remove('text-primary', 'bg-primary/10', 'font-bold', 'border-r-2', 'border-primary');
        el.classList.add('text-on-surface-variant');
    });
    const activeLink = document.querySelector(`.nav-item[data-tab='${tabId}']`);
    if(activeLink) {
        activeLink.classList.remove('text-on-surface-variant');
        activeLink.classList.add('text-primary', 'bg-primary/10', 'font-bold', 'border-r-2', 'border-primary');
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });
    setTimeout(() => window.dispatchEvent(new Event('resize')), 50);
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

// ── Bankruptcy Card ──────────────────────────────────────────────────────────────────────
function renderBankruptcyCard(prob) {
    const pct = (prob * 100).toFixed(1);
    const color = prob >= 0.6 ? '#b91c1c' : prob >= 0.35 ? '#d97706' : '#15803d';
    const label = prob >= 0.6 ? 'HIGH' : prob >= 0.35 ? 'MODERATE' : 'LOW';
    const el = document.getElementById('card-bankruptcy');
    if(!el) return;
    el.innerHTML = `
        <div class="text-[10px] text-outline font-black uppercase tracking-widest mb-4">Bankruptcy Risk</div>
        <div class="text-4xl font-extrabold mb-1" style="color:${color}">${pct}%</div>
        <div class="text-xs font-bold mb-3" style="color:${color}">${label} RISK</div>
        <div class="h-2 w-full bg-surface-container-highest rounded-full overflow-hidden">
            <div class="h-full rounded-full transition-all duration-700" style="width:${pct}%;background:${color}"></div>
        </div>
        <div class="mt-2 text-[10px] text-outline italic">Derived from credit + fraud signals</div>`;
}

// ── Trend Charts ──────────────────────────────────────────────────────────────────────
async function loadTrendData(gstin) {
    try {
        const res = await fetch(`/api/trend/${gstin}`);
        const d = await res.json();

        // Escalation alert
        const alertEl = document.getElementById('trend-escalation-alert');
        const alertTxt = document.getElementById('trend-escalation-text');
        if(d.escalation_alert && alertEl) {
            alertEl.style.display = 'flex';
            alertTxt.textContent = d.escalation_message;
        } else if(alertEl) { alertEl.style.display = 'none'; }

        const layout = (title) => ({
            margin: {t:10,b:30,l:40,r:10},
            paper_bgcolor:'transparent', plot_bgcolor:'transparent',
            font:{size:10}, xaxis:{showgrid:false}, yaxis:{showgrid:true,gridcolor:'#e5e7eb'}
        });
        const cfg = {responsive:true, displayModeBar:false};

        Plotly.newPlot('chart-trend-score', [{
            x: d.months, y: d.risk_scores, type:'scatter', mode:'lines+markers',
            line:{color:'#006d4e',width:2}, marker:{size:5}, fill:'tozeroy', fillcolor:'rgba(0,109,78,0.07)'
        }], layout(), cfg);

        Plotly.newPlot('chart-trend-revenue', [{
            x: d.months, y: d.revenues, type:'bar',
            marker:{color:'#1565C0', opacity:0.8}
        }], layout(), cfg);

        Plotly.newPlot('chart-trend-gst', [{
            x: d.months, y: d.gst_delays, type:'bar',
            marker:{color: d.gst_delays.map(v => v >= 3 ? '#b91c1c' : v >= 1 ? '#d97706' : '#15803d')}
        }], layout(), cfg);

        Plotly.newPlot('chart-trend-loan', [{
            x: d.months, y: d.loan_health, type:'scatter', mode:'lines+markers',
            line:{color:'#7c3aed',width:2}, fill:'tozeroy', fillcolor:'rgba(124,58,237,0.07)'
        }], layout(), cfg);
    } catch(e) { console.error('Trend load failed', e); }
}

// ── AI Risk Analyst ─────────────────────────────────────────────────────────────────────
function renderAIAnalyst(data) {
    const container = document.getElementById('ai-analyst-report');
    if(!container) return;

    const score = data.credit_score;
    const band = data.risk_band;
    const fraud = (data.fraud_probability * 100).toFixed(1);
    const bankrupt = data.bankruptcy_probability ? (data.bankruptcy_probability * 100).toFixed(1) : 'N/A';
    const decision = data.decision;
    const loanAmt = data.recommended_loan_amount?.toLocaleString('en-IN');

    // Parse SHAP into sentences
    const risks = [], strengths = [];
    (data.explanations || []).forEach(e => {
        const t = e.trim();
        if(t.startsWith('[!]') || t.startsWith('  [!]')) risks.push(t.replace(/^\s*\[!\]\s*/, ''));
        else if(t.startsWith('+') || t.startsWith('  +')) strengths.push(t.replace(/^\s*\+\s*/, ''));
    });

    const fraudSignals = (data.fraud_indicators || []).map(f => f.description).join('; ') || 'No indicators detected.';

    const decisionMap = {
        APPROVE: {color:'#15803d', label:'APPROVE', note:'The business meets lending criteria and presents acceptable risk.'},
        'APPROVE WITH CONDITIONS': {color:'#d97706', label:'APPROVE WITH CONDITIONS', note:'Approval is recommended but subject to additional covenant requirements.'},
        'REQUIRE COLLATERAL': {color:'#ea580c', label:'REQUIRE COLLATERAL', note:'Elevated risk warrants collateral-backed lending to mitigate potential defaults.'},
        REJECT: {color:'#b91c1c', label:'REJECT', note:'Risk profile exceeds acceptable thresholds for unsecured lending.'},
    };
    const dec = decisionMap[decision] || {color:'#64748b', label:decision, note:''};

    const section = (icon, title, body, border='#006d4e') =>
        `<div class="p-6 border border-outline-variant bg-surface-bright rounded-sm border-l-4" style="border-left-color:${border}">
            <div class="flex items-center gap-2 mb-3">
                <span class="material-symbols-outlined text-base" style="color:${border}">${icon}</span>
                <h3 class="font-extrabold text-sm tracking-tight" style="color:${border}">${title}</h3>
            </div>
            <p class="text-[13px] text-on-surface-variant leading-relaxed font-medium">${body}</p>
         </div>`;

    container.innerHTML = [
        section('summarize', 'Executive Summary',
            `This AI-generated financial dossier synthesizes the credit risk profile of <b>${data.business_name}</b> (GSTIN: ${data.gstin}), a ${data.business_age}-year-old entity in the ${data.sector} sector. The business has been assigned a credit score of <b>${score}/900</b> (${band}), indicating a ${band.toLowerCase()} creditworthiness profile. The system's underwriting recommendation is: <b style="color:${dec.color}">${dec.label}</b>, with a recommended exposure limit of Rs. ${loanAmt}.`),
        section('warning', 'Key Risk Drivers',
            risks.length > 0
                ? `The risk evaluation model identified the following primary stress signals: ${risks.join('. ')}. These factors were weighted by the neural SHAP layer to determine their contribution to the final credit score degradation.`
                : 'No significant risk drivers were identified by the model at this time.',
            '#b91c1c'),
        section('verified', 'Mitigating Strengths',
            strengths.length > 0
                ? `Counterbalancing the risk drivers, several entity strengths were recognized: ${strengths.join('. ')}. These positive indicators partially offset the downside risk and support the lending recommendation.`
                : 'No specific mitigating strengths were flagged by the model.',
            '#15803d'),
        section('gpp_maybe', 'Fraud Risk Assessment',
            `The fraud detection module assigns a probability of <b>${fraud}%</b>. Detected anomaly signals include: <i>${fraudSignals}</i>. A bankruptcy risk estimate of <b>${bankrupt}%</b> has been computed from the combined credit and fraud signal vector.`,
            fraud > 50 ? '#b91c1c' : '#d97706'),
        section('gavel', 'Underwriting Recommendation',
            `The Credit Decision Engine outputs: <b style="color:${dec.color}">${dec.label}</b>. ${dec.note} The recommended loan limit is Rs. ${loanAmt} with a suggested interest rate of ${suggestRate(score)}% per annum. Decision confidence: ${(data.decision_confidence * 100).toFixed(0)}%.`,
            dec.color),
    ].join('');
}

function suggestRate(score) {
    if(score >= 750) return'8.5';
    if(score >= 650) return '10.5';
    if(score >= 550) return '13.0';
    if(score >= 450) return '16.0';
    return '19.5';
}

// ── Credit Decision Engine Panel ───────────────────────────────────────────────────────
function renderDecisionEngine(data) {
    const container = document.getElementById('decision-engine-panel');
    if(!container) return;

    const decision = data.decision;
    const rate = suggestRate(data.credit_score);
    const decColors = { APPROVE:'#15803d', 'APPROVE WITH CONDITIONS':'#d97706', 'REQUIRE COLLATERAL':'#ea580c', REJECT:'#b91c1c' };
    const color = decColors[decision] || '#64748b';
    const confidence = (data.decision_confidence * 100).toFixed(1);
    const loan = data.recommended_loan_amount?.toLocaleString('en-IN');

    const reasonsHtml = (data.decision_reasons || []).map(r => {
        const isPos = r.toLowerCase().includes('strong') || r.toLowerCase().includes('low fraud') || r.toLowerCase().includes('stable');
        const ic = isPos ? 'check_circle' : 'cancel';
        const cl = isPos ? '#15803d' : '#b91c1c';
        return `<div class="flex items-start gap-3 p-3 border border-outline-variant rounded-sm bg-white">
            <span class="material-symbols-outlined text-sm mt-0.5" style="color:${cl}">${ic}</span>
            <span class="text-[13px] font-medium text-on-surface">${r}</span></div>`;
    }).join('');

    container.innerHTML = `
        <div class="grid grid-cols-4 gap-4 mb-6">
            <div class="col-span-2 p-6 border-2 rounded-sm flex flex-col gap-2" style="border-color:${color};background:${color}10">
                <div class="text-[10px] font-black uppercase tracking-widest" style="color:${color}">Decision</div>
                <div class="text-2xl font-extrabold" style="color:${color}">${decision}</div>
                <div class="text-[11px] font-bold text-outline">Confidence: ${confidence}%</div>
            </div>
            <div class="p-6 border border-outline-variant bg-white rounded-sm">
                <div class="text-[10px] font-black uppercase tracking-widest text-outline mb-2">Recommended Limit</div>
                <div class="text-xl font-extrabold text-on-surface">Rs. ${loan}</div>
            </div>
            <div class="p-6 border border-outline-variant bg-white rounded-sm">
                <div class="text-[10px] font-black uppercase tracking-widest text-outline mb-2">Suggested Rate</div>
                <div class="text-xl font-extrabold text-on-surface">${rate}% <span class="text-sm font-medium text-outline">p.a.</span></div>
            </div>
        </div>
        <div class="space-y-2">
            <div class="text-[10px] font-black uppercase tracking-widest text-outline mb-3">Decision Rationale</div>
            ${reasonsHtml}
        </div>`;
}

// ── Stress Test ──────────────────────────────────────────────────────────────────────
async function runStressTest() {
    if(!currentResult) { showToast('Run an analysis first', 'error'); return; }
    const gstin = currentResult.gstin;
    const body = {
        gstin,
        revenue_drop_pct: parseFloat(document.getElementById('stress-revenue').value),
        loan_increase_pct: parseFloat(document.getElementById('stress-loan').value),
        gst_delay_months: parseInt(document.getElementById('stress-gst').value),
        industry_risk_delta: parseFloat(document.getElementById('stress-industry').value),
    };
    const resultsEl = document.getElementById('stress-results');
    resultsEl.innerHTML = '<div class="text-sm text-outline animate-pulse">Running simulation...</div>';
    try {
        const res = await fetch('/api/stress-test', {
            method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)
        });
        const d = await res.json();
        const delta = d.delta;
        const fmt = (v, isScore) => {
            const sign = v > 0 ? '+' : '';
            const color = isScore ? (v >= 0 ? '#15803d' : '#b91c1c') : (v <= 0 ? '#15803d' : '#b91c1c');
            const suffix = isScore ? '' : '%';
            const val = isScore ? v : (v*100).toFixed(1);
            return `<span style="color:${color};font-weight:700">${sign}${val}${suffix}</span>`;
        };
        resultsEl.innerHTML = `
            <div class="w-full space-y-4">
                <h3 class="font-extrabold text-sm mb-4">Before vs After Stress Scenario</h3>
                ${[['Credit Score',d.before.credit_score,d.after.credit_score,delta.credit_score,true],
                   ['Fraud Probability',(d.before.fraud_probability*100).toFixed(1)+'%',(d.after.fraud_probability*100).toFixed(1)+'%',delta.fraud_probability,false],
                   ['Bankruptcy Risk',(d.before.bankruptcy_probability*100).toFixed(1)+'%',(d.after.bankruptcy_probability*100).toFixed(1)+'%',delta.bankruptcy_probability,false]
                  ].map(([label,b,a,dv,isScore]) => `
                    <div class="flex items-center gap-4 p-4 border border-outline-variant bg-white rounded-sm">
                        <div class="w-1/3 text-[11px] font-black uppercase tracking-widest text-outline">${label}</div>
                        <div class="flex-1 flex items-center gap-3 text-sm font-bold">
                            <span class="text-on-surface">${b}</span>
                            <span class="material-symbols-outlined text-sm text-outline">arrow_forward</span>
                            <span class="text-on-surface">${a}</span>
                        </div>
                        <div class="text-sm">${fmt(dv, isScore)}</div>
                    </div>`).join('')}
                <div class="text-[10px] text-outline mt-2 italic">Risk band after stress: <b>${d.after.risk_band}</b></div>
            </div>`;
    } catch(e) { resultsEl.innerHTML = `<div class="text-error text-sm">Simulation failed: ${e.message}</div>`; }
}
