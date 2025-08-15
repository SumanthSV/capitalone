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
    setupEventListeners(); // Set up event listeners first
    updateOnlineStatus();
    checkAuthStatus(); // Check auth after listeners are set up
    
    // Monitor online/offline status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    
    console.log('initializeApp completed');
}

function setupEventListeners() {
    console.log('Setting up event listeners - SIMPLE VERSION');
    
    // Wait a bit for DOM to be ready
    setTimeout(() => {
        // Set up submit button click
        const submitBtn = document.getElementById('sendBtn');
        if (submitBtn) {
            console.log('Found submit button, adding click handler');
            
            submitBtn.onclick = function(e) {
                console.log('SUBMIT BUTTON CLICKED!');
                e.preventDefault();
                e.stopPropagation();
                
                // Get the text
                const textQuery = document.getElementById('unifiedQuery').value?.trim();
                console.log('Text query:', textQuery);
                
                if (!textQuery) {
                    alert('Please enter a question!');
                    return false;
                }
                
                // Call the submission handler directly
                submitQuery(textQuery);
                return false;
            };
            
            console.log('Submit button handler attached successfully');
        } else {
            console.error('Submit button not found!');
        }
        
        // Set up Enter key on textarea
        const textarea = document.getElementById('unifiedQuery');
        if (textarea) {
            textarea.onkeydown = function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    console.log('Enter key pressed');
                    e.preventDefault();
                    
                    const textQuery = textarea.value?.trim();
                    if (textQuery && !isProcessingQuery) {
                        submitQuery(textQuery);
                    }
                }
            };
        }
        
        // Other button handlers
        const imageBtn = document.getElementById('imageBtn');
        if (imageBtn) {
            imageBtn.onclick = () => {
                document.getElementById('imageInput').click();
            };
        }
        
        const voiceBtn = document.getElementById('voiceBtn');
        if (voiceBtn) {
            voiceBtn.onclick = handleVoiceInput;
        }
        
    }, 1000); // Give more time for DOM to be ready
}

// Simple, direct submission function
async function submitQuery(textQuery) {
    console.log('submitQuery called with:', textQuery);
    
    if (isProcessingQuery) {
        alert('Please wait for the previous query to complete');
        return;
    }
    
    try {
        isProcessingQuery = true;
        disableInput();
        showTypingIndicator();
        
        // Add user message to chat
        addMessageToChat('user', textQuery);
        
        // Create form data
        const formData = new FormData();
        formData.append('text', textQuery);
        formData.append('language', 'hindi');
        
        // Add image if selected
        const imageInput = document.getElementById('imageInput');
        if (imageInput.files[0]) {
            formData.append('image', imageInput.files[0]);
        }
        
        console.log('Sending API request to /api/unified-query');
        
        // Make API request
        const response = await fetch('/api/unified-query', {
            method: 'POST',
            body: formData
        });
        
        console.log('API response status:', response.status);
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('API result:', result);
        
        if (result.success) {
            addMessageToChat('ai', result.response || 'Query processed successfully', {
                confidence: result.confidence_score || 0.8
            });
            
            // Clear the textarea
            document.getElementById('unifiedQuery').value = '';
            
        } else {
            addMessageToChat('ai', result.error || 'Sorry, there was an error processing your request', {
                confidence: 0.1,
                isError: true
            });
        }
        
    } catch (error) {
        console.error('Error submitting query:', error);
        addMessageToChat('ai', 'Network error: ' + error.message, {
            confidence: 0.1,
            isError: true
        });
    } finally {
        isProcessingQuery = false;
        enableInput();
        hideTypingIndicator();
    }
}

// Authentication Functions
function checkAuthStatus() {
    authToken = localStorage.getItem('authToken');
    currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
    
    if (authToken && currentUser) {
        updateUserInterface();
        loadUserContext();
    } else {
        showAuthModal();
    }
}

function updateUserInterface() {
    document.getElementById('userInfo').textContent = currentUser.name;
    document.querySelector('.logout-btn').style.display = 'inline-block';
    hideAuthModal();
}

function showAuthModal() {
    // Make the modal non-blocking - allow users to interact with the app even without auth
    const authModal = document.getElementById('authModal');
    if (authModal) {
        authModal.style.display = 'flex';
        // Add a close button or allow clicking outside to dismiss
        authModal.addEventListener('click', function(e) {
            if (e.target === authModal) {
                hideAuthModal();
            }
        });
    }
}

function hideAuthModal() {
    document.getElementById('authModal').style.display = 'none';
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
            
            // Load user context after login
            setTimeout(loadUserContext, 500);
        } else {
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
    
    document.getElementById('userInfo').textContent = 'Guest User';
    document.querySelector('.logout-btn').style.display = 'none';
    
    // Clear chat history
    chatHistory = [];
    updateChatDisplay();
    
    showMessage('Logged out successfully', 'success');
    showAuthModal();
}

// Farming Context Functions
async function loadUserContext() {
    if (!authToken) return;
    
    try {
        const response = await fetch('/api/context/farming', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
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
    document.getElementById('farmingContextModal').style.display = 'flex';
}

function hideFarmingContextModal() {
    document.getElementById('farmingContextModal').style.display = 'none';
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
    console.log('handleUnifiedQuery called', event);
    
    try {
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }
        
        if (isProcessingQuery) {
            showMessage('Please wait for your previous query to complete', 'warning');
            return;
        }
        
        console.log('Processing query started...');
        
        // Get the form - handle both form submission and direct calls
        let form;
        if (event && event.target && event.target.tagName === 'FORM') {
            form = event.target;
        } else {
            form = document.getElementById('unifiedForm');
        }
        
        if (!form) {
            console.error('Form not found!');
            showMessage('Error: Form not found', 'error');
            return;
        }
        
        console.log('Form found, creating FormData...');
        const formData = new FormData(form);
        const textQuery = formData.get('text')?.trim() || document.getElementById('unifiedQuery').value?.trim();
        const imageFile = formData.get('image') || document.getElementById('imageInput').files[0];
        
        console.log('Form data extracted:', { 
            textQuery: textQuery || 'empty', 
            imageFile: imageFile ? imageFile.name : 'none',
            hasVoiceData: !!formData.get('voice_data'),
            hasSensorData: !!formData.get('sensor_data')
        });
        
        // Validate input
        if (!textQuery && !imageFile) {
            showMessage('Please enter a question or upload an image', 'warning');
            return;
        }
        
        // Block further queries
        isProcessingQuery = true;
        disableInput();
        showTypingIndicator();
        
        console.log('Adding user message to chat...');
        
        // Add user message to chat
        if (textQuery) {
            addMessageToChat('user', textQuery);
        }
        if (imageFile) {
            addMessageToChat('user', `📷 Uploaded image: ${imageFile.name}`);
        }
        
        console.log('User message added, preparing API request...');
        
        // Ensure FormData has the text value
        if (textQuery && !formData.has('text')) {
            formData.set('text', textQuery);
        }
        
        // Ensure FormData has the image file if selected
        if (imageFile && !formData.has('image')) {
            formData.set('image', imageFile);
        }
    
    try {
        console.log('Preparing to send API request...');
        
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
            console.log('Using authentication token');
        } else {
            console.log('No authentication token - using anonymous access');
        }
        
        console.log('Sending request to /api/unified-query with form data:', formData);
        
        console.log('Sending request to API...');
        const response = await fetch('/api/unified-query', {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        console.log('API response received - Status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        if (!response.ok) {
            console.error('HTTP error:', response.status, response.statusText);
            const errorText = await response.text();
            console.error('Error response body:', errorText);
            
            addMessageToChat('ai', `Server error: ${response.status} ${response.statusText}. Please try again.`, {
                confidence: 0.1,
                isError: true
            });
            return;
        }
        
        const result = await response.json();
        console.log('API response result:', result);
        
        if (result.success) {
            console.log('Query processed successfully');
            console.log('AI response:', result.response);
            
            // Add AI response to chat
            addMessageToChat('ai', result.response || 'I received your query and processed it successfully.', {
                confidence: result.confidence_score || 0.8,
                dataSources: result.data_sources || [],
                recommendations: result.recommendations || [],
                dataAvailability: result.data_availability || {},
                followUpSuggestions: result.follow_up_suggestions || []
            });
            
            console.log('AI response added to chat');
            
            // Clear form
            const form = document.getElementById('unifiedForm');
            if (form) {
                form.reset();
            }
            
            // Clear additional data
            const sensorDataInput = document.getElementById('sensorData');
            const voiceDataInput = document.getElementById('voiceData');
            
            if (sensorDataInput) sensorDataInput.value = '';
            if (voiceDataInput) voiceDataInput.value = '';
            
            console.log('Form cleared');
            
        } else {
            console.error('API returned error:', result.error);
            const errorMessage = result.error || 'I apologize, but I encountered an error processing your request.';
            addMessageToChat('ai', errorMessage, {
                confidence: 0.1,
                isError: true
            });
        }
        
    } catch (error) {
        console.error('Network/fetch error:', error);
        console.error('Error details:', error.stack);
        const errorMessage = `I apologize, but I encountered a network error: ${error.message}. Please check your connection and try again.`;
        addMessageToChat('ai', errorMessage, {
            confidence: 0.1,
            isError: true
        });
    } finally {
        // Re-enable input
        console.log('Re-enabling input controls...');
        isProcessingQuery = false;
        enableInput();
        hideTypingIndicator();
        console.log('Query processing completed');
    }
    
    } catch (outerError) {
        console.error('Outer error in handleUnifiedQuery:', outerError);
        showMessage('Unexpected error: ' + outerError.message, 'error');
        
        // Ensure we re-enable input even in case of outer errors
        isProcessingQuery = false;
        enableInput();
        hideTypingIndicator();
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
                        `<button class="response-action" onclick="setQuickQuery('${rec}')">${rec}</button>`
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
                        `<button class="response-action" onclick="setQuickQuery('${suggestion}')">${suggestion}</button>`
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
    document.getElementById('unifiedQuery').disabled = true;
    document.getElementById('sendBtn').disabled = true;
    document.getElementById('imageBtn').disabled = true;
    document.getElementById('voiceBtn').disabled = true;
    document.getElementById('sensorBtn').disabled = true;
    
    // Update send button
    document.getElementById('sendBtn').innerHTML = '<div class="spinner" style="width: 20px; height: 20px; margin: 0;"></div>';
}

function enableInput() {
    document.getElementById('unifiedQuery').disabled = false;
    document.getElementById('sendBtn').disabled = false;
    document.getElementById('imageBtn').disabled = false;
    document.getElementById('voiceBtn').disabled = false;
    document.getElementById('sensorBtn').disabled = false;
    
    // Restore send button
    document.getElementById('sendBtn').innerHTML = '<span class="send-icon">➤</span>';
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'flex';
    document.getElementById('chatHistory').scrollTop = document.getElementById('chatHistory').scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
}

// Image handling
function handleImageSelection(event) {
    const file = event.target.files[0];
    if (file) {
        // Show image preview
        const reader = new FileReader();
        reader.onload = function(e) {
            showMessage(`Image selected: ${file.name}`, 'info');
        };
        reader.readAsDataURL(file);
    }
}

// Voice input (placeholder)
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
    
    if (sensorDisplay.style.display === 'none') {
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
    document.getElementById('soilMoistureValue').textContent = sensorData.soil_moisture.toFixed(1) + '%';
    document.getElementById('temperatureValue').textContent = sensorData.temperature.toFixed(1) + '°C';
    document.getElementById('phValue').textContent = sensorData.ph.toFixed(1);
    document.getElementById('humidityValue').textContent = sensorData.humidity.toFixed(1) + '%';
    
    // Update hidden input if sensor panel is active
    if (document.getElementById('sensorDataDisplay').style.display !== 'none') {
        document.getElementById('sensorData').value = JSON.stringify(sensorData);
    }
}

function getSensorData() {
    // Simulate realistic sensor readings (in production, this would call real IoT APIs)
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
    document.getElementById('unifiedQuery').value = query;
    document.getElementById('unifiedQuery').focus();
}

// Test function for debugging
function testQuery() {
    console.log('=== TEST QUERY DEBUG START ===');
    const testQuestion = "What is the mandi price of rice in Karnataka";
    
    // Set the test question in the textarea
    const queryInput = document.getElementById('unifiedQuery');
    if (queryInput) {
        queryInput.value = testQuestion;
        console.log('Test question set in textarea:', testQuestion);
    } else {
        console.error('Query input textarea not found!');
        return;
    }
    
    // Get the form
    const form = document.getElementById('unifiedForm');
    if (!form) {
        console.error('Form not found!');
        showMessage('Error: Form not found', 'error');
        return;
    }
    
    console.log('Form found:', form);
    console.log('Form action:', form.action);
    console.log('Form method:', form.method);
    console.log('Form enctype:', form.enctype);
    
    // Check if handleUnifiedQuery function exists
    if (typeof handleUnifiedQuery !== 'function') {
        console.error('handleUnifiedQuery function not found!');
        return;
    }
    
    console.log('Calling handleUnifiedQuery directly with synthetic event...');
    
    // Create a synthetic event that mimics form submission
    const syntheticEvent = {
        preventDefault: function() { 
            console.log('preventDefault called on synthetic event'); 
        },
        stopPropagation: function() { 
            console.log('stopPropagation called on synthetic event'); 
        },
        target: form,
        type: 'submit',
        isTrusted: false
    };
    
    try {
        console.log('About to call handleUnifiedQuery...');
        handleUnifiedQuery(syntheticEvent);
        console.log('handleUnifiedQuery called successfully');
    } catch (error) {
        console.error('Error calling handleUnifiedQuery:', error);
        showMessage('Error in handleUnifiedQuery: ' + error.message, 'error');
    }
    
    console.log('=== TEST QUERY DEBUG END ===');
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
        return;
    }
    document.getElementById('createPostModal').style.display = 'flex';
}

function hideCreatePostModal() {
    document.getElementById('createPostModal').style.display = 'none';
}

// Notifications
async function loadNotifications() {
    if (!authToken) return;
    
    try {
        const response = await fetch('/api/notifications', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
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
    document.getElementById('notificationCount').textContent = unreadCount;
    
    if (unreadCount > 0) {
        document.getElementById('notificationsBadge').style.background = 'var(--error-color)';
    } else {
        document.getElementById('notificationsBadge').style.background = 'var(--primary-color)';
    }
}

function displayNotifications(notifications) {
    const container = document.getElementById('notificationsContent');
    
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
    panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
}

// Utility functions
function updateOnlineStatus() {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const offlineIndicator = document.getElementById('offlineIndicator');
    
    if (navigator.onLine) {
        statusDot.classList.remove('offline');
        statusText.textContent = 'Online';
        offlineIndicator.classList.remove('show');
    } else {
        statusDot.classList.add('offline');
        statusText.textContent = 'Offline';
        offlineIndicator.classList.add('show');
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