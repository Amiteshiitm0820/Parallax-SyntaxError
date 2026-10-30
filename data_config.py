# data_config.py
# PERSON 1: Dataset & Threat Signal Rules

# 1. Threat & Urgency Dictionaries (Multilingual)
URGENCY_KEYWORDS = {
    "english": [
        "urgent", "immediate action", "blocked", "suspended", "restricted", 
        "verify now", "expire", "deactivated", "kyc", "otp", "claim now", 
        "lottery", "winner", "prize"
    ],
    "hindi": [
        "कट जाएगी", "ब्लॉक", "तुरंत", "सस्पेंड", "चेतावनी", "बधाई हो", 
        "जीते हैं", "लॉटरी", "भुगतान करें", "बंद", "लिंक करें"
    ],
    "hinglish": [
        "block ho jayega", "kyc update karo", "urgent hai", "account ban", 
        "jaldi se", "warna", "suspend ho gaya", "approve ho gaya"
    ]
}

# 2. Known Official Domains vs Suspicious Keywords
DOMAIN_WHITELIST = {
    "sbi": ["onlinesbi.sbi", "sbi.co.in"],
    "hdfc": ["hdfcbank.com"],
    "icici": ["icicibank.com"],
    "axis": ["axisbank.com"],
    "jio": ["jio.com"],
    "airtel": ["airtel.in"],
    "india_post": ["indiapost.gov.in"],
    "income_tax": ["incometax.gov.in"],
    "uppcl": ["uppcl.org"]
}

SUSPICIOUS_DOMAIN_TOKENS = [
    "update", "kyc", "verify", "secure", "support", "refund", "login", 
    "prize", "yojana", "free", "claim"
]

URL_SHORTENERS = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd", "cutt.ly"]

# 3. Synthetic Dataset (25 Samples: Phishing vs Safe)
MESSAGES_DATASET = [
    # --- PHISHING: ENGLISH ---
    {"id": "MSG_001", "type": "phishing", "lang": "english", "text": "Dear SBI User, your YONO account will be blocked today. Please update your Pan card on sbi-kyc-verify.com/update immediately."},
    {"id": "MSG_002", "type": "phishing", "lang": "english", "text": "Income Tax Refund of Rs 15,490 has been approved. Claim now at incometax-refund-gov.in to avoid delays."},
    {"id": "MSG_003", "type": "phishing", "lang": "english", "text": "Your Axis Bank credit card has been blocked due to suspicious activity. Verify here: axis-secure-login.com"},
    {"id": "MSG_004", "type": "phishing", "lang": "english", "text": "Urgent: Your EPF account needs verification. Click here to verify your UAN: epfindia-verify.co.in"},
    {"id": "MSG_005", "type": "phishing", "lang": "english", "text": "You have received a package but address is missing. Pay Rs 5 to redeliver: indiapost-tracker.info"},
    {"id": "MSG_006", "type": "phishing", "lang": "english", "text": "Netflix subscription expired. Renew immediately to avoid account suspension: netflix-billing-update.com"},
    {"id": "MSG_007", "type": "phishing", "lang": "english", "text": "Your Apple ID has been locked for security reasons. Unlock here: apple-support-recovery.com"},
    {"id": "MSG_008", "type": "phishing", "lang": "english", "text": "Dear User, your WhatsApp account will be deleted tonight. Verify identity: whatsapp-verify-web.com"},
    
    # --- PHISHING: HINDI ---
    {"id": "MSG_009", "type": "phishing", "lang": "hindi", "text": "प्रिय ग्राहक, आपका बिजली बिल बकाया है। रात 9:30 बजे बिजली कट जाएगी। तुरंत भुगतान करें: http://uppcl-bill-update.in"},
    {"id": "MSG_010", "type": "phishing", "lang": "hindi", "text": "बधाई हो! आपने Jio लकी ड्रा में ₹1,00,000 जीते हैं। क्लेम करने के लिए: jio-winner-prize.com"},
    {"id": "MSG_011", "type": "phishing", "lang": "hindi", "text": "ध्यान दें! आपका पैन कार्ड आधार से लिंक नहीं है, कल से बैंक खाता बंद। अभी लिंक करें: aadhar-pan-link.com"},
    {"id": "MSG_012", "type": "phishing", "lang": "hindi", "text": "प्रिय नागरिक, आपको 50,000 रुपये का सरकारी लोन मिला है। रजिस्टर करें: pm-yojana-loan.in"},
    
    # --- PHISHING: HINGLISH ---
    {"id": "MSG_013", "type": "phishing", "lang": "hinglish", "text": "Aapka HDFC bank acc suspend ho gaya hai. Reactivate karne ke liye is link par click kare: bit.ly/hdfc-secure"},
    {"id": "MSG_014", "type": "phishing", "lang": "hinglish", "text": "Jaldi se apna KYC update karlo warna Airtel sim block ho jayega kal se. Link: airtel-kyc-verify.com"},
    {"id": "MSG_015", "type": "phishing", "lang": "hinglish", "text": "Sir aapka loan approve ho gaya 5 lakh ka. Process fee 2000 rupees pay karein is link par: fast-loan-india.com"},
    {"id": "MSG_016", "type": "phishing", "lang": "hinglish", "text": "Congratulations! Aapko KBC ki taraf se 25 lakh ka lottery mila hai. WhatsApp call karein: wa.me/92xxxxxx"},

    # --- SAFE: ENGLISH ---
    {"id": "MSG_017", "type": "safe", "lang": "english", "text": "Your OTP for HDFC Bank NetBanking login is 482910. Do not share this with anyone."},
    {"id": "MSG_018", "type": "safe", "lang": "english", "text": "Dear Customer, your recent transaction of INR 500 at Amazon is successful. - ICICI Bank"},
    {"id": "MSG_019", "type": "safe", "lang": "english", "text": "Your Amazon package is out for delivery. Track it here: amazon.in/track/12345"},
    {"id": "MSG_020", "type": "safe", "lang": "english", "text": "Dear customer, your Swiggy order #1293 is confirmed and will arrive in 30 mins."},
    {"id": "MSG_021", "type": "safe", "lang": "english", "text": "Your monthly statement for HDFC Bank Credit Card is ready for viewing."},
    {"id": "MSG_022", "type": "safe", "lang": "english", "text": "Use 492812 to verify your Uber login. Never share this code."},

    # --- SAFE: HINDI ---
    {"id": "MSG_023", "type": "safe", "lang": "hindi", "text": "एसबीआई: आपके खाते से 100 रुपये निकाले गए हैं। उपलब्ध बैलेंस 5000 रुपये है।"},
    {"id": "MSG_024", "type": "safe", "lang": "hindi", "text": "आपका इंडेन गैस सिलेंडर सफलतापूर्वक बुक हो गया है। रिफरेंस नंबर: 129381"},

    # --- SAFE: HINGLISH ---
    {"id": "MSG_025", "type": "safe", "lang": "hinglish", "text": "Aapka mobile recharge Rs 299 ka successful ho gaya hai. Valid till 30 Nov."}
]