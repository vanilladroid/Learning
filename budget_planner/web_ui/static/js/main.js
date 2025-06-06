const API_BASE_URL = 'http://localhost:8000'; // Assuming API is on port 8000
let authToken = localStorage.getItem('authToken');
let currentUserId = localStorage.getItem('currentUserId'); // For placeholder auth

// Views
const loginView = document.getElementById('login-view');
const registerView = document.getElementById('register-view');
const dashboardView = document.getElementById('dashboard-view');
const appContent = document.getElementById('app-content');

// Nav links
const navLogin = document.getElementById('nav-login');
const navRegister = document.getElementById('nav-register');
const navDashboard = document.getElementById('nav-dashboard');
const navLogout = document.getElementById('nav-logout');

// Forms & Buttons
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const categoryForm = document.getElementById('category-form');
const transactionForm = document.getElementById('transaction-form');
const categorySubmitBtn = document.getElementById('category-submit-btn');
const categoryCancelEditBtn = document.getElementById('category-cancel-edit-btn');
const transactionSubmitBtn = document.getElementById('transaction-submit-btn');
const transactionCancelEditBtn = document.getElementById('transaction-cancel-edit-btn');


// Error displays
const loginError = document.getElementById('login-error');
const registerError = document.getElementById('register-error');
const categoryError = document.getElementById('category-error');
const transactionError = document.getElementById('transaction-error');

// Dashboard elements
const dashUsername = document.getElementById('dash-username');
const categoriesTableBody = document.querySelector('#categories-table tbody');
const transactionsTableBody = document.querySelector('#transactions-table tbody');
const transactionCategorySelect = document.getElementById('transaction-category');

function showView(viewToShow) {
    loginView.classList.add('hidden');
    registerView.classList.add('hidden');
    dashboardView.classList.add('hidden');
    appContent.classList.add('hidden'); // Hide the initial welcome message

    if (viewToShow) {
        viewToShow.classList.remove('hidden');
    } else {
        appContent.classList.remove('hidden'); // Show welcome if no specific view
    }
}

function updateNav() {
    if (authToken) {
        navLogin.classList.add('hidden');
        navRegister.classList.add('hidden');
        navDashboard.classList.remove('hidden');
        navLogout.classList.remove('hidden');
    } else {
        navLogin.classList.remove('hidden');
        navRegister.classList.remove('hidden');
        navDashboard.classList.add('hidden');
        navLogout.classList.add('hidden');
    }
}

async function apiRequest(endpoint, method = 'GET', body = null, token = null) {
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
        headers['Authorization'] = \`Bearer \${token}\`; // Standard token auth
    }
    // For placeholder auth, the user_id is part of the URL or handled by Depends in FastAPI
    // This is a simplification for the dummy token.
    // If your placeholder auth requires user_id in header, add it here.
    // if (currentUserId) headers['X-User-ID'] = currentUserId; // Example if header needed

    const config = { method, headers };
    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(API_BASE_URL + endpoint, config);
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: response.statusText }));
            console.error('API Error:', response.status, errorData);
            throw new Error(errorData.detail || \`HTTP error! status: \${response.status}\`);
        }
        if (response.status === 204) return null; // No content
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        throw error;
    }
}

// --- Auth ---
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.textContent = '';
        const username = document.getElementById('login-username').value;
        const password = document.getElementById('login-password').value;
        try {
            const data = await apiRequest('/auth/login', 'POST', { username, password });
            authToken = data.access_token;
            // The dummy token contains user_id, extract it IF NEEDED for placeholder.
            // currentUserId = authToken.split('_').pop(); // Example: "dummytoken_for_user_1" -> "1"
            // For now, placeholder user is hardcoded in FastAPI dependencies.
            // If your API returns user info on login, use that.
            localStorage.setItem('authToken', authToken);
            // localStorage.setItem('currentUserId', currentUserId);
            updateNav();
            showView(dashboardView);
            loadDashboardData();
        } catch (error) {
            loginError.textContent = error.message;
        }
    });
}

if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        registerError.textContent = '';
        const username = document.getElementById('register-username').value;
        const password = document.getElementById('register-password').value;
        try {
            await apiRequest('/auth/register', 'POST', { username, password });
            alert('Registration successful! Please login.');
            showView(loginView);
        } catch (error) {
            registerError.textContent = error.message;
        }
    });
}

navLogin.addEventListener('click', (e) => { e.preventDefault(); showView(loginView); });
navRegister.addEventListener('click', (e) => { e.preventDefault(); showView(registerView); });
navDashboard.addEventListener('click', (e) => { e.preventDefault(); if(authToken) showView(dashboardView); loadDashboardData(); });
navLogout.addEventListener('click', (e) => {
    e.preventDefault();
    authToken = null;
    currentUserId = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUserId');
    updateNav();
    showView(null); // Show welcome message
    dashUsername.textContent = '';
});

// --- Categories ---
async function loadCategories() {
    if (!authToken) return;
    try {
        const categories = await apiRequest('/categories/', 'GET', null, authToken);
        categoriesTableBody.innerHTML = ''; // Clear existing
        transactionCategorySelect.innerHTML = '<option value="">Select Category</option>'; // Clear and add default
        categories.forEach(cat => {
            const row = categoriesTableBody.insertRow();
            row.insertCell().textContent = cat.name;
            const actionsCell = row.insertCell();
            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => setupEditCategory(cat);
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.style.backgroundColor = '#d9534f'; // Red color for delete
            deleteBtn.onclick = () => deleteCategory(cat.id);
            actionsCell.appendChild(editBtn);
            actionsCell.appendChild(deleteBtn);

            const option = document.createElement('option');
            option.value = cat.id;
            option.textContent = cat.name;
            transactionCategorySelect.appendChild(option);
        });
    } catch (error) {
        categoryError.textContent = \`Error loading categories: \${error.message}\`;
    }
}

if (categoryForm) {
    categoryForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        categoryError.textContent = '';
        const name = document.getElementById('category-name').value;
        const id = document.getElementById('category-id').value;
        const method = id ? 'PUT' : 'POST';
        const endpoint = id ? \`/categories/\${id}\` : '/categories/';
        try {
            await apiRequest(endpoint, method, { name }, authToken);
            resetCategoryForm();
            loadCategories();
        } catch (error) {
            categoryError.textContent = error.message;
        }
    });
}
categoryCancelEditBtn.addEventListener('click', resetCategoryForm);

function setupEditCategory(category) {
    document.getElementById('category-id').value = category.id;
    document.getElementById('category-name').value = category.name;
    categorySubmitBtn.textContent = 'Update Category';
    categoryCancelEditBtn.classList.remove('hidden');
}

function resetCategoryForm() {
    categoryForm.reset();
    document.getElementById('category-id').value = '';
    categorySubmitBtn.textContent = 'Add Category';
    categoryCancelEditBtn.classList.add('hidden');
    categoryError.textContent = '';
}

async function deleteCategory(id) {
    if (!authToken || !confirm('Are you sure you want to delete this category?')) return;
    try {
        await apiRequest(\`/categories/\${id}\`, 'DELETE', null, authToken);
        loadCategories(); // Refresh list
    } catch (error) {
        categoryError.textContent = \`Error deleting category: \${error.message}\`;
    }
}

// --- Transactions ---
async function loadTransactions() {
    if (!authToken) return;
    try {
        const transactions = await apiRequest('/transactions/', 'GET', null, authToken);
        transactionsTableBody.innerHTML = ''; // Clear existing
        transactions.forEach(tx => {
            const row = transactionsTableBody.insertRow();
            row.insertCell().textContent = new Date(tx.date).toLocaleString();
            row.insertCell().textContent = tx.category.name; // Assuming category is nested
            row.insertCell().textContent = tx.type;
            row.insertCell().textContent = tx.amount.toFixed(2);
            row.insertCell().textContent = tx.description || '';
            const actionsCell = row.insertCell();
            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => setupEditTransaction(tx);
            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.style.backgroundColor = '#d9534f';
            deleteBtn.onclick = () => deleteTransaction(tx.id);
            actionsCell.appendChild(editBtn);
            actionsCell.appendChild(deleteBtn);
        });
    } catch (error) {
        transactionError.textContent = \`Error loading transactions: \${error.message}\`;
    }
}

if (transactionForm) {
    transactionForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        transactionError.textContent = '';
        const id = document.getElementById('transaction-id').value;
        const transactionData = {
            amount: parseFloat(document.getElementById('transaction-amount').value),
            type: document.getElementById('transaction-type').value,
            date: new Date(document.getElementById('transaction-date').value).toISOString(),
            category_id: parseInt(document.getElementById('transaction-category').value),
            description: document.getElementById('transaction-description').value,
        };

        const method = id ? 'PUT' : 'POST';
        const endpoint = id ? \`/transactions/\${id}\` : '/transactions/';
        try {
            await apiRequest(endpoint, method, transactionData, authToken);
            resetTransactionForm();
            loadTransactions();
        } catch (error) {
            transactionError.textContent = error.message;
        }
    });
}
transactionCancelEditBtn.addEventListener('click', resetTransactionForm);

function setupEditTransaction(transaction) {
    document.getElementById('transaction-id').value = transaction.id;
    document.getElementById('transaction-amount').value = transaction.amount;
    document.getElementById('transaction-type').value = transaction.type;
    // Format date for datetime-local input: YYYY-MM-DDTHH:mm
    const dt = new Date(transaction.date);
    // dt.setMinutes(dt.getMinutes() - dt.getTimezoneOffset()); // Adjust for local timezone if needed for display
    document.getElementById('transaction-date').value = dt.toISOString().slice(0,16);
    document.getElementById('transaction-category').value = transaction.category_id;
    document.getElementById('transaction-description').value = transaction.description || '';
    transactionSubmitBtn.textContent = 'Update Transaction';
    transactionCancelEditBtn.classList.remove('hidden');
}

function resetTransactionForm() {
    transactionForm.reset();
    document.getElementById('transaction-id').value = '';
    document.getElementById('transaction-date').valueAsISOString; // Or set to now
    transactionSubmitBtn.textContent = 'Add Transaction';
    transactionCancelEditBtn.classList.add('hidden');
    transactionError.textContent = '';
}

async function deleteTransaction(id) {
    if (!authToken || !confirm('Are you sure you want to delete this transaction?')) return;
    try {
        await apiRequest(\`/transactions/\${id}\`, 'DELETE', null, authToken);
        loadTransactions(); // Refresh list
    } catch (error) {
        transactionError.textContent = \`Error deleting transaction: \${error.message}\`;
    }
}


// --- Initial Load ---
function loadDashboardData() {
    if (authToken) {
        // dashUsername.textContent = currentUserId; // Or fetch actual username
        // Try to get actual username from a /users/me endpoint if it exists
        // For now, just indicate logged in
        dashUsername.textContent = "User"; // Placeholder
        loadCategories(); // This will also populate transaction category dropdown
        loadTransactions();
    }
}

// Check auth status on page load
if (authToken) {
    // Potentially verify token with API here, for now assume it's valid if present
    updateNav();
    showView(dashboardView);
    loadDashboardData();
} else {
    updateNav();
    showView(null); // Show welcome
}

// Set current date for transaction form
document.getElementById('transaction-date').value = new Date().toISOString().slice(0,16);

console.log("Basic UI loaded. API calls will target:", API_BASE_URL);

// --- Goals ---
const goalForm = document.getElementById('goal-form');
const goalSubmitBtn = document.getElementById('goal-submit-btn');
const goalCancelEditBtn = document.getElementById('goal-cancel-edit-btn');
const goalError = document.getElementById('goal-error');
const goalsTableBody = document.querySelector('#goals-table tbody');

async function loadGoals() {
    if (!authToken || !goalsTableBody) return; // Check if element exists
    try {
        const goals = await apiRequest('/goals/', 'GET', null, authToken);
        goalsTableBody.innerHTML = ''; // Clear existing
        goals.forEach(goal => {
            const row = goalsTableBody.insertRow();
            row.insertCell().textContent = goal.name;
            row.insertCell().textContent = goal.target_amount.toFixed(2);
            row.insertCell().textContent = goal.current_amount.toFixed(2);

            const progressCell = row.insertCell();
            const progressBar = document.createElement('div');
            progressBar.style.width = '100px';
            progressBar.style.height = '20px';
            progressBar.style.border = '1px solid #ccc';
            progressBar.style.backgroundColor = '#e9ecef';
            progressBar.style.position = 'relative'; // For text overlay
            const progressFill = document.createElement('div');
            progressFill.style.width = `${goal.progress_percentage}%`;
            progressFill.style.height = '100%';
            progressFill.style.backgroundColor = '#5cb85c';

            const progressText = document.createElement('span'); // For text
            progressText.textContent = `${goal.progress_percentage}%`;
            progressText.style.position = 'absolute';
            progressText.style.left = '50%';
            progressText.style.top = '50%';
            progressText.style.transform = 'translate(-50%, -50%)';
            progressText.style.fontSize = '12px';
            progressText.style.color = goal.progress_percentage > 40 ? 'white' : 'black';


            progressBar.appendChild(progressFill);
            progressBar.appendChild(progressText);
            progressCell.appendChild(progressBar);

            row.insertCell().textContent = goal.target_date ? new Date(goal.target_date).toLocaleDateString() : 'N/A';

            const actionsCell = row.insertCell();
            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.onclick = () => setupEditGoal(goal);
            actionsCell.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.style.backgroundColor = '#d9534f';
            deleteBtn.onclick = () => deleteGoal(goal.id);
            actionsCell.appendChild(deleteBtn);

            const contributeInput = document.createElement('input');
            contributeInput.type = 'number';
            contributeInput.placeholder = 'Amount';
            contributeInput.style.width = '70px';
            contributeInput.step = '0.01';
            contributeInput.className = 'contribute-input'; // For styling/selection
            actionsCell.appendChild(contributeInput);

            const contributeBtn = document.createElement('button');
            contributeBtn.textContent = 'Save';
            contributeBtn.className = 'contribute-btn';
            contributeBtn.onclick = () => {
                const amount = parseFloat(contributeInput.value);
                if (isNaN(amount)) {
                    if(goalError) goalError.textContent = 'Invalid amount for contribution.';
                    return;
                }
                contributeToGoal(goal.id, amount);
                contributeInput.value = ''; // Clear input after attempt
            };
            actionsCell.appendChild(contributeBtn);
        });
    } catch (error) {
        if(goalError) goalError.textContent = `Error loading goals: ${error.message}`;
        console.error("Error loading goals:", error);
    }
}

if (goalForm) {
    goalForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if(goalError) goalError.textContent = '';
        const id = document.getElementById('goal-id').value;
        const targetDateValue = document.getElementById('goal-target-date').value;

        const goalData = { // This is for GoalCreate or parts of GoalUpdate
            name: document.getElementById('goal-name').value,
            target_amount: parseFloat(document.getElementById('goal-target-amount').value),
            current_amount: parseFloat(document.getElementById('goal-current-amount').value),
            // API expects ISO string for datetime, or null
            target_date: targetDateValue ? new Date(targetDateValue).toISOString() : null
        };

        const method = id ? 'PUT' : 'POST';
        const endpoint = id ? `/goals/${id}` : '/goals/';

        let payload = goalData; // For POST (GoalCreate)
        if (method === 'PUT') { // For PUT (GoalUpdate)
            payload = {
                name: goalData.name,
                target_amount: goalData.target_amount,
                current_amount: goalData.current_amount,
                target_date: goalData.target_date, // API handles None
                clear_target_date: !goalData.target_date // if target_date is null/empty, clear it.
            };
        }

        try {
            await apiRequest(endpoint, method, payload, authToken);
            resetGoalForm();
            loadGoals();
        } catch (error) {
            if(goalError) goalError.textContent = error.message;
        }
    });
}

if (goalCancelEditBtn) {
    goalCancelEditBtn.addEventListener('click', resetGoalForm);
}

function setupEditGoal(goal) {
    document.getElementById('goal-id').value = goal.id;
    document.getElementById('goal-name').value = goal.name;
    document.getElementById('goal-target-amount').value = goal.target_amount;
    document.getElementById('goal-current-amount').value = goal.current_amount;
    document.getElementById('goal-target-date').value = goal.target_date ? new Date(goal.target_date).toISOString().slice(0,16) : '';
    if(goalSubmitBtn) goalSubmitBtn.textContent = 'Update Goal';
    if(goalCancelEditBtn) goalCancelEditBtn.classList.remove('hidden');
}

function resetGoalForm() {
    if(goalForm) goalForm.reset();
    document.getElementById('goal-id').value = '';
    document.getElementById('goal-current-amount').value = '0';
    if(goalSubmitBtn) goalSubmitBtn.textContent = 'Add Goal';
    if(goalCancelEditBtn) goalCancelEditBtn.classList.add('hidden');
    if(goalError) goalError.textContent = '';
}

async function deleteGoal(id) {
    if (!authToken || !confirm('Are you sure you want to delete this goal?')) return;
    try {
        await apiRequest(`/goals/${id}`, 'DELETE', null, authToken);
        loadGoals();
    } catch (error) {
        if(goalError) goalError.textContent = `Error deleting goal: ${error.message}`;
    }
}

async function contributeToGoal(id, amount) {
    if (!authToken || isNaN(amount) || amount <= 0) { // Check amount is valid number
        if(goalError) goalError.textContent = 'Please enter a valid positive amount to contribute.';
        return;
    }
    if(goalError) goalError.textContent = '';
    try {
        await apiRequest(`/goals/${id}/contribute`, 'POST', { amount }, authToken);
        loadGoals();
    } catch (error) {
        if(goalError) goalError.textContent = `Error contributing to goal: ${error.message}`;
    }
}

// Modify loadDashboardData to include loading goals
// This requires loadDashboardData to be defined before this modification.
// Ensure this script block is appended at the very end of main.js or structure carefully.
// A safer way is to redefine loadDashboardData if we know its full previous content.
// For now, assuming it's defined and this append approach works.
// This is a common pattern: store old function, redefine, call old one inside new one.
if (typeof loadDashboardData === 'function') {
    const original_loadDashboardData = loadDashboardData;
    loadDashboardData = function() {
        original_loadDashboardData();
        if (authToken) {
            loadGoals();
        }
    };
} else {
    // If loadDashboardData was not defined, define it now (less ideal)
    console.warn("loadDashboardData was not previously defined. Defining now with goals.")
    loadDashboardData = function() {
        if (authToken) {
            dashUsername.textContent = "User"; // Placeholder
            loadCategories();
            loadTransactions();
            loadGoals(); // Add goals here
        }
    }
}
