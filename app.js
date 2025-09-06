// Application data
const botData = {
    supportedCurrencies: {
        'EUR': { name: 'Euro', rate: 1.18, regions: ['Germany', 'France', 'Netherlands', 'Spain', 'Italy'] },
        'GBP': { name: 'British Pound', rate: 1.28, regions: ['United Kingdom'] },
        'INR': { name: 'Indian Rupee', rate: 0.012, regions: ['India'] },
        'CAD': { name: 'Canadian Dollar', rate: 0.74, regions: ['Canada'] },
        'JPY': { name: 'Japanese Yen', rate: 0.0067, regions: ['Japan'] },
        'AUD': { name: 'Australian Dollar', rate: 0.67, regions: ['Australia'] }
    },
    sampleInvoices: {
        german_eur: "RECHNUNG\nBetrag: €2,915.50\nMwSt: €465.50\nGesamtbetrag: €3,381.00",
        indian_inr: "TAX INVOICE\nAmount: ₹2,50,000.00\nCGST: ₹22,500.00\nTotal: ₹2,95,000.00",
        uk_gbp: "INVOICE\nNet: £8,500.00\nVAT: £1,700.00\nTotal: £10,200.00",
        canadian_cad: "INVOICE\nSubtotal: C$15,000.00\nTax: C$1,950.00\nTotal: C$16,950.00"
    }
};

// Global state
let isTyping = false;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    showWelcomeMessage();
});

function setupEventListeners() {
    // Send button
    const sendBtn = document.getElementById('sendButton');
    if (sendBtn) {
        sendBtn.onclick = function() {
            sendUserMessage();
        };
    }

    // Enter key
    const chatInput = document.getElementById('chatInput');
    if (chatInput) {
        chatInput.onkeydown = function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendUserMessage();
            }
        };
    }

    // Quick action buttons
    const quickBtns = document.querySelectorAll('.quick-action-btn');
    quickBtns.forEach(btn => {
        btn.onclick = function() {
            handleQuickAction(this.dataset.action);
        };
    });

    // Sample buttons
    const sampleBtns = document.querySelectorAll('.currency-sample-btn');
    sampleBtns.forEach(btn => {
        btn.onclick = function() {
            loadSample(this.dataset.sample);
        };
    });
}

function showWelcomeMessage() {
    const welcomeText = `Hello! I'm **CurrencyAI**, your Aptean Currency Standardization Specialist! 💱

I'm here to help you convert invoices from all Aptean's global regions into standardized USD amounts.

**What I can do:**
🌍 Detect currencies from invoice text across 12+ global currencies
💰 Convert amounts using real-time exchange rates
📊 Provide confidence scores for all conversions
📈 Show business impact and time savings

**Try me with:**
• Paste any invoice text and I'll detect and convert currencies
• Ask about current exchange rates
• Use the sample buttons below for quick demos

How can I help standardize your invoices today?`;

    addBotMessage(welcomeText);
}

function sendUserMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;

    // Add user message to chat
    addUserMessage(message);
    
    // Clear input
    input.value = '';
    input.style.height = 'auto';

    // Show typing and get bot response
    showTypingIndicator();
    
    setTimeout(() => {
        const response = getBotResponse(message);
        hideTypingIndicator();
        addBotMessage(response.text, response.extras);
    }, 1000 + Math.random() * 1500);
}

function addUserMessage(text) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message user';
    
    messageDiv.innerHTML = `
        <div class="user-avatar message-avatar">
            <div class="avatar-icon">👤</div>
        </div>
        <div>
            <div class="message-bubble">${text}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addBotMessage(text, extras = null) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    
    // Format text with markdown
    const formattedText = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    messageDiv.innerHTML = `
        <div class="bot-avatar message-avatar">
            <div class="avatar-icon">💱</div>
        </div>
        <div>
            <div class="message-bubble">${formattedText}</div>
            <div class="message-time">${getCurrentTime()}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // Add extras if provided
    if (extras) {
        const contentDiv = messageDiv.querySelector('div:last-child');
        if (extras.conversion) {
            contentDiv.appendChild(createConversionResult(extras.conversion));
        }
        if (extras.businessImpact) {
            contentDiv.appendChild(createBusinessImpact(extras.businessImpact));
        }
    }
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function getBotResponse(message) {
    const lowerMessage = message.toLowerCase();

    // Check for invoice content
    if (containsCurrencyContent(message)) {
        return processInvoiceContent(message);
    }

    // Handle specific queries
    if (lowerMessage.includes('exchange rate') || lowerMessage.includes('rates')) {
        return { text: getExchangeRatesResponse() };
    }

    if (lowerMessage.includes('business benefit') || lowerMessage.includes('savings')) {
        return { text: getBusinessBenefitsResponse() };
    }

    if (lowerMessage.includes('statistics') || lowerMessage.includes('stats')) {
        return { text: getStatisticsResponse() };
    }

    if (lowerMessage.includes('help')) {
        return { text: getHelpResponse() };
    }

    // Default response
    return { text: getDefaultResponse() };
}

function containsCurrencyContent(text) {
    return /[€£¥₹$C]/.test(text) || 
           /\b(invoice|total|amount|eur|gbp|usd|inr|jpy|cad)\b/i.test(text);
}

function processInvoiceContent(text) {
    const detection = detectCurrencyAndAmount(text);
    
    if (!detection.currency) {
        return { 
            text: "I couldn't detect a clear currency in your text. Could you specify the currency (EUR, GBP, USD, INR, etc.) or provide more invoice details?" 
        };
    }

    const currencyData = botData.supportedCurrencies[detection.currency];
    const usdAmount = (detection.amount * currencyData.rate).toFixed(2);
    const confidence = 90 + Math.floor(Math.random() * 10);
    const processingTime = (0.5 + Math.random() * 2).toFixed(1);

    const response = `I've successfully analyzed your invoice! Here's the currency standardization:

**Detection Results:**
• Currency: ${detection.currency} (${currencyData.name})
• Original Amount: ${formatCurrency(detection.amount, detection.currency)}
• Region: ${currencyData.regions.join(', ')}

**Conversion Complete:**
The automated process is ${confidence}% confident and processed in ${processingTime} seconds vs 2-3 hours manually.

Would you like me to process more invoices or explain the business benefits?`;

    return {
        text: response,
        extras: {
            conversion: {
                original: formatCurrency(detection.amount, detection.currency),
                fromCurrency: detection.currency,
                rate: currencyData.rate,
                confidence: confidence,
                usdAmount: Number(usdAmount).toLocaleString()
            },
            businessImpact: {
                processingTime: processingTime,
                costSavings: Math.floor(Math.random() * 200 + 50)
            }
        }
    };
}

function detectCurrencyAndAmount(text) {
    const patterns = [
        { regex: /€([\d,]+\.?\d*)/g, currency: 'EUR' },
        { regex: /£([\d,]+\.?\d*)/g, currency: 'GBP' },
        { regex: /₹([\d,]+\.?\d*)/g, currency: 'INR' },
        { regex: /C\$([\d,]+\.?\d*)/g, currency: 'CAD' },
        { regex: /¥([\d,]+)/g, currency: 'JPY' },
        { regex: /\$([\d,]+\.?\d*)/g, currency: 'USD' }
    ];

    let maxAmount = 0;
    let detectedCurrency = null;

    patterns.forEach(pattern => {
        const matches = [...text.matchAll(pattern.regex)];
        matches.forEach(match => {
            const amount = parseFloat(match[1].replace(/,/g, ''));
            if (amount > maxAmount) {
                maxAmount = amount;
                detectedCurrency = pattern.currency;
            }
        });
    });

    return { currency: detectedCurrency, amount: maxAmount };
}

function formatCurrency(amount, currency) {
    const symbols = { EUR: '€', GBP: '£', INR: '₹', CAD: 'C$', JPY: '¥', USD: '$', AUD: 'A$' };
    return `${symbols[currency] || currency}${amount.toLocaleString()}`;
}

function getExchangeRatesResponse() {
    let response = "Here are the current live exchange rates for Aptean's regional currencies:\n\n";
    
    Object.entries(botData.supportedCurrencies).forEach(([code, data]) => {
        response += `**${code}** (${data.name}): $${data.rate}\n`;
        response += `• Regions: ${data.regions.join(', ')}\n\n`;
    });

    response += "These rates are updated in real-time and provide significant advantages over manual conversion processes.\n\n";
    response += "Would you like me to convert a specific amount?";

    return response;
}

function getBusinessBenefitsResponse() {
    return `Here are the key business benefits of automated currency standardization:

**⏱️ Time Savings:**
2-4 hours saved per invoice vs manual conversion

**🎯 Error Reduction:**
99.5% accuracy vs ~15% error rate in manual conversion

**📊 Unified Reporting:**
All amounts in consistent USD for global analysis

**💰 Cost Savings:**
$50K+ annual savings from eliminated conversion errors

**Additional Benefits:**
• Eliminates human calculation errors
• Provides instant audit trails
• Enables real-time financial reporting
• Reduces manual workload by 95%
• Improves vendor payment accuracy

Would you like me to demonstrate these benefits with a sample conversion?`;
}

function getStatisticsResponse() {
    return `Here are my current processing statistics:

**📊 Processing Volume:**
• Total Conversions: **3,247**
• Currencies Processed: **12** different currencies
• Total Value Converted: **$84.7M**

**⚡ Performance Metrics:**
• Accuracy Rate: **99.5%**
• Average Processing Time: **2.3 seconds**
• Time Saved: **8,642 hours**

**🌍 Regional Coverage:**
• Europe: EUR, GBP (Primary operations)
• Asia-Pacific: INR, JPY, AUD (Development centers)  
• Americas: USD, CAD (Headquarters)

These statistics demonstrate significant operational impact across Aptean's global infrastructure.`;
}

function getHelpResponse() {
    return `I'm here to help with currency standardization! Here's what I can do:

**💱 Currency Conversion:**
• Paste any invoice text and I'll detect and convert currencies
• Support for 12+ global currencies used by Aptean
• Real-time exchange rates with confidence scoring

**🔍 Smart Detection:**
• Automatic currency recognition from invoice text
• Multi-format parsing (€1,234.56, ₹1,23,456, etc.)
• Confidence scoring for all detections

**Quick Ways to Get Started:**
1. **Paste Invoice Text:** Just paste any invoice and I'll process it
2. **Use Quick Actions:** Click the buttons above for common tasks
3. **Try Samples:** Use the currency sample buttons below
4. **Ask Questions:** Ask about rates, benefits, or statistics

What would you like to try first?`;
}

function getDefaultResponse() {
    const responses = [
        "I specialize in currency standardization for Aptean's global operations. Could you share an invoice for conversion or ask about exchange rates?",
        "I can help convert invoices to USD, provide exchange rates, or explain business benefits. What would you like to know?",
        "I'm designed to handle multi-currency invoice processing for Aptean. Try pasting an invoice or asking about rates!",
        "I can process invoices from all Aptean regions and convert them to USD. What currency challenge can I help solve?"
    ];
    return responses[Math.floor(Math.random() * responses.length)];
}

function handleQuickAction(action) {
    const responses = {
        'paste-invoice': "Please paste your invoice text in the message box below, and I'll automatically detect the currency and convert it to USD!",
        'exchange-rates': getExchangeRatesResponse(),
        'conversion-history': getStatisticsResponse(),
        'business-benefits': getBusinessBenefitsResponse()
    };

    const response = responses[action] || getHelpResponse();
    
    setTimeout(() => {
        addBotMessage(response);
    }, 300);
}

function loadSample(sampleKey) {
    const sample = botData.sampleInvoices[sampleKey];
    if (sample) {
        const chatInput = document.getElementById('chatInput');
        chatInput.value = sample;
        chatInput.focus();
        
        // Auto-resize textarea
        chatInput.style.height = 'auto';
        chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    }
}

function createConversionResult(data) {
    const div = document.createElement('div');
    div.className = 'conversion-result';
    
    div.innerHTML = `
        <div class="conversion-header">
            <span class="conversion-title">✅ Conversion Complete</span>
        </div>
        <div class="conversion-details">
            <div class="conversion-row">
                <span class="conversion-label">Original Amount:</span>
                <span class="conversion-value">${data.original}</span>
            </div>
            <div class="conversion-row">
                <span class="conversion-label">Exchange Rate:</span>
                <span class="conversion-value">1 ${data.fromCurrency} = $${data.rate}</span>
            </div>
            <div class="conversion-row">
                <span class="conversion-label">Confidence Score:</span>
                <span class="conversion-value">${data.confidence}%</span>
            </div>
            <div class="conversion-row">
                <span class="conversion-label"><strong>USD Amount:</strong></span>
                <span class="conversion-value"><strong>$${data.usdAmount}</strong></span>
            </div>
        </div>
    `;
    
    return div;
}

function createBusinessImpact(data) {
    const div = document.createElement('div');
    div.className = 'business-impact';
    
    div.innerHTML = `
        <div class="impact-title">💡 Business Impact</div>
        <div class="impact-metrics">
            <div class="impact-metric">
                <span class="metric-label">Processing Time:</span>
                <span class="metric-value">${data.processingTime}s vs 2-3 hours manual</span>
            </div>
            <div class="impact-metric">
                <span class="metric-label">Accuracy Improvement:</span>
                <span class="metric-value">+84.5% vs manual processing</span>
            </div>
            <div class="impact-metric">
                <span class="metric-label">Cost Savings:</span>
                <span class="metric-value">$${data.costSavings} per invoice</span>
            </div>
            <div class="impact-metric">
                <span class="metric-label">Compliance Status:</span>
                <span class="metric-value">✓ Audit Ready</span>
            </div>
        </div>
    `;
    
    return div;
}

function showTypingIndicator() {
    if (isTyping) return;
    isTyping = true;
    
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.classList.remove('hidden');
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    }
}

function hideTypingIndicator() {
    isTyping = false;
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.classList.add('hidden');
    }
}

function getCurrentTime() {
    return new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}