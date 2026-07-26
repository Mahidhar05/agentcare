# services/translations.py
"""
Multi-language translations for AgentCare UI, emails, and AI responses.
Supports English, Hindi, Tamil, Telugu.
"""

TRANSLATIONS = {
    "en": {
        # ─── Common ─────────────────────────────
        "app_name": "AgentCare",
        "sign_in": "Sign In",
        "sign_out": "Sign Out",
        "tab_login": "Login",
        "tab_register": "Register as Patient",
        "welcome": "Welcome",
        "loading": "Loading...",
        "save": "Save",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "delete": "Delete",
        "edit": "Edit",
        "search": "Search",
        "filter": "Filter",
        "submit": "Submit",
        "back": "Back",
        "next": "Next",
        "close": "Close",
        "yes": "Yes",
        "no": "No",

        # ── Login Hero Panel ──
        "login_hero_badge": "✨ HACKATHON 2026 · TOP SUBMISSION",
        "login_brand_sub": "AI HEALTHCARE PLATFORM",
        "login_headline_1": "Your Care Journey,",
        "login_headline_2": "Orchestrated by AI.",
        "login_tagline": "8 specialized AI agents working together to handle registration, appointments, documents, reminders & escalations — safely and instantly.",
        "feature_agents_title": "8 AI Agents",
        "feature_agents_sub": "Orchestrated",
        "feature_voice_title": "Voice Input",
        "feature_voice_sub": "Whisper AI",
        "feature_lang_title": "4 Languages",
        "feature_lang_sub": "Multilingual",
        "feature_rag_title": "RAG Powered",
        "feature_rag_sub": "Knowledge Base",
        "feature_safety_title": "Safety Guard",
        "feature_safety_sub": "Human Oversight",
        "feature_realtime_title": "Real-Time",
        "feature_realtime_sub": "Escalations",
        "trust_jwt": "🔒 JWT Secured",
        "trust_audit": "📊 Full Audit Trail",
        "trust_admin": "⚕️ Admin-Only Scope",
        "instant_demo_access": "Instant Demo Access",
        "click_any_button": "Click any button to log in instantly — no typing needed.",
        "patient_portal_label": "Patient Portal",
        "staff_portal_label": "Staff Portal",
        "login_as_patient": "Login as Patient",
        "login_as_staff": "Login as Staff",
        "footer_built_for": "Built for AgentCare Build Challenge 2026",
        "footer_disclaimer": "⚠️ Administrative AI Only · Does NOT provide medical advice, diagnosis, or treatment",
        "hero_badge": "⚡ Powered by 8 AI Agents · RAG · Voice · 4 Languages",
        "brand_name": "AgentCare",

        # ─── Register Page ──────────────────────
        "create_account": "Create Your Account",
        "join_message": "Join AgentCare to manage your appointments seamlessly",
        "full_name": "Full Name",
        "dob_format": "DOB (YYYY-MM-DD)",
        "password": "Password",
        "enter_credentials": "Enter your credentials to continue",
        "navigation": "Navigation",
        
        # ─── Quick Actions Sub-labels ───────────
        "ask_anything": "Ask anything",
        "schedule_now": "Schedule now",
        "share_records": "Share records",
        "welcome_back": "Welcome back!",
        
        # ─── Navigation ─────────────────────────
        "nav_dashboard": "Dashboard",
        "nav_ai_assistant": "AI Assistant",
        "nav_appointments": "Appointments",
        "nav_documents": "Documents",
        "nav_reminders": "Reminders",
        "nav_notifications": "My Notifications",
        "nav_profile": "Profile",
        "nav_analytics": "Analytics",
        "nav_search": "Search & Filter",
        "nav_patients": "Patients",
        "nav_doctors": "Doctors",
        "nav_departments": "Departments",
        
        # ─── Dashboard ──────────────────────────
        "dashboard_welcome": "Welcome back",
        "your_overview": "Your Overview",
        "total_appointments": "Total Appointments",
        "active_appointments": "Active Appointments",
        "documents_uploaded": "Documents Uploaded",
        "ai_requests": "AI Requests",
        "upcoming_appointments": "Upcoming Appointments",
        "quick_actions": "Quick Actions",
        
        # ─── AI Assistant ───────────────────────
        "ai_assistant_title": "AI Assistant Chat",
        "chat_placeholder": "Type your message here...",
        "quick_suggestions": "Quick suggestions",
        "new_chat": "New Chat",
        "attach_document": "Attach a medical document",
        
        # ─── Appointments ───────────────────────
        "book_appointment": "Book Appointment",
        "reschedule": "Reschedule",
        "cancel_appt": "Cancel",
        "appointment_confirmed": "Appointment Confirmed",
        "appointment_letter_sent": "Appointment letter sent to your email",
        "doctor": "Doctor",
        "date": "Date",
        "time": "Time",
        "status": "Status",
        "reason": "Reason",

        # ─── Appointment Card Labels ────────────
        "appt_date": "DATE",
        "appt_time": "TIME",
        "appt_id_label": "APPOINTMENT ID",
        "appt_reason_label": "REASON",
        "status_confirmed": "CONFIRMED",
        "status_pending": "PENDING",
        "status_cancelled": "CANCELLED",
        "status_completed": "COMPLETED",
        "status_rescheduled": "RESCHEDULED",
        "powered_by": "Powered by",
        "ai_agents": "AI Agents",

        # ─── Appointment List Labels ────────────
        "showing_appointments": "Showing",
        "appointments_count": "appointment(s)",
        "filter_by_status": "Filter by status",
        "no_appointments": "No appointments found",
        "no_appointments_yet": "No appointments yet",
        "cancel_appointment_btn": "Cancel Appointment",
        "book_first_appt": "Use the AI Assistant to book your first appointment!",
        
        # ─── Profile ────────────────────────────
        "my_profile": "My Profile",
        "update_profile": "Update Profile",
        "name": "Name",
        "email": "Email",
        "phone": "Phone",
        "age": "Age",
        "gender": "Gender",
        "date_of_birth": "Date of Birth",
        "blood_group": "Blood Group",
        "address": "Address",
        "emergency_contact": "Emergency Contact",
        "preferred_language": "Preferred Language",
        
        # ─── Messages ───────────────────────────
        "success": "Success",
        "error": "Error",
        "warning": "Warning",
        "info": "Information",
        "please_provide": "Please provide",
        "no_data": "No data available",
        
        # ─── Email Templates ────────────────────
        "email_greeting": "Dear",
        "email_appt_confirmed_subject": "Appointment Confirmed",
        "email_appt_confirmed_body": "Your appointment has been successfully scheduled",
        "email_appt_details": "Appointment Details",
        "email_instructions": "Important Instructions",
        "email_arrive_early": "Please arrive 15 minutes early",
        "email_bring_id": "Bring a valid photo ID",
        "email_bring_records": "Bring any previous medical records",
        "email_reschedule_subject": "Appointment Rescheduled",
        "email_cancel_subject": "Appointment Cancelled",
        "email_document_received": "Document Received",
        "email_signature": "AgentCare Team",
    },
    
    "hi": {  # Hindi
        # ─── Common ─────────────────────────────
        "app_name": "एजेंटकेयर",
        "sign_in": "साइन इन करें",
        "sign_out": "साइन आउट करें",
        "welcome": "स्वागत है",
        "loading": "लोड हो रहा है...",
        "save": "सहेजें",
        "cancel": "रद्द करें",
        "confirm": "पुष्टि करें",
        "delete": "हटाएं",
        "edit": "संपादित करें",
        "search": "खोजें",
        "filter": "फिल्टर",
        "submit": "जमा करें",
        "back": "वापस",
        "next": "अगला",
        "close": "बंद करें",
        "yes": "हाँ",
        "no": "नहीं",
        "tab_login": "लॉगिन",
        "tab_register": "मरीज़ के रूप में पंजीकरण करें",

                # ── Login Hero Panel ──
        "login_hero_badge": "✨ हैकाथॉन 2026 · शीर्ष सबमिशन",
        "login_brand_sub": "एआई हेल्थकेयर प्लेटफ़ॉर्म",
        "login_headline_1": "आपकी देखभाल यात्रा,",
        "login_headline_2": "एआई द्वारा संचालित।",
        "login_tagline": "8 विशेष एआई एजेंट पंजीकरण, अपॉइंटमेंट, दस्तावेज़, अनुस्मारक और एस्केलेशन को सुरक्षित रूप से और तुरंत संभालने के लिए एक साथ काम करते हैं।",
        "feature_agents_title": "8 एआई एजेंट",
        "feature_agents_sub": "व्यवस्थित",
        "feature_voice_title": "आवाज़ इनपुट",
        "feature_voice_sub": "व्हिस्पर एआई",
        "feature_lang_title": "4 भाषाएँ",
        "feature_lang_sub": "बहुभाषी",
        "feature_rag_title": "आरएजी संचालित",
        "feature_rag_sub": "ज्ञान आधार",
        "feature_safety_title": "सुरक्षा गार्ड",
        "feature_safety_sub": "मानव निरीक्षण",
        "feature_realtime_title": "रीयल-टाइम",
        "feature_realtime_sub": "एस्केलेशन",
        "trust_jwt": "🔒 जेडब्ल्यूटी सुरक्षित",
        "trust_audit": "📊 पूर्ण ऑडिट ट्रेल",
        "trust_admin": "⚕️ केवल-व्यवस्थापक स्कोप",
        "instant_demo_access": "तत्काल डेमो एक्सेस",
        "click_any_button": "तुरंत लॉग इन करने के लिए किसी भी बटन पर क्लिक करें — टाइप करने की आवश्यकता नहीं।",
        "patient_portal_label": "रोगी पोर्टल",
        "staff_portal_label": "स्टाफ़ पोर्टल",
        "login_as_patient": "रोगी के रूप में लॉगिन करें",
        "login_as_staff": "स्टाफ़ के रूप में लॉगिन करें",
        "footer_built_for": "एजेंटकेयर बिल्ड चैलेंज 2026 के लिए निर्मित",
        "footer_disclaimer": "⚠️ केवल प्रशासनिक एआई · चिकित्सा सलाह, निदान या उपचार प्रदान नहीं करता",
        "hero_badge": "⚡ 8 एआई एजेंट्स द्वारा संचालित · आरएजी · आवाज़ · 4 भाषाएँ",
        "brand_name": "एजेंटकेयर",
        
        # ─── Navigation ─────────────────────────
        "nav_dashboard": "डैशबोर्ड",
        "nav_ai_assistant": "एआई सहायक",
        "nav_appointments": "अपॉइंटमेंट",
        "nav_documents": "दस्तावेज़",
        "nav_reminders": "अनुस्मारक",
        "nav_notifications": "मेरी सूचनाएं",
        "nav_profile": "प्रोफ़ाइल",
        "nav_analytics": "विश्लेषण",
        "nav_search": "खोज एवं फ़िल्टर",
        "nav_patients": "मरीज़",
        "nav_doctors": "डॉक्टर",
        "nav_departments": "विभाग",

        # ─── Appointment Card Labels ────────────
        "appt_date": "तारीख़",
        "appt_time": "समय",
        "appt_id_label": "अपॉइंटमेंट आईडी",
        "appt_reason_label": "कारण",
        "status_confirmed": "पुष्ट",
        "status_pending": "लंबित",
        "status_cancelled": "रद्द",
        "status_completed": "पूर्ण",
        "status_rescheduled": "पुनर्निर्धारित",
        "powered_by": "द्वारा संचालित",
        "ai_agents": "एआई एजेंट्स",

        # ─── Appointment List Labels ────────────
        "showing_appointments": "दिखा रहे हैं",
        "appointments_count": "अपॉइंटमेंट",
        "filter_by_status": "स्थिति के अनुसार फ़िल्टर करें",
        "no_appointments": "कोई अपॉइंटमेंट नहीं मिली",
        "no_appointments_yet": "अभी तक कोई अपॉइंटमेंट नहीं",
        "cancel_appointment_btn": "अपॉइंटमेंट रद्द करें",
        "book_first_appt": "अपनी पहली अपॉइंटमेंट बुक करने के लिए AI सहायक का उपयोग करें!",
        
        # ─── Dashboard ──────────────────────────
        "dashboard_welcome": "वापसी पर स्वागत है",
        "your_overview": "आपका अवलोकन",
        "total_appointments": "कुल अपॉइंटमेंट",
        "active_appointments": "सक्रिय अपॉइंटमेंट",
        "documents_uploaded": "अपलोड किए गए दस्तावेज़",
        "ai_requests": "एआई अनुरोध",
        "upcoming_appointments": "आगामी अपॉइंटमेंट",
        "quick_actions": "त्वरित कार्रवाई",
        
        # ─── AI Assistant ───────────────────────
        "ai_assistant_title": "एआई सहायक चैट",
        "chat_placeholder": "यहां अपना संदेश लिखें...",
        "quick_suggestions": "त्वरित सुझाव",
        "new_chat": "नई चैट",
        "attach_document": "एक चिकित्सा दस्तावेज़ संलग्न करें",

        # ─── Register Page ──────────────────────
        "create_account": "अपना खाता बनाएँ",
        "join_message": "अपनी अपॉइंटमेंट को आसानी से प्रबंधित करने के लिए एजेंटकेयर से जुड़ें",
        "full_name": "पूरा नाम",
        "dob_format": "जन्म तिथि (YYYY-MM-DD)",
        "password": "पासवर्ड",
        "enter_credentials": "जारी रखने के लिए अपनी साख दर्ज करें",
        "navigation": "नेविगेशन",
        
        # ─── Quick Actions Sub-labels ───────────
        "ask_anything": "कुछ भी पूछें",
        "schedule_now": "अभी शेड्यूल करें",
        "share_records": "रिकॉर्ड साझा करें",
        "welcome_back": "वापस स्वागत है!",
        
        # ─── Appointments ───────────────────────
        "book_appointment": "अपॉइंटमेंट बुक करें",
        "reschedule": "पुनर्निर्धारित करें",
        "cancel_appt": "रद्द करें",
        "appointment_confirmed": "अपॉइंटमेंट की पुष्टि हो गई",
        "appointment_letter_sent": "अपॉइंटमेंट पत्र आपके ईमेल पर भेजा गया",
        "doctor": "डॉक्टर",
        "date": "तारीख",
        "time": "समय",
        "status": "स्थिति",
        "reason": "कारण",
        
        # ─── Profile ────────────────────────────
        "my_profile": "मेरी प्रोफ़ाइल",
        "update_profile": "प्रोफ़ाइल अपडेट करें",
        "name": "नाम",
        "email": "ईमेल",
        "phone": "फ़ोन",
        "age": "आयु",
        "gender": "लिंग",
        "date_of_birth": "जन्म तिथि",
        "blood_group": "रक्त समूह",
        "address": "पता",
        "emergency_contact": "आपातकालीन संपर्क",
        "preferred_language": "पसंदीदा भाषा",
        
        # ─── Messages ───────────────────────────
        "success": "सफलता",
        "error": "त्रुटि",
        "warning": "चेतावनी",
        "info": "जानकारी",
        "please_provide": "कृपया प्रदान करें",
        "no_data": "कोई डेटा उपलब्ध नहीं",
        
        # ─── Email Templates ────────────────────
        "email_greeting": "प्रिय",
        "email_appt_confirmed_subject": "अपॉइंटमेंट पुष्टि",
        "email_appt_confirmed_body": "आपका अपॉइंटमेंट सफलतापूर्वक निर्धारित हो गया है",
        "email_appt_details": "अपॉइंटमेंट विवरण",
        "email_instructions": "महत्वपूर्ण निर्देश",
        "email_arrive_early": "कृपया 15 मिनट पहले पहुँचें",
        "email_bring_id": "एक वैध फोटो आईडी लाएं",
        "email_bring_records": "पिछले चिकित्सा रिकॉर्ड लाएं",
        "email_reschedule_subject": "अपॉइंटमेंट पुनर्निर्धारित",
        "email_cancel_subject": "अपॉइंटमेंट रद्द",
        "email_document_received": "दस्तावेज़ प्राप्त",
        "email_signature": "एजेंटकेयर टीम",
    },
    
    "ta": {  # Tamil
        # ─── Common ─────────────────────────────
        "app_name": "ஏஜென்ட்கேர்",
        "sign_in": "உள்நுழைக",
        "sign_out": "வெளியேறு",
        "tab_login": "உள்நுழைவு",
        "tab_register": "நோயாளியாக பதிவு",
        "welcome": "வரவேற்கிறோம்",
        "loading": "ஏற்றுகிறது...",
        "save": "சேமி",
        "cancel": "ரத்து",
        "confirm": "உறுதி",
        "delete": "நீக்கு",
        "edit": "திருத்து",
        "search": "தேடு",
        "filter": "வடிகட்டி",
        "submit": "சமர்ப்பி",
        "back": "பின்",
        "next": "அடுத்து",
        "close": "மூடு",
        "yes": "ஆம்",
        "no": "இல்லை",

                # ── Login Hero Panel ──
        "login_hero_badge": "✨ ஹேக்கத்தான் 2026 · சிறந்த சமர்ப்பிப்பு",
        "login_brand_sub": "ஏஐ சுகாதார தளம்",
        "login_headline_1": "உங்கள் பராமரிப்பு பயணம்,",
        "login_headline_2": "ஏஐ-ஆல் ஒழுங்கமைக்கப்பட்டது.",
        "login_tagline": "8 சிறப்பு ஏஐ முகவர்கள் பதிவு, சந்திப்புகள், ஆவணங்கள், நினைவூட்டல்கள் மற்றும் அதிகரிப்புகளைப் பாதுகாப்பாகவும் உடனடியாகவும் கையாள ஒன்றாக வேலை செய்கின்றனர்.",
        "feature_agents_title": "8 ஏஐ முகவர்கள்",
        "feature_agents_sub": "ஒழுங்கமைக்கப்பட்டது",
        "feature_voice_title": "குரல் உள்ளீடு",
        "feature_voice_sub": "விஸ்பர் ஏஐ",
        "feature_lang_title": "4 மொழிகள்",
        "feature_lang_sub": "பன்மொழி",
        "feature_rag_title": "ஆர்ஏஜி இயக்கப்பட்டது",
        "feature_rag_sub": "அறிவுத் தளம்",
        "feature_safety_title": "பாதுகாப்பு காவலர்",
        "feature_safety_sub": "மனித மேற்பார்வை",
        "feature_realtime_title": "நிகழ்நேரம்",
        "feature_realtime_sub": "அதிகரிப்புகள்",
        "trust_jwt": "🔒 ஜேடபிள்யூடி பாதுகாக்கப்பட்டது",
        "trust_audit": "📊 முழு தணிக்கை பாதை",
        "trust_admin": "⚕️ நிர்வாகி-மட்டும் நோக்கம்",
        "instant_demo_access": "உடனடி டெமோ அணுகல்",
        "click_any_button": "உடனடியாக உள்நுழைய எந்த பொத்தானையும் கிளிக் செய்யவும் — தட்டச்சு தேவையில்லை.",
        "patient_portal_label": "நோயாளி வாசல்",
        "staff_portal_label": "பணியாளர் வாசல்",
        "login_as_patient": "நோயாளியாக உள்நுழையவும்",
        "login_as_staff": "பணியாளராக உள்நுழையவும்",
        "footer_built_for": "ஏஜென்ட்கேர் பில்ட் சேலஞ்ச் 2026 க்காக கட்டப்பட்டது",
        "footer_disclaimer": "⚠️ நிர்வாக ஏஐ மட்டுமே · மருத்துவ ஆலோசனை, நோய் கண்டறிதல் அல்லது சிகிச்சை வழங்கவில்லை",
        "hero_badge": "⚡ 8 ஏஐ முகவர்களால் இயக்கப்படுகிறது · ஆர்ஏஜி · குரல் · 4 மொழிகள்",
        "brand_name": "ஏஜென்ட்கேர்",

        # ─── Appointment Card Labels ────────────
        "appt_date": "தேதி",
        "appt_time": "நேரம்",
        "appt_id_label": "நேர எண்",
        "appt_reason_label": "காரணம்",
        "status_confirmed": "உறுதிப்படுத்தப்பட்டது",
        "status_pending": "நிலுவையில்",
        "status_cancelled": "ரத்து",
        "status_completed": "முடிந்தது",
        "status_rescheduled": "மறு-திட்டமிடப்பட்டது",
        "powered_by": "இயக்குகிறது",
        "ai_agents": "AI முகவர்கள்",

        # ─── Appointment List Labels ────────────
        "showing_appointments": "காட்டுகிறது",
        "appointments_count": "நேரம்(ங்கள்)",
        "filter_by_status": "நிலை மூலம் வடிகட்டு",
        "no_appointments": "நேரம் இல்லை",
        "no_appointments_yet": "இதுவரை நேரம் இல்லை",
        "cancel_appointment_btn": "நேரத்தை ரத்து செய்",
        "book_first_appt": "உங்கள் முதல் நேரத்தை முன்பதிவு செய்ய AI உதவியாளரைப் பயன்படுத்தவும்!",
        
        # ─── Navigation ─────────────────────────
        "nav_dashboard": "டாஷ்போர்டு",
        "nav_ai_assistant": "AI உதவியாளர்",
        "nav_appointments": "நேரங்கள்",
        "nav_documents": "ஆவணங்கள்",
        "nav_reminders": "நினைவூட்டல்கள்",
        "nav_notifications": "என் அறிவிப்புகள்",
        "nav_profile": "சுயவிவரம்",
        "nav_analytics": "பகுப்பாய்வு",
        "nav_search": "தேடல் மற்றும் வடிகட்டி",
        "nav_patients": "நோயாளிகள்",
        "nav_doctors": "மருத்துவர்கள்",
        "nav_departments": "துறைகள்",

        # ─── Register Page ──────────────────────
        "create_account": "உங்கள் கணக்கை உருவாக்கவும்",
        "join_message": "உங்கள் நேரங்களை எளிதாக நிர்வகிக்க ஏஜென்ட்கேரில் சேரவும்",
        "full_name": "முழு பெயர்",
        "dob_format": "பிறந்த தேதி (YYYY-MM-DD)",
        "password": "கடவுச்சொல்",
        "enter_credentials": "தொடர உங்கள் அடையாளங்களை உள்ளிடவும்",
        "navigation": "வழிசெலுத்தல்",
        
        # ─── Quick Actions Sub-labels ───────────
        "ask_anything": "எதையும் கேளுங்கள்",
        "schedule_now": "இப்போது திட்டமிடுங்கள்",
        "share_records": "பதிவுகளை பகிரவும்",
        "welcome_back": "மீண்டும் வரவேற்கிறோம்!",
        
        # ─── Dashboard ──────────────────────────
        "dashboard_welcome": "மீண்டும் வரவேற்கிறோம்",
        "your_overview": "உங்கள் மேலோட்டம்",
        "total_appointments": "மொத்த நேரங்கள்",
        "active_appointments": "செயலில் உள்ள நேரங்கள்",
        "documents_uploaded": "பதிவேற்றப்பட்ட ஆவணங்கள்",
        "ai_requests": "AI கோரிக்கைகள்",
        "upcoming_appointments": "வரவிருக்கும் நேரங்கள்",
        "quick_actions": "விரைவு செயல்கள்",
        
        # ─── AI Assistant ───────────────────────
        "ai_assistant_title": "AI உதவியாளர் அரட்டை",
        "chat_placeholder": "உங்கள் செய்தியை இங்கே தட்டச்சு செய்யவும்...",
        "quick_suggestions": "விரைவு பரிந்துரைகள்",
        "new_chat": "புதிய அரட்டை",
        "attach_document": "மருத்துவ ஆவணத்தை இணைக்கவும்",
        
        # ─── Appointments ───────────────────────
        "book_appointment": "நேரம் முன்பதிவு",
        "reschedule": "மறு-நேரம்",
        "cancel_appt": "ரத்து",
        "appointment_confirmed": "நேரம் உறுதிப்படுத்தப்பட்டது",
        "appointment_letter_sent": "நேர கடிதம் உங்கள் மின்னஞ்சலுக்கு அனுப்பப்பட்டது",
        "doctor": "மருத்துவர்",
        "date": "தேதி",
        "time": "நேரம்",
        "status": "நிலை",
        "reason": "காரணம்",
        
        # ─── Profile ────────────────────────────
        "my_profile": "என் சுயவிவரம்",
        "update_profile": "சுயவிவரத்தை புதுப்பிக்கவும்",
        "name": "பெயர்",
        "email": "மின்னஞ்சல்",
        "phone": "தொலைபேசி",
        "age": "வயது",
        "gender": "பாலினம்",
        "date_of_birth": "பிறந்த தேதி",
        "blood_group": "இரத்த வகை",
        "address": "முகவரி",
        "emergency_contact": "அவசர தொடர்பு",
        "preferred_language": "விருப்பமான மொழி",
        
        # ─── Messages ───────────────────────────
        "success": "வெற்றி",
        "error": "பிழை",
        "warning": "எச்சரிக்கை",
        "info": "தகவல்",
        "please_provide": "வழங்கவும்",
        "no_data": "தரவு இல்லை",
        
        # ─── Email Templates ────────────────────
        "email_greeting": "அன்பான",
        "email_appt_confirmed_subject": "நேரம் உறுதிப்படுத்தப்பட்டது",
        "email_appt_confirmed_body": "உங்கள் நேரம் வெற்றிகரமாக திட்டமிடப்பட்டது",
        "email_appt_details": "நேர விவரங்கள்",
        "email_instructions": "முக்கியமான வழிமுறைகள்",
        "email_arrive_early": "தயவுசெய்து 15 நிமிடங்கள் முன்னதாக வாருங்கள்",
        "email_bring_id": "செல்லுபடியாகும் புகைப்பட அடையாள அட்டையை கொண்டு வாருங்கள்",
        "email_bring_records": "முந்தைய மருத்துவ பதிவுகளை கொண்டு வாருங்கள்",
        "email_reschedule_subject": "நேரம் மறு-திட்டமிடப்பட்டது",
        "email_cancel_subject": "நேரம் ரத்து",
        "email_document_received": "ஆவணம் பெறப்பட்டது",
        "email_signature": "ஏஜென்ட்கேர் குழு",
    },
    
    "te": {  # Telugu
        # ─── Common ─────────────────────────────
        "app_name": "ఏజెంట్‌కేర్",
        "sign_in": "సైన్ ఇన్",
        "sign_out": "సైన్ అవుట్",
        "tab_login": "లాగిన్",
        "tab_register": "రోగిగా నమోదు",
        "welcome": "స్వాగతం",
        "loading": "లోడ్ అవుతోంది...",
        "save": "సేవ్",
        "cancel": "రద్దు",
        "confirm": "నిర్ధారించండి",
        "delete": "తొలగించండి",
        "edit": "సవరించండి",
        "search": "శోధించండి",
        "filter": "వడపోత",
        "submit": "సమర్పించండి",
        "back": "వెనుకకు",
        "next": "తదుపరి",
        "close": "మూసివేయండి",
        "yes": "అవును",
        "no": "కాదు",

                # ── Login Hero Panel ──
        "login_hero_badge": "✨ హ్యాకథాన్ 2026 · అగ్ర సమర్పణ",
        "login_brand_sub": "ఏఐ హెల్త్‌కేర్ ప్లాట్‌ఫారమ్",
        "login_headline_1": "మీ సంరక్షణ ప్రయాణం,",
        "login_headline_2": "ఏఐ ద్వారా నిర్వహించబడింది.",
        "login_tagline": "8 ప్రత్యేక ఏఐ ఏజెంట్‌లు నమోదు, అపాయింట్‌మెంట్‌లు, పత్రాలు, రిమైండర్‌లు మరియు ఎస్కలేషన్‌లను సురక్షితంగా మరియు తక్షణమే నిర్వహించడానికి కలిసి పనిచేస్తారు.",
        "feature_agents_title": "8 ఏఐ ఏజెంట్లు",
        "feature_agents_sub": "నిర్వహించబడింది",
        "feature_voice_title": "వాయిస్ ఇన్‌పుట్",
        "feature_voice_sub": "విస్పర్ ఏఐ",
        "feature_lang_title": "4 భాషలు",
        "feature_lang_sub": "బహుభాషా",
        "feature_rag_title": "ఆర్ఏజీ శక్తితో",
        "feature_rag_sub": "నాలెడ్జ్ బేస్",
        "feature_safety_title": "భద్రతా గార్డు",
        "feature_safety_sub": "మానవ పర్యవేక్షణ",
        "feature_realtime_title": "రియల్-టైమ్",
        "feature_realtime_sub": "ఎస్కలేషన్లు",
        "trust_jwt": "🔒 జేడబ్ల్యూటీ భద్రపరచబడింది",
        "trust_audit": "📊 పూర్తి ఆడిట్ ట్రయల్",
        "trust_admin": "⚕️ నిర్వాహక-మాత్రమే పరిధి",
        "instant_demo_access": "తక్షణ డెమో యాక్సెస్",
        "click_any_button": "తక్షణమే లాగిన్ చేయడానికి ఏదైనా బటన్‌ను క్లిక్ చేయండి — టైప్ చేయవలసిన అవసరం లేదు.",
        "patient_portal_label": "రోగి పోర్టల్",
        "staff_portal_label": "సిబ్బంది పోర్టల్",
        "login_as_patient": "రోగిగా లాగిన్ చేయండి",
        "login_as_staff": "సిబ్బందిగా లాగిన్ చేయండి",
        "footer_built_for": "ఏజెంట్‌కేర్ బిల్డ్ ఛాలెంజ్ 2026 కోసం నిర్మించబడింది",
        "footer_disclaimer": "⚠️ పరిపాలనా ఏఐ మాత్రమే · వైద్య సలహా, నిర్ధారణ లేదా చికిత్సను అందించదు",
        "hero_badge": "⚡ 8 ఏఐ ఏజెంట్లచే శక్తిని పొందింది · ఆర్ఏజీ · వాయిస్ · 4 భాషలు",
        "brand_name": "ఏజెంట్‌కేర్",

        # ─── Register Page ──────────────────────
        "create_account": "మీ ఖాతాను సృష్టించండి",
        "join_message": "మీ అపాయింట్‌మెంట్‌లను సులభంగా నిర్వహించడానికి ఏజెంట్‌కేర్‌లో చేరండి",
        "full_name": "పూర్తి పేరు",
        "dob_format": "పుట్టిన తేదీ (YYYY-MM-DD)",
        "password": "పాస్‌వర్డ్",
        "enter_credentials": "కొనసాగించడానికి మీ ఆధారాలను నమోదు చేయండి",
        "navigation": "నావిగేషన్",
        
        # ─── Quick Actions Sub-labels ───────────
        "ask_anything": "ఏదైనా అడగండి",
        "schedule_now": "ఇప్పుడు షెడ్యూల్ చేయండి",
        "share_records": "రికార్డ్‌లను షేర్ చేయండి",
        "welcome_back": "తిరిగి స్వాగతం!",

        # ─── Appointment List Labels ────────────
        "showing_appointments": "చూపిస్తోంది",
        "appointments_count": "అపాయింట్‌మెంట్(లు)",
        "filter_by_status": "స్థితి ద్వారా ఫిల్టర్",
        "no_appointments": "అపాయింట్‌మెంట్‌లు కనుగొనబడలేదు",
        "no_appointments_yet": "ఇంకా అపాయింట్‌మెంట్‌లు లేవు",
        "cancel_appointment_btn": "అపాయింట్‌మెంట్ రద్దు",
        "book_first_appt": "మీ మొదటి అపాయింట్‌మెంట్‌ను బుక్ చేయడానికి AI అసిస్టెంట్‌ను ఉపయోగించండి!",

        # ─── Appointment Card Labels ────────────
        "appt_date": "తేదీ",
        "appt_time": "సమయం",
        "appt_id_label": "అపాయింట్‌మెంట్ ID",
        "appt_reason_label": "కారణం",
        "status_confirmed": "నిర్ధారించబడింది",
        "status_pending": "పెండింగ్",
        "status_cancelled": "రద్దు",
        "status_completed": "పూర్తయింది",
        "status_rescheduled": "రీషెడ్యూల్",
        "powered_by": "శక్తినిచ్చినది",
        "ai_agents": "AI ఏజెంట్‌లు",
        
        # ─── Navigation ─────────────────────────
        "nav_dashboard": "డాష్‌బోర్డ్",
        "nav_ai_assistant": "AI అసిస్టెంట్",
        "nav_appointments": "అపాయింట్‌మెంట్‌లు",
        "nav_documents": "పత్రాలు",
        "nav_reminders": "రిమైండర్‌లు",
        "nav_notifications": "నా నోటిఫికేషన్‌లు",
        "nav_profile": "ప్రొఫైల్",
        "nav_analytics": "విశ్లేషణలు",
        "nav_search": "శోధన & ఫిల్టర్",
        "nav_patients": "రోగులు",
        "nav_doctors": "వైద్యులు",
        "nav_departments": "విభాగాలు",
        
        # ─── Dashboard ──────────────────────────
        "dashboard_welcome": "తిరిగి స్వాగతం",
        "your_overview": "మీ అవలోకనం",
        "total_appointments": "మొత్తం అపాయింట్‌మెంట్‌లు",
        "active_appointments": "క్రియాశీల అపాయింట్‌మెంట్‌లు",
        "documents_uploaded": "అప్‌లోడ్ చేసిన పత్రాలు",
        "ai_requests": "AI అభ్యర్థనలు",
        "upcoming_appointments": "రాబోయే అపాయింట్‌మెంట్‌లు",
        "quick_actions": "త్వరిత చర్యలు",
        
        # ─── AI Assistant ───────────────────────
        "ai_assistant_title": "AI అసిస్టెంట్ చాట్",
        "chat_placeholder": "మీ సందేశాన్ని ఇక్కడ టైప్ చేయండి...",
        "quick_suggestions": "త్వరిత సూచనలు",
        "new_chat": "కొత్త చాట్",
        "attach_document": "వైద్య పత్రాన్ని జోడించండి",
        
        # ─── Appointments ───────────────────────
        "book_appointment": "అపాయింట్‌మెంట్ బుక్ చేయండి",
        "reschedule": "రీషెడ్యూల్",
        "cancel_appt": "రద్దు",
        "appointment_confirmed": "అపాయింట్‌మెంట్ నిర్ధారించబడింది",
        "appointment_letter_sent": "అపాయింట్‌మెంట్ లేఖ మీ ఇమెయిల్‌కు పంపబడింది",
        "doctor": "వైద్యుడు",
        "date": "తేదీ",
        "time": "సమయం",
        "status": "స్థితి",
        "reason": "కారణం",
        
        # ─── Profile ────────────────────────────
        "my_profile": "నా ప్రొఫైల్",
        "update_profile": "ప్రొఫైల్‌ను నవీకరించండి",
        "name": "పేరు",
        "email": "ఇమెయిల్",
        "phone": "ఫోన్",
        "age": "వయసు",
        "gender": "లింగం",
        "date_of_birth": "పుట్టిన తేదీ",
        "blood_group": "రక్త వర్గం",
        "address": "చిరునామా",
        "emergency_contact": "అత్యవసర సంప్రదింపు",
        "preferred_language": "ప్రాధాన్య భాష",
        
        # ─── Messages ───────────────────────────
        "success": "విజయం",
        "error": "లోపం",
        "warning": "హెచ్చరిక",
        "info": "సమాచారం",
        "please_provide": "దయచేసి అందించండి",
        "no_data": "డేటా అందుబాటులో లేదు",
        
        # ─── Email Templates ────────────────────
        "email_greeting": "ప్రియమైన",
        "email_appt_confirmed_subject": "అపాయింట్‌మెంట్ నిర్ధారించబడింది",
        "email_appt_confirmed_body": "మీ అపాయింట్‌మెంట్ విజయవంతంగా షెడ్యూల్ చేయబడింది",
        "email_appt_details": "అపాయింట్‌మెంట్ వివరాలు",
        "email_instructions": "ముఖ్యమైన సూచనలు",
        "email_arrive_early": "దయచేసి 15 నిమిషాల ముందు రండి",
        "email_bring_id": "చెల్లుబాటు అయ్యే ఫోటో ID తీసుకురండి",
        "email_bring_records": "మునుపటి వైద్య రికార్డులను తీసుకురండి",
        "email_reschedule_subject": "అపాయింట్‌మెంట్ రీషెడ్యూల్ చేయబడింది",
        "email_cancel_subject": "అపాయింట్‌మెంట్ రద్దు చేయబడింది",
        "email_document_received": "పత్రం స్వీకరించబడింది",
        "email_signature": "ఏజెంట్‌కేర్ బృందం",
    },
}


# ─── Available languages ─────────────────────────────
LANGUAGES = {
    "en": {"name": "English", "flag": "🇬🇧"},
    "hi": {"name": "हिंदी", "flag": "🇮🇳"},
    "ta": {"name": "தமிழ்", "flag": "🇮🇳"},
    "te": {"name": "తెలుగు", "flag": "🇮🇳"},
}


def t(key: str, lang: str = "en") -> str:
    """
    Translate a key to the specified language.
    Falls back to English if key/lang not found.
    """
    lang = lang.lower() if lang else "en"
    if lang not in TRANSLATIONS:
        lang = "en"
    
    return TRANSLATIONS.get(lang, {}).get(
        key,
        TRANSLATIONS["en"].get(key, key)
    )


def get_language_name(lang_code: str) -> str:
    """Get display name for a language code."""
    return LANGUAGES.get(lang_code, {"name": "English"})["name"]


def get_language_flag(lang_code: str) -> str:
    """Get flag emoji for a language code."""
    return LANGUAGES.get(lang_code, {"flag": "🇬🇧"})["flag"]


def get_supported_languages() -> dict:
    """Returns dict of all supported languages."""
    return LANGUAGES

# ═══════════════════════════════════════════════════════════════
# DYNAMIC CONTENT TRANSLATIONS
# ═══════════════════════════════════════════════════════════════

DOCTOR_NAMES = {
    "en": {
        "Dr. Aisha Sharma":    "Dr. Aisha Sharma",
        "Dr. Rajan Mehta":     "Dr. Rajan Mehta",
        "Dr. Priya Nair":      "Dr. Priya Nair",
        "Dr. Samuel D'souza":  "Dr. Samuel D'souza",
        "Dr. Kavita Joshi":    "Dr. Kavita Joshi",
        "Dr. Arjun Patel":     "Dr. Arjun Patel",
        "Dr. Meena Krishnan":  "Dr. Meena Krishnan",
        "Dr. Vikram Reddy":    "Dr. Vikram Reddy",
        "Dr. Sunita Agarwal":  "Dr. Sunita Agarwal",
        "Dr. Farah Sheikh":    "Dr. Farah Sheikh",
        "Dr. Rohit Gupta":     "Dr. Rohit Gupta",
        "Dr. Ananya Pillai":   "Dr. Ananya Pillai",
        "Dr. Deepa Iyer":      "Dr. Deepa Iyer",
        "Dr. Nikhil Bose":     "Dr. Nikhil Bose",
    },
    "hi": {
        "Dr. Aisha Sharma":    "डॉ. आयशा शर्मा",
        "Dr. Rajan Mehta":     "डॉ. राजन मेहता",
        "Dr. Priya Nair":      "डॉ. प्रिया नायर",
        "Dr. Samuel D'souza":  "डॉ. सैमुअल डिसूजा",
        "Dr. Kavita Joshi":    "डॉ. कविता जोशी",
        "Dr. Arjun Patel":     "डॉ. अर्जुन पटेल",
        "Dr. Meena Krishnan":  "डॉ. मीना कृष्णन",
        "Dr. Vikram Reddy":    "डॉ. विक्रम रेड्डी",
        "Dr. Sunita Agarwal":  "डॉ. सुनीता अग्रवाल",
        "Dr. Farah Sheikh":    "डॉ. फराह शेख",
        "Dr. Rohit Gupta":     "डॉ. रोहित गुप्ता",
        "Dr. Ananya Pillai":   "डॉ. अनन्या पिल्लई",
        "Dr. Deepa Iyer":      "डॉ. दीपा अय्यर",
        "Dr. Nikhil Bose":     "डॉ. निखिल बोस",
    },
    "ta": {
        "Dr. Aisha Sharma":    "டாக்டர் ஆயிஷா சர்மா",
        "Dr. Rajan Mehta":     "டாக்டர் ராஜன் மேத்தா",
        "Dr. Priya Nair":      "டாக்டர் பிரியா நாயர்",
        "Dr. Samuel D'souza":  "டாக்டர் சாமுவேல் டி'சூசா",
        "Dr. Kavita Joshi":    "டாக்டர் கவிதா ஜோஷி",
        "Dr. Arjun Patel":     "டாக்டர் அர்ஜுன் படேல்",
        "Dr. Meena Krishnan":  "டாக்டர் மீனா கிருஷ்ணன்",
        "Dr. Vikram Reddy":    "டாக்டர் விக்ரம் ரெட்டி",
        "Dr. Sunita Agarwal":  "டாக்டர் சுனிதா அகர்வால்",
        "Dr. Farah Sheikh":    "டாக்டர் ஃபராஹ் ஷேக்",
        "Dr. Rohit Gupta":     "டாக்டர் ரோஹித் குப்தா",
        "Dr. Ananya Pillai":   "டாக்டர் அனன்யா பிள்ளை",
        "Dr. Deepa Iyer":      "டாக்டர் தீபா ஐயர்",
        "Dr. Nikhil Bose":     "டாக்டர் நிகில் போஸ்",
    },
    "te": {
        "Dr. Aisha Sharma":    "డాక్టర్ ఆయిషా శర్మ",
        "Dr. Rajan Mehta":     "డాక్టర్ రాజన్ మెహతా",
        "Dr. Priya Nair":      "డాక్టర్ ప్రియా నాయర్",
        "Dr. Samuel D'souza":  "డాక్టర్ సామ్యూల్ డిసౌజా",
        "Dr. Kavita Joshi":    "డాక్టర్ కవితా జోషి",
        "Dr. Arjun Patel":     "డాక్టర్ అర్జున్ పటేల్",
        "Dr. Meena Krishnan":  "డాక్టర్ మీనా కృష్ణన్",
        "Dr. Vikram Reddy":    "డాక్టర్ విక్రమ్ రెడ్డి",
        "Dr. Sunita Agarwal":  "డాక్టర్ సునీతా అగర్వాల్",
        "Dr. Farah Sheikh":    "డాక్టర్ ఫరాహ్ షేక్",
        "Dr. Rohit Gupta":     "డాక్టర్ రోహిత్ గుప్తా",
        "Dr. Ananya Pillai":   "డాక్టర్ అనన్య పిళ్ళై",
        "Dr. Deepa Iyer":      "డాక్టర్ దీపా అయ్యర్",
        "Dr. Nikhil Bose":     "డాక్టర్ నిఖిల్ బోస్",
    },
}


SPECIALIZATIONS = {
    "en": {
        "Interventional Cardiology":  "Interventional Cardiology",
        "Electrophysiology":           "Electrophysiology",
        "Stroke & Epilepsy":           "Stroke & Epilepsy",
        "Movement Disorders":          "Movement Disorders",
        "Joint Replacement":           "Joint Replacement",
        "Spine Surgery":               "Spine Surgery",
        "Internal Medicine":           "Internal Medicine",
        "Diabetology":                 "Diabetology",
        "MRI & CT Imaging":            "MRI & CT Imaging",
        "Cosmetic Dermatology":        "Cosmetic Dermatology",
        "Retina & Vitreous":           "Retina & Vitreous",
        "Neonatology":                 "Neonatology",
        "Maternal Fetal Medicine":     "Maternal Fetal Medicine",
        "Hepatology":                  "Hepatology",
        
    },
    "hi": {
        "Interventional Cardiology":  "इंटरवेंशनल कार्डियोलॉजी",
        "Electrophysiology":           "इलेक्ट्रोफिजियोलॉजी",
        "Stroke & Epilepsy":           "स्ट्रोक और मिर्गी",
        "Movement Disorders":          "मूवमेंट डिसऑर्डर्स",
        "Joint Replacement":           "जोड़ प्रतिस्थापन",
        "Spine Surgery":               "रीढ़ की सर्जरी",
        "Internal Medicine":           "आंतरिक चिकित्सा",
        "Diabetology":                 "डायबेटोलॉजी",
        "MRI & CT Imaging":            "एमआरआई और सीटी इमेजिंग",
        "Cosmetic Dermatology":        "कॉस्मेटिक त्वचाविज्ञान",
        "Retina & Vitreous":           "रेटिना और विट्रीयस",
        "Neonatology":                 "नवजातविज्ञान",
        "Maternal Fetal Medicine":     "मातृ भ्रूण चिकित्सा",
        "Hepatology":                  "हेपेटोलॉजी",
        
    },
    "ta": {
        "Interventional Cardiology":  "தலையீட்டு இதயவியல்",
        "Electrophysiology":           "மின் உடலியல்",
        "Stroke & Epilepsy":           "பக்கவாதம் & வலிப்பு",
        "Movement Disorders":          "அசைவு கோளாறுகள்",
        "Joint Replacement":           "மூட்டு மாற்று",
        "Spine Surgery":               "முதுகுத்தண்டு அறுவை சிகிச்சை",
        "Internal Medicine":           "உள் மருத்துவம்",
        "Diabetology":                 "நீரிழிவியல்",
        "MRI & CT Imaging":            "MRI & CT படமெடுத்தல்",
        "Cosmetic Dermatology":        "அழகுசாதன தோலியல்",
        "Retina & Vitreous":           "விழித்திரை & விட்ரியஸ்",
        "Neonatology":                 "பிறந்த குழந்தை மருத்துவம்",
        "Maternal Fetal Medicine":     "தாய் கருவூட்டு மருத்துவம்",
        "Hepatology":                  "கல்லீரல் மருத்துவம்",
        
    },
    "te": {
        "Interventional Cardiology":  "ఇంటర్‌వెన్షనల్ కార్డియాలజీ",
        "Electrophysiology":           "ఎలక్ట్రోఫిజియాలజీ",
        "Stroke & Epilepsy":           "స్ట్రోక్ & ఎపిలెప్సీ",
        "Movement Disorders":          "కదలిక రుగ్మతలు",
        "Joint Replacement":           "కీలు మార్పిడి",
        "Spine Surgery":               "వెన్నెముక శస్త్రచికిత్స",
        "Internal Medicine":           "అంతర్గత వైద్యం",
        "Diabetology":                 "డయాబెటాలజీ",
        "MRI & CT Imaging":            "MRI & CT ఇమేజింగ్",
        "Cosmetic Dermatology":        "కాస్మెటిక్ డెర్మటాలజీ",
        "Retina & Vitreous":           "రెటినా & విట్రియస్",
        "Neonatology":                 "నియోనాటాలజీ",
        "Maternal Fetal Medicine":     "మాతృ పిండ వైద్యం",
        "Hepatology":                  "హెపటాలజీ",
    
    },
}


DEPARTMENT_NAMES = {
    "en": {
        "Cardiology":        "Cardiology",
        "Neurology":         "Neurology",
        "Orthopedics":       "Orthopedics",
        "General Medicine":  "General Medicine",
        "Radiology":         "Radiology",
        "Dermatology":       "Dermatology",
        "Ophthalmology":     "Ophthalmology",
        "Pediatrics":        "Pediatrics",
        "Gynecology":        "Gynecology",
        "Gastroenterology":  "Gastroenterology",
    },
    "hi": {
        "Cardiology":        "हृदय रोग विज्ञान",
        "Neurology":         "स्नायु विज्ञान",
        "Orthopedics":       "अस्थि रोग विज्ञान",
        "General Medicine":  "सामान्य चिकित्सा",
        "Radiology":         "रेडियोलॉजी",
        "Dermatology":       "त्वचाविज्ञान",
        "Ophthalmology":     "नेत्र विज्ञान",
        "Pediatrics":        "बाल रोग विज्ञान",
        "Gynecology":        "स्त्री रोग विज्ञान",
        "Gastroenterology":  "जठर विज्ञान",
    },
    "ta": {
        "Cardiology":        "இதயவியல்",
        "Neurology":         "நரம்பியல்",
        "Orthopedics":       "எலும்பியல்",
        "General Medicine":  "பொது மருத்துவம்",
        "Radiology":         "கதிரியக்கவியல்",
        "Dermatology":       "தோலியல்",
        "Ophthalmology":     "கண் மருத்துவம்",
        "Pediatrics":        "குழந்தை மருத்துவம்",
        "Gynecology":        "பெண் நோய் மருத்துவம்",
        "Gastroenterology":  "இரைப்பை குடலியல்",
    },
    "te": {
        "Cardiology":        "కార్డియాలజీ",
        "Neurology":         "న్యూరాలజీ",
        "Orthopedics":       "ఆర్థోపెడిక్స్",
        "General Medicine":  "సాధారణ వైద్యం",
        "Radiology":         "రేడియాలజీ",
        "Dermatology":       "డెర్మటాలజీ",
        "Ophthalmology":     "నేత్ర వైద్యం",
        "Pediatrics":        "పీడియాట్రిక్స్",
        "Gynecology":        "గైనకాలజీ",
        "Gastroenterology":  "గ్యాస్ట్రోఎంటరాలజీ",
    },
}


def translate_doctor(name: str, lang: str = "en") -> str:
    """Translates a doctor's name to the target language."""
    if not name:
        return name
    lang = lang.lower() if lang else "en"
    if lang not in DOCTOR_NAMES:
        lang = "en"
    return DOCTOR_NAMES.get(lang, {}).get(name, name)


def translate_specialization(spec: str, lang: str = "en") -> str:
    """Translates a specialization to the target language."""
    if not spec:
        return spec
    lang = lang.lower() if lang else "en"
    if lang not in SPECIALIZATIONS:
        lang = "en"
    return SPECIALIZATIONS.get(lang, {}).get(spec, spec)


def translate_department(dept: str, lang: str = "en") -> str:
    """Translates a department name to the target language."""
    if not dept:
        return dept
    lang = lang.lower() if lang else "en"
    if lang not in DEPARTMENT_NAMES:
        lang = "en"
    return DEPARTMENT_NAMES.get(lang, {}).get(dept, dept)    