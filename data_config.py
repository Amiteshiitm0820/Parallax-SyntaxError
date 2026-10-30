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
# 4. Advanced Threat Scenarios (Add to data_config.py)
EXTENDED_DATASET = [
    # --- E-CHALLAN & TRAFFIC SCAMS ---
    {"id": "MSG_026", "type": "phishing", "lang": "english", "text": "Traffic Police: Your vehicle KA-01 has a pending challan of Rs 2000. Pay via echallan-parivahan-gov.in to avoid court notice."},
    {"id": "MSG_027", "type": "phishing", "lang": "hindi", "text": "यातायात पुलिस: आपका 1000 रुपये का चालान पेंडिंग है। आज ही echallan-pay-india.com पर भुगतान करें वरना गाड़ी ज़ब्त होगी।"},
    {"id": "MSG_028", "type": "phishing", "lang": "hinglish", "text": "Sir aapka traffic challan pending hai court me jayega kal. Pay fast: e-challan-online.in"},
    {"id": "MSG_029", "type": "safe", "lang": "english", "text": "E-challan generated for vehicle KA01XX1234. Amount: Rs 500. Visit official portal echallan.parivahan.gov.in to view."},

    # --- CUSTOMS & COURIER SCAMS ---
    {"id": "MSG_030", "type": "phishing", "lang": "english", "text": "FedEx: Your international package is held at customs. Clear Rs 499 duty fee here immediately: fedex-customs-clearance.info"},
    {"id": "MSG_031", "type": "phishing", "lang": "hindi", "text": "कस्टम विभाग: आपका पार्सल रोका गया है। 500 रुपये की कस्टम ड्यूटी भरें: india-customs-post.in"},
    {"id": "MSG_032", "type": "phishing", "lang": "hinglish", "text": "Aapka courier hold par hai custom clearance ke liye. Rs 250 pay karein delivery ke liye: bluedart-track-update.com"},
    {"id": "MSG_033", "type": "safe", "lang": "hindi", "text": "आपका पार्सल (ID: 9382) आज शाम तक डिलीवर कर दिया जाएगा। - Amazon"},
    
    # --- PART-TIME JOB & TELEGRAM SCAMS ---
    {"id": "MSG_034", "type": "phishing", "lang": "english", "text": "HR Department: You are selected for a WFH job. Earn Rs 5000 daily by liking YouTube videos. Message on Telegram: t.me/hr_recruiter_99"},
    {"id": "MSG_035", "type": "phishing", "lang": "hindi", "text": "अमेज़ॅन पार्ट टाइम जॉब! घर बैठे रोज़ाना ₹3000 कमाएं। अभी व्हाट्सएप करें: wa.me/918xxxxxxxxx"},
    {"id": "MSG_036", "type": "phishing", "lang": "hinglish", "text": "Google reviews part time job. Earn 2000 per day. Joining bonus Rs 500. Click here to join our WhatsApp group: chat.whatsapp.com/fakegroup"},
    
    # --- PAN-AADHAAR & BANKING EDGE CASES ---
    {"id": "MSG_037", "type": "phishing", "lang": "hinglish", "text": "Dear user, PAN-Aadhar link last date is today. Penalty Rs 10000. Link fast: incometax-gov-link.in"},
    {"id": "MSG_038", "type": "safe", "lang": "english", "text": "Your Aadhar XX4829 has been successfully authenticated for e-KYC on 30-Oct-2026. - UIDAI"},
    {"id": "MSG_039", "type": "phishing", "lang": "hindi", "text": "आपका योनो खाता सस्पेंड हो गया है। अपना पैन कार्ड तुरंत अपडेट करें: sbi-yono-kyc.in"},
    {"id": "MSG_040", "type": "safe", "lang": "hinglish", "text": "Aapka Swiggy Instamart order raste me hai. Delivery partner 10 minute me pahuchega."}
]
OBFUSCATED_EDGE_CASES = [
    {"id": "EDGE_001", "lang": "english", "text": "Verify your account at sbí.co.in"}, # Cyrillic 'í'
    {"id": "EDGE_002", "lang": "english", "text": "Update KYC on hdfcbank.com.update-kyc.info"}, # Subdomain trick
    {"id": "EDGE_003", "lang": "english", "text": "Claim refund at lnc0metax.gov.in"}, # 'l' for 'I', '0' for 'o'
    {"id": "EDGE_004", "lang": "hindi", "text": "पैन लिंक करें: aadhar-pan-Iink.com"}, # Capital 'I' instead of 'l'
    {"id": "EDGE_005", "lang": "hinglish", "text": "Account bIocked. Login: icici-bank-secure.com"}, # Fake hyphen
    {"id": "EDGE_006", "lang": "english", "text": "Track package: indiapost.gov.in.delivery-alert.com"}, 
    {"id": "EDGE_007", "lang": "hinglish", "text": "Jio free recharge 599: j!o.com/free"}, # Symbol substitution
    {"id": "EDGE_008", "lang": "english", "text": "Secure now: 192.168.1.105/sbi-update"}, # IP address routing
    {"id": "EDGE_009", "lang": "hindi", "text": "बिजली बिल: uppcl.0rg/pay"}, # Zero instead of 'o'
    {"id": "EDGE_010", "lang": "english", "text": "Netflix billing: netfIix.com"} # Capital 'I' instead of 'l'
]
EXPECTED_RISK_TIERS = {
    # High Risk (Urgency + Phishing Link)
    "MSG_001": "High", "MSG_002": "High", "MSG_003": "High", "MSG_004": "High", 
    "MSG_006": "High", "MSG_007": "High", "MSG_008": "High", "MSG_009": "High", 
    "MSG_011": "High", "MSG_013": "High", "MSG_014": "High",
    
    # Medium Risk (Suspicious Link or Vague Urgency)
    "MSG_005": "Medium", "MSG_010": "Medium", "MSG_012": "Medium", 
    "MSG_015": "Medium", "MSG_016": "Medium",
    
    # Safe (Verified patterns, no suspicious links)
    "MSG_017": "Safe", "MSG_018": "Safe", "MSG_019": "Safe", "MSG_020": "Safe",
    "MSG_021": "Safe", "MSG_022": "Safe", "MSG_023": "Safe", "MSG_024": "Safe", 
    "MSG_025": "Safe",
    
    # Obfuscated Edge Cases (All High/Medium Risk)
    "EDGE_001": "High", "EDGE_002": "High", "EDGE_003": "High", "EDGE_004": "High",
    "EDGE_005": "Medium", "EDGE_006": "High", "EDGE_007": "High", "EDGE_008": "High",
    "EDGE_009": "High", "EDGE_010": "Medium"
}
EXPECTED_RISK_TIERS.update({
    "MSG_026": "High", "MSG_027": "High", "MSG_028": "High", "MSG_029": "Safe",
    "MSG_030": "High", "MSG_031": "High", "MSG_032": "High", "MSG_033": "Safe",
    "MSG_034": "Medium", "MSG_035": "Medium", "MSG_036": "Medium", 
    "MSG_037": "High", "MSG_038": "Safe", "MSG_039": "High", "MSG_040": "Safe"
})