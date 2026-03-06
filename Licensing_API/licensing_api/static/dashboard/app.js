const API_BASE = '';
let currentProductId = null;
let currentLicenses = [];
let accessToken = localStorage.getItem('access_token');

// DOM Elements
const loginScreen = document.getElementById('login-screen');
const dashboardScreen = document.getElementById('dashboard-screen');
const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const modalOverlay = document.getElementById('modal-overlay');

// Check auth on load
async function init() {
    if (accessToken) {
        // Verify token is valid
        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: { 'Authorization': `Bearer ${accessToken}` }
            });
            if (response.ok) {
                showDashboard();
                return;
            }
        } catch (e) {
            // Token invalid
        }
    }
    showLogin();
}

init();

// Login
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const formData = new URLSearchParams();
        formData.append('username', email);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: formData
        });

        if (!response.ok) {
            throw new Error('Invalid credentials');
        }

        const data = await response.json();
        accessToken = data.access_token;
        localStorage.setItem('access_token', accessToken);
        showDashboard();
    } catch (error) {
        loginError.textContent = 'Invalid email or password';
    }
});

// Logout
document.getElementById('logout-btn').addEventListener('click', () => {
    accessToken = null;
    localStorage.removeItem('access_token');
    showLogin();
});

// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        
        document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
        
        if (page === 'products') {
            document.getElementById('products-page').classList.remove('hidden');
            document.querySelector('.page-title').textContent = 'Products';
            document.querySelector('.page-subtitle').textContent = 'Manage your products and licenses';
            loadProducts();
        } else if (page === 'api-keys') {
            document.getElementById('api-keys-page').classList.remove('hidden');
            document.querySelector('.page-title').textContent = 'API Keys';
            document.querySelector('.page-subtitle').textContent = 'Manage client API access keys';
            loadApiKeys();
        } else if (page === 'audit-logs') {
            document.getElementById('audit-logs-page').classList.remove('hidden');
            document.querySelector('.page-title').textContent = 'Audit Logs';
            document.querySelector('.page-subtitle').textContent = 'View license validation and activation history';
            loadAuditLogs();
        }
    });
});

// Show Login
function showLogin() {
    loginScreen.classList.remove('hidden');
    dashboardScreen.classList.add('hidden');
    // Clear any old token to prevent issues
    accessToken = null;
    localStorage.removeItem('access_token');
}

// Show Dashboard
function showDashboard() {
    loginScreen.classList.add('hidden');
    dashboardScreen.classList.remove('hidden');
    loadProducts();
}

// API Helpers
async function apiRequest(endpoint, options = {}) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        accessToken = null;
        localStorage.removeItem('access_token');
        showLogin();
        throw new Error('Session expired');
    }
    
    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }
    
    const text = await response.text();
    if (!text) return null;
    return JSON.parse(text);
}

// Load Products
async function loadProducts() {
    const container = document.getElementById('products-list');
    container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';
    
    try {
        const products = await apiRequest('/products');
        
        if (products.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>No products yet</p>
                    <button class="btn btn-primary" onclick="showModal('product-modal')">Create First Product</button>
                </div>
            `;
            return;
        }
        
        // Get license counts for each product
        const productsWithCounts = await Promise.all(
            products.map(async (p) => {
                const licenses = await apiRequest(`/products/${p.product_id}/licenses`).catch(() => []);
                return { ...p, licenseCount: licenses.length };
            })
        );
        
        container.innerHTML = productsWithCounts.map(product => `
            <div class="card" onclick="viewProduct(${product.product_id})">
                <div class="card-header">
                    <span class="card-title">${product.product_name}</span>
                    <span class="card-code">${product.product_code}</span>
                </div>
                <div class="card-stats">
                    <div class="card-stat">
                        <span class="card-stat-value">${product.licenseCount}</span>
                        <span class="card-stat-label">Licenses</span>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<p class="error">Failed to load products</p>';
    }
}

// View Product
async function viewProduct(productId) {
    currentProductId = productId;
    
    const products = await apiRequest('/products');
    const product = products.find(p => p.product_id === productId);
    
    document.getElementById('product-title').textContent = product.product_name;
    document.getElementById('products-page').classList.add('hidden');
    document.getElementById('product-detail-page').classList.remove('hidden');
    
    loadLicenses(productId);
}

// Back to Products
document.getElementById('back-to-products').addEventListener('click', () => {
    document.getElementById('product-detail-page').classList.add('hidden');
    document.getElementById('products-page').classList.remove('hidden');
    loadProducts();
});

// Load Licenses
async function loadLicenses(productId) {
    const tbody = document.getElementById('licenses-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div></td></tr>';
    
    try {
        const licenses = await apiRequest(`/products/${productId}/licenses`);
        currentLicenses = licenses;
        
        const active = licenses.filter(l => l.state === 'active').length;
        const expired = licenses.filter(l => new Date(l.expiry_date) < new Date()).length;
        
        document.getElementById('total-licenses').textContent = licenses.length;
        document.getElementById('active-licenses').textContent = active;
        document.getElementById('expired-licenses').textContent = expired;
        
        renderLicenses(licenses);
    } catch (error) {
        console.error('Error loading licenses:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="error">Failed to load licenses</td></tr>';
    }
}

function renderLicenses(licenses) {
    const tbody = document.getElementById('licenses-table-body');
    
    if (licenses.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No licenses found</td></tr>';
        return;
    }
    
    tbody.innerHTML = licenses.map(license => {
        const isExpired = new Date(license.expiry_date) < new Date();
        const isRevoked = license.state === 'revoked' || license.is_revoked === true;
        const badgeClass = license.state === 'active' && !isExpired ? 'badge-success' : 
                         license.state === 'suspended' ? 'badge-warning' : 
                         isRevoked ? 'badge-danger' : 'badge-secondary';
        
        const displayState = isRevoked ? 'revoked' : (license.state || 'unknown');
        
        const expiryDate = new Date(license.expiry_date);
        const now = new Date();
        const daysLeft = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
        const daysLeftDisplay = daysLeft > 0 ? `${daysLeft} days` : 'Expired';
        const expiryDisplay = expiryDate.toLocaleString();
        
        return `
            <tr>
                <td onclick="showLicenseDetails('${license.license_key}')" style="cursor:pointer"><code>${license.license_key}</code></td>
                <td onclick="showLicenseDetails('${license.license_key}')" style="cursor:pointer">${license.company_name}</td>
                <td onclick="showLicenseDetails('${license.license_key}')" style="cursor:pointer"><span class="badge ${badgeClass}">${displayState}</span></td>
                <td onclick="showLicenseDetails('${license.license_key}')" style="cursor:pointer">${daysLeftDisplay}</td>
                <td onclick="showLicenseDetails('${license.license_key}')" style="cursor:pointer" title="${expiryDisplay}">${expiryDate.toLocaleDateString()}</td>
                <td>
                    <div class="actions">
                        <button class="btn btn-sm btn-ghost" onclick="event.stopPropagation(); showLicenseDetails('${license.license_key}')" title="View Details">
                            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                                <path d="M7 3.5C4.5 3.5 2.5 5.5 1.5 7c1 1.5 3 3.5 5.5 3.5s4.5-2 5.5-3.5c-1-1.5-3-3.5-5.5-3.5z" stroke="currentColor" stroke-width="1.2"/>
                                <circle cx="7" cy="7" r="1.5" stroke="currentColor" stroke-width="1.2"/>
                            </svg>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); copyKey('${license.license_key}')">Copy</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function filterLicenses() {
    const searchTerm = document.getElementById('license-search').value.toLowerCase();
    const statusFilter = document.getElementById('license-status-filter').value;
    const dateFrom = document.getElementById('license-date-from').value;
    const dateTo = document.getElementById('license-date-to').value;
    
    let filtered = currentLicenses.filter(license => {
        if (searchTerm && !license.license_key.toLowerCase().includes(searchTerm) && 
            !license.company_name.toLowerCase().includes(searchTerm) &&
            !license.email.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        if (statusFilter) {
            const isRevoked = license.state === 'revoked' || license.is_revoked === true;
            const state = isRevoked ? 'revoked' : license.state;
            if (state !== statusFilter) return false;
        }
        
        if (dateFrom) {
            const expiryDate = new Date(license.expiry_date);
            const fromDate = new Date(dateFrom);
            if (expiryDate < fromDate) return false;
        }
        
        if (dateTo) {
            const expiryDate = new Date(license.expiry_date);
            const toDate = new Date(dateTo);
            toDate.setHours(23, 59, 59, 999);
            if (expiryDate > toDate) return false;
        }
        
        return true;
    });
    
    renderLicenses(filtered);
}

function clearLicenseFilters() {
    document.getElementById('license-search').value = '';
    document.getElementById('license-status-filter').value = '';
    document.getElementById('license-date-from').value = '';
    document.getElementById('license-date-to').value = '';
    renderLicenses(currentLicenses);
}

// Load API Keys
async function loadApiKeys() {
    const tbody = document.getElementById('api-keys-table-body');
    tbody.innerHTML = '<tr><td colspan="5" class="loading"><div class="spinner"></div></td></tr>';
    
    try {
        const keys = await apiRequest('/api-keys');
        
        if (keys.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No API keys yet</td></tr>';
            return;
        }
        
        tbody.innerHTML = keys.map(key => `
            <tr>
                <td>${key.name || 'Unnamed'}</td>
                <td><code>${key.key_prefix}</code></td>
                <td>${new Date(key.created_at).toLocaleDateString()}</td>
                <td><span class="badge ${key.is_active ? 'badge-success' : 'badge-danger'}">${key.is_active ? 'Active' : 'Inactive'}</span></td>
                <td>
                    <button class="btn btn-sm btn-danger" onclick="deleteApiKey(${key.key_id})">Delete</button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5" class="error">Failed to load API keys</td></tr>';
    }
}

// Copy License Key
function copyKey(key) {
    navigator.clipboard.writeText(key);
    alert('License key copied!');
}

// Show License Details Modal
let currentLicenseKey = null;
let currentLicenseData = null;

async function showLicenseDetails(licenseKey) {
    currentLicenseKey = licenseKey;
    
    try {
        const license = await apiRequest(`/licenses/${licenseKey}`);
        currentLicenseData = license;
        
        // Calculate days remaining
        const expiryDate = new Date(license.expiry_date);
        const now = new Date();
        const daysLeft = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
        
        // Set values
        document.getElementById('detail-license-key').textContent = license.license_key;
        document.getElementById('detail-company').textContent = license.company_name;
        document.getElementById('detail-email').textContent = license.email;
        document.getElementById('detail-expiry').textContent = expiryDate.toLocaleString();
        document.getElementById('detail-days-left').textContent = daysLeft > 0 ? `${daysLeft} days` : 'Expired';
        document.getElementById('detail-type').textContent = license.license_type;
        document.getElementById('detail-activation').textContent = license.activation_date 
            ? new Date(license.activation_date).toLocaleString() 
            : 'Not activated';
        
        // Status badge
        const isRevoked = license.state === 'revoked' || license.is_revoked === true;
        const isExpired = daysLeft <= 0;
        let statusBadge = '';
        if (isRevoked) {
            statusBadge = '<span class="detail-badge badge-danger">Revoked</span>';
        } else if (license.state === 'suspended') {
            statusBadge = '<span class="detail-badge badge-warning">Suspended</span>';
        } else if (license.state === 'active' && !isExpired) {
            statusBadge = '<span class="detail-badge badge-success">Active</span>';
        } else if (isExpired) {
            statusBadge = '<span class="detail-badge badge-danger">Expired</span>';
        } else {
            statusBadge = '<span class="detail-badge badge-secondary">Inactive</span>';
        }
        document.getElementById('detail-status').innerHTML = statusBadge;
        
        // Show/hide action buttons based on current state
        const btnActivate = document.getElementById('btn-activate');
        const btnSuspend = document.getElementById('btn-suspend');
        const btnUnsuspend = document.getElementById('btn-unsuspend');
        const btnExtend = document.getElementById('btn-extend');
        const btnRevoke = document.getElementById('btn-revoke');
        const btnMaxMachines = document.getElementById('btn-max-machines');
        
        if (license.state === 'inactive') {
            btnActivate.style.display = 'inline-flex';
            btnSuspend.style.display = 'none';
            btnUnsuspend.style.display = 'none';
            btnExtend.style.display = 'none';
            btnRevoke.style.display = 'inline-flex';
            btnMaxMachines.style.display = 'inline-flex';
        } else if (license.state === 'active') {
            btnActivate.style.display = 'none';
            btnSuspend.style.display = 'inline-flex';
            btnUnsuspend.style.display = 'none';
            btnExtend.style.display = 'inline-flex';
            btnRevoke.style.display = 'inline-flex';
            btnMaxMachines.style.display = 'inline-flex';
        } else if (license.state === 'suspended') {
            btnActivate.style.display = 'none';
            btnSuspend.style.display = 'none';
            btnUnsuspend.style.display = 'inline-flex';
            btnExtend.style.display = 'none';
            btnRevoke.style.display = 'inline-flex';
            btnMaxMachines.style.display = 'inline-flex';
        } else if (isRevoked) {
            btnActivate.style.display = 'none';
            btnSuspend.style.display = 'none';
            btnUnsuspend.style.display = 'none';
            btnExtend.style.display = 'none';
            btnRevoke.style.display = 'none';
            btnMaxMachines.style.display = 'none';
        }
        
        showModal('license-details-modal');
        
        switchLicenseTab('details');
        
    } catch (error) {
        alert('Failed to load license details');
    }
}

function switchLicenseTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('hidden', content.id !== `tab-${tab}`);
    });
    
    if (tab === 'machines' && currentLicenseKey) {
        loadMachines(currentLicenseKey);
    }
}

async function loadMachines(licenseKey) {
    const machinesList = document.getElementById('machines-list');
    const machineCount = document.getElementById('machine-count');
    const maxMachinesEl = document.getElementById('max-machines');
    
    try {
        const license = await apiRequest(`/licenses/${licenseKey}`);
        const machines = await apiRequest(`/licenses/${licenseKey}/machines`);
        
        const maxMachines = license.max_machines || 1;
        machineCount.textContent = machines.length;
        maxMachinesEl.textContent = `${machines.length} / ${maxMachines} machines`;
        
        if (machines.length === 0) {
            machinesList.innerHTML = '<div class="machines-empty">No machines bound</div>';
            return;
        }
        
        machinesList.innerHTML = machines.map(machine => `
            <div class="machine-item">
                <div class="machine-info">
                    <span class="machine-mac">${machine.mac_address}</span>
                    <span class="machine-name">${machine.machine_name || 'Unnamed'}</span>
                    <span class="machine-date">Bound: ${new Date(machine.bound_at).toLocaleDateString()}</span>
                </div>
                <button class="btn btn-sm btn-ghost" onclick="unbindMachine('${licenseKey}', '${machine.mac_address}')" title="Unbind">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M10 4L4 10M4 4l6 6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load machines:', error);
        machinesList.innerHTML = '<div class="machines-empty">Failed to load machines</div>';
    }
}

async function refreshMachines() {
    if (currentLicenseKey) {
        loadMachines(currentLicenseKey);
    }
}

async function unbindMachine(licenseKey, macAddress) {
    if (!confirm(`Unbind machine ${macAddress}?`)) return;
    
    try {
        await apiRequest(`/licenses/${licenseKey}/machines/${macAddress}`, { method: 'DELETE' });
        alert('Machine unbound successfully');
        loadMachines(licenseKey);
    } catch (error) {
        alert('Failed to unbind machine');
    }
}

function showAddMachineModal() {
    const mac = prompt('Enter MAC address (e.g., AA:BB:CC:DD:EE:FF):');
    if (!mac) return;
    
    const name = prompt('Enter machine name (optional):');
    
    bindMachine(currentLicenseKey, mac, name || null);
}

async function bindMachine(licenseKey, macAddress, machineName) {
    try {
        await apiRequest(`/licenses/${licenseKey}/machines`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mac_address: macAddress, machine_name: machineName })
        });
        alert('Machine bound successfully');
        loadMachines(licenseKey);
    } catch (error) {
        alert('Failed to bind machine: ' + (error.message || 'Unknown error'));
    }
}

async function resetAllMachines() {
    if (!currentLicenseKey) return;
    if (!confirm('Reset all machines for this license? This will allow the license to be bound to new machines.')) return;
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/machines`, { method: 'DELETE' });
        alert('Machines reset successfully');
        loadMachines(currentLicenseKey);
    } catch (error) {
        alert('Failed to reset machines');
    }
}

// Modal Action Functions
async function modalActivate() {
    if (!currentLicenseKey) return;
    if (!confirm('Activate this license?')) return;
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/activate`, { method: 'POST' });
        hideModal();
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to activate license');
    }
}

async function modalSuspend() {
    if (!currentLicenseKey) return;
    if (!confirm('Suspend this license?')) return;
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/suspend`, { method: 'POST' });
        hideModal();
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to suspend license');
    }
}

async function modalUnsuspend() {
    if (!currentLicenseKey) return;
    if (!confirm('Unsuspend this license?')) return;
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/unsuspend`, { method: 'POST' });
        hideModal();
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to unsuspend license');
    }
}

async function modalRevoke() {
    if (!currentLicenseKey) return;
    if (!confirm('Revoke this license? This action cannot be undone.')) return;
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/revoke`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'Revoked via dashboard' })
        });
        hideModal();
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to revoke license');
    }
}

async function modalExtend() {
    if (!currentLicenseKey) return;
    
    // Show the extend modal
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    document.getElementById('extend-modal').classList.remove('hidden');
    modalOverlay.classList.remove('hidden');
}

document.getElementById('extend-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const days = parseInt(document.getElementById('extend-days').value);
    
    try {
        await apiRequest(`/licenses/${currentLicenseKey}/extend`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ additional_days: days })
        });
        
        // Hide both modals
        hideModal();
        document.getElementById('extend-modal').classList.add('hidden');
        
        // Reload licenses
        loadLicenses(currentProductId);
        
        // Refresh the details modal if still open
        if (currentLicenseKey) {
            showLicenseDetails(currentLicenseKey);
        }
    } catch (error) {
        alert('Failed to extend license');
    }
});

function toggleMaxMachinesInput() {
    const select = document.getElementById('max-machines-select');
    const customGroup = document.getElementById('custom-max-machines-group');
    customGroup.style.display = select.value === 'custom' ? 'block' : 'none';
}

async function modalMaxMachines() {
    if (!currentLicenseKey) {
        alert('No license selected');
        return;
    }
    
    let license;
    try {
        license = await apiRequest(`/licenses/${currentLicenseKey}`);
    } catch (error) {
        console.error('Failed to load license:', error);
        alert('Failed to load license details');
        return;
    }
    
    const currentMax = license.max_machines != null ? license.max_machines : -1;
    
    const select = document.getElementById('max-machines-select');
    const customInput = document.getElementById('max-machines-custom');
    const customGroup = document.getElementById('custom-max-machines-group');
    
    if (currentMax === -1 || currentMax === null) {
        select.value = '-1';
        customGroup.style.display = 'none';
    } else if (['1', '2', '3', '5', '10'].includes(String(currentMax))) {
        select.value = String(currentMax);
        customGroup.style.display = 'none';
    } else {
        select.value = 'custom';
        customInput.value = currentMax;
        customGroup.style.display = 'block';
    }
    
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    document.getElementById('max-machines-modal').classList.remove('hidden');
    modalOverlay.classList.remove('hidden');
}

document.getElementById('max-machines-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const select = document.getElementById('max-machines-select');
    let maxMachines = parseInt(select.value);
    
    if (select.value === 'custom') {
        maxMachines = parseInt(document.getElementById('max-machines-custom').value);
    }
    
    try {
        const result = await apiRequest(`/licenses/${currentLicenseKey}/max-machines`, { 
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ max_machines: maxMachines })
        });
        
        hideModal();
        document.getElementById('max-machines-modal').classList.add('hidden');
        
        loadLicenses(currentProductId);
        
        if (currentLicenseKey) {
            showLicenseDetails(currentLicenseKey);
        }
        
        alert('Max machines updated successfully');
    } catch (error) {
        console.error('Error updating max machines:', error);
        alert('Failed to update max machines: ' + error.message);
    }
});

// Activate License
async function activateLicense(licenseKey) {
    try {
        await apiRequest(`/licenses/${licenseKey}/activate`, {
            method: 'POST'
        });
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to activate license');
    }
}

// Revoke License
async function revokeLicense(licenseKey) {
    if (!confirm('Are you sure you want to revoke this license?')) return;
    
    try {
        await apiRequest(`/licenses/${licenseKey}/revoke`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: 'Revoked via dashboard' })
        });
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to revoke license');
    }
}

// Delete API Key
async function deleteApiKey(keyId) {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
        await apiRequest(`/api-keys/${keyId}`, { method: 'DELETE' });
        loadApiKeys();
    } catch (error) {
        alert('Failed to delete API key');
    }
}

// Modal Handling
function showModal(modalId) {
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
    document.getElementById(modalId).classList.remove('hidden');
    modalOverlay.classList.remove('hidden');
}

function hideModal() {
    modalOverlay.classList.add('hidden');
    document.querySelectorAll('.modal').forEach(m => m.classList.add('hidden'));
}

// Modal Event Listeners
document.querySelectorAll('.modal-close, .modal-cancel').forEach(btn => {
    btn.addEventListener('click', hideModal);
});

modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) hideModal();
});

// Add Product
document.getElementById('add-product-btn').addEventListener('click', () => {
    showModal('product-modal');
});

document.getElementById('product-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const productName = document.getElementById('product-name').value;
    const productCode = document.getElementById('product-code').value;
    
    try {
        await apiRequest('/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ product_name: productName, product_code: productCode })
        });
        
        hideModal();
        document.getElementById('product-form').reset();
        loadProducts();
    } catch (error) {
        alert('Failed to create product');
    }
});

// Add License
document.getElementById('add-license-btn').addEventListener('click', () => {
    showModal('license-modal');
});

document.getElementById('license-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const payload = {
        company_name: document.getElementById('license-company').value,
        email: document.getElementById('license-email').value,
        license_type: document.getElementById('license-type').value,
        period_days: parseInt(document.getElementById('license-period').value),
        product_id: currentProductId
    };
    
    try {
        await apiRequest('/licenses', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        hideModal();
        document.getElementById('license-form').reset();
        loadLicenses(currentProductId);
    } catch (error) {
        alert('Failed to create license');
    }
});

// Add API Key
document.getElementById('add-api-key-btn').addEventListener('click', () => {
    showModal('api-key-modal');
});

document.getElementById('api-key-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('api-key-name').value;
    const expiresAt = document.getElementById('api-key-expires').value;
    
    const payload = {
        name: name,
        expires_at: expiresAt ? new Date(expiresAt).toISOString() : null
    };
    
    try {
        const result = await apiRequest('/api-keys', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        hideModal();
        document.getElementById('api-key-form').reset();
        
        // Show the new keys
        document.getElementById('new-api-key').textContent = result.api_key;
        document.getElementById('new-api-secret').textContent = result.secret;
        showModal('show-api-key-modal');
        
        loadApiKeys();
    } catch (error) {
        alert('Failed to create API key');
    }
});

// ==========================================
// Audit Logs
// ==========================================

let currentAuditLogs = [];

async function loadAuditLogs() {
    const tbody = document.getElementById('audit-logs-table-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div></td></tr>';
    
    try {
        const params = new URLSearchParams();
        params.append('limit', 100);
        
        const logs = await apiRequest(`/licenses/audit/logs?${params.toString()}`);
        currentAuditLogs = Array.isArray(logs) ? logs : (logs.logs || []);
        
        // Calculate stats
        const total = currentAuditLogs.length;
        const success = currentAuditLogs.filter(l => l.success).length;
        const failed = currentAuditLogs.filter(l => !l.success).length;
        const offline = currentAuditLogs.filter(l => l.is_offline).length;
        
        document.getElementById('audit-total').textContent = total;
        document.getElementById('audit-success').textContent = success;
        document.getElementById('audit-failed').textContent = failed;
        document.getElementById('audit-offline').textContent = offline;
        
        renderAuditLogs(currentAuditLogs);
    } catch (error) {
        console.error('Error loading audit logs:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="error">Failed to load audit logs</td></tr>';
    }
}

function renderAuditLogs(logs) {
    const tbody = document.getElementById('audit-logs-table-body');
    
    if (!logs || logs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No audit logs found</td></tr>';
        return;
    }
    
    tbody.innerHTML = logs.map(log => {
        const eventType = log.event_type || 'unknown';
        const statusBadge = log.success 
            ? '<span class="badge badge-success">Success</span>' 
            : '<span class="badge badge-danger">Failed</span>';
        const typeBadge = log.is_offline 
            ? '<span class="badge badge-warning">Offline</span>' 
            : '<span class="badge badge-info">Online</span>';
        
        return `
            <tr>
                <td>${new Date(log.created_at).toLocaleString()}</td>
                <td><code>${log.license_key || '-'}</code></td>
                <td>${eventType}</td>
                <td>${statusBadge}</td>
                <td>${typeBadge}</td>
                <td>${log.ip_address || '-'}</td>
            </tr>
        `;
    }).join('');
}

function filterAuditLogs() {
    const searchTerm = document.getElementById('audit-search').value.toLowerCase();
    const eventFilter = document.getElementById('audit-event-filter').value;
    const offlineFilter = document.getElementById('audit-offline-filter').value;
    const dateFrom = document.getElementById('audit-date-from').value;
    const dateTo = document.getElementById('audit-date-to').value;
    
    let filtered = currentAuditLogs.filter(log => {
        if (searchTerm && log.license_key && !log.license_key.toLowerCase().includes(searchTerm)) {
            return false;
        }
        
        if (eventFilter && log.event_type !== eventFilter) {
            return false;
        }
        
        if (offlineFilter !== '') {
            const isOffline = log.is_offline === true;
            if (offlineFilter === 'true' && !isOffline) return false;
            if (offlineFilter === 'false' && isOffline) return false;
        }
        
        if (dateFrom) {
            const logDate = new Date(log.created_at);
            const fromDate = new Date(dateFrom);
            if (logDate < fromDate) return false;
        }
        
        if (dateTo) {
            const logDate = new Date(log.created_at);
            const toDate = new Date(dateTo);
            toDate.setHours(23, 59, 59, 999);
            if (logDate > toDate) return false;
        }
        
        return true;
    });
    
    renderAuditLogs(filtered);
}

function clearAuditFilters() {
    document.getElementById('audit-search').value = '';
    document.getElementById('audit-event-filter').value = '';
    document.getElementById('audit-offline-filter').value = '';
    document.getElementById('audit-date-from').value = '';
    document.getElementById('audit-date-to').value = '';
    renderAuditLogs(currentAuditLogs);
}
