// Insurance Agent Dashboard JavaScript

const API_BASE = window.location.origin;
let currentCustomer = null;
let currentCustomerData = null;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardStats();
    
    // Add enter key support for search
    document.getElementById('customerSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCustomer();
        }
    });
});

// Load dashboard statistics from API
async function loadDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/api/customers/stats`);
        if (response.ok) {
            const stats = await response.json();
            document.getElementById('totalCustomers').textContent = Number(stats.total_customers).toLocaleString();
            document.getElementById('activeOpportunities').textContent = Number(stats.active_policies).toLocaleString();
            document.getElementById('aiInsights').textContent = Number(stats.total_claims).toLocaleString();
            document.getElementById('retentionScore').textContent = `$${Number(stats.avg_premium).toLocaleString()}`;
        } else {
            document.getElementById('totalCustomers').textContent = '--';
            document.getElementById('activeOpportunities').textContent = '--';
            document.getElementById('aiInsights').textContent = '--';
            document.getElementById('retentionScore').textContent = '--';
        }
    } catch (error) {
        console.error('Error loading stats:', error);
        document.getElementById('totalCustomers').textContent = '--';
        document.getElementById('activeOpportunities').textContent = '--';
        document.getElementById('aiInsights').textContent = '--';
        document.getElementById('retentionScore').textContent = '--';
    }
}

// Search for customer via API
async function searchCustomer() {
    const query = document.getElementById('customerSearch').value.trim();
    if (!query) return;
    
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/customers/search?query=${encodeURIComponent(query)}&limit=50`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.results && data.results.length > 0) {
            displaySearchResults(data.results, data.count);
        } else {
            resultsDiv.innerHTML = '<p>No customers found. Try a customer ID (e.g. "C0052225"), state (e.g. "NC"), or region (e.g. "Southeast").</p>';
        }
    } catch (error) {
        console.error('Error searching:', error);
        resultsDiv.innerHTML = '<p style="color: red;">Error searching for customers. Please try again.</p>';
    }
}

// Display search results
function displaySearchResults(results, totalCount) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<p>No customers found</p>';
        return;
    }
    
    let html = `<h3>Search Results (${totalCount} found)</h3>`;
    results.forEach(customer => {
        const ltv = typeof customer.lifetime_value === 'number' ? customer.lifetime_value.toLocaleString() : customer.lifetime_value;
        const location = [customer.state, customer.region].filter(Boolean).join(', ');
        html += `
            <div class="result-item" onclick='selectCustomer("${customer.id}")'>
                <strong>${customer.name || customer.id}</strong> (${customer.id})
                <br>
                <small>${location ? location + ' • ' : ''}${customer.type} • ${customer.policy_count} policies • $${ltv} premium</small>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}

// Select and load customer profile
async function selectCustomer(customerId) {
    currentCustomer = customerId;
    
    // Show profile section
    document.getElementById('customerProfile').style.display = 'block';
    document.getElementById('customerProfile').scrollIntoView({ behavior: 'smooth' });
    
    // Load customer data from API
    await loadCustomerProfile(customerId);
}

// Load customer profile from API
async function loadCustomerProfile(customerId) {
    try {
        const response = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(customerId)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const customer = await response.json();
        
        if (customer.error) {
            alert('Customer not found');
            return;
        }
        
        currentCustomerData = customer;
        
        // Update header
        document.getElementById('customerName').textContent = customer.name || customer.id;
        const typeClass = customer.type === 'Premium' ? 'badge-premium' : 'badge-standard';
        document.getElementById('customerType').className = `badge ${typeClass}`;
        document.getElementById('customerType').textContent = customer.type;
        
        // Load overview tab
        loadOverviewTab(customer);
        loadPoliciesTab(customer);
    } catch (error) {
        console.error('Error loading customer profile:', error);
        alert('Error loading customer profile. Please try again.');
    }
}

// Load overview tab
function loadOverviewTab(customer) {
    const infoHtml = `
        <p><strong>Customer ID:</strong> ${customer.id}</p>
        <p><strong>State:</strong> ${customer.state || 'N/A'}</p>
        <p><strong>Region:</strong> ${customer.region || 'N/A'}</p>
        <p><strong>ZIP Code:</strong> ${customer.zip || 'N/A'}</p>
        <p><strong>Age:</strong> ${customer.age || 'N/A'}</p>
        <p><strong>Marital Status:</strong> ${customer.marital_status || 'N/A'}</p>
        <p><strong>Income Band:</strong> ${customer.income_band || 'N/A'}</p>
        <p><strong>Homeowner:</strong> ${customer.is_homeowner ? 'Yes' : 'No'}</p>
        <p><strong>Has Kids:</strong> ${customer.has_kids ? 'Yes' : 'No'}</p>
        <p><strong>Status:</strong> ${customer.status}</p>
        <p><strong>Total Premium:</strong> $${(customer.lifetime_value || 0).toLocaleString()}</p>
        <p><strong>Policies:</strong> ${(customer.policies || []).length}</p>
        <p><strong>Claims:</strong> ${(customer.claim_history || []).length}</p>
        <p><strong>Satisfaction:</strong> ${customer.satisfaction_score || 'N/A'}/5.0 ⭐</p>
        <p><strong>Risk Score:</strong> ${customer.risk_score != null ? (customer.risk_score * 100).toFixed(0) + '%' : 'N/A'}</p>
        <p><strong>Data Source:</strong> ${customer.data_source || 'unknown'}</p>
    `;
    
    document.getElementById('customerInfo').innerHTML = infoHtml;
    
    // Load weather for customer location
    loadCustomerWeather(customer);
    
    // Load hazard risk if ZIP is available
    if (customer.zip) {
        loadHazardRisk(customer.zip);
    }
    
    const activityHtml = `
        <div class="insight-card">
            <div class="insight-icon">📋</div>
            <div class="insight-title">Policies</div>
            <div class="insight-description">${(customer.policies || []).length} active policies</div>
        </div>
        <div class="insight-card">
            <div class="insight-icon">📄</div>
            <div class="insight-title">Claims</div>
            <div class="insight-description">${(customer.claim_history || []).length} claims on file</div>
        </div>
    `;
    
    document.getElementById('recentActivity').innerHTML = activityHtml;
}

// Load current weather for customer's location
async function loadCustomerWeather(customer) {
    const weatherSection = document.getElementById('weatherSection');
    const weatherContent = document.getElementById('weatherContent');
    
    // Determine location (prefer ZIP for accurate customer-local weather)
    const location = customer.zip || customer.state || customer.region;
    if (!location) {
        weatherSection.style.display = 'none';
        return;
    }
    
    weatherSection.style.display = 'block';
    weatherContent.innerHTML = '<div class="loading" style="padding: 15px;">Loading weather data...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/weather/current?location=${encodeURIComponent(location)}&units=imperial`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        
        if (data.error) {
            weatherContent.innerHTML = `<p style="color: #999;">Weather data unavailable: ${data.error}</p>`;
            return;
        }
        
        let html = '<div class="weather-grid">';
        
        // Temperature
        const temp = data.temperature?.value ?? data.temperature ?? '--';
        const feelsLike = data.feels_like?.value ?? data.feels_like ?? '';
        const temperatureUnit = (data.temperature_unit || data.temperature?.unit || 'F').toString().toUpperCase();
        html += `
            <div class="weather-metric">
                <div class="metric-icon">🌡️</div>
                <div class="metric-value">${typeof temp === 'number' ? Math.round(temp) + `°${temperatureUnit}` : temp}</div>
                <div class="metric-label">Temperature${feelsLike ? ` (Feels ${typeof feelsLike === 'number' ? Math.round(feelsLike) + `°${temperatureUnit}` : feelsLike})` : ''}</div>
            </div>
        `;
        
        // Conditions
        const conditions = data.conditions || data.description || data.weather_description || '--';
        html += `
            <div class="weather-metric">
                <div class="metric-icon">${getWeatherIcon(conditions)}</div>
                <div class="metric-value" style="font-size: 1.2em;">${conditions}</div>
                <div class="metric-label">Conditions</div>
            </div>
        `;
        
        // Humidity
        const humidity = data.humidity?.value ?? data.humidity ?? '--';
        html += `
            <div class="weather-metric">
                <div class="metric-icon">💧</div>
                <div class="metric-value">${typeof humidity === 'number' ? humidity + '%' : humidity}</div>
                <div class="metric-label">Humidity</div>
            </div>
        `;
        
        // Wind
        const windSpeed = data.wind?.speed?.value ?? data.wind_speed ?? data.wind?.speed ?? '--';
        const windUnit = data.wind_unit || data.wind?.speed?.unit || 'mph';
        html += `
            <div class="weather-metric">
                <div class="metric-icon">💨</div>
                <div class="metric-value">${typeof windSpeed === 'number' ? Math.round(windSpeed) + ' ' + windUnit : windSpeed}</div>
                <div class="metric-label">Wind Speed</div>
            </div>
        `;
        
        html += '</div>';
        
        // AI narrative if available
        if (data.ai_insurance_narrative) {
            html += `
                <div class="weather-ai-narrative">
                    <h4>🤖 AI Insurance Weather Analysis</h4>
                    ${formatAIText(data.ai_insurance_narrative)}
                </div>
            `;
        }
        
        // Timestamp
        if (data.retrieved_at) {
            html += `<div class="weather-timestamp">Updated: ${new Date(data.retrieved_at).toLocaleString()}</div>`;
        }
        
        weatherContent.innerHTML = html;
    } catch (error) {
        console.error('Error loading weather:', error);
        weatherContent.innerHTML = '<p style="color: #999;">Unable to load weather data for this location.</p>';
    }
}

// Get weather icon based on conditions text
function getWeatherIcon(conditions) {
    if (!conditions) return '🌤️';
    const c = conditions.toLowerCase();
    if (c.includes('rain') || c.includes('drizzle')) return '🌧️';
    if (c.includes('snow') || c.includes('sleet')) return '🌨️';
    if (c.includes('thunder') || c.includes('storm')) return '⛈️';
    if (c.includes('cloud') || c.includes('overcast')) return '☁️';
    if (c.includes('fog') || c.includes('mist') || c.includes('haze')) return '🌫️';
    if (c.includes('clear') || c.includes('sunny')) return '☀️';
    if (c.includes('partly')) return '⛅';
    if (c.includes('wind')) return '💨';
    return '🌤️';
}

// Format AI-generated text: convert raw strings with newlines, bullets, dashes into clean HTML
function formatAIText(text) {
    if (!text) return '';
    if (typeof text !== 'string') {
        // If it's an object/array, render it nicely
        if (Array.isArray(text)) {
            return '<ul>' + text.map(item => `<li>${formatAIText(item)}</li>`).join('') + '</ul>';
        }
        if (typeof text === 'object') {
            let html = '';
            for (const [key, value] of Object.entries(text)) {
                html += `<p><strong>${formatLabel(key)}:</strong> ${typeof value === 'object' ? formatAIText(value) : value}</p>`;
            }
            return html;
        }
        return String(text);
    }
    
    // Split by newlines and process each line
    const lines = text.split(/\n/).map(l => l.trim()).filter(l => l.length > 0);
    
    let html = '';
    let inList = false;
    
    for (const line of lines) {
        // Check if this line is a bullet/dash/numbered item
        const bulletMatch = line.match(/^[\-\*•→]\s*(.*)/) || line.match(/^\d+[\.\)]\s*(.*)/);
        
        if (bulletMatch) {
            if (!inList) { html += '<ul>'; inList = true; }
            html += `<li>${bulletMatch[1]}</li>`;
        } else {
            if (inList) { html += '</ul>'; inList = false; }
            // Check if it looks like a section header (ends with colon or is all caps/title case and short)
            if (line.endsWith(':') && line.length < 60) {
                html += `<strong>${line}</strong>`;
            } else {
                html += `<p>${line}</p>`;
            }
        }
    }
    if (inList) html += '</ul>';
    
    return html;
}

// Format an AI response object into readable HTML sections
function formatAIResponse(data, excludeKeys = []) {
    const skip = new Set(['customer_id', 'retrieved_at', 'generated_at', 'ai_generated', 'context', ...excludeKeys]);
    let html = '';
    
    for (const [key, value] of Object.entries(data)) {
        if (skip.has(key)) continue;
        
        if (Array.isArray(value)) {
            html += `<div class="ai-section"><h4>${formatLabel(key)}</h4>`;
            if (value.length === 0) {
                html += '<p>None available</p>';
            } else if (typeof value[0] === 'string') {
                html += '<ul>' + value.map(v => `<li>${v}</li>`).join('') + '</ul>';
            } else if (typeof value[0] === 'object') {
                // Array of objects - render each as a card
                value.forEach(item => {
                    html += '<div class="info-card">';
                    for (const [k, v] of Object.entries(item)) {
                        if (Array.isArray(v)) {
                            html += `<p><strong>${formatLabel(k)}:</strong></p><ul>${v.map(x => `<li>${x}</li>`).join('')}</ul>`;
                        } else {
                            html += `<p><strong>${formatLabel(k)}:</strong> ${v}</p>`;
                        }
                    }
                    html += '</div>';
                });
            }
            html += '</div>';
        } else if (typeof value === 'object' && value !== null) {
            html += `<div class="ai-section"><h4>${formatLabel(key)}</h4>`;
            for (const [k, v] of Object.entries(value)) {
                if (Array.isArray(v)) {
                    html += `<p><strong>${formatLabel(k)}:</strong></p><ul>${v.map(x => `<li>${typeof x === 'object' ? JSON.stringify(x) : x}</li>`).join('')}</ul>`;
                } else if (typeof v === 'object' && v !== null) {
                    html += `<p><strong>${formatLabel(k)}:</strong></p>`;
                    for (const [kk, vv] of Object.entries(v)) {
                        html += `<p style="margin-left: 15px;">• <strong>${formatLabel(kk)}:</strong> ${vv}</p>`;
                    }
                } else {
                    html += `<p><strong>${formatLabel(k)}:</strong> ${v}</p>`;
                }
            }
            html += '</div>';
        } else if (typeof value === 'string' && value.length > 80) {
            // Long text — format it nicely
            html += `<div class="ai-section"><h4>${formatLabel(key)}</h4>${formatAIText(value)}</div>`;
        } else {
            html += `<div class="ai-section"><p><strong>${formatLabel(key)}:</strong> ${value}</p></div>`;
        }
    }
    
    return html;
}

// Load policies tab
function loadPoliciesTab(customer) {
    const policies = customer.policies || [];
    let html = `<h3>Active Policies (${policies.length})</h3>`;
    
    if (policies.length === 0) {
        html += '<p>No policies found for this customer.</p>';
    } else {
        policies.forEach(policy => {
            html += `
                <div class="info-card">
                    <h4>${policy.type}</h4>
                    <p><strong>Policy #:</strong> ${policy.policy_number}</p>
                    <p><strong>Premium:</strong> $${policy.premium.toLocaleString()}/year</p>
                    <p><strong>Status:</strong> ${policy.status}</p>
                    <p><strong>Coverage:</strong> ${policy.coverage || 'Standard'}</p>
                    ${policy.effective_date ? `<p><strong>Effective:</strong> ${policy.effective_date}</p>` : ''}
                    ${policy.expiration_date ? `<p><strong>Expires:</strong> ${policy.expiration_date}</p>` : ''}
                </div>
            `;
        });
        
        const totalPremium = policies.reduce((sum, p) => sum + (p.premium || 0), 0);
        html += `<p style="margin-top: 20px;"><strong>Total Annual Premium:</strong> $${totalPremium.toLocaleString()}</p>`;
    }
    
    document.getElementById('policiesList').innerHTML = html;
}

// Show cross-sell opportunities (from API)
async function showCrossSell() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💰 Cross-Sell Opportunities';
    document.getElementById('panelContent').innerHTML = '<div class="loading">Loading recommendations...</div>';
    panel.classList.add('open');
    
    try {
        const response = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(currentCustomer)}/cross-sell`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        let html = '<h3>Cross-Sell Recommendations';
        if (data.ai_generated) html += ' <span class="ai-badge">🤖 AI Generated</span>';
        html += '</h3>';
        
        if (data.total_potential_revenue || data.total_additional_revenue) {
            const rev = data.total_potential_revenue || data.total_additional_revenue || 0;
            html += `<p style="margin-bottom: 15px; font-size: 1.1em;">💰 <strong>Total Revenue Potential:</strong> $${Number(rev).toLocaleString()}/year</p>`;
        }
        
        const recommendations = data.recommendations || data.opportunities || [];
        if (recommendations.length === 0 && typeof data === 'object') {
            html += formatAIResponse(data);
        } else {
            recommendations.forEach(rec => {
                html += `
                    <div class="recommendation-card">
                        <div class="recommendation-header">
                            <h4>${rec.product || rec.name || rec.type || 'Recommendation'}</h4>
                            <span class="priority-badge priority-${(rec.priority || 'medium').toLowerCase()}">${rec.priority || 'Medium'}</span>
                        </div>
                        ${rec.confidence ? `<p><strong>Confidence:</strong> ${typeof rec.confidence === 'number' && rec.confidence <= 1 ? (rec.confidence * 100).toFixed(0) : rec.confidence}%</p>` : ''}
                        ${rec.potential_premium ? `<p><strong>Potential Premium:</strong> $${Number(rec.potential_premium).toLocaleString()}/year</p>` : ''}
                        ${rec.bundle_discount ? `<p><strong>Bundle Discount:</strong> ${rec.bundle_discount}% off</p>` : ''}
                        ${rec.reasoning ? `<p><strong>Reasoning:</strong> ${rec.reasoning}</p>` : ''}
                        ${rec.talking_points && rec.talking_points.length > 0 ? `<h5 style="margin-top: 10px;">Talking Points:</h5><ul>${rec.talking_points.map(t => `<li>${t}</li>`).join('')}</ul>` : ''}
                        <button class="btn btn-success" style="margin-top: 10px;">Generate Quote</button>
                    </div>
                `;
            });
        }
        
        document.getElementById('panelContent').innerHTML = html;
    } catch (error) {
        console.error('Error loading cross-sell:', error);
        document.getElementById('panelContent').innerHTML = '<p style="color: red;">Error loading recommendations.</p>';
    }
}

// Show up-sell options (from API)
async function showUpSell() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '📈 Up-Sell Opportunities';
    document.getElementById('panelContent').innerHTML = '<div class="loading">Loading upgrade options...</div>';
    panel.classList.add('open');
    
    try {
        const response = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(currentCustomer)}/upsell`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        let html = '<h3>Policy Enhancement Options';
        if (data.ai_generated) html += ' <span class="ai-badge">🤖 AI Generated</span>';
        html += '</h3>';
        
        if (data.total_additional_revenue) {
            html += `<p style="margin-bottom: 15px; font-size: 1.1em;">📈 <strong>Total Additional Revenue:</strong> +$${Number(data.total_additional_revenue).toLocaleString()}/year</p>`;
        }
        
        const recommendations = data.recommendations || data.opportunities || [];
        if (recommendations.length === 0 && typeof data === 'object') {
            html += formatAIResponse(data);
        } else {
            recommendations.forEach(rec => {
                html += `
                    <div class="recommendation-card">
                        <div class="recommendation-header">
                            <h4>${rec.product || rec.policy_type || rec.name || rec.type || 'Upgrade Option'}</h4>
                            <span class="priority-badge priority-${(rec.priority || 'medium').toLowerCase()}">${rec.priority || 'Medium'}</span>
                        </div>
                        ${rec.current_coverage ? `<p><strong>Current:</strong> ${rec.current_coverage}</p>` : ''}
                        ${rec.recommended_coverage || rec.recommended ? `<p><strong>Recommended:</strong> ${rec.recommended_coverage || rec.recommended}</p>` : ''}
                        ${rec.confidence ? `<p><strong>Confidence:</strong> ${typeof rec.confidence === 'number' && rec.confidence <= 1 ? (rec.confidence * 100).toFixed(0) : rec.confidence}%</p>` : ''}
                        ${rec.additional_premium ? `<p><strong>Additional Premium:</strong> +$${Number(rec.additional_premium).toLocaleString()}/year</p>` : ''}
                        ${rec.reasoning ? `<p><strong>Reasoning:</strong> ${rec.reasoning}</p>` : ''}
                        ${rec.benefits && rec.benefits.length > 0 ? `<h5 style="margin-top: 10px;">Benefits:</h5><ul>${rec.benefits.map(b => `<li>${b}</li>`).join('')}</ul>` : ''}
                        ${rec.talking_points && rec.talking_points.length > 0 ? `<h5 style="margin-top: 10px;">Talking Points:</h5><ul>${rec.talking_points.map(t => `<li>${t}</li>`).join('')}</ul>` : ''}
                        <button class="btn btn-info" style="margin-top: 10px;">Present Upgrade</button>
                    </div>
                `;
            });
        }
        
        document.getElementById('panelContent').innerHTML = html;
    } catch (error) {
        console.error('Error loading upsell:', error);
        document.getElementById('panelContent').innerHTML = '<p style="color: red;">Error loading upgrade options.</p>';
    }
}

// Show customer insights (from API)
async function showInsights() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💡 Customer Insights & Trends';
    document.getElementById('panelContent').innerHTML = '<div class="loading">Loading insights...</div>';
    panel.classList.add('open');
    
    try {
        const response = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(currentCustomer)}/insights`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        let html = '<h3>AI-Powered Insights';
        if (data.ai_generated) html += ' <span class="ai-badge">🤖 AI Generated</span>';
        html += '</h3>';
        
        const insights = data.insights || [];
        if (insights.length > 0 && typeof insights[0] === 'object' && insights[0].title) {
            // Structured insight objects with title/description/action
            insights.forEach(insight => {
                const icon = insight.icon || '💡';
                html += `
                    <div class="insight-card">
                        <div class="insight-icon">${icon}</div>
                        <div class="insight-title">${insight.title || insight.category || 'Insight'}</div>
                        <div class="insight-description">${insight.description || ''}</div>
                        ${insight.action ? `<div class="insight-action"><strong>Action:</strong> ${insight.action}</div>` : ''}
                    </div>
                `;
            });
        } else if (insights.length > 0) {
            // Array of strings or simpler objects
            insights.forEach(insight => {
                html += `<div class="insight-card"><div class="insight-description">${typeof insight === 'string' ? insight : formatAIText(JSON.stringify(insight))}</div></div>`;
            });
        } else {
            // Fallback: format the entire response nicely
            html += formatAIResponse(data);
        }
        
        // Overall health if present
        if (data.overall_health) {
            const h = data.overall_health;
            html += `<div class="ai-section" style="margin-top: 20px;">
                <h4>Overall Health Score</h4>
                <p style="font-size: 1.4em; font-weight: bold; color: ${h.color || '#333'};">
                    ${h.score}/100 — ${h.rating}
                </p>
            </div>`;
        }
        
        // Load trends
        try {
            const trendsResponse = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(currentCustomer)}/trends`);
            if (trendsResponse.ok) {
                const trends = await trendsResponse.json();
                html += '<h3 style="margin-top: 30px;">📈 Customer Trends';
                if (trends.ai_generated) html += ' <span class="ai-badge">🤖 AI Generated</span>';
                html += '</h3>';
                
                // Key observations
                if (trends.key_observations && trends.key_observations.length > 0) {
                    html += '<div class="ai-section"><h4>Key Observations</h4><ul>';
                    trends.key_observations.forEach(obs => { html += `<li>${obs}</li>`; });
                    html += '</ul></div>';
                }
                
                // Trends
                if (trends.trends && typeof trends.trends === 'object') {
                    html += '<div class="ai-section"><h4>Trend Summary</h4>';
                    for (const [key, value] of Object.entries(trends.trends)) {
                        const icon = value === 'increasing' || value === 'improving' ? '📈' :
                                     value === 'decreasing' ? '📉' : '➡️';
                        html += `<p>${icon} <strong>${formatLabel(key)}:</strong> ${formatLabel(String(value))}</p>`;
                    }
                    html += '</div>';
                }
                
                // Predictions
                if (trends.predictions && typeof trends.predictions === 'object') {
                    html += '<div class="ai-section"><h4>Predictions</h4>';
                    for (const [key, value] of Object.entries(trends.predictions)) {
                        const display = typeof value === 'number' && value <= 1 ? (value * 100).toFixed(0) + '%' : value;
                        html += `<p><strong>${formatLabel(key)}:</strong> ${display}</p>`;
                    }
                    html += '</div>';
                }
            }
        } catch (e) {
            console.warn('Could not load trends:', e);
        }
        
        document.getElementById('panelContent').innerHTML = html;
    } catch (error) {
        console.error('Error loading insights:', error);
        document.getElementById('panelContent').innerHTML = '<p style="color: red;">Error loading insights.</p>';
    }
}

// Helper function to calculate years since a date
function calculateYearsSince(dateString) {
    const MS_PER_YEAR = 1000 * 60 * 60 * 24 * 365;
    const date = new Date(dateString);
    const now = new Date();
    return ((now - date) / MS_PER_YEAR).toFixed(1);
}

// Show talking points (from API)
async function showTalkingPoints() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💬 AI-Generated Talking Points';
    document.getElementById('panelContent').innerHTML = '<div class="loading">Generating talking points...</div>';
    panel.classList.add('open');
    
    try {
        const response = await fetch(`${API_BASE}/api/customers/${encodeURIComponent(currentCustomer)}/talking-points?context=general`);
        
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        const data = await response.json();
        let html = '<h3>Conversation Guide';
        if (data.ai_generated) html += ' <span class="ai-badge">🤖 AI Generated</span>';
        html += '</h3>';
        
        const tp = data.talking_points || data;
        
        // Greeting
        if (tp.greeting) {
            html += `<div class="info-card"><h4>👋 Greeting</h4><p>${tp.greeting}</p></div>`;
        }
        
        // Relationship highlights
        if (tp.relationship_highlights && tp.relationship_highlights.length > 0) {
            html += `<div class="info-card"><h4>🤝 Relationship Highlights</h4><ul>`;
            tp.relationship_highlights.forEach(h => { html += `<li>${h}</li>`; });
            html += `</ul></div>`;
        }
        
        // Conversation starters
        if (tp.conversation_starters && tp.conversation_starters.length > 0) {
            html += `<div class="info-card"><h4>💬 Conversation Starters</h4><ul>`;
            tp.conversation_starters.forEach(s => { html += `<li>${s}</li>`; });
            html += `</ul></div>`;
        }
        
        // Key facts
        if (tp.key_facts && tp.key_facts.length > 0) {
            html += `<div class="info-card"><h4>📋 Key Facts</h4><ul>`;
            tp.key_facts.forEach(f => { html += `<li>${f}</li>`; });
            html += `</ul></div>`;
        }
        
        // Objection handlers (AI-generated)
        if (tp.objection_handlers && tp.objection_handlers.length > 0) {
            html += `<div class="info-card"><h4>🛡️ Objection Handlers</h4><ul>`;
            tp.objection_handlers.forEach(o => { html += `<li>${o}</li>`; });
            html += `</ul></div>`;
        }
        
        // Closing
        if (tp.closing) {
            html += `<div class="info-card"><h4>✅ Closing</h4><p>${tp.closing}</p></div>`;
        }
        
        // Fallback for any other keys we haven't explicitly handled
        const handled = new Set(['greeting', 'relationship_highlights', 'conversation_starters', 'key_facts', 'objection_handlers', 'closing']);
        for (const [key, value] of Object.entries(tp)) {
            if (handled.has(key) || key === 'customer_id' || key === 'retrieved_at' || key === 'generated_at' || key === 'ai_generated' || key === 'context' || key === 'talking_points') continue;
            html += `<div class="info-card"><h4>${formatLabel(key)}</h4>`;
            if (Array.isArray(value)) {
                html += '<ul>' + value.map(v => `<li>${typeof v === 'object' ? JSON.stringify(v) : v}</li>`).join('') + '</ul>';
            } else if (typeof value === 'string') {
                html += formatAIText(value);
            } else if (typeof value === 'object' && value !== null) {
                html += formatAIText(value);
            } else {
                html += `<p>${value}</p>`;
            }
            html += '</div>';
        }
        
        document.getElementById('panelContent').innerHTML = html;
    } catch (error) {
        console.error('Error loading talking points:', error);
        document.getElementById('panelContent').innerHTML = '<p style="color: red;">Error loading talking points.</p>';
    }
}

// Close panel
function closePanel() {
    document.getElementById('insightsPanel').classList.remove('open');
}

// Show tab
function showTab(tabName, event) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load recommendations tab if selected
    if (tabName === 'recommendations') {
        loadRecommendationsTab();
    } else if (tabName === 'insights') {
        loadInsightsTab();
    }
}

// Load recommendations tab
function loadRecommendationsTab() {
    const customer = currentCustomerData;
    if (!customer) return;
    
    let html = '<h3>AI-Powered Recommendations</h3>';
    html += '<p style="margin-bottom: 20px; color: #666;">One-click access to cross-sell and up-sell opportunities</p>';
    
    html += '<div class="quick-actions" style="margin-bottom: 30px;">';
    html += '<button onclick="showCrossSell()" class="btn btn-success">View Cross-Sell</button>';
    html += '<button onclick="showUpSell()" class="btn btn-info">View Up-Sell</button>';
    html += '</div>';
    
    html += '<h4>Summary</h4>';
    const policyCount = (customer.policies || []).length;
    html += `<p>✅ ${policyCount} active policies</p>`;
    html += `<p>✅ Total Premium: $${(customer.lifetime_value || 0).toLocaleString()}</p>`;
    html += `<p>✅ ${(customer.claim_history || []).length} claims on file</p>`;
    
    document.getElementById('recommendationsList').innerHTML = html;
}

// Load insights tab
function loadInsightsTab() {
    const customer = currentCustomerData;
    if (!customer) return;
    
    let html = '<h3>Customer Intelligence</h3>';
    html += '<p style="margin-bottom: 20px; color: #666;">Real-time insights and trend analysis</p>';
    
    // Show AI summary if available
    if (customer.ai_summary) {
        html += `<div class="info-card" style="border-left: 4px solid #667eea; margin-bottom: 20px;">
            <h4>🤖 AI Customer Summary</h4>
            <p style="line-height: 1.6;">${customer.ai_summary}</p>
        </div>`;
    }
    
    html += '<div class="quick-actions" style="margin-bottom: 30px;">';
    html += '<button onclick="showInsights()" class="btn btn-warning">View All Insights</button>';
    html += '<button onclick="showTalkingPoints()" class="btn btn-secondary">Get Talking Points</button>';
    html += '</div>';
    
    html += '<h4>Quick Insights</h4>';
    html += `<div class="insight-card">
        <strong>Customer Type:</strong> ${customer.type} — ${customer.income_band || 'N/A'} income
    </div>`;
    
    html += `<div class="insight-card">
        <strong>Risk Score:</strong> ${customer.risk_score != null ? (customer.risk_score * 100).toFixed(0) + '%' : 'N/A'}
    </div>`;
    
    html += `<div class="insight-card">
        <strong>Satisfaction:</strong> ${customer.satisfaction_score || 'N/A'}/5.0
    </div>`;
    
    document.getElementById('insightsList').innerHTML = html;
}

// Load hazard risk data for a ZIP code
async function loadHazardRisk(zipCode) {
    const hazardSection = document.getElementById('hazardRiskSection');
    hazardSection.style.display = 'block';
    
    // Load all three hazard types in parallel
    try {
        const [floodData, wildfireData, earthquakeData] = await Promise.all([
            fetchHazardRisk('flood', zipCode),
            fetchHazardRisk('wildfire', zipCode),
            fetchHazardRisk('earthquake', zipCode)
        ]);
        
        displayHazardRisk('flood', floodData);
        displayHazardRisk('wildfire', wildfireData);
        displayHazardRisk('earthquake', earthquakeData);
    } catch (error) {
        console.error('Error loading hazard risk:', error);
        hazardSection.style.display = 'none';
    }
}

// Fetch hazard risk data from API
async function fetchHazardRisk(hazardType, zipCode) {
    try {
        const response = await fetch(`${API_BASE}/api/risk/${hazardType}?zip=${zipCode}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${hazardType} risk:`, error);
        return {
            hazard_type: hazardType,
            zip: zipCode,
            risk_score: 0,
            band: 'Unknown',
            drivers: ['Data unavailable - API not responding'],
            error: error.message
        };
    }
}

// Display hazard risk data in the card
function displayHazardRisk(hazardType, data) {
    const scoreElem = document.getElementById(`${hazardType}Score`);
    const bandElem = document.getElementById(`${hazardType}Band`);
    const driversElem = document.getElementById(`${hazardType}Drivers`);
    
    if (!data || data.error) {
        scoreElem.textContent = '--';
        bandElem.textContent = 'Data Unavailable';
        bandElem.className = 'risk-band';
        driversElem.innerHTML = '<small>Unable to load risk data</small>';
        return;
    }
    
    // Display score
    scoreElem.textContent = data.risk_score.toFixed(0);
    
    // Display band with appropriate styling
    bandElem.textContent = data.band;
    bandElem.className = `risk-band ${data.band.toLowerCase()}`;
    
    // Display drivers
    if (data.drivers && data.drivers.length > 0) {
        const driversHtml = `
            <strong style="display: block; margin-bottom: 8px;">Key Factors:</strong>
            <ul style="margin: 0; padding-left: 0;">
                ${data.drivers.map(driver => `<li>${driver}</li>`).join('')}
            </ul>
        `;
        driversElem.innerHTML = driversHtml;
    } else {
        driversElem.innerHTML = '<small>No significant risk factors identified</small>';
    }
}

// Helper: render a generic data object as a recommendation card
function renderGenericRecommendation(data) {
    let html = '<div class="recommendation-card">';
    for (const [key, value] of Object.entries(data)) {
        if (key === 'customer_id' || key === 'retrieved_at') continue;
        if (Array.isArray(value)) {
            html += `<p><strong>${formatLabel(key)}:</strong></p><ul>${value.map(v => `<li>${typeof v === 'object' ? JSON.stringify(v) : v}</li>`).join('')}</ul>`;
        } else if (typeof value === 'object' && value !== null) {
            html += `<p><strong>${formatLabel(key)}:</strong></p><pre style="white-space:pre-wrap;">${JSON.stringify(value, null, 2)}</pre>`;
        } else {
            html += `<p><strong>${formatLabel(key)}:</strong> ${value}</p>`;
        }
    }
    html += '</div>';
    return html;
}

// Helper: format a snake_case or camelCase label to Title Case
function formatLabel(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .replace(/^\w/, c => c.toUpperCase())
        .trim();
}