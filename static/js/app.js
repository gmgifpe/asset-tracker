// Global variables
let currentUser = null;
let assets = [];
let accounts = [];
let charts = {};

// DOM Ready
$(document).ready(function() {
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Initialize dark mode
    initializeDarkMode();
    
    // Check if user is already logged in (session)
    // For now, show login form
    showAuthForms();
}

function setupEventListeners() {
    // Auth events
    $('#login-submit').click(handleLogin);
    $('#register-submit').click(handleRegister);
    $('#show-register').click(() => {
        $('#login-form').addClass('hidden');
        $('#register-form').removeClass('hidden');
    });
    $('#show-login').click(() => {
        $('#register-form').addClass('hidden');
        $('#login-form').removeClass('hidden');
    });
    $('#logout-btn').click(handleLogout);
    $('#switch-user-btn').click(showUserSelectModal);

    // Tab navigation
    $('.tab-btn').click(function() {
        const tabName = $(this).data('tab');
        if (tabName) {
            switchTab(tabName);
        }
    });

    // Dark mode toggle
    $('#dark-mode-toggle').click(toggleDarkMode);

    // Asset events
    $('#add-asset-btn').click(() => {
        resetAssetForm();
        $('#add-asset-form').removeClass('hidden');
        loadAccountsForSelect();
    });
    $('#cancel-asset-btn').click(() => {
        $('#add-asset-form').addClass('hidden');
        resetAssetForm();
    });
    $('#asset-form').submit(handleAddAsset);
    $('#search-symbol-btn').click(searchSymbol);
    
    // Show/hide equity compensation fields based on asset type
    $('#asset-type').change(handleAssetTypeChange);
    $('#asset-status').change(handleStatusChange);
    
    // Tax rate preset handling
    $('#asset-tax-rate-preset').change(handleTaxRatePresetChange);
    $('#asset-tax-country').change(handleTaxCountryChange);

    // Transaction events
    $('#add-transaction-btn').click(() => {
        $('#add-transaction-form').removeClass('hidden');
        loadAccountsForTransactionSelect();
        setTodaysDate();
    });
    $('#cancel-transaction-btn').click(() => {
        $('#add-transaction-form').addClass('hidden');
        $('#transaction-form')[0].reset();
    });
    $('#transaction-form').submit(handleAddTransaction);
    $('#search-transaction-symbol-btn').click(searchTransactionSymbol);
    $('#view-realized-gains-btn').click(showRealizedGains);
    
    // Auto-calculate total amount
    $('#transaction-quantity, #transaction-price').on('input', calculateTransactionTotal);

    // Account events
    $('#add-account-btn').click(() => {
        $('#add-account-form').removeClass('hidden');
    });
    $('#cancel-account-btn').click(() => {
        $('#add-account-form').addClass('hidden');
        $('#account-form')[0].reset();
    });
    $('#account-form').submit(handleAddAccount);

    // Other events
    $('#update-prices-btn').click(updatePrices);

    // Modal events
    $('.close').click(closeModal);
    $(window).click(function(event) {
        if (event.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Authentication functions
function handleLogin(e) {
    e.preventDefault();
    const username = $('#login-username').val();
    const password = $('#login-password').val();

    $.ajax({
        url: '/api/login',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ username, password }),
        success: function(response) {
            currentUser = { id: response.user_id, username: username };
            $('#current-user').text(username);
            showMainContent();
            loadDashboard();
            showAlert('Login successful!', 'success');
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Login failed';
            showAlert(error, 'error');
        }
    });
}

function handleRegister(e) {
    e.preventDefault();
    const username = $('#register-username').val();
    const email = $('#register-email').val();
    const password = $('#register-password').val();

    $.ajax({
        url: '/api/users',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ username, email, password }),
        success: function(response) {
            showAlert('Account created successfully! Please login.', 'success');
            $('#show-login').click();
            $('#register-form')[0].reset();
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Registration failed';
            showAlert(error, 'error');
        }
    });
}

function handleLogout() {
    $.ajax({
        url: '/api/logout',
        method: 'POST',
        success: function() {
            currentUser = null;
            showAuthForms();
            showAlert('Logged out successfully', 'success');
        }
    });
}

function showUserSelectModal() {
    $('#user-select-modal').removeClass('hidden');
    loadUsers();
}

function loadUsers() {
    $.ajax({
        url: '/api/users',
        method: 'GET',
        success: function(users) {
            const userList = $('#user-list');
            userList.empty();
            
            users.forEach(user => {
                const userItem = $(`
                    <div class="user-item" data-user-id="${user.id}">
                        <h4>${user.username}</h4>
                        <div class="email">${user.email}</div>
                    </div>
                `);
                
                userItem.click(() => switchToUser(user.id, user.username));
                userList.append(userItem);
            });
        }
    });
}

function switchToUser(userId, username) {
    $.ajax({
        url: `/api/switch-user/${userId}`,
        method: 'POST',
        success: function() {
            currentUser = { id: userId, username: username };
            $('#current-user').text(username);
            closeModal();
            loadDashboard();
            showAlert(`Switched to ${username}`, 'success');
        }
    });
}

// UI functions
function showAuthForms() {
    $('#auth-forms').removeClass('hidden');
    $('#user-info').addClass('hidden');
    $('#main-content').addClass('hidden');
}

function showMainContent() {
    $('#auth-forms').addClass('hidden');
    $('#user-info').removeClass('hidden');
    $('#main-content').removeClass('hidden');
}

function switchTab(tabName) {
    $('.tab-btn').removeClass('active');
    $('.tab-content').removeClass('active');
    
    $(`.tab-btn[data-tab="${tabName}"]`).addClass('active');
    $(`#${tabName}`).addClass('active');
    
    // Load tab-specific data with automatic price updates
    switch(tabName) {
        case 'dashboard':
            showTabLoadingMessage('Updating prices and loading dashboard...');
            updatePricesAndLoadDashboard();
            break;
        case 'assets':
            showTabLoadingMessage('Updating asset prices...');
            updatePricesAndLoadAssets();
            break;
        case 'accounts':
            loadAccounts();
            break;
        case 'transactions':
            showTabLoadingMessage('Updating portfolio data...');
            updatePricesAndLoadTransactions();
            break;
        case 'analytics':
            showTabLoadingMessage('Updating analytics data...');
            updatePricesAndLoadAnalytics();
            break;
    }
}

function closeModal() {
    $('.modal').addClass('hidden');
}

function showAlert(message, type) {
    const alertDiv = $(`<div class="alert alert-${type}">${message}</div>`);
    $('.container').prepend(alertDiv);
    
    setTimeout(() => {
        alertDiv.fadeOut(() => alertDiv.remove());
    }, 5000);
}

// Dashboard functions
function loadDashboard() {
    loadPortfolioSummary();
    loadAssets();
}

function loadPortfolioSummary() {
    $.ajax({
        url: '/api/portfolio-summary',
        method: 'GET',
        success: function(data) {
            $('#total-value').text(formatCurrency(data.total_value));
            $('#asset-count').text(data.asset_count);
            
            const changeClass = data.total_gain_loss >= 0 ? 'gain' : 'loss';
            const changeSign = data.total_gain_loss >= 0 ? '+' : '';
            $('#total-change')
                .text(`${changeSign}${formatCurrency(data.total_gain_loss)} (${data.total_gain_loss_percent.toFixed(2)}%)`)
                .removeClass('gain loss')
                .addClass(changeClass);
            
            // Update charts
            updateAssetDistributionChart(data.asset_distribution);
            updateAccountDistributionChart(data.account_distribution);
            updateStockDistributionChart(data.stock_distribution);
        },
        error: function() {
            showAlert('Failed to load portfolio summary', 'error');
        }
    });
}

function updateAssetDistributionChart(distribution) {
    const ctx = document.getElementById('asset-pie-chart').getContext('2d');
    
    if (charts.assetPie) {
        charts.assetPie.destroy();
    }
    
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    const colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'];
    
    charts.assetPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateAccountDistributionChart(distribution) {
    const ctx = document.getElementById('account-pie-chart').getContext('2d');
    
    if (charts.accountPie) {
        charts.accountPie.destroy();
    }
    
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    const colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'];
    
    charts.accountPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

function updateStockDistributionChart(distribution) {
    const ctx = document.getElementById('stock-pie-chart').getContext('2d');
    
    if (charts.stockPie) {
        charts.stockPie.destroy();
    }
    
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    
    // Use a more varied color palette for potentially many stocks
    const colors = [
        '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
        '#FF6384', '#C9CBCF', '#4BC0C0', '#FF6384', '#36A2EB', '#FFCE56',
        '#E7E9ED', '#71B37C', '#FFA8BA', '#8E8E93', '#007AFF', '#FF3B30',
        '#FF9500', '#FFCC00', '#34C759', '#5AC8FA', '#AF52DE', '#A2845E'
    ];
    
    // Sort by value descending to show largest holdings first
    const sortedEntries = Object.entries(distribution).sort((a, b) => b[1] - a[1]);
    const sortedLabels = sortedEntries.map(entry => entry[0]);
    const sortedData = sortedEntries.map(entry => entry[1]);
    
    charts.stockPie = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: sortedLabels,
            datasets: [{
                data: sortedData,
                backgroundColor: colors.slice(0, sortedLabels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 8,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: $${value.toLocaleString()} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Assets functions
function loadAssets() {
    $.ajax({
        url: '/api/assets',
        method: 'GET',
        success: function(data) {
            assets = data;
            displayAssets();
        },
        error: function() {
            showAlert('Failed to load assets', 'error');
        }
    });
}

function displayAssets() {
    const tbody = $('#assets-tbody');
    tbody.empty();
    
    assets.forEach(asset => {
        const gainLossClass = asset.gain_loss >= 0 ? 'gain' : 'loss';
        const gainLossSign = asset.gain_loss >= 0 ? '+' : '';
        
        // Special handling for equity compensation
        let assetTypeDisplay = asset.asset_type;
        let purchasePriceDisplay = formatCurrency(asset.purchase_price);
        let additionalInfo = '';
        
        if (asset.asset_type === 'stock_option') {
            assetTypeDisplay = `${asset.asset_type} <span class="status-${asset.status}">(${asset.status})</span>`;
            purchasePriceDisplay = asset.strike_price ? formatCurrency(asset.strike_price) : 'N/A';
            
            // Show intrinsic value for options
            if (asset.strike_price && asset.current_price > asset.strike_price) {
                additionalInfo = `<br><small class="option-in-money">In-the-money: ${formatCurrency(asset.current_price - asset.strike_price)}/share</small>`;
            } else if (asset.strike_price && asset.current_price < asset.strike_price) {
                additionalInfo = `<br><small class="option-out-money">Out-of-money</small>`;
            }
            
            if (asset.expiration_date) {
                const expDate = new Date(asset.expiration_date).toLocaleDateString();
                additionalInfo += `<br><small>Expires: ${expDate}</small>`;
            }
        } else if (asset.asset_type === 'rsu') {
            assetTypeDisplay = `${asset.asset_type.toUpperCase()} <span class="status-${asset.status}">(${asset.status})</span>`;
            
            if (asset.vesting_date) {
                const vestDate = new Date(asset.vesting_date).toLocaleDateString();
                additionalInfo = `<br><small>Vests: ${vestDate}</small>`;
            }
            
            if (asset.vest_fmv) {
                additionalInfo += `<br><small>Vest FMV: ${formatCurrency(asset.vest_fmv)}</small>`;
            }
        } else if (asset.asset_type === 'espp') {
            assetTypeDisplay = `${asset.asset_type.toUpperCase()} <span class="status-${asset.status}">(${asset.status})</span>`;
        }
        
        // Add tax liability information for equity compensation with custom tax rates
        if (['stock_option', 'rsu'].includes(asset.asset_type) && asset.tax_rate && asset.tax_rate > 0) {
            const countryFlag = {
                'TW': '🇹🇼',
                'US': '🇺🇸', 
                'HK': '🇭🇰',
                'SG': '🇸🇬',
                'OTHER': '🌍'
            }[asset.tax_country] || '🌍';
            
            const taxRateDisplay = `${asset.tax_rate}%`;
            
            if (asset.current_tax_liability && asset.current_tax_liability > 0) {
                additionalInfo += `<br><small class="tax-liability">${countryFlag} Tax Owed: ${formatCurrency(asset.current_tax_liability)} (${taxRateDisplay})</small>`;
            } else if (asset.potential_tax_liability && asset.potential_tax_liability > 0) {
                additionalInfo += `<br><small class="potential-tax">${countryFlag} Potential Tax: ${formatCurrency(asset.potential_tax_liability)} (${taxRateDisplay})</small>`;
            } else {
                // Show tax rate even if no liability calculated yet
                additionalInfo += `<br><small class="tax-rate-info">${countryFlag} Tax Rate: ${taxRateDisplay}</small>`;
            }
        }
        
        const row = $(`
            <tr>
                <td>${asset.symbol}</td>
                <td>${asset.name}${additionalInfo}</td>
                <td>${assetTypeDisplay}</td>
                <td>${asset.account_name || 'No Account'}</td>
                <td>${asset.quantity}</td>
                <td>${purchasePriceDisplay}</td>
                <td>${formatCurrency(asset.current_price)}</td>
                <td>${formatCurrency(asset.total_value)}</td>
                <td class="${gainLossClass}">${gainLossSign}${formatCurrency(asset.gain_loss)}</td>
                <td class="${gainLossClass}">${gainLossSign}${asset.gain_loss_percent.toFixed(2)}%</td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="editAsset(${asset.id})">Edit</button>
                    <button class="btn btn-small btn-secondary" onclick="deleteAsset(${asset.id})">Delete</button>
                </td>
            </tr>
        `);
        
        tbody.append(row);
    });
}

function handleAssetTypeChange() {
    const assetType = $('#asset-type').val();
    const equityFields = $('#equity-fields');
    
    if (['stock_option', 'rsu', 'espp'].includes(assetType)) {
        equityFields.removeClass('hidden');
        
        // Set default labels based on type
        if (assetType === 'stock_option') {
            $('label[for="asset-price"]').text('Exercise Cost (per share)');
            $('#asset-strike-price').closest('.form-group').removeClass('hidden');
        } else if (assetType === 'rsu') {
            $('label[for="asset-price"]').text('Cost Basis (usually $0)');
            $('#asset-strike-price').closest('.form-group').addClass('hidden');
            $('#asset-price').val('0'); // RSUs typically have no cost
        } else if (assetType === 'espp') {
            $('label[for="asset-price"]').text('Purchase Price (discounted)');
            $('#asset-strike-price').closest('.form-group').addClass('hidden');
        }
        
        // Handle tax-related field visibility based on status
        handleStatusChange();
    } else {
        equityFields.addClass('hidden');
        $('label[for="asset-price"]').text('Purchase Price');
    }
}

function handleStatusChange() {
    const status = $('#asset-status').val();
    const assetType = $('#asset-type').val();
    
    // Show exercise fields if status is exercised and asset is stock option
    if (status === 'exercised' && assetType === 'stock_option') {
        $('#exercise-fields').removeClass('hidden');
    } else {
        $('#exercise-fields').addClass('hidden');
    }
    
    // Show vest price field if status is vested and asset is RSU
    if (status === 'vested' && assetType === 'rsu') {
        $('#vest-price-field').removeClass('hidden');
    } else {
        $('#vest-price-field').addClass('hidden');
    }
}

function handleTaxRatePresetChange() {
    const selectedPreset = $('#asset-tax-rate-preset').val();
    const taxRateInput = $('#asset-tax-rate');
    
    if (selectedPreset && selectedPreset !== 'custom') {
        // Set the preset value
        taxRateInput.val(selectedPreset);
        taxRateInput.attr('readonly', true);
        taxRateInput.addClass('preset-selected');
    } else if (selectedPreset === 'custom') {
        // Enable custom input
        taxRateInput.val('');
        taxRateInput.attr('readonly', false);
        taxRateInput.removeClass('preset-selected');
        taxRateInput.focus();
        taxRateInput.attr('placeholder', '請輸入自定義稅率%');
    } else {
        // No selection, enable input
        taxRateInput.attr('readonly', false);
        taxRateInput.removeClass('preset-selected');
        taxRateInput.attr('placeholder', '輸入稅率%');
    }
}

function handleTaxCountryChange() {
    const selectedCountry = $('#asset-tax-country').val();
    const taxRatePreset = $('#asset-tax-rate-preset');
    const taxRateInput = $('#asset-tax-rate');
    
    // Update default tax rates based on country
    switch(selectedCountry) {
        case 'TW':
            // Reset to Taiwan common rates
            taxRatePreset.val('40'); // Default to 40% for Taiwan
            taxRateInput.val('40');
            break;
        case 'US':
            taxRatePreset.val('37'); // US highest rate
            taxRateInput.val('37');
            break;
        case 'HK':
            taxRatePreset.val('17'); // HK standard rate
            taxRateInput.val('17');
            break;
        case 'SG':
            taxRatePreset.val('22'); // Singapore high income rate
            taxRateInput.val('22');
            break;
        default:
            taxRatePreset.val('');
            taxRateInput.val('');
    }
    
    // Always allow custom input when country changes
    taxRateInput.attr('readonly', false);
    taxRateInput.removeClass('preset-selected');
}

function handleAddAsset(e) {
    e.preventDefault();
    
    const assetData = {
        symbol: $('#asset-symbol').val().toUpperCase(),
        name: $('#asset-name').val(),
        asset_type: $('#asset-type').val(),
        account_id: $('#asset-account').val() || null,
        quantity: $('#asset-quantity').val(),
        purchase_price: $('#asset-price').val(),
        currency: $('#asset-currency').val(),
        notes: $('#asset-notes').val()
    };
    
    // Add equity compensation fields if applicable
    const assetType = $('#asset-type').val();
    if (['stock_option', 'rsu', 'espp'].includes(assetType)) {
        assetData.grant_date = $('#asset-grant-date').val() || null;
        assetData.vesting_date = $('#asset-vesting-date').val() || null;
        assetData.expiration_date = $('#asset-expiration-date').val() || null;
        assetData.strike_price = $('#asset-strike-price').val() || null;
        assetData.vest_fmv = $('#asset-vest-fmv').val() || null;
        assetData.status = $('#asset-status').val();
        
        // Add tax tracking fields
        assetData.tax_country = $('#asset-tax-country').val();
        assetData.tax_rate = $('#asset-tax-rate').val();
        assetData.exercise_price = $('#asset-exercise-price').val() || null;
        assetData.exercise_date = $('#asset-exercise-date').val() || null;
        assetData.vest_market_price = $('#asset-vest-market-price').val() || null;
        
        // Validate tax rate
        if (assetData.tax_rate && assetData.tax_rate !== '') {
            const taxRate = parseFloat(assetData.tax_rate);
            if (isNaN(taxRate) || taxRate < 0 || taxRate > 100) {
                showAlert('稅率必須在 0% 到 100% 之間', 'error');
                return;
            }
        }
    }
    
    const assetId = $('#asset-id').val();
    const isEditing = assetId && assetId !== '';
    
    $.ajax({
        url: isEditing ? `/api/assets/${assetId}` : '/api/assets',
        method: isEditing ? 'PUT' : 'POST',
        contentType: 'application/json',
        data: JSON.stringify(assetData),
        success: function() {
            const message = isEditing ? 'Asset updated successfully!' : 'Asset added successfully!';
            showAlert(message, 'success');
            $('#add-asset-form').addClass('hidden');
            resetAssetForm();
            loadAssets();
            loadPortfolioSummary();
        },
        error: function(xhr) {
            const action = isEditing ? 'update' : 'add';
            const error = xhr.responseJSON?.error || `Failed to ${action} asset`;
            showAlert(error, 'error');
        }
    });
}

function searchSymbol() {
    const symbol = $('#asset-symbol').val();
    if (!symbol) return;
    
    $.ajax({
        url: `/api/search-symbol/${symbol}`,
        method: 'GET',
        success: function(data) {
            $('#asset-name').val(data.name);
            $('#asset-price').val(data.price);
            $('#asset-currency').val(data.currency);
            showAlert('Symbol found and details filled!', 'success');
        },
        error: function() {
            showAlert('Symbol not found', 'error');
        }
    });
}

function deleteAsset(assetId) {
    if (confirm('Are you sure you want to delete this asset?')) {
        $.ajax({
            url: `/api/assets/${assetId}`,
            method: 'DELETE',
            success: function() {
                showAlert('Asset deleted successfully!', 'success');
                loadAssets();
                loadPortfolioSummary();
            },
            error: function() {
                showAlert('Failed to delete asset', 'error');
            }
        });
    }
}

function editAsset(assetId) {
    // Fetch asset data
    $.ajax({
        url: `/api/assets/${assetId}`,
        method: 'GET',
        success: function(asset) {
            // Populate form with asset data
            $('#asset-id').val(asset.id);
            $('#asset-type').val(asset.asset_type);
            $('#asset-symbol').val(asset.symbol);
            $('#asset-name').val(asset.name);
            $('#asset-account').val(asset.account_id || '');
            $('#asset-quantity').val(asset.quantity);
            $('#asset-price').val(asset.purchase_price);
            $('#asset-currency').val(asset.currency);
            $('#asset-notes').val(asset.notes || '');
            
            // Populate equity compensation fields
            if (asset.grant_date) $('#asset-grant-date').val(asset.grant_date.split('T')[0]);
            if (asset.vesting_date) $('#asset-vesting-date').val(asset.vesting_date.split('T')[0]);
            if (asset.expiration_date) $('#asset-expiration-date').val(asset.expiration_date.split('T')[0]);
            if (asset.strike_price) $('#asset-strike-price').val(asset.strike_price);
            if (asset.vest_fmv) $('#asset-vest-fmv').val(asset.vest_fmv);
            $('#asset-status').val(asset.status || 'granted');
            
            // Populate tax fields
            $('#asset-tax-country').val(asset.tax_country || 'TW');
            if (asset.tax_rate) $('#asset-tax-rate').val(asset.tax_rate);
            if (asset.exercise_price) $('#asset-exercise-price').val(asset.exercise_price);
            if (asset.exercise_date) $('#asset-exercise-date').val(asset.exercise_date.split('T')[0]);
            if (asset.vest_market_price) $('#asset-vest-market-price').val(asset.vest_market_price);
            
            // Set tax rate preset based on current rate
            if (asset.tax_rate) {
                const presetValue = asset.tax_rate.toString();
                const presetOption = $(`#asset-tax-rate-preset option[value="${presetValue}"]`);
                if (presetOption.length > 0) {
                    $('#asset-tax-rate-preset').val(presetValue);
                    $('#asset-tax-rate').attr('readonly', true).addClass('preset-selected');
                } else {
                    $('#asset-tax-rate-preset').val('custom');
                    $('#asset-tax-rate').attr('readonly', false).removeClass('preset-selected');
                }
            }
            
            // Trigger handlers to show/hide appropriate fields
            handleAssetTypeChange();
            handleStatusChange();
            
            // Load accounts for the dropdown
            loadAccountsForSelect();
            
            // Update form title and button
            $('#asset-form-title').text('Edit Asset');
            $('#asset-submit-btn').text('Update Asset');
            
            // Show form
            $('#add-asset-form').removeClass('hidden');
        },
        error: function() {
            showAlert('Failed to load asset data', 'error');
        }
    });
}

function resetAssetForm() {
    $('#asset-form')[0].reset();
    $('#asset-id').val('');
    $('#asset-form-title').text('Add New Asset');
    $('#asset-submit-btn').text('Add Asset');
    
    // Reset equity compensation fields visibility
    $('#equity-fields').addClass('hidden');
    $('#exercise-fields').addClass('hidden');
    $('#vest-price-field').addClass('hidden');
    
    // Reset tax rate fields
    $('#asset-tax-rate').attr('readonly', false).removeClass('preset-selected');
    $('#asset-tax-rate-preset').val('');
}

// Accounts functions
function loadAccounts() {
    $.ajax({
        url: '/api/accounts',
        method: 'GET',
        success: function(data) {
            accounts = data;
            displayAccounts();
        },
        error: function() {
            showAlert('Failed to load accounts', 'error');
        }
    });
}

function displayAccounts() {
    const container = $('#accounts-list');
    container.empty();
    
    if (accounts.length === 0) {
        container.append(`
            <div class="empty-state">
                <p>No accounts yet. Click "Add Account" to create your first account.</p>
            </div>
        `);
        return;
    }
    
    accounts.forEach(account => {
        const assetCountText = account.asset_count > 0 ? 
            `${account.asset_count} asset${account.asset_count > 1 ? 's' : ''}` : 
            'No assets';
            
        const card = $(`
            <div class="account-card" data-account-id="${account.id}">
                <div class="account-header">
                    <h4>${account.name}</h4>
                    <div class="account-actions">
                        <button class="btn btn-sm btn-danger delete-account-btn" 
                                data-account-id="${account.id}" 
                                title="Delete Account">
                            🗑️
                        </button>
                    </div>
                </div>
                <div class="account-details">
                    <div class="account-type">${account.account_type}</div>
                    <div class="account-currency">Currency: ${account.currency}</div>
                    <div class="account-assets">${assetCountText}</div>
                    <div class="account-created">Created: ${new Date(account.created_at).toLocaleDateString()}</div>
                </div>
            </div>
        `);
        
        container.append(card);
    });
    
    // Add click handlers for delete buttons
    $('.delete-account-btn').click(function(e) {
        e.stopPropagation();
        const accountId = $(this).data('account-id');
        showDeleteAccountConfirmation(accountId);
    });
}

function loadAccountsForSelect() {
    $.ajax({
        url: '/api/accounts',
        method: 'GET',
        success: function(data) {
            const select = $('#asset-account');
            select.find('option:not(:first)').remove();
            
            data.forEach(account => {
                select.append(`<option value="${account.id}">${account.name}</option>`);
            });
        }
    });
}

function handleAddAccount(e) {
    e.preventDefault();
    
    const accountData = {
        name: $('#account-name').val(),
        account_type: $('#account-type').val(),
        currency: $('#account-currency').val()
    };
    
    $.ajax({
        url: '/api/accounts',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(accountData),
        success: function() {
            showAlert('Account added successfully!', 'success');
            $('#add-account-form').addClass('hidden');
            $('#account-form')[0].reset();
            loadAccounts();
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to add account';
            showAlert(error, 'error');
        }
    });
}

// Account deletion functions
function showDeleteAccountConfirmation(accountId) {
    // First get account details
    $.ajax({
        url: `/api/accounts/${accountId}/info`,
        method: 'GET',
        success: function(accountInfo) {
            showDeleteAccountModal(accountInfo);
        },
        error: function() {
            showAlert('Failed to load account information', 'error');
        }
    });
}

function showDeleteAccountModal(accountInfo) {
    const hasAssets = accountInfo.asset_count > 0;
    const totalValue = accountInfo.total_value || 0;
    
    const assetsList = hasAssets ? accountInfo.assets.map(asset => 
        `<li>${asset.symbol} - ${asset.quantity} shares (${asset.name})</li>`
    ).join('') : '';
    
    const modalHTML = `
        <div class="modal delete-account-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Delete Account: "${accountInfo.name}"</h3>
                    <button class="close-modal">&times;</button>
                </div>
                
                <div class="modal-body">
                    <div class="account-deletion-warning">
                        <div class="warning-icon">⚠️</div>
                        <p><strong>This action cannot be undone!</strong></p>
                    </div>
                    
                    <div class="account-info">
                        <h4>Account Details:</h4>
                        <ul>
                            <li><strong>Name:</strong> ${accountInfo.name}</li>
                            <li><strong>Type:</strong> ${accountInfo.account_type}</li>
                            <li><strong>Currency:</strong> ${accountInfo.currency}</li>
                            <li><strong>Assets:</strong> ${accountInfo.asset_count}</li>
                            ${totalValue > 0 ? `<li><strong>Total Value:</strong> $${totalValue.toFixed(2)}</li>` : ''}
                        </ul>
                    </div>
                    
                    ${hasAssets ? `
                        <div class="assets-in-account">
                            <h4>Assets in this account:</h4>
                            <ul class="asset-list">
                                ${assetsList}
                            </ul>
                            
                            <div class="asset-handling-options">
                                <h4>What should happen to these assets?</h4>
                                <div class="radio-group">
                                    <label>
                                        <input type="radio" name="asset-action" value="move_to_default" checked>
                                        <span>Move assets to "No Account" (recommended)</span>
                                    </label>
                                    <label>
                                        <input type="radio" name="asset-action" value="delete">
                                        <span class="danger-option">Delete all assets permanently</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    ` : `
                        <div class="no-assets">
                            <p>This account has no assets and can be safely deleted.</p>
                        </div>
                    `}
                    
                    <div class="confirmation-input">
                        <p>To confirm deletion, type the account name: <strong>${accountInfo.name}</strong></p>
                        <input type="text" id="delete-confirmation-input" placeholder="Type account name here..." class="form-control">
                        <div id="confirmation-error" class="error-message hidden">Account name doesn't match</div>
                    </div>
                </div>
                
                <div class="modal-footer">
                    <button id="confirm-delete-account" class="btn btn-danger" disabled 
                            data-account-id="${accountInfo.id}" data-account-name="${accountInfo.name}">
                        Delete Account
                    </button>
                    <button class="btn btn-secondary close-modal">Cancel</button>
                </div>
            </div>
        </div>
    `;
    
    // Remove any existing modal
    $('.delete-account-modal').remove();
    
    // Add modal to body
    $('body').append(modalHTML);
    
    // Set up event handlers
    $('.close-modal').click(closeModal);
    
    // Enable/disable delete button based on confirmation input
    $('#delete-confirmation-input').on('input', function() {
        const inputValue = $(this).val().trim();
        const accountName = $('#confirm-delete-account').data('account-name');
        const confirmButton = $('#confirm-delete-account');
        const errorDiv = $('#confirmation-error');
        
        if (inputValue === accountName) {
            confirmButton.prop('disabled', false);
            errorDiv.addClass('hidden');
        } else {
            confirmButton.prop('disabled', true);
            if (inputValue.length > 0) {
                errorDiv.removeClass('hidden');
            } else {
                errorDiv.addClass('hidden');
            }
        }
    });
    
    // Handle delete confirmation
    $('#confirm-delete-account').click(function() {
        const accountId = $(this).data('account-id');
        const action = $('input[name="asset-action"]:checked').val() || 'move_to_default';
        deleteAccount(accountId, action);
    });
}

function deleteAccount(accountId, action) {
    const confirmButton = $('#confirm-delete-account');
    const originalText = confirmButton.text();
    
    // Show loading state
    confirmButton.prop('disabled', true).text('Deleting...');
    
    $.ajax({
        url: `/api/accounts/${accountId}`,
        method: 'DELETE',
        contentType: 'application/json',
        data: JSON.stringify({
            handle_assets: action
        }),
        success: function(response) {
            closeModal();
            showAlert(response.message, 'success');
            
            // Reload accounts and assets
            loadAccounts();
            if (action === 'delete_assets') {
                // If assets were deleted, refresh the assets tab too
                loadAssets();
            }
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to delete account';
            showAlert(error, 'error');
            
            // Restore button state
            confirmButton.prop('disabled', false).text(originalText);
        }
    });
}

// Analytics functions
function loadAnalytics() {
    loadPortfolioHistory();
    loadPortfolioMetrics();
    loadAssetPerformance();
}

function loadPortfolioHistory() {
    $.ajax({
        url: '/api/portfolio-history',
        method: 'GET',
        success: function(data) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            if (charts.performance) {
                charts.performance.destroy();
            }
            
            const labels = data.map(item => item.date);
            const values = data.map(item => item.value);
            
            charts.performance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Portfolio Value',
                        data: values,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false,
                            ticks: {
                                callback: function(value) {
                                    return formatCurrency(value);
                                }
                            }
                        },
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `Portfolio Value: ${formatCurrency(context.parsed.y)}`;
                                }
                            }
                        }
                    }
                }
            });
        },
        error: function() {
            showAlert('Failed to load portfolio history', 'error');
        }
    });
}

function loadPortfolioMetrics() {
    $.ajax({
        url: '/api/portfolio-metrics',
        method: 'GET',
        success: function(data) {
            // Update analytics cards if they exist
            if ($('#analytics-metrics').length === 0) {
                // Create metrics display
                const metricsHTML = `
                    <div id="analytics-metrics" class="analytics-metrics">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <h4>Best Performer</h4>
                                <div class="metric-value" id="best-performer">-</div>
                            </div>
                            <div class="metric-card">
                                <h4>Worst Performer</h4>
                                <div class="metric-value" id="worst-performer">-</div>
                            </div>
                            <div class="metric-card">
                                <h4>Avg Days Held</h4>
                                <div class="metric-value" id="avg-days-held">0</div>
                            </div>
                            <div class="metric-card">
                                <h4>Diversification</h4>
                                <div class="metric-value" id="diversification-score">0</div>
                            </div>
                        </div>
                    </div>
                `;
                $('.analytics-grid').prepend(metricsHTML);
            }
            
            // Update metric values
            if (data.best_performer) {
                $('#best-performer').html(`${data.best_performer.symbol}<br><small>+${data.best_performer.gain_percent.toFixed(2)}%</small>`);
            }
            if (data.worst_performer) {
                $('#worst-performer').html(`${data.worst_performer.symbol}<br><small>${data.worst_performer.gain_percent.toFixed(2)}%</small>`);
            }
            $('#avg-days-held').text(`${data.avg_days_held} days`);
            $('#diversification-score').text(`${data.diversification_score} types`);
        },
        error: function() {
            console.log('Portfolio metrics not available');
        }
    });
}

function loadAssetPerformance() {
    $.ajax({
        url: '/api/asset-performance',
        method: 'GET',
        success: function(data) {
            // Create asset performance table if it doesn't exist
            if ($('#asset-performance-table').length === 0) {
                const tableHTML = `
                    <div class="chart-container">
                        <h3>Asset Performance Details</h3>
                        <table id="asset-performance-table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Name</th>
                                    <th>Value</th>
                                    <th>Gain/Loss</th>
                                    <th>Annual Return</th>
                                    <th>Days Held</th>
                                    <th>Allocation</th>
                                </tr>
                            </thead>
                            <tbody id="asset-performance-tbody">
                            </tbody>
                        </table>
                    </div>
                `;
                $('.analytics-grid').append(tableHTML);
            }
            
            const tbody = $('#asset-performance-tbody');
            tbody.empty();
            
            data.forEach(asset => {
                const gainLossClass = asset.gain_loss >= 0 ? 'gain' : 'loss';
                const gainLossSign = asset.gain_loss >= 0 ? '+' : '';
                
                const row = $(`
                    <tr>
                        <td>${asset.symbol}</td>
                        <td>${asset.name}</td>
                        <td>${formatCurrency(asset.total_value)}</td>
                        <td class="${gainLossClass}">${gainLossSign}${formatCurrency(asset.gain_loss)} (${gainLossSign}${asset.gain_loss_percent.toFixed(2)}%)</td>
                        <td class="${asset.annual_return >= 0 ? 'gain' : 'loss'}">${asset.annual_return.toFixed(2)}%</td>
                        <td>${asset.days_held} days</td>
                        <td>${asset.allocation_percent.toFixed(2)}%</td>
                    </tr>
                `);
                
                tbody.append(row);
            });
        },
        error: function() {
            console.log('Asset performance data not available');
        }
    });
}

// Utility functions
function updatePrices() {
    $.ajax({
        url: '/api/update-prices',
        method: 'POST',
        success: function(response) {
            showAlert(response.message, 'success');
            loadAssets();
            loadPortfolioSummary();
        },
        error: function() {
            showAlert('Failed to update prices', 'error');
        }
    });
}

function formatCurrency(value, currency = 'USD') {
    // Handle Taiwan Dollar formatting
    if (currency === 'TWD') {
        return new Intl.NumberFormat('zh-TW', {
            style: 'currency',
            currency: 'TWD'
        }).format(value);
    }
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(value);
}

// Dark Mode Functions
function initializeDarkMode() {
    const isDarkMode = localStorage.getItem('darkMode') === 'true';
    if (isDarkMode) {
        document.body.classList.add('dark-mode');
    }
}

function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode);
    showAlert(`${isDarkMode ? 'Dark' : 'Light'} mode enabled`, 'info');
}

// Transaction Functions
function loadTransactions() {
    loadTransactionList();
    loadTransactionSummary();
    loadHoldings();
}

function loadTransactionList() {
    $.ajax({
        url: '/api/transactions',
        method: 'GET',
        success: function(data) {
            displayTransactions(data);
        },
        error: function() {
            showAlert('Failed to load transactions', 'error');
        }
    });
}

function displayTransactions(transactions) {
    const tbody = $('#transactions-tbody');
    tbody.empty();
    
    $('#total-transactions').text(transactions.length);
    
    transactions.forEach(txn => {
        const typeClass = txn.transaction_type === 'BUY' ? 'gain' : 'loss';
        const typeText = txn.transaction_type === 'BUY' ? 'BUY' : 'SELL';
        
        const row = $(`
            <tr>
                <td>${new Date(txn.transaction_date).toLocaleDateString()}</td>
                <td><span class="${typeClass}">${typeText}</span></td>
                <td>${txn.symbol}</td>
                <td>${txn.name}</td>
                <td>${txn.quantity}</td>
                <td>${formatCurrency(txn.price_per_unit)}</td>
                <td>${formatCurrency(txn.total_amount)}</td>
                <td>${txn.account_name || 'No Account'}</td>
                <td>${txn.notes || '-'}</td>
            </tr>
        `);
        
        tbody.append(row);
    });
}

function loadTransactionSummary() {
    $.ajax({
        url: '/api/realized-gains',
        method: 'GET',
        success: function(data) {
            let totalRealizedGains = 0;
            
            data.forEach(gain => {
                totalRealizedGains += gain.realized_gain_loss;
            });
            
            const gainClass = totalRealizedGains >= 0 ? 'gain' : 'loss';
            const gainSign = totalRealizedGains >= 0 ? '+' : '';
            
            $('#total-realized-gains')
                .text(`${gainSign}${formatCurrency(totalRealizedGains)}`)
                .removeClass('gain loss')
                .addClass(gainClass);
        },
        error: function() {
            console.log('Realized gains data not available');
        }
    });
}

function loadHoldings() {
    $.ajax({
        url: '/api/holdings',
        method: 'GET',
        success: function(data) {
            displayHoldings(data);
            updateHoldingsSummary(data);
        },
        error: function() {
            console.log('Holdings data not available');
        }
    });
}

function displayHoldings(holdings) {
    const tbody = $('#holdings-tbody');
    tbody.empty();
    
    Object.values(holdings).forEach(holding => {
        const gainLossClass = holding.unrealized_gain_loss >= 0 ? 'gain' : 'loss';
        const gainLossSign = holding.unrealized_gain_loss >= 0 ? '+' : '';
        
        const row = $(`
            <tr>
                <td>${holding.symbol}</td>
                <td>${holding.name}</td>
                <td>${holding.quantity}</td>
                <td>${formatCurrency(holding.average_cost)}</td>
                <td>${formatCurrency(holding.current_price)}</td>
                <td>${formatCurrency(holding.current_value)}</td>
                <td class="${gainLossClass}">${gainLossSign}${formatCurrency(holding.unrealized_gain_loss)}</td>
                <td class="${gainLossClass}">${gainLossSign}${holding.unrealized_gain_loss_percent.toFixed(2)}%</td>
                <td>
                    <button class="btn btn-small btn-secondary" onclick="viewTransactionHistory('${holding.symbol}')">History</button>
                    <button class="btn btn-small btn-primary" onclick="quickSell('${holding.symbol}')">Quick Sell</button>
                </td>
            </tr>
        `);
        
        tbody.append(row);
    });
}

function updateHoldingsSummary(holdings) {
    let totalCurrentValue = 0;
    let totalUnrealizedGains = 0;
    
    Object.values(holdings).forEach(holding => {
        totalCurrentValue += holding.current_value;
        totalUnrealizedGains += holding.unrealized_gain_loss;
    });
    
    $('#current-holdings-value').text(formatCurrency(totalCurrentValue));
    
    const gainClass = totalUnrealizedGains >= 0 ? 'gain' : 'loss';
    const gainSign = totalUnrealizedGains >= 0 ? '+' : '';
    $('#unrealized-gains')
        .text(`${gainSign}${formatCurrency(totalUnrealizedGains)}`)
        .removeClass('gain loss')
        .addClass(gainClass);
}

function handleAddTransaction(e) {
    e.preventDefault();
    
    const transactionData = {
        transaction_type: $('#transaction-type').val(),
        symbol: $('#transaction-symbol').val().toUpperCase(),
        name: $('#transaction-name').val(),
        asset_type: $('#transaction-asset-type').val(),
        quantity: $('#transaction-quantity').val(),
        price_per_unit: $('#transaction-price').val(),
        transaction_date: $('#transaction-date').val(),
        account_id: $('#transaction-account').val() || null,
        currency: $('#transaction-currency').val(),
        notes: $('#transaction-notes').val()
    };
    
    $.ajax({
        url: '/api/transactions',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(transactionData),
        success: function() {
            showAlert('Transaction added successfully!', 'success');
            $('#add-transaction-form').addClass('hidden');
            $('#transaction-form')[0].reset();
            loadTransactions();
            loadDashboard(); // Refresh dashboard
        },
        error: function(xhr) {
            const error = xhr.responseJSON?.error || 'Failed to add transaction';
            showAlert(error, 'error');
        }
    });
}

function searchTransactionSymbol() {
    const symbol = $('#transaction-symbol').val();
    if (!symbol) return;
    
    $.ajax({
        url: `/api/search-symbol/${symbol}`,
        method: 'GET',
        success: function(data) {
            $('#transaction-name').val(data.name);
            $('#transaction-price').val(data.price);
            $('#transaction-currency').val(data.currency);
            calculateTransactionTotal();
            showAlert('Symbol found and details filled!', 'success');
        },
        error: function() {
            showAlert('Symbol not found', 'error');
        }
    });
}

function calculateTransactionTotal() {
    const quantity = parseFloat($('#transaction-quantity').val()) || 0;
    const price = parseFloat($('#transaction-price').val()) || 0;
    const total = quantity * price;
    $('#transaction-total').val(total.toFixed(2));
}

function setTodaysDate() {
    const today = new Date().toISOString().split('T')[0];
    $('#transaction-date').val(today);
}

function loadAccountsForTransactionSelect() {
    $.ajax({
        url: '/api/accounts',
        method: 'GET',
        success: function(data) {
            const select = $('#transaction-account');
            select.find('option:not(:first)').remove();
            
            data.forEach(account => {
                select.append(`<option value="${account.id}">${account.name}</option>`);
            });
        }
    });
}

function viewTransactionHistory(symbol) {
    $.ajax({
        url: `/api/transaction-summary/${symbol}`,
        method: 'GET',
        success: function(data) {
            showTransactionHistoryModal(data);
        },
        error: function() {
            showAlert('Failed to load transaction history', 'error');
        }
    });
}

function showTransactionHistoryModal(data) {
    const modal = $(`
        <div class="modal">
            <div class="modal-content" style="max-width: 800px;">
                <span class="close">&times;</span>
                <h2>${data.symbol} - Transaction History</h2>
                <div class="summary-info">
                    <p><strong>Name:</strong> ${data.name}</p>
                    <p><strong>Current Holdings:</strong> ${data.current_holdings}</p>
                    <p><strong>Average Cost Basis:</strong> ${formatCurrency(data.average_cost_basis)}</p>
                    <p><strong>Total Realized Gains:</strong> <span class="${data.realized_gain_loss >= 0 ? 'gain' : 'loss'}">${formatCurrency(data.realized_gain_loss)}</span></p>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Type</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Total</th>
                            <th>Realized P&L</th>
                        </tr>
                    </thead>
                    <tbody id="history-tbody">
                    </tbody>
                </table>
            </div>
        </div>
    `);
    
    const tbody = modal.find('#history-tbody');
    data.transactions.forEach(txn => {
        const typeClass = txn.transaction_type === 'BUY' ? 'gain' : 'loss';
        const realizedPL = txn.realized_gain_loss ? formatCurrency(txn.realized_gain_loss) : '-';
        
        tbody.append(`
            <tr>
                <td>${new Date(txn.transaction_date).toLocaleDateString()}</td>
                <td><span class="${typeClass}">${txn.transaction_type}</span></td>
                <td>${txn.quantity}</td>
                <td>${formatCurrency(txn.price_per_unit)}</td>
                <td>${formatCurrency(txn.total_amount)}</td>
                <td>${realizedPL}</td>
            </tr>
        `);
    });
    
    $('body').append(modal);
    modal.removeClass('hidden');
    
    modal.find('.close').click(() => modal.remove());
    modal.click(function(e) {
        if (e.target === this) {
            modal.remove();
        }
    });
}

function quickSell(symbol) {
    // Pre-fill sell form with symbol
    $('#transaction-type').val('SELL');
    $('#transaction-symbol').val(symbol);
    $('#transaction-asset-type').val('stock'); // Default, user can change
    $('#add-transaction-btn').click();
    
    // Search symbol to get current price
    $('#search-transaction-symbol-btn').click();
}

function showRealizedGains() {
    $.ajax({
        url: '/api/realized-gains',
        method: 'GET',
        success: function(data) {
            showRealizedGainsModal(data);
        },
        error: function() {
            showAlert('Failed to load realized gains', 'error');
        }
    });
}

function showRealizedGainsModal(data) {
    const modal = $(`
        <div class="modal">
            <div class="modal-content" style="max-width: 1000px;">
                <span class="close">&times;</span>
                <h2>Realized Gains/Losses</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Symbol</th>
                            <th>Sell Date</th>
                            <th>Quantity Sold</th>
                            <th>Sell Price</th>
                            <th>Sell Amount</th>
                            <th>Cost Basis</th>
                            <th>Realized P&L</th>
                            <th>%</th>
                        </tr>
                    </thead>
                    <tbody id="realized-gains-tbody">
                    </tbody>
                </table>
            </div>
        </div>
    `);
    
    const tbody = modal.find('#realized-gains-tbody');
    data.forEach(gain => {
        const gainClass = gain.realized_gain_loss >= 0 ? 'gain' : 'loss';
        const gainSign = gain.realized_gain_loss >= 0 ? '+' : '';
        
        tbody.append(`
            <tr>
                <td>${gain.symbol}</td>
                <td>${new Date(gain.sell_date).toLocaleDateString()}</td>
                <td>${gain.quantity_sold}</td>
                <td>${formatCurrency(gain.sell_price)}</td>
                <td>${formatCurrency(gain.sell_amount)}</td>
                <td>${formatCurrency(gain.cost_basis_total)}</td>
                <td class="${gainClass}">${gainSign}${formatCurrency(gain.realized_gain_loss)}</td>
                <td class="${gainClass}">${gainSign}${gain.realized_gain_loss_percent.toFixed(2)}%</td>
            </tr>
        `);
    });
    
    $('body').append(modal);
    modal.removeClass('hidden');
    
    modal.find('.close').click(() => modal.remove());
    modal.click(function(e) {
        if (e.target === this) {
            modal.remove();
        }
    });
}

// Auto Price Update Functions
function showTabLoadingMessage(message) {
    // Show a subtle loading message
    showAlert(message, 'info');
}

function hideTabLoadingMessage() {
    // Remove info alerts after a delay
    setTimeout(() => {
        $('.alert-info').fadeOut(() => $('.alert-info').remove());
    }, 2000);
}

function updatePricesAndLoadDashboard() {
    // Update prices first, then load dashboard
    $.ajax({
        url: '/api/update-prices',
        method: 'POST',
        success: function(response) {
            hideTabLoadingMessage();
            loadDashboard();
            showAlert('✅ Dashboard prices updated!', 'success');
        },
        error: function() {
            hideTabLoadingMessage();
            loadDashboard();
            showAlert('⚠️ Failed to update some prices, showing cached data', 'error');
        }
    });
}

function updatePricesAndLoadAssets() {
    // Update prices first, then load assets
    $.ajax({
        url: '/api/update-prices',
        method: 'POST',
        success: function(response) {
            hideTabLoadingMessage();
            loadAssets();
            showAlert('✅ Asset prices updated!', 'success');
        },
        error: function() {
            hideTabLoadingMessage();
            loadAssets();
            showAlert('⚠️ Failed to update some prices, showing cached data', 'error');
        }
    });
}

function updatePricesAndLoadTransactions() {
    // Update prices first, then load transaction data
    $.ajax({
        url: '/api/update-prices',
        method: 'POST',
        success: function(response) {
            hideTabLoadingMessage();
            loadTransactions();
            showAlert('✅ Portfolio data updated!', 'success');
        },
        error: function() {
            hideTabLoadingMessage();
            loadTransactions();
            showAlert('⚠️ Failed to update some prices, showing cached data', 'error');
        }
    });
}

function updatePricesAndLoadAnalytics() {
    // Update prices first, then load analytics
    $.ajax({
        url: '/api/update-prices',
        method: 'POST',
        success: function(response) {
            hideTabLoadingMessage();
            loadAnalytics();
            showAlert('✅ Analytics data updated!', 'success');
        },
        error: function() {
            hideTabLoadingMessage();
            loadAnalytics();
            showAlert('⚠️ Failed to update some prices, showing cached data', 'error');
        }
    });
}

// CSV Import functionality
let selectedFile = null;

function initializeImport() {
    console.log('Initializing import functionality...');
    const uploadArea = document.getElementById('csv-upload-area');
    const fileInput = document.getElementById('csv-file-input');
    const selectBtn = document.getElementById('select-csv-btn');
    const importBtn = document.getElementById('import-csv-btn');
    const removeFileBtn = document.getElementById('remove-csv-file');
    
    // File selection
    selectBtn?.addEventListener('click', () => {
        fileInput?.click();
    });
    
    // Drag and drop
    uploadArea?.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea?.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea?.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    });
    
    // Click to select
    uploadArea?.addEventListener('click', () => {
        fileInput?.click();
    });
    
    fileInput?.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
    
    // Remove file
    removeFileBtn?.addEventListener('click', () => {
        clearFileSelection();
    });
    
    // Import button
    importBtn?.addEventListener('click', () => {
        console.log('Import button clicked, selectedFile:', selectedFile);
        if (selectedFile) {
            const previewEnabled = document.getElementById('preview-import')?.checked;
            console.log('Preview enabled:', previewEnabled);
            if (previewEnabled) {
                previewCSV();
            } else {
                importCSV();
            }
        } else {
            console.log('No file selected');
        }
    });
    
    // Preview actions
    document.getElementById('confirm-import-btn')?.addEventListener('click', () => {
        importCSV();
    });
    
    document.getElementById('cancel-import-btn')?.addEventListener('click', () => {
        hideImportPreview();
    });
    
    // Results actions
    document.getElementById('view-imported-assets')?.addEventListener('click', () => {
        switchTab('assets');
    });
    
    document.getElementById('view-imported-transactions')?.addEventListener('click', () => {
        switchTab('transactions');
    });
}

function handleFileSelection(file) {
    console.log('File selected:', file.name, 'Size:', file.size);
    if (!file.name.toLowerCase().endsWith('.csv')) {
        showAlert('❌ Please select a CSV file', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showAlert('❌ File is too large. Please select a file smaller than 10MB', 'error');
        return;
    }
    
    selectedFile = file;
    console.log('File accepted, selectedFile set to:', selectedFile);
    
    // Update UI
    document.getElementById('csv-file-name').textContent = file.name;
    document.getElementById('csv-file-size').textContent = formatFileSize(file.size);
    document.getElementById('csv-file-info').classList.remove('hidden');
    document.getElementById('csv-upload-area').style.display = 'none';
    document.getElementById('import-csv-btn').disabled = false;
    
    // Reset previous states
    hideImportPreview();
    hideImportResults();
    hideImportStatus();
}

function clearFileSelection() {
    selectedFile = null;
    document.getElementById('csv-file-info').classList.add('hidden');
    document.getElementById('csv-upload-area').style.display = 'block';
    document.getElementById('import-csv-btn').disabled = true;
    document.getElementById('csv-file-input').value = '';
    
    // Reset states
    hideImportPreview();
    hideImportResults();
    hideImportStatus();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function previewCSV() {
    if (!selectedFile) return;
    
    console.log('previewCSV called, sending request to preview-csv endpoint');
    showImportStatus('Processing CSV file...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    
    $.ajax({
        url: '/api/preview-csv',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            console.log('Preview response:', response);
            hideImportStatus();
            
            if (response.success) {
                showImportPreview();
                populatePreviewTable({
                    transactions: response.transactions,
                    broker: response.broker,
                    total_count: response.total_count
                });
            } else {
                showAlert('❌ Preview failed: ' + (response.error || 'Unknown error'), 'error');
            }
        },
        error: function(xhr) {
            console.error('Preview error:', xhr);
            hideImportStatus();
            let errorMsg = 'Failed to preview CSV file';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMsg = response.error || errorMsg;
            } catch (e) {
                // Use default error message
            }
            showAlert('❌ ' + errorMsg, 'error');
        }
    });
}

function importCSV() {
    console.log('importCSV called, selectedFile:', selectedFile);
    if (!selectedFile) {
        console.log('No selectedFile, returning');
        return;
    }
    
    showImportStatus('Importing transactions...');
    
    const formData = new FormData();
    formData.append('file', selectedFile);
    console.log('FormData created, sending AJAX request...');
    
    $.ajax({
        url: '/api/import-csv',
        method: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        success: function(response) {
            hideImportStatus();
            hideImportPreview();
            
            if (response.success) {
                showImportResults({
                    transactions_imported: response.transactions_imported,
                    assets_updated: response.assets_updated,
                    broker: response.broker
                });
                showAlert('✅ ' + response.message, 'success');
                
                // Refresh data
                loadAssets();
                loadTransactions();
                loadDashboard();
            } else {
                showAlert('❌ Import failed: ' + (response.error || 'Unknown error'), 'error');
            }
        },
        error: function(xhr) {
            hideImportStatus();
            let errorMsg = 'Failed to import CSV file';
            try {
                const response = JSON.parse(xhr.responseText);
                errorMsg = response.error || errorMsg;
            } catch (e) {
                // Use default error message
            }
            showAlert('❌ ' + errorMsg, 'error');
        }
    });
}

function showImportStatus(message) {
    document.getElementById('import-message').textContent = message;
    document.getElementById('import-status').classList.remove('hidden');
    document.getElementById('import-csv-btn').disabled = true;
}

function hideImportStatus() {
    document.getElementById('import-status').classList.add('hidden');
    document.getElementById('import-csv-btn').disabled = false;
}

function showImportPreview() {
    document.getElementById('import-preview').classList.remove('hidden');
}

function hideImportPreview() {
    document.getElementById('import-preview').classList.add('hidden');
}

function populatePreviewTable(data) {
    const tbody = document.getElementById('preview-transactions-tbody');
    const transactionCount = document.getElementById('transaction-count');
    const detectedBroker = document.getElementById('detected-broker');
    
    tbody.innerHTML = '';
    transactionCount.textContent = data.total_count || data.transactions.length;
    detectedBroker.textContent = data.broker;
    
    data.transactions.forEach(transaction => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${transaction.date}</td>
            <td>${transaction.symbol}</td>
            <td><span class="transaction-type ${transaction.type.toLowerCase()}">${transaction.type}</span></td>
            <td>${transaction.quantity}</td>
            <td>$${transaction.price.toFixed(2)}</td>
            <td>$${transaction.amount.toFixed(2)}</td>
            <td>${transaction.description}</td>
        `;
        tbody.appendChild(row);
    });
}

function showImportResults(results) {
    document.getElementById('imported-transactions').textContent = results.transactions_imported;
    document.getElementById('updated-assets').textContent = results.assets_updated;
    document.getElementById('import-broker').textContent = results.broker;
    document.getElementById('import-results').classList.remove('hidden');
}

function hideImportResults() {
    document.getElementById('import-results').classList.add('hidden');
}

// Initialize import functionality when page loads
$(document).ready(function() {
    initializeImport();
});