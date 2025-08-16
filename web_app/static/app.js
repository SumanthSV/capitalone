// KrishiMitra - Unified AI Chat Application
console.log('KrishiMitra JavaScript loaded');

let currentUser = null;
let authToken = null;
let isProcessingQuery = false;
let chatHistory = [];

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - initializing app');
    initializeApp();
});

function initializeApp() {
    console.log('initializeApp called');
    setupEventListeners();
    updateOnlineStatus();
    checkAuthStatus();
    
    // Monitor online/offline status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    console.log('initializeApp completed');
}

function setupEventListeners() {
    console.log('Setting up event listeners');
    
    // Wait for DOM to be ready
    setTimeout(() => {
        // Set up form submission
        const form = document.getElementById('unifiedForm');
        if (form) {
            console.log('Found unified form, adding submit handler');
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                console.log('Form submitted');
                handleUnifiedQuery(e);
            });
        }
        
        // Set up submit button click
        const submitBtn = document.getElementById('sendBtn');
        if (submitBtn) {
            console.log('Found submit button, adding click handler');
            submitBtn.addEventListener('click', function(e) {
                e.preventDefault();
                console.log('Submit button clicked');
                
                const textQuery = document.getElementById('unifiedQuery').value?.trim();
                if (!textQuery) {
                    showMessage('Please enter a question!', 'warning');
                    return;
                }
                
                // Create synthetic form event
                const form = document.getElementById('unifiedForm');
                const syntheticEvent = {
                    preventDefault: () => {},
                    target: form,
                    type: 'submit'
                };
                
                handleUnifiedQuery(syntheticEvent);
            });
        }
        
        // Set up Enter key on textarea
        const textarea = document.getElementById('unifiedQuery');
        if (textarea) {
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!isProcessingQuery) {
                        const form = document.getElementById('unifiedForm');
                        const syntheticEvent = {
                            preventDefault: () => {},
                            target: form,
                            type: 'submit'
                        };
                        handleUnifiedQuery(syntheticEvent);
                    }
                }
            });
        }
        
        // Set up other button handlers
        const imageBtn = document.getElementById('imageBtn');
        if (imageBtn) {
            imageBtn.addEventListener('click', () => {
                document.getElementById('imageInput').click();
            });
        }
        
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.addEventListener('click', handleVoiceInput);
        }
        
        const sensorBtn = document.getElementById('sensorBtn');
        if (sensorBtn) {
            sensorBtn.addEventListener('click', toggleSensorData);
        }
        
        // Set up image input change handler
        const imageInput = document.getElementById('imageInput');
        if (imageInput) {
            imageInput.addEventListener('change', handleImageSelection);
        }
        
        console.log('Event listeners setup completed');
        
    }, 500);
}

// Authentication Functions
function checkAuthStatus() {
    authToken = localStorage.getItem('authToken');
    currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    
    console.log('Auth status:', { hasToken: !!authToken, hasUser: !!currentUser });
    
    if (authToken && currentUser) {
        updateUserInterface();
        // Only load authenticated data if user is actually logged in
        setTimeout(() => {
            loadUserContext();
            loadNotifications();
        }, 1000);
    } else {
        // Don't show auth modal immediately - let users try the app first
        console.log('No authentication - user can still use basic features');
        updateUserInterface(); // Update UI to show guest status
    }
}

function updateUserInterface() {
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.querySelector('.logout-btn');
    
    if (currentUser) {
        userInfo.textContent = currentUser.name;
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
        hideAuthModal();
    } else {
        userInfo.textContent = 'Guest User (Click to Login)';
        if (logoutBtn) logoutBtn.style.display = 'none';
        
        // Make user info clickable to show auth modal
        userInfo.style.cursor = 'pointer';
        userInfo.onclick = showAuthModal;
    }
}

function showAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.style.display = 'flex';
        // Allow clicking outside to dismiss
        authModal.addEventListener('click', function(e) {
            if (e.target === authModal) {
                hideAuthModal();
            }
        });
    }
}

function hideAuthModal() {
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.style.display = 'none';
    }
}

function switchAuthTab(tabName) {
    // Hide all auth tabs
    document.querySelectorAll('.auth-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.auth-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'AuthTab').classList.add('active');
    event.target.classList.add('active');
}

async function handleLogin(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const loginData = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (result.access_token) {
            authToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateUserInterface();
            showMessage('Login successful!', 'success');
            }, 500);
        } else {
        function updateLanguagePreference() {
            const responseLanguage = document.getElementById('responseLanguage').value;
            const languageInput = document.getElementById('languageInput');
            if (languageInput) {
                languageInput.value = responseLanguage;
            }
            console.log('[INFO] Language preference updated to:', responseLanguage);
        }
        
            showMessage('Login failed: ' + (result.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        showMessage('Login error: ' + error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const registerData = {
        email: formData.get('email'),
        name: formData.get('name'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (result.access_token) {
            authToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateUserInterface();
            showMessage('Registration successful!', 'success');
            
            // Show farming context modal for new users
            setTimeout(showFarmingContextModal, 1000);
        } else {
            showMessage('Registration failed: ' + (result.detail || 'Unknown error'), 'error');
        }
    } catch (error) {
        showMessage('Registration error: ' + error.message, 'error');
    }
}

async function sendOTP() {
    const phoneNumber = document.getElementById('phoneNumber').value;
    const countryCode = document.getElementById('countryCode').value;
    
    if (!phoneNumber) {
        showMessage('Please enter phone number', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/send-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                country_code: countryCode
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('sessionId').value = result.session_id;
            document.getElementById('otpSection').style.display = 'block';
            document.getElementById('sendOtpBtn').disabled = true;
            showMessage('OTP sent successfully!', 'success');
            
            // Start countdown
            startOTPCountdown(600); // 10 minutes
        } else {
            showMessage('Failed to send OTP: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('OTP error: ' + error.message, 'error');
    }
}

async function verifyOTP() {
    const sessionId = document.getElementById('sessionId').value;
    const otpCode = document.getElementById('otpCode').value;
    
    if (!otpCode) {
        showMessage('Please enter OTP', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                otp_code: otpCode
            })
        });
        
        const result = await response.json();
        
        if (result.success && result.access_token) {
            authToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            updateUserInterface();
            showMessage('Phone verification successful!', 'success');
            
            // Show farming context modal for new users
            if (result.user.new_user) {
                setTimeout(showFarmingContextModal, 1000);
            }
        } else {
            showMessage('OTP verification failed: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('Verification error: ' + error.message, 'error');
    }
}

function startOTPCountdown(seconds) {
    const countdownElement = document.getElementById('otpCountdown');
    
    const interval = setInterval(() => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        countdownElement.textContent = `OTP expires in ${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
        
        seconds--;
        
        if (seconds < 0) {
            clearInterval(interval);
            countdownElement.textContent = 'OTP expired. Please request a new one.';
            document.getElementById('sendOtpBtn').disabled = false;
        }
    }, 1000);
}

function logout() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    authToken = null;
    currentUser = null;
    
    updateUserInterface();
    
    // Clear chat history
    chatHistory = [];
    updateChatDisplay();
    
    showMessage('Logged out successfully', 'success');
}

// Farming Context Functions
async function loadUserContext() {
    if (!authToken) {
        console.log('No auth token - skipping user context load');
        return;
    }
    
    try {
        const response = await fetch('/api/context/farming', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.status === 401) {
            console.log('Unauthorized - clearing invalid token');
            logout();
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            displayUserContext(result.context);
        } else if (response.status === 404) {
            // No farming context found - show modal
            showFarmingContextModal();
        }
    } catch (error) {
        console.error('Error loading user context:', error);
    }
}

function showFarmingContextModal() {
    const modal = document.getElementById('farmingContextModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function hideFarmingContextModal() {
    const modal = document.getElementById('farmingContextModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function saveFarmingContext(event) {
    event.preventDefault();
    
    if (!authToken) {
        showMessage('Please login first', 'error');
        return;
    }
    
    const formData = new FormData(event.target);
    const contextData = {
        location: formData.get('location'),
        primary_crops: formData.get('primary_crops').split(',').map(c => c.trim()),
        secondary_crops: formData.get('secondary_crops') ? formData.get('secondary_crops').split(',').map(c => c.trim()) : [],
        farm_size_acres: parseFloat(formData.get('farm_size_acres')),
        soil_type: formData.get('soil_type'),
        irrigation_method: formData.get('irrigation_method'),
        irrigation_frequency_days: parseInt(formData.get('irrigation_frequency_days')),
        farming_experience: formData.get('farming_experience'),
        preferred_language: formData.get('preferred_language')
    };
    
    try {
        const response = await fetch('/api/context/farming', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(contextData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            hideFarmingContextModal();
            showMessage('Farming profile saved successfully!', 'success');
            loadUserContext(); // Reload to display
        } else {
            showMessage('Failed to save profile: ' + result.error, 'error');
        }
    } catch (error) {
        showMessage('Error saving profile: ' + error.message, 'error');
    }
}

function displayUserContext(context) {
    const contextInfo = document.getElementById('contextInfo');
    
    if (context && context.location) {
        contextInfo.style.display = 'block';
        contextInfo.innerHTML = `
            <div class="context-summary">
                <h4>🌾 Your Farm Profile</h4>
                <div class="context-details">
                    <span>📍 ${context.location}</span>
                    <span>🌾 ${context.primary_crops.join(', ')}</span>
                    <span>🏞️ ${context.farm_size_acres} acres</span>
                    <span>🚰 ${context.irrigation_method}</span>
                    <span>👨‍🌾 ${context.farming_experience}</span>
                    ${context.last_irrigation ? `<span>💧 Last irrigation: ${new Date(context.last_irrigation).toLocaleDateString()}</span>` : ''}
                </div>
            </div>
        `;
    } else {
        contextInfo.style.display = 'none';
    }
}

// Main Query Processing
async function handleUnifiedQuery(event) {
    console.log('\n=== FRONTEND QUERY PROCESSING START ===');
    console.log('handleUnifiedQuery called at:', new Date().toISOString());
    
    try {
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }
        
        if (isProcessingQuery) {
            console.log('[WARNING] Query already in progress, blocking new request');
            showMessage('Please wait for your previous query to complete', 'warning');
            return;
        }
        
        console.log('[INFO] Processing query started...');
        
        // Get form data
        const form = document.getElementById('unifiedForm');
        if (!form) {
            console.error('[ERROR] Form not found!');
            showMessage('Error: Form not found', 'error');
            return;
        }
        
        const formData = new FormData(form);
        const textQuery = document.getElementById('unifiedQuery').value?.trim();
        const imageFile = document.getElementById('imageInput').files[0];
        const languageSelect = document.getElementById('languageInput');
        const selectedLanguage = languageSelect ? languageSelect.value : 'english';
        
        console.log('[INFO] Form data extracted:', { 
            textQuery: textQuery || 'empty', 
            imageFile: imageFile ? imageFile.name : 'none',
            language: selectedLanguage
        });
        
        // Validate input
        if (!textQuery && !imageFile) {
            console.log('[ERROR] No valid input provided');
            showMessage('Please enter a question or upload an image', 'warning');
            return;
        }
        
        // Block further queries
        isProcessingQuery = true;
        console.log('[INFO] Query processing locked');
        disableInput();
        showTypingIndicator();
        
        // Add user message to chat
        if (textQuery) {
            console.log('[INFO] Adding user message to chat');
            addMessageToChat('user', textQuery);
        }
        if (imageFile) {
            console.log('[INFO] Adding image upload message to chat');
            addMessageToChat('user', `📷 Uploaded image: ${imageFile.name}`);
        }
        
        // Prepare form data for API
        const apiFormData = new FormData();
        apiFormData.append('text', textQuery);
        apiFormData.append('language', selectedLanguage);
        
        console.log('[INFO] API form data prepared with language:', selectedLanguage);
        
        if (imageFile) {
            apiFormData.append('image', imageFile);
            console.log('[INFO] Image added to form data');
        }
        
        // Add sensor data if active
        const sensorDataInput = document.getElementById('sensorData');
        if (sensorDataInput && sensorDataInput.value) {
            apiFormData.append('sensor_data', sensorDataInput.value);
            console.log('[INFO] Sensor data added to form data');
        }
        
        console.log('[INFO] Sending API request to /api/unified-query...');
        
        // Prepare headers
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
            console.log('[INFO] Authorization header added');
        }
        
        // Make API request
        const response = await fetch('/api/unified-query', {
            method: 'POST',
            headers: headers,
            body: apiFormData
        });
        
        console.log('[INFO] API response received, status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[ERROR] API error:', response.status, errorText);
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('[INFO] API result received:');
        console.log('  - Success:', result.success);
        console.log('  - Intent detected:', result.intent_detected);
        console.log('  - Language used:', result.language_used);
        console.log('  - APIs called:', result.apis_called);
        console.log('  - Context applied:', result.context_applied);
        console.log('  - Confidence score:', result.confidence_score);
        
        if (result.success) {
            console.log('[SUCCESS] Query processed successfully');
            addMessageToChat('ai', result.response || 'Query processed successfully', {
                confidence: result.confidence_score || 0.8,
                dataSources: result.data_sources || [],
                recommendations: result.recommendations || [],
                followUpSuggestions: result.follow_up_suggestions || []
            });
            
            // Clear form
            console.log('[INFO] Clearing form inputs');
            document.getElementById('unifiedQuery').value = '';
            document.getElementById('imageInput').value = '';
            if (sensorDataInput) sensorDataInput.value = '';
            
        } else {
            console.log('[ERROR] Query processing failed:', result.error);
            addMessageToChat('ai', result.error || 'Sorry, there was an error processing your request', {
                confidence: 0.1,
                isError: true
            });
        }
        
    } catch (error) {
        console.error('[ERROR] Frontend query processing error:', error);
        addMessageToChat('ai', 'Network error: ' + error.message, {
            confidence: 0.1,
            isError: true
        });
    } finally {
        isProcessingQuery = false;
        console.log('[INFO] Query processing unlocked');
        enableInput();
        hideTypingIndicator();
        console.log('=== FRONTEND QUERY PROCESSING END ===\n');
    }
}

function addMessageToChat(sender, content, metadata = {}) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `${sender}-message`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    if (sender === 'user') {
        messageDiv.innerHTML = `
            <div class="message-avatar">👨‍🌾</div>
            <div class="message-content">
                ${content}
                <div class="message-meta">
                    <span>${timestamp}</span>
                </div>
            </div>
        `;
    } else {
        // AI message
        let metaInfo = '';
        if (metadata.confidence) {
            metaInfo += `<span class="confidence-indicator">${(metadata.confidence * 100).toFixed(0)}% confidence</span>`;
        }
        if (metadata.dataSources && metadata.dataSources.length > 0) {
            metaInfo += `<span>Sources: ${metadata.dataSources.join(', ')}</span>`;
        }
        
        let recommendationsHtml = '';
        if (metadata.recommendations && metadata.recommendations.length > 0) {
            recommendationsHtml = `
                <div class="response-actions">
                    ${metadata.recommendations.slice(0, 3).map(rec => 
                        `<button class="response-action" onclick="setQuickQuery('${rec.replace(/'/g, '&apos;')}')">${rec}</button>`
                    ).join('')}
                </div>
            `;
        }
        
        let followUpHtml = '';
        if (metadata.followUpSuggestions && metadata.followUpSuggestions.length > 0) {
            followUpHtml = `
                <div class="follow-up-suggestions">
                    <p><strong>You might also ask:</strong></p>
                    ${metadata.followUpSuggestions.slice(0, 2).map(suggestion => 
                        `<button class="response-action" onclick="setQuickQuery('${suggestion.replace(/'/g, '&apos;')}')">${suggestion}</button>`
                    ).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-avatar">🌾</div>
            <div class="message-content">
                ${content}
                ${recommendationsHtml}
                ${followUpHtml}
                <div class="message-meta">
                    <span>${timestamp}</span>
                    ${metaInfo}
                </div>
            </div>
        `;
    }
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function disableInput() {
    const elements = ['unifiedQuery', 'sendBtn', 'imageBtn', 'voiceBtn', 'sensorBtn'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.disabled = true;
    });
    
    // Update send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; margin: 0;"></div>';
    }
}

function enableInput() {
    const elements = ['unifiedQuery', 'sendBtn', 'imageBtn', 'voiceBtn', 'sensorBtn'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.disabled = false;
    });
    
    // Restore send button
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn) {
        sendBtn.innerHTML = '<span class="send-icon">➤</span>';
    }
}

function showTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'flex';
        document.getElementById('chatHistory').scrollTop = document.getElementById('chatHistory').scrollHeight;
    }
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// Image handling
function handleImageSelection(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            showMessage(`Image selected: ${file.name}`, 'info');
        };
        reader.readAsDataURL(file);
    }
}

// Voice input
function handleVoiceInput() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        
        recognition.lang = 'hi-IN'; // Default to Hindi
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = function() {
            document.getElementById('voiceBtn').classList.add('active');
            showMessage('Listening... Speak now', 'info');
        };
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            document.getElementById('unifiedQuery').value = transcript;
            document.getElementById('voiceData').value = transcript;
            showMessage('Voice input captured', 'success');
        };
        
        recognition.onerror = function(event) {
            showMessage('Voice recognition error: ' + event.error, 'error');
        };
        
        recognition.onend = function() {
            document.getElementById('voiceBtn').classList.remove('active');
        };
        
        recognition.start();
    } else {
        showMessage('Voice recognition not supported in this browser', 'warning');
    }
}

// Sensor data handling
function toggleSensorData() {
    const sensorDisplay = document.getElementById('sensorDataDisplay');
    const sensorBtn = document.getElementById('sensorBtn');
    
    if (sensorDisplay.style.display === 'none' || !sensorDisplay.style.display) {
        sensorDisplay.style.display = 'block';
        sensorBtn.classList.add('active');
        refreshSensorData();
        
        // Set sensor data in hidden input
        const sensorData = getSensorData();
        document.getElementById('sensorData').value = JSON.stringify(sensorData);
    } else {
        sensorDisplay.style.display = 'none';
        sensorBtn.classList.remove('active');
        document.getElementById('sensorData').value = '';
    }
}

function refreshSensorData() {
    const sensorData = getSensorData();
    
    const elements = {
        'soilMoistureValue': sensorData.soil_moisture.toFixed(1) + '%',
        'temperatureValue': sensorData.temperature.toFixed(1) + '°C',
        'phValue': sensorData.ph.toFixed(1),
        'humidityValue': sensorData.humidity.toFixed(1) + '%'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    });
    
    // Update hidden input if sensor panel is active
    const sensorDisplay = document.getElementById('sensorDataDisplay');
    if (sensorDisplay && sensorDisplay.style.display !== 'none') {
        document.getElementById('sensorData').value = JSON.stringify(sensorData);
    }
}

function getSensorData() {
    // Simulate realistic sensor readings
    return {
        soil_moisture: 45 + Math.random() * 30, // 45-75%
        temperature: 22 + Math.random() * 15,   // 22-37°C
        ph: 6.0 + Math.random() * 2,           // 6.0-8.0
        humidity: 40 + Math.random() * 40,      // 40-80%
        timestamp: new Date().toISOString()
    };
}

// Quick actions
function setQuickQuery(query) {
    const textarea = document.getElementById('unifiedQuery');
    if (textarea) {
        textarea.value = query;
        textarea.focus();
    }
}

// Tab switching
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    const targetTab = tabName + 'Tab';
    const targetElement = document.getElementById(targetTab);
    if (targetElement) {
        targetElement.classList.add('active');
    }
    
    // Add active class to clicked button
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Load tab-specific data
    if (tabName === 'community') {
        loadCommunityPosts();
    } else if (tabName === 'schemes') {
        loadGovernmentSchemes();
    } else if (tabName === 'sensors') {
        loadEnhancedSensorData();
    }
}

// Community Functions
async function loadCommunityPosts() {
    try {
        const response = await fetch('/api/community/posts?limit=10');
        const result = await response.json();
        
        const postsContainer = document.getElementById('communityPosts');
        
        if (result.success && result.posts.length > 0) {
            postsContainer.innerHTML = result.posts.map(post => `
                <div class="community-post" onclick="viewPost('${post.post_id}')">
                    <div class="post-header">
                        <span class="post-type-badge ${post.post_type}">${post.post_type.replace('_', ' ')}</span>
                        <div class="post-meta">
                            <span>${post.author_name || 'Anonymous'}</span>
                            <span>${post.location || ''}</span>
                            <span>${new Date(post.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                    <h4 class="post-title">${post.title}</h4>
                    <p class="post-content">${post.content.substring(0, 200)}${post.content.length > 200 ? '...' : ''}</p>
                    <div class="post-stats">
                        <span>👍 ${post.likes}</span>
                        <span>👁️ ${post.views}</span>
                        <span>💬 ${post.comment_count || 0}</span>
                    </div>
                    ${post.crops_mentioned && post.crops_mentioned.length > 0 ? `
                        <div class="post-crops">
                            ${post.crops_mentioned.map(crop => `<span class="crop-tag">${crop}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        } else {
            postsContainer.innerHTML = '<div class="no-posts">No community posts available</div>';
        }
    } catch (error) {
        document.getElementById('communityPosts').innerHTML = '<div class="no-posts">Error loading posts</div>';
        console.error('Error loading community posts:', error);
    }
}

function showCreatePostModal() {
    if (!authToken) {
        showMessage('Please login to create posts', 'warning');
        showAuthModal();
        return;
    }
    const modal = document.getElementById('createPostModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function hideCreatePostModal() {
    const modal = document.getElementById('createPostModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function viewPost(postId) {
    // Placeholder for viewing post details
    showMessage(`Viewing post: ${postId}`, 'info');
}

function filterCommunityPosts() {
    // Placeholder for filtering posts
    loadCommunityPosts();
}

// Government Schemes Functions
async function loadGovernmentSchemes() {
    if (!authToken) {
        const container = document.getElementById('governmentSchemes');
        if (container) {
            container.innerHTML = `
                <div class="no-schemes">
                    <p>Please login to view personalized government schemes and subsidies.</p>
                    <button onclick="showAuthModal()" class="submit-btn">Login Now</button>
                </div>
            `;
        }
        return;
    }
    
    try {
        const response = await fetch('/api/government-schemes', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        const container = document.getElementById('governmentSchemes');
        
        if (result.success && result.schemes.length > 0) {
            container.innerHTML = result.schemes.map(scheme => `
                <div class="scheme-card ${scheme.eligibility_status}">
                    <div class="scheme-header">
                        <h4>${scheme.name}</h4>
                        <span class="eligibility-badge ${scheme.eligibility_status}">${scheme.eligibility_status.replace('_', ' ')}</span>
                    </div>
                    <p class="scheme-description">${scheme.description}</p>
                    <div class="scheme-details">
                        <span><strong>Type:</strong> ${scheme.scheme_type}</span>
                        <span><strong>Agency:</strong> ${scheme.implementing_agency}</span>
                        ${scheme.estimated_benefit ? `<span><strong>Benefit:</strong> ₹${scheme.estimated_benefit.toLocaleString()}</span>` : ''}
                    </div>
                    ${scheme.matching_criteria.length > 0 ? `
                        <div class="matching-criteria">
                            <h5>✅ You Meet These Criteria:</h5>
                            <ul>
                                ${scheme.matching_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    ${scheme.missing_criteria.length > 0 ? `
                        <div class="missing-criteria">
                            <h5>❌ Missing Requirements:</h5>
                            <ul>
                                ${scheme.missing_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                    <div class="scheme-actions">
                        <button class="view-details-btn" onclick="viewSchemeDetails('${scheme.scheme_id}')">View Details</button>
                        ${scheme.website_url ? `<a href="${scheme.website_url}" target="_blank" class="apply-btn">Apply Online</a>` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="no-schemes">No applicable schemes found. Complete your farming profile for better recommendations.</div>';
        }
    } catch (error) {
        document.getElementById('governmentSchemes').innerHTML = '<div class="no-schemes">Error loading schemes</div>';
        console.error('Error loading government schemes:', error);
    }
}

function viewSchemeDetails(schemeId) {
    showMessage(`Viewing details for scheme: ${schemeId}`, 'info');
}

// Enhanced Sensor Functions
async function loadEnhancedSensorData() {
    const container = document.getElementById('enhancedSensorContainer');
    
    try {
        // For demo purposes, show simulated sensor data
        const sensorData = getSensorData();
        
        container.innerHTML = `
            <div class="enhanced-sensor-display">
                <div class="sensor-data-header">
                    <h4>📊 Real-time Sensor Data</h4>
                    <span class="data-quality simulated">Simulated</span>
                </div>
                
                <div class="sensor-readings-grid">
                    <div class="sensor-reading-card">
                        <div class="sensor-type">Soil Moisture</div>
                        <div class="sensor-value">${sensorData.soil_moisture.toFixed(1)}%</div>
                        <div class="sensor-meta">
                            <span>Field 1</span>
                            <span>Just now</span>
                        </div>
                    </div>
                    <div class="sensor-reading-card">
                        <div class="sensor-type">Temperature</div>
                        <div class="sensor-value">${sensorData.temperature.toFixed(1)}°C</div>
                        <div class="sensor-meta">
                            <span>Field 1</span>
                            <span>Just now</span>
                        </div>
                    </div>
                    <div class="sensor-reading-card">
                        <div class="sensor-type">pH Level</div>
                        <div class="sensor-value">${sensorData.ph.toFixed(1)}</div>
                        <div class="sensor-meta">
                            <span>Field 1</span>
                            <span>Just now</span>
                        </div>
                    </div>
                    <div class="sensor-reading-card">
                        <div class="sensor-type">Humidity</div>
                        <div class="sensor-value">${sensorData.humidity.toFixed(1)}%</div>
                        <div class="sensor-meta">
                            <span>Field 1</span>
                            <span>Just now</span>
                        </div>
                    </div>
                </div>
                
                <div class="sensor-insights">
                    <h5>🧠 Intelligent Insights</h5>
                    ${generateSensorInsights(sensorData)}
                </div>
            </div>
        `;
        
    } catch (error) {
        container.innerHTML = '<div class="no-schemes">Error loading sensor data</div>';
        console.error('Error loading sensor data:', error);
    }
}

function generateSensorInsights(sensorData) {
    const insights = [];
    
    if (sensorData.soil_moisture < 30) {
        insights.push(`
            <div class="sensor-insight">
                <h6>🚨 Low Soil Moisture Alert</h6>
                <div class="insight-confidence">Confidence: High</div>
                <p>Soil moisture is critically low at ${sensorData.soil_moisture.toFixed(1)}%. Immediate irrigation recommended.</p>
                <ul class="insight-recommendations">
                    <li>Start irrigation within 2 hours</li>
                    <li>Check irrigation system for blockages</li>
                    <li>Monitor plant stress signs</li>
                </ul>
            </div>
        `);
    } else if (sensorData.soil_moisture > 80) {
        insights.push(`
            <div class="sensor-insight">
                <h6>⚠️ High Soil Moisture</h6>
                <div class="insight-confidence">Confidence: Medium</div>
                <p>Soil moisture is high at ${sensorData.soil_moisture.toFixed(1)}%. Risk of waterlogging.</p>
                <ul class="insight-recommendations">
                    <li>Avoid irrigation for 24-48 hours</li>
                    <li>Ensure proper drainage</li>
                    <li>Monitor for fungal diseases</li>
                </ul>
            </div>
        `);
    }
    
    if (sensorData.temperature > 35) {
        insights.push(`
            <div class="sensor-insight">
                <h6>🌡️ High Temperature Alert</h6>
                <div class="insight-confidence">Confidence: High</div>
                <p>Temperature is high at ${sensorData.temperature.toFixed(1)}°C. Crops may experience heat stress.</p>
                <ul class="insight-recommendations">
                    <li>Increase irrigation frequency</li>
                    <li>Provide shade protection</li>
                    <li>Apply mulching</li>
                </ul>
            </div>
        `);
    }
    
    if (insights.length === 0) {
        insights.push(`
            <div class="sensor-insight">
                <h6>✅ Normal Conditions</h6>
                <div class="insight-confidence">Confidence: Medium</div>
                <p>All sensor readings are within normal ranges. Continue regular monitoring.</p>
            </div>
        `);
    }
    
    return insights.join('');
}

// Notifications
async function loadNotifications() {
    if (!authToken) {
        console.log('No auth token - skipping notifications load');
        return;
    }
    
    try {
        const response = await fetch('/api/notifications', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        if (response.status === 401) {
            console.log('Unauthorized - clearing invalid token');
            logout();
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            updateNotificationsBadge(result.notifications);
            displayNotifications(result.notifications);
        }
    } catch (error) {
        console.error('Error loading notifications:', error);
    }
}

function updateNotificationsBadge(notifications) {
    const unreadCount = notifications.filter(n => !n.read).length;
    const countElement = document.getElementById('notificationCount');
    const badgeElement = document.getElementById('notificationsBadge');
    
    if (countElement) {
        countElement.textContent = unreadCount;
    }
    
    if (badgeElement) {
        if (unreadCount > 0) {
            badgeElement.style.background = 'var(--error-color)';
        } else {
            badgeElement.style.background = 'var(--primary-color)';
        }
    }
}

function displayNotifications(notifications) {
    const container = document.getElementById('notificationsContent');
    
    if (!container) return;
    
    if (notifications.length === 0) {
        container.innerHTML = '<div class="no-notifications">No notifications</div>';
        return;
    }
    
    container.innerHTML = notifications.map(notification => `
        <div class="notification-item ${notification.read ? '' : 'unread'}" onclick="markNotificationRead('${notification.id}')">
            <div class="notification-title">${notification.title}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">${new Date(notification.created_at).toLocaleString()}</div>
        </div>
    `).join('');
}

function toggleNotifications() {
    const panel = document.getElementById('notificationsPanel');
    if (panel) {
        panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
    }
}

async function markNotificationRead(notificationId) {
    if (!authToken) return;
    
    try {
        await fetch(`/api/notifications/${notificationId}/read`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        // Reload notifications
        loadNotifications();
    } catch (error) {
        console.error('Error marking notification as read:', error);
    }
}

// Utility functions
function updateOnlineStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const offlineIndicator = document.getElementById('offlineIndicator');
    
    if (navigator.onLine) {
        if (statusDot) statusDot.classList.remove('offline');
        if (statusText) statusText.textContent = 'Online';
        if (offlineIndicator) offlineIndicator.classList.remove('show');
    } else {
        if (statusDot) statusDot.classList.add('offline');
        if (statusText) statusText.textContent = 'Offline';
        if (offlineIndicator) offlineIndicator.classList.add('show');
    }
}

function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.textContent = message;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.left = '50%';
    messageDiv.style.transform = 'translateX(-50%)';
    messageDiv.style.zIndex = '9999';
    messageDiv.style.padding = '15px 25px';
    messageDiv.style.borderRadius = '25px';
    messageDiv.style.fontWeight = '600';
    messageDiv.style.boxShadow = '0 4px 15px rgba(0,0,0,0.2)';
    
    // Set colors based on type
    if (type === 'success') {
        messageDiv.style.background = '#4CAF50';
        messageDiv.style.color = 'white';
    } else if (type === 'error') {
        messageDiv.style.background = '#f44336';
        messageDiv.style.color = 'white';
    } else if (type === 'warning') {
        messageDiv.style.background = '#FF9800';
        messageDiv.style.color = 'white';
    } else {
        messageDiv.style.background = '#2196F3';
        messageDiv.style.color = 'white';
    }
    
    document.body.appendChild(messageDiv);
    
    // Remove after 3 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 3000);
}

// Initialize chat history display
function updateChatDisplay() {
    const chatHistoryElement = document.getElementById('chatHistory');
    
    if (!chatHistoryElement) return;
    
    // Keep welcome message and add any stored chat history
    const welcomeMessage = chatHistoryElement.querySelector('.welcome-message');
    chatHistoryElement.innerHTML = '';
    
    if (welcomeMessage) {
        chatHistoryElement.appendChild(welcomeMessage);
    }
    
    // Add stored chat messages
    chatHistory.forEach(message => {
        addMessageToChat(message.sender, message.content, message.metadata);
    });
}

// Test function for debugging
function testQuery() {
    console.log('=== TEST QUERY START ===');
    const testQuestion = "What is the market price of rice in Karnataka?";
    
    const queryInput = document.getElementById('unifiedQuery');
    if (queryInput) {
        queryInput.value = testQuestion;
        console.log('Test question set:', testQuestion);
        
        // Trigger the form submission
        const form = document.getElementById('unifiedForm');
        if (form) {
            const syntheticEvent = {
                preventDefault: () => {},
                target: form,
                type: 'submit'
            };
            
            handleUnifiedQuery(syntheticEvent);
        }
    }
    console.log('=== TEST QUERY END ===');
}

// Make functions globally available for HTML onclick handlers
window.switchAuthTab = switchAuthTab;
window.handleLogin = handleLogin;
window.handleRegister = handleRegister;
window.sendOTP = sendOTP;
window.verifyOTP = verifyOTP;
window.logout = logout;
window.saveFarmingContext = saveFarmingContext;
window.showCreatePostModal = showCreatePostModal;
window.hideCreatePostModal = hideCreatePostModal;
window.showFarmingContextModal = showFarmingContextModal;
window.hideFarmingContextModal = hideFarmingContextModal;
window.toggleNotifications = toggleNotifications;
window.switchTab = switchTab;
window.setQuickQuery = setQuickQuery;
window.testQuery = testQuery;
window.loadGovernmentSchemes = loadGovernmentSchemes;
window.loadEnhancedSensorData = loadEnhancedSensorData;
window.refreshSensorData = refreshSensorData;
window.toggleSensorData = toggleSensorData;
window.handleVoiceInput = handleVoiceInput;
window.viewPost = viewPost;
window.filterCommunityPosts = filterCommunityPosts;
window.viewSchemeDetails = viewSchemeDetails;
window.markNotificationRead = markNotificationRead;
window.updateLanguagePreference = updateLanguagePreference;