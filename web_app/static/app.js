// KrishiMitra PWA - Enhanced JavaScript Application
let authToken = localStorage.getItem('authToken');
let currentUser = JSON.parse(localStorage.getItem('currentUser') || 'null');
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let chatHistory = [];

// Initialize application
function initializeApp() {
    console.log('Initializing KrishiMitra application...');
    
    // Check authentication
    checkAuthStatus();
    
    // Only load authenticated data if user is logged in
    if (authToken && currentUser) {
        setTimeout(() => {
            loadUserContext();
            loadNotifications();
        }, 1000);
    }
    
    // Load community posts (public data)
    loadCommunityPosts();
    
    // Setup real-time features
    setupRealtimeFeatures();
    
    // Auto-refresh notifications every 5 minutes (only if authenticated)
    setInterval(() => {
        if (authToken) {
            loadNotifications();
        }
    }, 5 * 60 * 1000);
    
    // Refresh sensor data display
    refreshSensorData();
    setInterval(refreshSensorData, 30000); // Every 30 seconds
    
    // Setup event listeners
    setupEventListeners();
}

function setupEventListeners() {
    // Image upload handling
    const imageInput = document.getElementById('imageInput');
    const imageBtn = document.getElementById('imageBtn');
    
    if (imageBtn && imageInput) {
        imageBtn.addEventListener('click', () => {
            imageInput.click();
        });
        
        imageInput.addEventListener('change', (e) => {
            if (e.target.files && e.target.files[0]) {
                imageBtn.classList.add('active');
                imageBtn.innerHTML = '📷✓';
            }
        });
    }
    
    // Voice recording
    const voiceBtn = document.getElementById('voiceBtn');
    if (voiceBtn) {
        voiceBtn.addEventListener('click', toggleVoiceRecording);
    }
    
    // Sensor data toggle
    const sensorBtn = document.getElementById('sensorBtn');
    if (sensorBtn) {
        sensorBtn.addEventListener('click', toggleSensorData);
    }
    
    // Enter key submission
    const queryInput = document.getElementById('unifiedQuery');
    if (queryInput) {
        queryInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                document.getElementById('sendBtn').click();
            }
        });
    }
}

function checkAuthStatus() {
    const userInfo = document.getElementById('userInfo');
    const logoutBtn = document.querySelector('.logout-btn');
    
    if (authToken && currentUser) {
        userInfo.textContent = `👋 ${currentUser.name}`;
        if (logoutBtn) logoutBtn.style.display = 'inline-block';
        
        // Check if user needs to complete profile
        checkUserProfile();
    } else {
        userInfo.textContent = 'Guest User';
        if (logoutBtn) logoutBtn.style.display = 'none';
        
        // Show auth modal for new users
        setTimeout(() => {
            document.getElementById('authModal').style.display = 'flex';
        }, 2000);
    }
}

function checkUserProfile() {
    if (!authToken) return;
    
    fetch('/api/profile', {
        headers: {
            'Authorization': `Bearer ${authToken}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            // User needs to complete profile
            setTimeout(() => {
                document.getElementById('farmingContextModal').style.display = 'flex';
            }, 1000);
        }
    })
    .catch(error => {
        console.log('Profile check failed:', error);
    });
}

// Authentication functions
function switchAuthTab(tabName) {
    // Hide all auth tabs
    document.querySelectorAll('.auth-tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.auth-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName + 'AuthTab').classList.add('active');
    
    // Add active class to clicked button
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
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(loginData)
        });
        
        const result = await response.json();
        
        if (result.access_token) {
            authToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            document.getElementById('authModal').style.display = 'none';
            checkAuthStatus();
            loadUserContext();
            loadNotifications();
            
            showMessage('Login successful!', 'success');
        } else {
            showMessage(result.detail || 'Login failed', 'error');
        }
    } catch (error) {
        showMessage('Login failed: ' + error.message, 'error');
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const registerData = {
        name: formData.get('name'),
        email: formData.get('email'),
        password: formData.get('password')
    };
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(registerData)
        });
        
        const result = await response.json();
        
        if (result.access_token) {
            authToken = result.access_token;
            currentUser = result.user;
            
            localStorage.setItem('authToken', authToken);
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            document.getElementById('authModal').style.display = 'none';
            checkAuthStatus();
            
            // Show farming context modal for new users
            setTimeout(() => {
                document.getElementById('farmingContextModal').style.display = 'flex';
            }, 500);
            
            showMessage('Registration successful!', 'success');
        } else {
            showMessage(result.detail || 'Registration failed', 'error');
        }
    } catch (error) {
        showMessage('Registration failed: ' + error.message, 'error');
    }
}

// Phone authentication functions
async function sendOTP() {
    const phoneNumber = document.getElementById('phoneNumber').value;
    const countryCode = document.getElementById('countryCode').value;
    
    if (!phoneNumber || phoneNumber.length < 10) {
        showMessage('Please enter a valid 10-digit phone number', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/send-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
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
            
            // Start countdown
            startOTPCountdown(result.expires_in_minutes || 10);
            
            showMessage('OTP sent successfully!', 'success');
        } else {
            showMessage(result.error || 'Failed to send OTP', 'error');
        }
    } catch (error) {
        showMessage('Failed to send OTP: ' + error.message, 'error');
    }
}

async function verifyOTP() {
    const sessionId = document.getElementById('sessionId').value;
    const otpCode = document.getElementById('otpCode').value;
    
    if (!otpCode || otpCode.length !== 6) {
        showMessage('Please enter the 6-digit OTP', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/verify-otp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
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
            
            document.getElementById('authModal').style.display = 'none';
            checkAuthStatus();
            
            if (result.user.new_user) {
                // Show farming context modal for new users
                setTimeout(() => {
                    document.getElementById('farmingContextModal').style.display = 'flex';
                }, 500);
            }
            
            loadUserContext();
            loadNotifications();
            
            showMessage('Phone verification successful!', 'success');
        } else {
            showMessage(result.error || 'OTP verification failed', 'error');
        }
    } catch (error) {
        showMessage('OTP verification failed: ' + error.message, 'error');
    }
}

function startOTPCountdown(minutes) {
    let timeLeft = minutes * 60;
    const countdownElement = document.getElementById('otpCountdown');
    
    const countdown = setInterval(() => {
        const mins = Math.floor(timeLeft / 60);
        const secs = timeLeft % 60;
        
        countdownElement.textContent = `OTP expires in ${mins}:${secs.toString().padStart(2, '0')}`;
        
        if (timeLeft <= 0) {
            clearInterval(countdown);
            countdownElement.textContent = 'OTP expired. Please request a new one.';
            document.getElementById('sendOtpBtn').disabled = false;
        }
        
        timeLeft--;
    }, 1000);
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('authToken');
    localStorage.removeItem('currentUser');
    
    checkAuthStatus();
    showMessage('Logged out successfully', 'success');
    
    // Clear sensitive data
    document.getElementById('contextInfo').style.display = 'none';
    document.getElementById('notificationCount').textContent = '0';
}

// Farming context functions
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
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify(contextData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('farmingContextModal').style.display = 'none';
            loadUserContext();
            showMessage('Farming profile saved successfully!', 'success');
        } else {
            showMessage(result.error || 'Failed to save farming profile', 'error');
        }
    } catch (error) {
        showMessage('Failed to save farming profile: ' + error.message, 'error');
    }
}

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
        }
    } catch (error) {
        console.log('Failed to load user context:', error);
    }
}

function displayUserContext(context) {
    const contextInfo = document.getElementById('contextInfo');
    
    if (context) {
        contextInfo.innerHTML = `
            <div class="context-summary">
                <h4>🌾 Your Farm Profile</h4>
                <div class="context-details">
                    <span>📍 ${context.location}</span>
                    <span>🌾 ${context.primary_crops.join(', ')}</span>
                    <span>📏 ${context.farm_size_acres} acres</span>
                    <span>🚰 ${context.irrigation_method}</span>
                    <span>💧 Every ${context.irrigation_frequency_days} days</span>
                </div>
            </div>
        `;
        contextInfo.style.display = 'block';
    }
}

// Main unified query handler
async function handleUnifiedQuery(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const textQuery = formData.get('text')?.trim();
    const imageFile = formData.get('image');
    const language = document.getElementById('responseLanguage').value || 'hindi';
    
    // Validate input
    if (!textQuery && !imageFile) {
        showMessage('Please enter a question or upload an image', 'error');
        return;
    }
    
    // Show typing indicator
    showTypingIndicator();
    
    // Disable send button
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = true;
    sendBtn.innerHTML = '⏳';
    
    try {
        // Add user message to chat
        if (textQuery) {
            addMessageToChat('user', textQuery);
        }
        if (imageFile) {
            addMessageToChat('user', `📷 Image uploaded: ${imageFile.name}`);
        }
        
        // Prepare form data for submission
        const submitFormData = new FormData();
        if (textQuery) submitFormData.append('text', textQuery);
        if (imageFile) submitFormData.append('image', imageFile);
        submitFormData.append('language', language);
        
        // Add sensor data if available
        const sensorData = getCurrentSensorData();
        if (sensorData) {
            submitFormData.append('sensor_data', JSON.stringify(sensorData));
        }
        
        // Submit to unified endpoint
        const response = await fetch('/api/unified-query', {
            method: 'POST',
            headers: authToken ? {
                'Authorization': `Bearer ${authToken}`
            } : {},
            body: submitFormData
        });
        
        const result = await response.json();
        
        // Hide typing indicator
        hideTypingIndicator();
        
        if (result.success) {
            // Add AI response to chat
            addMessageToChat('ai', result.response, {
                recommendations: result.recommendations,
                confidence: result.confidence_score,
                dataSources: result.data_sources,
                intent: result.intent_detected,
                followUps: result.follow_up_suggestions
            });
            
            // Clear form
            document.getElementById('unifiedQuery').value = '';
            document.getElementById('imageInput').value = '';
            resetInputButtons();
            
        } else {
            addMessageToChat('ai', result.error || result.fallback_response || 'Sorry, I encountered an error processing your request.');
            showMessage(result.error || 'Query processing failed', 'error');
        }
        
    } catch (error) {
        hideTypingIndicator();
        addMessageToChat('ai', 'I apologize, but I\'m having trouble connecting right now. Please check your internet connection and try again.');
        showMessage('Network error: ' + error.message, 'error');
    } finally {
        // Re-enable send button
        sendBtn.disabled = false;
        sendBtn.innerHTML = '➤';
    }
}

function addMessageToChat(sender, message, metadata = {}) {
    const chatHistory = document.getElementById('chatHistory');
    const messageDiv = document.createElement('div');
    messageDiv.className = `${sender}-message`;
    
    const timestamp = new Date().toLocaleTimeString();
    
    if (sender === 'ai') {
        messageDiv.innerHTML = `
            <div class="message-avatar">🌾</div>
            <div class="message-content">
                <div class="message-text">${formatMessage(message)}</div>
                ${metadata.recommendations && metadata.recommendations.length > 0 ? `
                    <div class="message-recommendations">
                        <h5>📋 Recommendations:</h5>
                        <ul>
                            ${metadata.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                ${metadata.followUps && metadata.followUps.length > 0 ? `
                    <div class="follow-up-actions">
                        <h5>💡 You can also ask:</h5>
                        <div class="response-actions">
                            ${metadata.followUps.map(followUp => 
                                `<button class="response-action" onclick="setQuickQuery('${followUp}')">${followUp}</button>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                <div class="message-meta">
                    <span>${timestamp}</span>
                    ${metadata.confidence ? `<span class="confidence-indicator">${Math.round(metadata.confidence * 100)}% confident</span>` : ''}
                </div>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-content">
                <div class="message-text">${formatMessage(message)}</div>
                <div class="message-meta">
                    <span>${timestamp}</span>
                </div>
            </div>
        `;
    }
    
    chatHistory.appendChild(messageDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function formatMessage(message) {
    // Convert newlines to <br> and format lists
    return message
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

function showTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'flex';
    const chatHistory = document.getElementById('chatHistory');
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function hideTypingIndicator() {
    document.getElementById('typingIndicator').style.display = 'none';
}

function setQuickQuery(query) {
    document.getElementById('unifiedQuery').value = query;
    document.getElementById('unifiedQuery').focus();
}

function resetInputButtons() {
    const imageBtn = document.getElementById('imageBtn');
    const voiceBtn = document.getElementById('voiceBtn');
    const sensorBtn = document.getElementById('sensorBtn');
    
    if (imageBtn) {
        imageBtn.classList.remove('active');
        imageBtn.innerHTML = '📷';
    }
    if (voiceBtn) {
        voiceBtn.classList.remove('active');
        voiceBtn.innerHTML = '🎤';
    }
    if (sensorBtn) {
        sensorBtn.classList.remove('active');
        sensorBtn.innerHTML = '📊';
    }
}

// Voice recording functions
async function toggleVoiceRecording() {
    if (!isRecording) {
        await startVoiceRecording();
    } else {
        stopVoiceRecording();
    }
}

async function startVoiceRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        
        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };
        
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            const reader = new FileReader();
            reader.onloadend = () => {
                document.getElementById('voiceData').value = reader.result;
            };
            reader.readAsDataURL(audioBlob);
        };
        
        mediaRecorder.start();
        isRecording = true;
        
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.classList.add('active');
        voiceBtn.innerHTML = '🔴';
        
        showMessage('Recording... Click again to stop', 'info');
        
    } catch (error) {
        showMessage('Microphone access denied or not available', 'error');
    }
}

function stopVoiceRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
        isRecording = false;
        
        const voiceBtn = document.getElementById('voiceBtn');
        voiceBtn.classList.add('active');
        voiceBtn.innerHTML = '🎤✓';
        
        showMessage('Voice recorded successfully', 'success');
    }
}

// Sensor data functions
function toggleSensorData() {
    const sensorDisplay = document.getElementById('sensorDataDisplay');
    const sensorBtn = document.getElementById('sensorBtn');
    
    if (sensorDisplay.style.display === 'none' || !sensorDisplay.style.display) {
        sensorDisplay.style.display = 'block';
        sensorBtn.classList.add('active');
        sensorBtn.innerHTML = '📊✓';
        refreshSensorData();
    } else {
        sensorDisplay.style.display = 'none';
        sensorBtn.classList.remove('active');
        sensorBtn.innerHTML = '📊';
    }
}

function refreshSensorData() {
    // Simulate real sensor data (in production, this would call real IoT APIs)
    const sensorData = getSensorData();
    
    const elements = {
        'soilMoistureValue': sensorData.soil_moisture.toFixed(1) + '%',
        'temperatureValue': sensorData.temperature.toFixed(1) + '°C',
        'phValue': sensorData.ph.toFixed(1),
        'humidityValue': sensorData.humidity.toFixed(1) + '%'
    };
    
    Object.entries(elements).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    });
}

function getSensorData() {
    // Simulate realistic sensor readings
    return {
        soil_moisture: 45 + Math.random() * 30, // 45-75%
        temperature: 22 + Math.random() * 15,   // 22-37°C
        ph: 6.0 + Math.random() * 2,           // 6.0-8.0
        humidity: 40 + Math.random() * 40       // 40-80%
    };
}

function getCurrentSensorData() {
    const sensorDisplay = document.getElementById('sensorDataDisplay');
    if (sensorDisplay && sensorDisplay.style.display !== 'none') {
        return getSensorData();
    }
    return null;
}

// Notification functions
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
            displayNotifications(result.notifications);
            updateNotificationCount(result.notifications.filter(n => !n.read).length);
        }
    } catch (error) {
        console.log('Failed to load notifications:', error);
    }
}

function displayNotifications(notifications) {
    const content = document.getElementById('notificationsContent');
    
    if (notifications.length === 0) {
        content.innerHTML = '<div class="no-notifications">No notifications yet</div>';
        return;
    }
    
    content.innerHTML = notifications.map(notification => `
        <div class="notification-item ${!notification.read ? 'unread' : ''}" 
             onclick="markNotificationRead('${notification.id}')">
            <div class="notification-title">${notification.title}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">${formatTime(notification.created_at)}</div>
        </div>
    `).join('');
}

function updateNotificationCount(count) {
    document.getElementById('notificationCount').textContent = count;
}

function toggleNotifications() {
    const panel = document.getElementById('notificationsPanel');
    panel.style.display = panel.style.display === 'block' ? 'none' : 'block';
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
        
        loadNotifications();
    } catch (error) {
        console.log('Failed to mark notification as read:', error);
    }
}

// Community functions
async function loadCommunityPosts() {
    try {
        const response = await fetch('/api/community/posts?limit=10');
        const result = await response.json();
        
        if (result.success) {
            displayCommunityPosts(result.posts);
        } else {
            document.getElementById('communityPosts').innerHTML = 
                '<div class="no-posts">Unable to load community posts</div>';
        }
    } catch (error) {
        document.getElementById('communityPosts').innerHTML = 
            '<div class="no-posts">Failed to load community posts</div>';
    }
}

function displayCommunityPosts(posts) {
    const container = document.getElementById('communityPosts');
    
    if (posts.length === 0) {
        container.innerHTML = '<div class="no-posts">No community posts yet. Be the first to share!</div>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="community-post" onclick="viewPostDetails('${post.post_id}')">
            <div class="post-header">
                <span class="post-type-badge ${post.post_type}">${post.post_type.replace('_', ' ')}</span>
                <div class="post-meta">
                    <span>👤 ${post.author_name}</span>
                    <span>📍 ${post.location || 'Unknown'}</span>
                    <span>📅 ${formatTime(post.created_at)}</span>
                </div>
            </div>
            <h4 class="post-title">${post.title}</h4>
            <p class="post-content">${post.content.substring(0, 200)}${post.content.length > 200 ? '...' : ''}</p>
            <div class="post-stats">
                <span>👍 ${post.likes} likes</span>
                <span>👁️ ${post.views} views</span>
                <span>💬 ${post.comment_count || 0} comments</span>
            </div>
            ${post.crops_mentioned && post.crops_mentioned.length > 0 ? `
                <div class="post-crops">
                    ${post.crops_mentioned.map(crop => `<span class="crop-tag">${crop}</span>`).join('')}
                </div>
            ` : ''}
        </div>
    `).join('');
}

// Government schemes functions
async function loadGovernmentSchemes() {
    if (!authToken) {
        document.getElementById('governmentSchemes').innerHTML = 
            '<div class="no-schemes">Please login to view personalized government schemes</div>';
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
            document.getElementById('governmentSchemes').innerHTML = 
                `<div class="no-schemes">${result.error || 'Unable to load schemes'}</div>`;
        }
    } catch (error) {
        document.getElementById('governmentSchemes').innerHTML = 
            '<div class="no-schemes">Failed to load government schemes</div>';
    }
}

function displayGovernmentSchemes(schemes) {
    const container = document.getElementById('governmentSchemes');
    
    if (schemes.length === 0) {
        container.innerHTML = '<div class="no-schemes">No applicable schemes found. Complete your profile for better recommendations.</div>';
        return;
    }
    
    container.innerHTML = schemes.map(scheme => `
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
            
            ${scheme.matching_criteria && scheme.matching_criteria.length > 0 ? `
                <div class="matching-criteria">
                    <h5>✅ You meet these criteria:</h5>
                    <ul>
                        ${scheme.matching_criteria.map(criteria => `<li>${criteria}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            
            ${scheme.missing_criteria && scheme.missing_criteria.length > 0 ? `
                <div class="missing-criteria">
                    <h5>❌ Missing criteria:</h5>
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
}

// Enhanced sensor data functions
async function loadEnhancedSensorData() {
    const container = document.getElementById('enhancedSensorContainer');
    
    try {
        // Simulate enhanced sensor data (in production, this would call real IoT APIs)
        const sensorData = await getEnhancedSensorData();
        displayEnhancedSensorData(sensorData);
        
    } catch (error) {
        container.innerHTML = '<div class="error-message">Failed to load sensor data</div>';
    }
}

async function getEnhancedSensorData() {
    // Simulate realistic IoT sensor data with insights
    return {
        success: true,
        farm_id: 'demo_farm_001',
        timestamp: new Date().toISOString(),
        sensor_readings: {
            soil_moisture: {
                current_value: 45 + Math.random() * 30,
                unit: '%',
                quality_score: 0.85 + Math.random() * 0.1,
                sensor_id: 'soil_001',
                location: 'Field_1'
            },
            temperature: {
                current_value: 22 + Math.random() * 15,
                unit: '°C',
                quality_score: 0.90 + Math.random() * 0.05,
                sensor_id: 'temp_001',
                location: 'Field_1'
            },
            ph_level: {
                current_value: 6.0 + Math.random() * 2,
                unit: 'pH',
                quality_score: 0.80 + Math.random() * 0.15,
                sensor_id: 'ph_001',
                location: 'Field_1'
            },
            humidity: {
                current_value: 40 + Math.random() * 40,
                unit: '%',
                quality_score: 0.85 + Math.random() * 0.1,
                sensor_id: 'humid_001',
                location: 'Field_1'
            }
        },
        insights: [
            {
                insight_type: 'irrigation_recommendation',
                description: 'Soil moisture levels indicate irrigation may be needed within 24 hours',
                confidence: 0.8,
                recommendations: [
                    'Monitor soil moisture closely',
                    'Prepare irrigation system',
                    'Check weather forecast for rain'
                ]
            }
        ],
        alerts: [],
        data_quality: {
            overall_quality: 'good',
            quality_score: 0.85
        },
        simulation_mode: true
    };
}

function displayEnhancedSensorData(data) {
    const container = document.getElementById('enhancedSensorContainer');
    
    if (!data.success) {
        container.innerHTML = '<div class="error-message">Sensor data unavailable</div>';
        return;
    }
    
    const readings = data.sensor_readings || {};
    const insights = data.insights || [];
    const alerts = data.alerts || [];
    
    container.innerHTML = `
        <div class="enhanced-sensor-display">
            <div class="sensor-data-header">
                <h4>📊 Real-time Sensor Data</h4>
                <span class="data-quality ${data.data_quality.overall_quality}">${data.data_quality.overall_quality}</span>
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
                ${Object.entries(readings).map(([type, reading]) => `
                    <div class="sensor-reading-card">
                        <div class="sensor-type">${type.replace('_', ' ')}</div>
                        <div class="sensor-value">${reading.current_value.toFixed(1)}${reading.unit}</div>
                        <div class="sensor-meta">
                            <span>Quality: ${(reading.quality_score * 100).toFixed(0)}%</span>
                            <span>${reading.location}</span>
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
                            <div class="insight-confidence">Confidence: ${(insight.confidence * 100).toFixed(0)}%</div>
                            <ul class="insight-recommendations">
                                ${insight.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
            
            ${data.simulation_mode ? '<p style="text-align: center; color: #666; font-size: 12px; margin-top: 15px;">📡 Simulated sensor data for demonstration</p>' : ''}
        </div>
    `;
}

// Utility functions
function showMessage(message, type = 'info') {
    // Create message element
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.textContent = message;
    
    // Add to page
    document.body.appendChild(messageDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

function formatTime(timestamp) {
    try {
        return new Date(timestamp).toLocaleString();
    } catch {
        return 'Unknown time';
    }
}

function updateLanguagePreference() {
    const language = document.getElementById('responseLanguage').value;
    localStorage.setItem('preferredLanguage', language);
}

function setupRealtimeFeatures() {
    // Monitor online/offline status
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
    
    // Load preferred language
    const savedLanguage = localStorage.getItem('preferredLanguage');
    if (savedLanguage) {
        document.getElementById('responseLanguage').value = savedLanguage;
    }
}

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
    const targetTab = tabName === 'chat' ? 'chatTab' : tabName + 'Tab';
    const tabElement = document.getElementById(targetTab);
    if (tabElement) {
        tabElement.classList.add('active');
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

// Placeholder functions for features not yet implemented
function showCreatePostModal() {
    if (!authToken) {
        showMessage('Please login to create posts', 'error');
        return;
    }
    document.getElementById('createPostModal').style.display = 'flex';
}

function hideCreatePostModal() {
    document.getElementById('createPostModal').style.display = 'none';
}

function viewPostDetails(postId) {
    showMessage('Post details feature coming soon!', 'info');
}

function viewSchemeDetails(schemeId) {
    showMessage('Scheme details feature coming soon!', 'info');
}

function filterCommunityPosts() {
    showMessage('Community filtering feature coming soon!', 'info');
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing app...');
    initializeApp();
});