// KrishiMitra - Unified AI Chat Application
let currentUser = null;
let authToken = null;
let isProcessingQuery = false;
let chatHistory = [];
let voiceRecognition = null;
let isRecording = false;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    checkAuthStatus();
    setupEventListeners();
    updateOnlineStatus();
    
    // Monitor online/offline status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
}

function setupEventListeners() {
    // Unified form submission
    document.getElementById('unifiedForm').addEventListener('submit', handleUnifiedQuery);
    
    // Image upload button
    document.getElementById('imageBtn').addEventListener('click', () => {
        document.getElementById('imageInput').click();
    });
    
    // Image file selection
    document.getElementById('imageInput').addEventListener('change', handleImageSelection);
    
    // Voice button
    document.getElementById('voiceBtn').addEventListener('click', handleVoiceInput);
    
    // Sensor button
    document.getElementById('sensorBtn').addEventListener('click', toggleSensorData);
    
    // Enter key handling for textarea
    document.getElementById('unifiedQuery').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!isProcessingQuery) {
                handleUnifiedQuery(e);
            }
        }
    });
    
    // Initialize voice recognition
    initializeVoiceRecognition();
}

// Enhanced Voice Recognition
function initializeVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        voiceRecognition = new SpeechRecognition();
        
        voiceRecognition.continuous = false;
        voiceRecognition.interimResults = false;
        voiceRecognition.maxAlternatives = 3;
        
        voiceRecognition.onstart = function() {
            isRecording = true;
            document.getElementById('voiceBtn').classList.add('active');
            document.getElementById('voiceBtn').innerHTML = '🔴';
            showMessage('Listening... Speak now', 'info');
        };
        
        voiceRecognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            const confidence = event.results[0][0].confidence;
            
            document.getElementById('unifiedQuery').value = transcript;
            document.getElementById('voiceData').value = JSON.stringify({
                transcript: transcript,
                confidence: confidence,
                timestamp: new Date().toISOString()
            });
            
            showMessage(`Voice captured: "${transcript}" (${Math.round(confidence * 100)}% confidence)`, 'success');
        };
        
        voiceRecognition.onerror = function(event) {
            showMessage('Voice recognition error: ' + event.error, 'error');
            resetVoiceButton();
        };
        
        voiceRecognition.onend = function() {
            resetVoiceButton();
        };
    }
}

function resetVoiceButton() {
    isRecording = false;
    document.getElementById('voiceBtn').classList.remove('active');
    document.getElementById('voiceBtn').innerHTML = '🎤';
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
    document.getElementById('authModal').style.display = 'flex';
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
    event.preventDefault();
    
    if (isProcessingQuery) {
        showMessage('Please wait for your previous query to complete', 'warning');
        return;
    }
    
    const formData = new FormData(event.target);
    const textQuery = formData.get('text')?.trim();
    const imageFile = formData.get('image');
    
    if (!textQuery && !imageFile) {
        showMessage('Please enter a question or upload an image', 'warning');
        return;
    }
    
    // Block further queries
    isProcessingQuery = true;
    disableInput();
    showTypingIndicator();
    
    // Add user message to chat
    if (textQuery) {
        addMessageToChat('user', textQuery);
    }
    if (imageFile) {
        addMessageToChat('user', `📷 Uploaded image: ${imageFile.name}`);
    }
    
    try {
        const headers = {};
        if (authToken) {
            headers['Authorization'] = `Bearer ${authToken}`;
        }
        
        const response = await fetch('/api/unified-query', {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Add AI response to chat
            addMessageToChat('ai', result.response, {
                confidence: result.confidence_score,
                dataSources: result.data_sources,
                recommendations: result.recommendations,
                dataAvailability: result.data_availability,
                followUpSuggestions: result.follow_up_suggestions
            });
            
            // Clear form
            document.getElementById('unifiedForm').reset();
            document.getElementById('sensorData').value = '';
            document.getElementById('voiceData').value = '';
            
        } else {
            addMessageToChat('ai', result.error || 'I apologize, but I encountered an error processing your request.', {
                confidence: 0.1,
                isError: true
            });
        }
        
    } catch (error) {
        addMessageToChat('ai', 'I apologize, but I encountered a network error. Please check your connection and try again.', {
            confidence: 0.1,
            isError: true
        });
        console.error('Query processing error:', error);
    } finally {
        // Re-enable input
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
    if (!voiceRecognition) {
        showMessage('Voice recognition not supported in this browser', 'warning');
        return;
    }
    
    if (isRecording) {
        voiceRecognition.stop();
        return;
    }
    
    // Set language based on user preference
    const languageMap = {
        'hindi': 'hi-IN',
        'english': 'en-IN',
        'bengali': 'bn-IN',
        'telugu': 'te-IN',
        'marathi': 'mr-IN',
        'tamil': 'ta-IN',
        'gujarati': 'gu-IN'
    };
    
    const currentLanguage = document.getElementById('languageInput').value || 'hindi';
    voiceRecognition.lang = languageMap[currentLanguage] || 'hi-IN';
    
    try {
        voiceRecognition.start();
    } catch (error) {
        showMessage('Voice recognition error: ' + error.message, 'error');
        resetVoiceButton();
    }
}

// Advanced Reasoning Functions
async function processAdvancedReasoning(query, reasoningType = 'trade_off_analysis') {
    if (!authToken) {
        showMessage('Please login to use advanced reasoning features', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/advanced-reasoning', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                reasoning_type: reasoningType
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayAdvancedReasoningResult(result);
        } else {
            showMessage('Advanced reasoning failed: ' + result.error, 'error');
        }
        
    } catch (error) {
        showMessage('Advanced reasoning error: ' + error.message, 'error');
    }
}

function displayAdvancedReasoningResult(result) {
    const reasoningDiv = document.createElement('div');
    reasoningDiv.className = 'advanced-reasoning-result';
    reasoningDiv.innerHTML = `
        <div class="reasoning-header">
            <h4>🧠 Advanced Analysis: ${result.reasoning_type.replace('_', ' ').toUpperCase()}</h4>
            <span class="confidence-badge">${Math.round(result.confidence_score * 100)}% Confidence</span>
        </div>
        
        <div class="primary-recommendation">
            <h5>Primary Recommendation:</h5>
            <p>${result.primary_recommendation}</p>
        </div>
        
        ${result.reasoning_steps.length > 0 ? `
            <div class="reasoning-steps">
                <h5>Analysis Steps:</h5>
                ${result.reasoning_steps.map(step => `
                    <div class="reasoning-step">
                        <strong>Step ${step.step_number}:</strong> ${step.description}
                        <p>${step.analysis}</p>
                    </div>
                `).join('')}
            </div>
        ` : ''}
        
        ${result.risk_factors.length > 0 ? `
            <div class="risk-factors">
                <h5>Risk Factors:</h5>
                <ul>
                    ${result.risk_factors.map(risk => `<li>${risk}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
        
        ${result.alternative_strategies.length > 0 ? `
            <div class="alternatives">
                <h5>Alternative Strategies:</h5>
                <ul>
                    ${result.alternative_strategies.map(alt => `<li>${alt}</li>`).join('')}
                </ul>
            </div>
        ` : ''}
    `;
    
    // Add to chat history
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'ai-message';
    messageDiv.innerHTML = `
        <div class="message-avatar">🧠</div>
        <div class="message-content">
            ${reasoningDiv.outerHTML}
            <div class="message-meta">
                <span>${new Date().toLocaleTimeString()}</span>
                <span>Advanced Reasoning</span>
            </div>
        </div>
    `;
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Government Schemes Functions
async function loadGovernmentSchemes() {
    if (!authToken) {
        showMessage('Please login to view government schemes', 'warning');
        return;
    }
    
    try {
        const response = await fetch('/api/government-schemes', {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayGovernmentSchemes(result.schemes);
        } else {
            showMessage('Failed to load schemes: ' + result.error, 'error');
        }
        
    } catch (error) {
        showMessage('Error loading schemes: ' + error.message, 'error');
    }
}

function displayGovernmentSchemes(schemes) {
    const schemesContainer = document.getElementById('governmentSchemes');
    
    if (!schemes || schemes.length === 0) {
        schemesContainer.innerHTML = '<div class="no-schemes">No applicable schemes found. Complete your profile for personalized recommendations.</div>';
        return;
    }
    
    schemesContainer.innerHTML = schemes.map(scheme => `
        <div class="scheme-card ${scheme.eligibility_status}">
            <div class="scheme-header">
                <h4>${scheme.name}</h4>
                <span class="eligibility-badge ${scheme.eligibility_status}">
                    ${scheme.eligibility_status.replace('_', ' ').toUpperCase()}
                </span>
            </div>
            
            <p class="scheme-description">${scheme.description}</p>
            
            <div class="scheme-details">
                <div class="scheme-type">
                    <strong>Type:</strong> ${scheme.scheme_type.replace('_', ' ').toUpperCase()}
                </div>
                <div class="implementing-agency">
                    <strong>Agency:</strong> ${scheme.implementing_agency}
                </div>
                ${scheme.estimated_benefit ? `
                    <div class="estimated-benefit">
                        <strong>Estimated Benefit:</strong> ₹${scheme.estimated_benefit.toLocaleString()}
                    </div>
                ` : ''}
            </div>
            
            <div class="scheme-benefits">
                <h5>Benefits:</h5>
                <ul>
                    ${scheme.benefits.slice(0, 3).map(benefit => `<li>${benefit}</li>`).join('')}
                </ul>
            </div>
            
            ${scheme.matching_criteria.length > 0 ? `
                <div class="matching-criteria">
                    <h5>✅ You Meet:</h5>
                    <ul>
                        ${scheme.matching_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${scheme.missing_criteria.length > 0 ? `
                <div class="missing-criteria">
                    <h5>❌ Missing:</h5>
                    <ul>
                        ${scheme.missing_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            <div class="scheme-actions">
                <button onclick="viewSchemeDetails('${scheme.scheme_id}')" class="view-details-btn">
                    View Details
                </button>
                ${scheme.website_url ? `
                    <a href="${scheme.website_url}" target="_blank" class="apply-btn">
                        Apply Online
                    </a>
                ` : ''}
            </div>
        </div>
    `).join('');
}

function viewSchemeDetails(schemeId) {
    // This would open a detailed view of the scheme
    showMessage('Scheme details feature coming soon!', 'info');
}

// Enhanced Sensor Data Functions
async function loadEnhancedSensorData() {
    if (!authToken) {
        showMessage('Please login to view sensor data', 'warning');
        return;
    }
    
    try {
        // Use user's farm ID (in production, this would be from user profile)
        const farmId = currentUser?.id || 'demo_farm';
        
        const response = await fetch(`/api/sensors/${farmId}`, {
            headers: {
                'Authorization': `Bearer ${authToken}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayEnhancedSensorData(result);
        } else {
            showMessage('Failed to load sensor data: ' + result.error, 'error');
        }
        
    } catch (error) {
        showMessage('Error loading sensor data: ' + error.message, 'error');
    }
}

function displayEnhancedSensorData(sensorData) {
    const container = document.getElementById('enhancedSensorData');
    
    if (!container) {
        console.error('Enhanced sensor data container not found');
        return;
    }
    
    const readings = sensorData.sensor_readings;
    const insights = sensorData.insights || [];
    const alerts = sensorData.alerts || [];
    
    container.innerHTML = `
        <div class="sensor-data-header">
            <h4>📊 Real-time Sensor Data</h4>
            <div class="data-quality ${sensorData.data_quality.overall_quality}">
                Quality: ${sensorData.data_quality.overall_quality.toUpperCase()}
            </div>
        </div>
        
        ${alerts.length > 0 ? `
            <div class="sensor-alerts">
                <h5>🚨 Alerts</h5>
                ${alerts.map(alert => `
                    <div class="sensor-alert ${alert.alert_level}">
                        <strong>${alert.message}</strong>
                        <ul>
                            ${alert.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                `).join('')}
            </div>
        ` : ''}
        
        <div class="sensor-readings-grid">
            ${Object.entries(readings).map(([sensorType, data]) => `
                <div class="sensor-reading-card">
                    <div class="sensor-type">${sensorType.replace('_', ' ').toUpperCase()}</div>
                    <div class="sensor-value">${data.current_value} ${data.unit}</div>
                    <div class="sensor-meta">
                        <span>Quality: ${Math.round(data.quality_score * 100)}%</span>
                        <span>${new Date(data.timestamp).toLocaleTimeString()}</span>
                    </div>
                </div>
            `).join('')}
        </div>
        
        ${insights.length > 0 ? `
            <div class="sensor-insights">
                <h5>💡 Insights</h5>
                ${insights.map(insight => `
                    <div class="sensor-insight">
                        <h6>${insight.insight_type.replace('_', ' ').toUpperCase()}</h6>
                        <p>${insight.description}</p>
                        <div class="insight-confidence">
                            Confidence: ${Math.round(insight.confidence * 100)}%
                        </div>
                        ${insight.recommendations.length > 0 ? `
                            <ul class="insight-recommendations">
                                ${insight.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                `).join('')}
            </div>
        ` : ''}
    `;
}

// Enhanced Quick Actions
function addAdvancedQuickActions() {
    const quickActionsContainer = document.querySelector('.quick-actions');
    
    // Add advanced reasoning quick actions
    const advancedActions = [
        {
            text: '🧠 Should I sell now or wait?',
            action: () => processAdvancedReasoning('Should I sell my crops now or wait for better prices?', 'trade_off_analysis')
        },
        {
            text: '📋 Create seasonal plan',
            action: () => processAdvancedReasoning('Create a comprehensive seasonal farming plan for my crops', 'seasonal_planning')
        },
        {
            text: '🏛️ Show government schemes',
            action: () => loadGovernmentSchemes()
        },
        {
            text: '📊 Enhanced sensor data',
            action: () => loadEnhancedSensorData()
        }
    ];
    
    advancedActions.forEach(action => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'quick-action advanced-action';
        button.textContent = action.text;
        button.onclick = action.action;
        quickActionsContainer.appendChild(button);
    });
}

// Enhanced Tab Switching
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

// Initialize enhanced features
function initializeEnhancedFeatures() {
    // Add advanced quick actions
    addAdvancedQuickActions();
    
    // Load enhanced sensor data periodically
    if (authToken) {
        setInterval(loadEnhancedSensorData, 60000); // Every minute
    }
    
    // Initialize voice recognition
    initializeVoiceRecognition();
}

// Update the main initialization function
function initializeApp() {
    // Check authentication
    checkAuthStatus();
    
    // Load user context if authenticated
    loadUserContext();
    
    // Load notifications
    loadNotifications();
    
    // Load community posts
    loadCommunityPosts();
    
    // Setup real-time features
    setupRealtimeFeatures();
    
    // Initialize enhanced features
    initializeEnhancedFeatures();
    
    // Auto-refresh notifications every 5 minutes
    setInterval(loadNotifications, 5 * 60 * 1000);
    
    // Refresh sensor data display
    refreshSensorData();
    setInterval(refreshSensorData, 30000); // Every 30 seconds
}
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