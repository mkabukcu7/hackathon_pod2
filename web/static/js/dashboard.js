// Insurance Agent Dashboard JavaScript

const API_BASE = 'http://localhost:8000';
let currentCustomer = null;

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

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        // Mock data for demo
        document.getElementById('totalCustomers').textContent = '3';
        document.getElementById('activeOpportunities').textContent = '12';
        document.getElementById('aiInsights').textContent = '8';
        document.getElementById('retentionScore').textContent = '89%';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Search for customer
async function searchCustomer() {
    const query = document.getElementById('customerSearch').value.trim();
    if (!query) return;
    
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<div class="loading">Searching...</div>';
    
    try {
        // Try mock search first
        const mockResults = searchMockCustomers(query);
        
        if (mockResults.length > 0) {
            displaySearchResults(mockResults);
        } else {
            resultsDiv.innerHTML = '<p>No customers found. Try "Sarah", "Michael", or "Jennifer"</p>';
        }
    } catch (error) {
        console.error('Error searching:', error);
        resultsDiv.innerHTML = '<p style="color: red;">Error searching for customers. Please try again.</p>';
    }
}

// Mock customer search (when API is not available)
function searchMockCustomers(query) {
    const mockCustomers = [
        { id: 'C001', name: 'Sarah Johnson', email: 'sarah.johnson@email.com', type: 'Premium', policy_count: 2, lifetime_value: 45000 },
        { id: 'C002', name: 'Michael Chen', email: 'm.chen@techcorp.com', type: 'Standard', policy_count: 1, lifetime_value: 8500 },
        { id: 'C003', name: 'Jennifer Martinez', email: 'jmartinez@consulting.com', type: 'Premium', policy_count: 3, lifetime_value: 125000 }
    ];
    
    const queryLower = query.toLowerCase();
    return mockCustomers.filter(c => 
        c.name.toLowerCase().includes(queryLower) ||
        c.email.toLowerCase().includes(queryLower) ||
        c.id.toLowerCase().includes(queryLower)
    );
}

// Display search results
function displaySearchResults(results) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (results.length === 0) {
        resultsDiv.innerHTML = '<p>No customers found</p>';
        return;
    }
    
    let html = '<h3>Search Results</h3>';
    results.forEach(customer => {
        html += `
            <div class="result-item" onclick='selectCustomer("${customer.id}")'>
                <strong>${customer.name}</strong> (${customer.id})
                <br>
                <small>${customer.email} • ${customer.type} • ${customer.policy_count} policies • $${customer.lifetime_value.toLocaleString()} LTV</small>
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
    
    // Load customer data
    await loadCustomerProfile(customerId);
}

// Load customer profile
async function loadCustomerProfile(customerId) {
    try {
        // Load mock customer data
        const customer = getMockCustomer(customerId);
        
        if (!customer) {
            alert('Customer not found');
            return;
        }
        
        // Update header
        document.getElementById('customerName').textContent = customer.name;
        const typeClass = customer.type === 'Premium' ? 'badge-premium' : 'badge-standard';
        document.getElementById('customerType').className = `badge ${typeClass}`;
        document.getElementById('customerType').textContent = customer.type;
        
        // Load overview tab
        loadOverviewTab(customer);
        loadPoliciesTab(customer);
    } catch (error) {
        console.error('Error loading customer profile:', error);
    }
}

// Get mock customer data
function getMockCustomer(customerId) {
    const mockData = {
        'C001': {
            id: 'C001',
            name: 'Sarah Johnson',
            email: 'sarah.johnson@email.com',
            phone: '+1-555-0101',
            zip: '90001',
            type: 'Premium',
            status: 'Active',
            join_date: '2020-03-15',
            policies: [
                { policy_number: 'AUTO-2020-001', type: 'Auto Insurance', premium: 1250, status: 'Active', coverage: 'Standard' },
                { policy_number: 'HOME-2021-045', type: 'Home Insurance', premium: 1800, status: 'Active', coverage: 'Premium' }
            ],
            lifetime_value: 45000,
            satisfaction_score: 4.5,
            risk_score: 0.25
        },
        'C002': {
            id: 'C002',
            name: 'Michael Chen',
            email: 'm.chen@techcorp.com',
            phone: '+1-555-0202',
            zip: '33101',
            type: 'Standard',
            status: 'Active',
            join_date: '2022-08-10',
            policies: [
                { policy_number: 'AUTO-2022-089', type: 'Auto Insurance', premium: 980, status: 'Active', coverage: 'Standard' }
            ],
            lifetime_value: 8500,
            satisfaction_score: 4.2,
            risk_score: 0.15
        },
        'C003': {
            id: 'C003',
            name: 'Jennifer Martinez',
            email: 'jmartinez@consulting.com',
            phone: '+1-555-0303',
            zip: '94102',
            type: 'Premium',
            status: 'Active',
            join_date: '2019-01-20',
            policies: [
                { policy_number: 'HOME-2019-012', type: 'Home Insurance', premium: 2200, status: 'Active', coverage: 'Premium Plus' },
                { policy_number: 'AUTO-2019-013', type: 'Auto Insurance', premium: 1400, status: 'Active', coverage: 'Comprehensive' },
                { policy_number: 'LIFE-2020-078', type: 'Life Insurance', premium: 3200, status: 'Active', coverage: 'Term Life - 500K' }
            ],
            lifetime_value: 125000,
            satisfaction_score: 4.8,
            risk_score: 0.10
        }
    };
    
    return mockData[customerId];
}

// Load overview tab
function loadOverviewTab(customer) {
    const infoHtml = `
        <p><strong>Customer ID:</strong> ${customer.id}</p>
        <p><strong>Email:</strong> ${customer.email}</p>
        <p><strong>Phone:</strong> ${customer.phone}</p>
        <p><strong>ZIP Code:</strong> ${customer.zip || 'N/A'}</p>
        <p><strong>Status:</strong> ${customer.status}</p>
        <p><strong>Member Since:</strong> ${customer.join_date}</p>
        <p><strong>Lifetime Value:</strong> $${customer.lifetime_value.toLocaleString()}</p>
        <p><strong>Satisfaction:</strong> ${customer.satisfaction_score}/5.0 ⭐</p>
        <p><strong>Risk Score:</strong> ${(customer.risk_score * 100).toFixed(0)}%</p>
    `;
    
    document.getElementById('customerInfo').innerHTML = infoHtml;
    
    // Load hazard risk if ZIP is available
    if (customer.zip) {
        loadHazardRisk(customer.zip);
    }
    
    const activityHtml = `
        <div class="insight-card">
            <div class="insight-icon">📞</div>
            <div class="insight-title">Last Contact</div>
            <div class="insight-description">2 weeks ago - Policy review call</div>
        </div>
        <div class="insight-card">
            <div class="insight-icon">✅</div>
            <div class="insight-title">Recent Payment</div>
            <div class="insight-description">Auto insurance premium - On time</div>
        </div>
    `;
    
    document.getElementById('recentActivity').innerHTML = activityHtml;
}

// Load policies tab
function loadPoliciesTab(customer) {
    let html = '<h3>Active Policies</h3>';
    
    customer.policies.forEach(policy => {
        html += `
            <div class="info-card">
                <h4>${policy.type}</h4>
                <p><strong>Policy #:</strong> ${policy.policy_number}</p>
                <p><strong>Premium:</strong> $${policy.premium.toLocaleString()}/year</p>
                <p><strong>Status:</strong> ${policy.status}</p>
            </div>
        `;
    });
    
    const totalPremium = customer.policies.reduce((sum, p) => sum + p.premium, 0);
    html += `<p style="margin-top: 20px;"><strong>Total Annual Premium:</strong> $${totalPremium.toLocaleString()}</p>`;
    
    document.getElementById('policiesList').innerHTML = html;
}

// Show cross-sell opportunities
function showCrossSell() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💰 Cross-Sell Opportunities';
    
    let html = '<h3>AI-Generated Recommendations</h3>';
    
    const customer = getMockCustomer(currentCustomer);
    const hasPolicies = customer.policies.map(p => p.type);
    
    if (!hasPolicies.includes('Life Insurance')) {
        html += `
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <h4>Life Insurance</h4>
                    <span class="priority-badge priority-high">High Priority</span>
                </div>
                <p><strong>Confidence:</strong> 85%</p>
                <p><strong>Potential Premium:</strong> $2,800/year</p>
                <p><strong>Bundle Discount:</strong> 10%</p>
                <p><strong>Reasoning:</strong> Multi-policy customer with high lifetime value; good candidate for life insurance</p>
                <h5>Talking Points:</h5>
                <ul>
                    <li>As a valued multi-policy customer, you qualify for preferred rates</li>
                    <li>Protect your family's future with term life coverage</li>
                    <li>Additional 10% discount when bundled</li>
                </ul>
                <button class="btn btn-success" style="margin-top: 10px;">Generate Quote</button>
            </div>
        `;
    }
    
    html += `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <h4>Umbrella Liability Insurance</h4>
                <span class="priority-badge priority-medium">Medium Priority</span>
            </div>
            <p><strong>Confidence:</strong> 65%</p>
            <p><strong>Potential Premium:</strong> $450/year</p>
            <p><strong>Reasoning:</strong> Customer has property insurance; umbrella coverage provides extra protection</p>
            <h5>Talking Points:</h5>
            <ul>
                <li>Protect yourself from major liability claims beyond standard limits</li>
                <li>Affordable extra layer of protection for just $450/year</li>
                <li>Peace of mind with $1M to $5M in additional coverage</li>
            </ul>
            <button class="btn btn-success" style="margin-top: 10px;">Generate Quote</button>
        </div>
    `;
    
    document.getElementById('panelContent').innerHTML = html;
    panel.classList.add('open');
}

// Show up-sell options
function showUpSell() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '📈 Up-Sell Opportunities';
    
    let html = '<h3>Policy Enhancement Options</h3>';
    
    html += `
        <div class="recommendation-card">
            <div class="recommendation-header">
                <h4>Upgrade to Comprehensive Coverage</h4>
                <span class="priority-badge priority-high">High Priority</span>
            </div>
            <p><strong>Current Coverage:</strong> Standard</p>
            <p><strong>Recommended:</strong> Comprehensive</p>
            <p><strong>Additional Premium:</strong> +$350/year</p>
            <h5>Benefits:</h5>
            <ul>
                <li>Lower deductible: $250 vs $500</li>
                <li>Rental car coverage included</li>
                <li>Roadside assistance 24/7</li>
                <li>New car replacement within first 2 years</li>
            </ul>
            <h5>Talking Points:</h5>
            <ul>
                <li>Your excellent record qualifies you for our best rates</li>
                <li>Upgrade for just $29/month more</li>
                <li>Enhanced protection with lower out-of-pocket costs</li>
            </ul>
            <button class="btn btn-info" style="margin-top: 10px;">Present Upgrade</button>
        </div>
    `;
    
    document.getElementById('panelContent').innerHTML = html;
    panel.classList.add('open');
}

// Show customer insights
function showInsights() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💡 Customer Insights & Trends';
    
    const customer = getMockCustomer(currentCustomer);
    
    let html = '<h3>Real-Time AI Insights</h3>';
    
    if (customer.satisfaction_score >= 4.5) {
        html += `
            <div class="insight-card">
                <div class="insight-icon">🌟</div>
                <div class="insight-title">Highly Satisfied Customer</div>
                <div class="insight-description">Customer satisfaction score: ${customer.satisfaction_score}/5.0 - Among top 20% of customers</div>
                <div class="insight-action">Action: Opportunity for testimonial or referral program</div>
            </div>
        `;
    }
    
    if (customer.policies.length >= 3) {
        html += `
            <div class="insight-card">
                <div class="insight-icon">🎯</div>
                <div class="insight-title">Multi-Product Customer</div>
                <div class="insight-description">${customer.policies.length} active policies - High engagement and loyalty</div>
                <div class="insight-action">Action: VIP treatment and exclusive offers</div>
            </div>
        `;
    }
    
    if (customer.lifetime_value > 50000) {
        html += `
            <div class="insight-card">
                <div class="insight-icon">💎</div>
                <div class="insight-title">High-Value Customer</div>
                <div class="insight-description">Lifetime value: $${customer.lifetime_value.toLocaleString()} - Top tier customer</div>
                <div class="insight-action">Action: Prioritize with white-glove service</div>
            </div>
        `;
    }
    
    html += `
        <div class="insight-card">
            <div class="insight-icon">✅</div>
            <div class="insight-title">Excellent Claims History</div>
            <div class="insight-description">No recent claims - Perfect candidate for loyalty rewards</div>
            <div class="insight-action">Action: Offer claims-free discount or policy upgrade</div>
        </div>
    `;
    
    html += '<h3 style="margin-top: 30px;">Customer Trends</h3>';
    html += `
        <p><strong>Retention Score:</strong> 92/100 ✅</p>
        <p><strong>Engagement Trend:</strong> Stable 📊</p>
        <p><strong>Premium Trend:</strong> Increasing 📈</p>
        <p><strong>Satisfaction Trend:</strong> Improving 🎯</p>
        <p><strong>Churn Risk:</strong> Low (8%) 💚</p>
    `;
    
    document.getElementById('panelContent').innerHTML = html;
    panel.classList.add('open');
}

// Helper function to calculate years since a date
function calculateYearsSince(dateString) {
    const MS_PER_YEAR = 1000 * 60 * 60 * 24 * 365;
    const date = new Date(dateString);
    const now = new Date();
    return ((now - date) / MS_PER_YEAR).toFixed(1);
}

// Show talking points
function showTalkingPoints() {
    const panel = document.getElementById('insightsPanel');
    document.getElementById('panelTitle').textContent = '💬 AI-Generated Talking Points';
    
    const customer = getMockCustomer(currentCustomer);
    const years = calculateYearsSince(customer.join_date);
    
    let html = `
        <h3>Conversation Guide</h3>
        
        <div class="info-card">
            <h4>Opening</h4>
            <p>"Hello ${customer.name.split(' ')[0]}! It's great to connect with you today."</p>
        </div>
        
        <div class="info-card">
            <h4>Relationship Highlights</h4>
            <ul>
                <li>You've been with us for ${years} years - thank you for your loyalty!</li>
                ${customer.type === 'Premium' ? '<li>As a Premium customer, you have access to our best rates and exclusive benefits</li>' : ''}
                <li>Your satisfaction score of ${customer.satisfaction_score}/5.0 shows we're meeting your needs</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h4>Key Facts</h4>
            <ul>
                <li>Total policies: ${customer.policies.length}</li>
                <li>Customer type: ${customer.type}</li>
                <li>Satisfaction score: ${customer.satisfaction_score}/5.0</li>
                <li>Claims filed: None (excellent history!)</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h4>Conversation Starters</h4>
            <ul>
                <li>"I noticed you might benefit from bundling opportunities that could save you money"</li>
                <li>"Have you thought about enhancing your coverage to better protect your assets?"</li>
                <li>"We have some new products that align perfectly with your current policies"</li>
            </ul>
        </div>
        
        <div class="info-card">
            <h4>Closing</h4>
            <p>"Is there anything else I can help you with today? I'm here to ensure you have the best coverage for your needs."</p>
        </div>
    `;
    
    document.getElementById('panelContent').innerHTML = html;
    panel.classList.add('open');
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
    const customer = getMockCustomer(currentCustomer);
    
    let html = '<h3>AI-Powered Recommendations</h3>';
    html += '<p style="margin-bottom: 20px; color: #666;">One-click access to cross-sell and up-sell opportunities</p>';
    
    html += '<div class="quick-actions" style="margin-bottom: 30px;">';
    html += '<button onclick="showCrossSell()" class="btn btn-success">View Cross-Sell</button>';
    html += '<button onclick="showUpSell()" class="btn btn-info">View Up-Sell</button>';
    html += '</div>';
    
    html += '<h4>Summary</h4>';
    html += `<p>✅ ${customer.policies.length > 1 ? '3 cross-sell opportunities identified' : '5 cross-sell opportunities identified'}</p>`;
    html += '<p>✅ 2 up-sell opportunities available</p>';
    html += '<p>✅ Total potential revenue: $3,730/year</p>';
    
    document.getElementById('recommendationsList').innerHTML = html;
}

// Load insights tab
function loadInsightsTab() {
    const customer = getMockCustomer(currentCustomer);
    
    let html = '<h3>Customer Intelligence</h3>';
    html += '<p style="margin-bottom: 20px; color: #666;">Real-time insights and trend analysis</p>';
    
    html += '<div class="quick-actions" style="margin-bottom: 30px;">';
    html += '<button onclick="showInsights()" class="btn btn-warning">View All Insights</button>';
    html += '<button onclick="showTalkingPoints()" class="btn btn-secondary">Get Talking Points</button>';
    html += '</div>';
    
    html += '<h4>Quick Insights</h4>';
    html += `<div class="insight-card">
        <strong>Retention Score:</strong> 92/100 - Low churn risk
    </div>`;
    
    html += `<div class="insight-card">
        <strong>Customer Health:</strong> Excellent - Active engagement, high satisfaction
    </div>`;
    
    html += `<div class="insight-card">
        <strong>Upsell Readiness:</strong> 78% - Good time to present enhancements
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
        // Return mock data for demo
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
