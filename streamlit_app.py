# streamlit_app.py

import streamlit as st
import streamlit.components.v1 as components 
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from services.translations import (
    t, LANGUAGES, get_language_name, get_language_flag,
    translate_doctor, translate_specialization, translate_department
)

# ═══════════════════════════════════════════════════════════════
# CONFIG
# ═══════════════════════════════════════════════════════════════
import os
# Auto-detect: use deployed backend on cloud, localhost locally
API_BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="AgentCare | Healthcare AI",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════
# MODERN CSS DESIGN SYSTEM
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# HEALTHCARE-GRADE CSS DESIGN SYSTEM (v2 — Judge-Ready)
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif !important; }
    
    /* ═══ HEALTHCARE BACKGROUND ═══ */
    .stApp {
        background: 
            linear-gradient(135deg, rgba(6, 20, 40, 0.95) 0%, rgba(8, 25, 45, 0.97) 50%, rgba(4, 15, 30, 0.98) 100%),
            url('https://images.unsplash.com/photo-1631815589968-fdb09a223b1e?w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        inset: 0;
        background: 
            radial-gradient(circle at 15% 85%, rgba(13, 148, 136, 0.08) 0%, transparent 45%),
            radial-gradient(circle at 85% 15%, rgba(6, 182, 212, 0.06) 0%, transparent 45%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* ═══ LOGIN SPLIT-SCREEN HERO ═══ */
    .login-hero-panel {
        background: 
            linear-gradient(135deg, rgba(6, 78, 89, 0.92) 0%, rgba(8, 47, 73, 0.94) 100%),
            url('https://images.unsplash.com/photo-1587351021759-3e566b6af7cc?w=1200&q=80');
        background-size: cover;
        background-position: center;
        border-radius: 24px;
        padding: 40px 32px;
        min-height: 620px;
        color: white;
        position: relative;
        overflow: hidden;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(13, 148, 136, 0.2);
    }
    
    .login-hero-panel::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -30%;
        width: 500px;
        height: 500px;
        background: radial-gradient(circle, rgba(13, 148, 136, 0.25) 0%, transparent 70%);
        border-radius: 50%;
        animation: pulse-glow 4s ease-in-out infinite;
    }
    
    @keyframes pulse-glow {
        0%, 100% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.1); opacity: 0.9; }
    }
    
    .login-logo-mark {
        display: flex;
        align-items: center;
        gap: 14px;
        position: relative;
        z-index: 2;
        margin-bottom: 32px;
    }
    
    .login-logo-icon {
        width: 56px;
        height: 56px;
        background: linear-gradient(135deg, #14b8a6 0%, #0891b2 100%);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 24px rgba(20, 184, 166, 0.4);
    }
    
    .login-brand-name {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 32px;
        font-weight: 800;
        color: white;
        letter-spacing: -1px;
        line-height: 1;
    }
    
    .login-brand-sub {
        font-size: 12px;
        color: #5eead4;
        font-weight: 600;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .login-headline {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 40px;
        font-weight: 800;
        color: white;
        line-height: 1.15;
        margin: 40px 0 16px 0;
        position: relative;
        z-index: 2;
    }
    
    .login-headline .accent {
        background: linear-gradient(135deg, #5eead4 0%, #67e8f9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .login-tagline {
        color: rgba(255,255,255,0.85);
        font-size: 16px;
        line-height: 1.6;
        margin-bottom: 32px;
        position: relative;
        z-index: 2;
        max-width: 90%;
    }
    
    '<div class="feature-pill-grid">'
            
            # 🤖 8 AI Agents
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">🤖</div>'
            f'<div class="feature-pill-text">{tr("feature_agents_title")}<br>{tr("feature_agents_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">🤖 8 Specialized Agents</div>'
            '<div class="tooltip-body">Coordinator, Routing, Appointment, Document, Follow-up, Safety, Query & Knowledge — each with unique prompts, tools & responsibilities.</div>'
            '</div>'
            '</div>'
            
            # 🎤 Voice Input
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">🎤</div>'
            f'<div class="feature-pill-text">{tr("feature_voice_title")}<br>{tr("feature_voice_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">🎤 Speech-to-Text AI</div>'
            '<div class="tooltip-body">Speak your request in any language. Groq Whisper-Large-v3 transcribes voice into text instantly for the AI agents.</div>'
            '</div>'
            '</div>'
            
            # 🌐 4 Languages
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">🌐</div>'
            f'<div class="feature-pill-text">{tr("feature_lang_title")}<br>{tr("feature_lang_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">🌐 Truly Multilingual</div>'
            '<div class="tooltip-body">Full UI + AI responses in English, Hindi, Tamil & Telugu. Inclusive healthcare — not English-only.</div>'
            '</div>'
            '</div>'
            
            # 📚 RAG Powered
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">📚</div>'
            f'<div class="feature-pill-text">{tr("feature_rag_title")}<br>{tr("feature_rag_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">📚 Knowledge Retrieval</div>'
            '<div class="tooltip-body">ChromaDB vector store + sentence-transformer embeddings retrieve hospital policies, procedures & department info to ground answers in real data.</div>'
            '</div>'
            '</div>'
            
            # 🛡️ Safety Guard
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">🛡️</div>'
            f'<div class="feature-pill-text">{tr("feature_safety_title")}<br>{tr("feature_safety_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">🛡️ Human-in-the-Loop</div>'
            '<div class="tooltip-body">Blocks diagnosis, prescriptions & emergency requests. Auto-escalates uncertain cases to human staff with email alerts.</div>'
            '</div>'
            '</div>'
            
            # ⚡ Real-Time
            f'<div class="feature-pill">'
            '<div class="feature-pill-icon">⚡</div>'
            f'<div class="feature-pill-text">{tr("feature_realtime_title")}<br>{tr("feature_realtime_sub")}</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-title">⚡ Instant Alerts</div>'
            '<div class="tooltip-body">Every escalation triggers immediate email notifications. Staff dashboard pulses red until reviewed & resolved.</div>'
            '</div>'
            '</div>'
            
            '</div>'  # close feature-pill-grid
    
    .feature-pill {
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(94, 234, 212, 0.25);
        padding: 12px 14px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        transition: all 0.3s;
    }
    
    .feature-pill:hover {
        background: rgba(94, 234, 212, 0.15);
        border-color: rgba(94, 234, 212, 0.5);
        transform: translateY(-2px);
    }
    
    .feature-pill-icon {
        font-size: 20px;
        min-width: 20px;
    }
    
    .feature-pill-text {
        color: white;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.3;
    }
    
    .trust-strip {
        display: flex;
        gap: 20px;
        margin-top: 28px;
        padding-top: 20px;
        border-top: 1px solid rgba(255,255,255,0.15);
        position: relative;
        z-index: 2;
    }
    
    .trust-item {
        color: rgba(255,255,255,0.9);
        font-size: 11px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    /* ═══ RIGHT PANEL: LOGIN FORM CARD ═══ */
    .login-form-panel {
        background: linear-gradient(180deg, rgba(15, 23, 42, 0.95) 0%, rgba(10, 18, 35, 0.98) 100%);
        border: 1px solid rgba(94, 234, 212, 0.15);
        border-radius: 24px;
        padding: 36px 32px;
        min-height: 620px;
        box-shadow: 0 25px 60px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(20px);
    }
    
    .form-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        font-size: 28px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    
    .form-subtitle {
        color: #94a3b8;
        font-size: 14px;
        margin-bottom: 28px;
    }
    
    /* ═══ ONE-CLICK DEMO CARDS ═══ */
    .demo-section-title {
        color: #5eead4;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin: 24px 0 12px 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .demo-section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, rgba(94, 234, 212, 0.3), transparent);
    }
    
    /* ═══ HOSPITAL HERO HEADER (inside app) ═══ */
    .hospital-hero {
        position: relative;
        padding: 32px 36px;
        border-radius: 20px;
        margin-bottom: 24px;
        overflow: hidden;
        background: 
            linear-gradient(135deg, rgba(6, 78, 89, 0.88) 0%, rgba(8, 47, 73, 0.92) 100%),
            url('https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=1600&q=80');
        background-size: cover;
        background-position: center;
        box-shadow: 0 15px 40px rgba(6, 78, 89, 0.35);
        border: 1px solid rgba(94, 234, 212, 0.15);
    }
    
    .hospital-hero::before {
        content: '';
        position: absolute;
        top: -30%;
        right: -10%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(20, 184, 166, 0.2) 0%, transparent 70%);
        border-radius: 50%;
    }
    
    .hospital-hero-title {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: white !important;
        font-size: 32px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 14px;
    }
    
    .hospital-hero-subtitle {
        color: rgba(255,255,255,0.9) !important;
        font-size: 14px !important;
        margin-top: 8px !important;
        position: relative;
        z-index: 2;
    }
    
    .hospital-hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(94, 234, 212, 0.15);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(94, 234, 212, 0.4);
        color: #5eead4;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin-top: 14px;
        position: relative;
        z-index: 2;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* ═══ SIDEBAR ═══ */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a1628 0%, #06111f 100%);
        border-right: 1px solid rgba(94, 234, 212, 0.1);
    }
    
    /* ═══ BUTTONS ═══ */
    .stButton > button {
        background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
        color: white !important;
        border: none !important;
        padding: 11px 22px !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        transition: all 0.25s !important;
        box-shadow: 0 4px 14px rgba(13, 148, 136, 0.35) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.55) !important;
        background: linear-gradient(135deg, #14b8a6 0%, #06b6d4 100%) !important;
    }
    
    /* ═══ METRIC CARDS ═══ */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%) !important;
        padding: 22px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(94, 234, 212, 0.15) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2) !important;
        transition: all 0.2s;
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-3px);
        border-color: rgba(94, 234, 212, 0.4) !important;
        box-shadow: 0 12px 24px rgba(13, 148, 136, 0.15) !important;
    }
    
    /* ═══ APPOINTMENT CARDS ═══ */
    .appt-card {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%);
        border: 1px solid rgba(94, 234, 212, 0.15);
        border-left: 4px solid #0d9488;
        border-radius: 14px;
        padding: 18px;
        margin: 12px 0;
        transition: all 0.3s;
    }
    
    .appt-card:hover {
        border-color: rgba(94, 234, 212, 0.4);
        box-shadow: 0 8px 24px rgba(13, 148, 136, 0.15);
        transform: translateY(-2px);
    }
    
    .appt-status-confirmed { background: linear-gradient(135deg, #0d9488, #0891b2); color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3); }
    .appt-status-cancelled { background: linear-gradient(135deg, #ef4444, #dc2626); color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    .appt-status-rescheduled { background: linear-gradient(135deg, #3b82f6, #2563eb); color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700; }
    
    .appt-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
    .appt-doctor { font-size: 18px; font-weight: 700; color: #f8fafc; }
    .appt-specialty { color: #94a3b8; font-size: 13px; margin-top: 2px; }
    .appt-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px; }
    .appt-info-item { background: rgba(15, 23, 42, 0.5); padding: 12px; border-radius: 8px; }
    .appt-info-label { color: #64748b; font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 4px; }
    .appt-info-value { color: #f1f5f9; font-size: 15px; font-weight: 600; }
    
    /* ═══ SIDEBAR USER CARD ═══ */
    .sidebar-user-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(94, 234, 212, 0.15);
        padding: 16px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .user-avatar {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #0d9488, #06b6d4);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 20px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .user-name { color: #f1f5f9 !important; font-weight: 600 !important; font-size: 15px !important; margin: 0 !important; }
    .user-role { color: #5eead4 !important; font-size: 11px !important; margin: 2px 0 0 0 !important; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; }
    
    /* ═══ FORMS ═══ */
    div[data-testid="stForm"] {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%);
        padding: 24px !important;
        border-radius: 16px !important;
        border: 1px solid rgba(94, 234, 212, 0.15) !important;
    }
    
    /* ═══ INPUTS ═══ */
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(148, 163, 184, 0.2) !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
        padding: 12px !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.2) !important;
    }
    
    /* ═══ TABS ═══ */
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #94a3b8 !important;
        font-weight: 600 !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #0d9488, #0891b2) !important;
        color: white !important;
    }
    
    /* ═══ STATS BOX ═══ */
    .stat-box {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%);
        padding: 20px;
        border-radius: 14px;
        border: 1px solid rgba(94, 234, 212, 0.15);
        text-align: center;
        transition: all 0.3s;
    }
    
    .stat-box:hover {
        transform: translateY(-3px);
        border-color: rgba(94, 234, 212, 0.4);
        box-shadow: 0 8px 20px rgba(13, 148, 136, 0.15);
    }
    
    .stat-icon { font-size: 30px; margin-bottom: 6px; }
    .stat-value { font-size: 28px; font-weight: 800; color: #f8fafc; margin: 4px 0; font-family: 'Plus Jakarta Sans', sans-serif; }
    .stat-label { color: #94a3b8; font-size: 11px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    
    /* ═══ SUCCESS/WARNING/ERROR HEROES ═══ */
    .success-hero { background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15)); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 16px; padding: 24px; margin: 20px 0; }
    .success-hero h3 { color: #34d399 !important; margin: 0 0 8px 0 !important; font-size: 22px !important; }
    .error-hero { background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.15)); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 16px; padding: 24px; margin: 20px 0; }
    .warning-hero { background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(217, 119, 6, 0.15)); border: 1px solid rgba(245, 158, 11, 0.3); border-radius: 16px; padding: 24px; margin: 20px 0; }
    
    /* ═══ ANIMATIONS ═══ */
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); border-color: rgba(239, 68, 68, 0.8); }
        50% { box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); border-color: rgba(239, 68, 68, 1); }
    }
    .pulsing-alert { animation: pulse-red 2s infinite; border: 2px solid #ef4444 !important; background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.2)) !important; }
    .pulsing-alert .stat-value { color: #fca5a5 !important; }
    
    /* ═══ CHAT MESSAGES ═══ */
    div[data-testid="stChatMessage"][data-testid*="user"] {
        background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
        border-radius: 18px 18px 4px 18px !important;
        padding: 14px 18px !important;
        margin: 8px 0 8px auto !important;
        max-width: 75% !important;
        color: white !important;
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25) !important;
    }
    
    div[data-testid="stChatMessage"][data-testid*="assistant"] {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%) !important;
        border-radius: 18px 18px 18px 4px !important;
        padding: 16px 20px !important;
        margin: 8px auto 8px 0 !important;
        max-width: 90% !important;
        border: 1px solid rgba(94, 234, 212, 0.15) !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
    }
    
    /* ═══ EXPANDERS ═══ */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(94, 234, 212, 0.15) !important;
        padding: 12px 16px !important;
        color: #f1f5f9 !important;
        font-weight: 600 !important;
    }
    
    /* ═══ RADIO NAV ═══ */
    div[role="radiogroup"] label {
        background: rgba(30, 41, 59, 0.4) !important;
        padding: 12px 16px !important;
        border-radius: 10px !important;
        margin: 4px 0 !important;
        border: 1px solid transparent !important;
        transition: all 0.2s !important;
    }
    
    div[role="radiogroup"] label:hover {
        background: rgba(13, 148, 136, 0.15) !important;
        border-color: rgba(13, 148, 136, 0.4) !important;
    }
    
    /* ═══ ALERTS ═══ */
    .stAlert { border-radius: 12px !important; border-left-width: 4px !important; padding: 16px !important; }
    
    /* ═══ PROGRESS ═══ */
    .stProgress > div > div { background: linear-gradient(90deg, #0d9488, #06b6d4) !important; border-radius: 10px !important; }
    
    /* ═══ HIDE STREAMLIT BRANDING ═══ */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* ═══ CHAT INPUT ═══ */
    div[data-testid="stChatInput"] {
        background: linear-gradient(135deg, #1e293b 0%, #263445 100%) !important;
        border: 1px solid rgba(94, 234, 212, 0.3) !important;
        border-radius: 16px !important;
        padding: 8px !important;
    }
    
    div[data-testid="stChatInput"] textarea {
        background: transparent !important;
        color: #f8fafc !important;
        font-size: 15px !important;
        border: none !important;
    }

    /* ═══ INTERACTIVE FEATURE PILLS (Expanding + Always Sparkling) ═══ */
    
    /* Grid layout — force 2 columns */
    .feature-pill-grid {
        display: grid !important;
        grid-template-columns: 1fr 1fr !important;
        gap: 12px !important;
        margin-top: 24px !important;
        position: relative;
        z-index: 2;
        align-items: start !important;
    }
    
    /* Card container */
    .feature-pill {
        position: relative;
        cursor: pointer;
        background: rgba(15, 23, 42, 0.5) !important;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1.5px solid transparent !important;
        padding: 14px 16px !important;
        border-radius: 14px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 8px !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden !important;
        min-height: 62px;
    }
    
    /* ALWAYS-ON rotating gradient border (visible even when idle) */
    .feature-pill::before {
        content: '';
        position: absolute;
        inset: 0;
        border-radius: 14px;
        padding: 1.5px;
        background: linear-gradient(
            135deg,
            #5eead4 0%,
            #06b6d4 25%,
            #8b5cf6 50%,
            #06b6d4 75%,
            #5eead4 100%
        );
        background-size: 300% 300%;
        animation: rotate-gradient 3s linear infinite;
        -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
        -webkit-mask-composite: xor;
        mask-composite: exclude;
        pointer-events: none;
        opacity: 0.85;
        z-index: 1;
    }
    
    @keyframes rotate-gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Sparkle emojis floating on corners (always visible, subtle) */
    .feature-pill::after {
        content: '✨';
        position: absolute;
        top: 4px;
        right: 6px;
        font-size: 12px;
        opacity: 0.4;
        animation: sparkle-twinkle 2s ease-in-out infinite;
        pointer-events: none;
        z-index: 3;
    }
    
    @keyframes sparkle-twinkle {
        0%, 100% { opacity: 0.4; transform: scale(1) rotate(0deg); }
        50% { opacity: 1; transform: scale(1.3) rotate(15deg); }
    }
    
    /* Header row (icon + text) */
    .feature-pill-header {
        display: flex;
        align-items: center;
        gap: 10px;
        width: 100%;
        position: relative;
        z-index: 2;
    }
    
    .feature-pill-icon {
        font-size: 22px;
        min-width: 22px;
        transition: transform 0.3s ease;
    }
    
    .feature-pill-text {
        color: white;
        font-size: 12px;
        font-weight: 600;
        line-height: 1.3;
        flex: 1;
    }
    
    /* Tooltip content (hidden by default, expands on hover) */
    .feature-tooltip {
        max-height: 0;
        opacity: 0;
        overflow: hidden;
        transition: max-height 0.4s cubic-bezier(0.4, 0, 0.2, 1), 
                    opacity 0.3s ease 0.05s;
        color: #cbd5e1;
        font-size: 11.5px;
        line-height: 1.55;
        position: relative;
        z-index: 2;
    }
    
    .tooltip-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(94, 234, 212, 0.5), transparent);
        margin: 8px 0;
    }
    
    .tooltip-title {
        color: #5eead4;
        font-weight: 700;
        font-size: 10.5px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    
    .tooltip-body {
        color: #e2e8f0;
        font-size: 11.5px;
        line-height: 1.55;
    }
    
    /* HOVER STATE: Expand + Glow + Reveal tooltip */
    .feature-pill:hover {
        background: rgba(15, 23, 42, 0.85) !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 
            0 15px 35px rgba(13, 148, 136, 0.4),
            0 0 30px rgba(94, 234, 212, 0.35) !important;
        z-index: 100 !important;
    }
    
    .feature-pill:hover::before {
        opacity: 1;
        animation: rotate-gradient 1.5s linear infinite;
    }
    
    .feature-pill:hover::after {
        opacity: 1;
        animation: sparkle-hover 0.6s ease-in-out infinite;
        font-size: 16px;
    }
    
    @keyframes sparkle-hover {
        0%, 100% { transform: scale(1) rotate(0deg); }
        50% { transform: scale(1.5) rotate(180deg); }
    }
    
    .feature-pill:hover .feature-pill-icon {
        animation: icon-bounce 0.6s ease-in-out;
    }
    
    @keyframes icon-bounce {
        0%, 100% { transform: translateY(0) rotate(0); }
        30% { transform: translateY(-4px) rotate(-10deg); }
        60% { transform: translateY(-2px) rotate(10deg); }
    }
    
    .feature-pill:hover .feature-tooltip {
        max-height: 200px;
        opacity: 1;
    }
    
    /* CRITICAL: Allow cards to grow outside parent panel */
    .login-hero-panel {
        overflow: visible !important;
    } 


    /* ═══ PREMIUM SIDEBAR NAVIGATION ═══ */
    
    /* Navigation section header */
    section[data-testid="stSidebar"] h3 {
        color: #5eead4 !important;
        font-size: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        margin: 16px 0 12px 0 !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }
    
    /* Radio group container */
    section[data-testid="stSidebar"] div[role="radiogroup"] {
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    
    /* Individual radio option labels */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.6) 100%) !important;
        padding: 12px 14px !important;
        border-radius: 12px !important;
        margin: 3px 0 !important;
        border: 1px solid rgba(94, 234, 212, 0.08) !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        cursor: pointer !important;
        position: relative !important;
        overflow: hidden !important;
    }
    
    /* Hover state */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: linear-gradient(135deg, rgba(13, 148, 136, 0.15) 0%, rgba(6, 182, 212, 0.12) 100%) !important;
        border-color: rgba(94, 234, 212, 0.35) !important;
        transform: translateX(4px) !important;
        box-shadow: 0 4px 12px rgba(13, 148, 136, 0.2) !important;
    }
    
    /* Hide the default radio circle */
    section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    
    /* Selected state — highlighted with teal gradient */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%) !important;
        border-color: rgba(94, 234, 212, 0.6) !important;
        box-shadow: 
            0 6px 18px rgba(13, 148, 136, 0.4),
            0 0 20px rgba(94, 234, 212, 0.25) !important;
        transform: translateX(4px) !important;
    }
    
    /* Left indicator bar on selected item */
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked)::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, #5eead4, #06b6d4);
        border-radius: 4px 0 0 4px;
        box-shadow: 0 0 12px rgba(94, 234, 212, 0.8);
    }
    
    /* Label text (make brighter when selected) */
    section[data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #cbd5e1 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin: 0 !important;
        transition: color 0.25s ease !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: white !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover p {
        color: #f8fafc !important;
    }
    
    /* Sidebar sign-out button */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(220, 38, 38, 0.1)) !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        color: #fca5a5 !important;
        font-weight: 600 !important;
        transition: all 0.2s !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #ef4444, #dc2626) !important;
        color: white !important;
        border-color: #ef4444 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(239, 68, 68, 0.4) !important;
    }
    
    /* Sidebar horizontal dividers */
    section[data-testid="stSidebar"] hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, rgba(94, 234, 212, 0.3), transparent) !important;
        margin: 16px 0 !important;
    }
    
    /* Language switcher label */
    section[data-testid="stSidebar"] .stSelectbox label {
        color: #5eead4 !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
    }
    
    /* Language selectbox */
    section[data-testid="stSidebar"] .stSelectbox > div > div {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(94, 234, 212, 0.2) !important;
        border-radius: 10px !important;
    }   
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# API HELPERS
# ═══════════════════════════════════════════════════════════════

def api_post(endpoint, data, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=data, headers=headers, timeout=120)
        return {"ok": resp.status_code < 400, "data": resp.json(), "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}, "status": 500}

def api_get(endpoint, token=None, params=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=headers, params=params or {}, timeout=30)
        return {"ok": resp.status_code < 400, "data": resp.json(), "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}, "status": 500}

def api_post_form(endpoint, data, files=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", data=data, files=files, headers=headers, timeout=120)
        return {"ok": resp.status_code < 400, "data": resp.json(), "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}, "status": 500}

def api_put(endpoint, data, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.put(f"{API_BASE}{endpoint}", json=data, headers=headers, timeout=30)
        return {"ok": resp.status_code < 400, "data": resp.json(), "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}, "status": 500}

def api_delete(endpoint, data=None, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = requests.delete(f"{API_BASE}{endpoint}", json=data, headers=headers, timeout=30)
        return {"ok": resp.status_code < 400, "data": resp.json(), "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}, "status": 500}

def api_login(email, password):
    try:
        resp = requests.post(
            f"{API_BASE}/api/auth/login",
            data={"username": email, "password": password}, timeout=30,
        )
        return {"ok": resp.status_code == 200, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "data": {"detail": str(e)}}


# ═══════════════════════════════════════════════════════════════
# SESSION STATE
# ═══════════════════════════════════════════════════════════════

def is_logged_in(): return st.session_state.get("token") is not None
def get_token(): return st.session_state.get("token")
def get_role(): return st.session_state.get("role")
def get_user_name(): return st.session_state.get("name", "User")
def get_user_email(): return st.session_state.get("email", "")
def get_user_id(): return st.session_state.get("user_id")

# ═══════════════════════════════════════════════════════════════
# LANGUAGE HELPERS
# ═══════════════════════════════════════════════════════════════

def get_language() -> str:
    """Get current UI language from session state."""
    return st.session_state.get("ui_language", "en")


def set_language(lang_code: str):
    """Set the UI language."""
    st.session_state["ui_language"] = lang_code


def tr(key: str) -> str:
    """Shortcut to translate a key using current language."""
    return t(key, get_language())

def tr_doctor(name: str) -> str:
    """Translate doctor name based on current language."""
    return translate_doctor(name, get_language())


def tr_spec(spec: str) -> str:
    """Translate specialization based on current language."""
    return translate_specialization(spec, get_language())


def tr_dept(dept: str) -> str:
    """Translate department based on current language."""
    return translate_department(dept, get_language())


def load_language_from_profile(token: str):
    """Load user's preferred language from their profile on login."""
    if "language_loaded" not in st.session_state:
        try:
            result = api_get("/api/patients/profile", token)
            if result["ok"]:
                pref_lang = result["data"].get("preferred_language", "English")
                # Map full language name to code
                lang_map = {
                    "English": "en",
                    "Hindi": "hi",
                    "Tamil": "ta",
                    "Telugu": "te",
                    "Bengali": "en",  # Fallback
                }
                lang_code = lang_map.get(pref_lang, "en")
                set_language(lang_code)
        except Exception:
            set_language("en")
        st.session_state["language_loaded"] = True

def logout():
    for key in ["token", "role", "user_id", "name", "email"]:
        st.session_state.pop(key, None)
    st.rerun()


# ═══════════════════════════════════════════════════════════════
# COMPONENTS
# ═══════════════════════════════════════════════════════════════

def hero_header(subtitle="Agentic AI for Patient Administration and Care Coordination"):
    """Hospital-themed page header with imagery."""
    st.markdown(f"""
    <div class="hospital-hero">
        <h1 class="hospital-hero-title">
            <span style='font-size: 40px;'>🏥</span> {subtitle}
        </h1>
        <div class="hospital-hero-badge">
            {tr('hero_badge')}
        </div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_brand():
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #0d9488 0%, #0891b2 100%);
                padding: 20px; border-radius: 14px; margin-bottom: 16px;
                text-align: center; box-shadow: 0 6px 20px rgba(13, 148, 136, 0.3);
                position: relative; overflow: hidden;'>
        <div style='position: absolute; top: -10px; right: -5px; font-size: 60px;
                    opacity: 0.1;'>⚕️</div>
        <h2 style='color: white; margin: 0; font-size: 22px; font-weight: 800;
                   position: relative; z-index: 1;'>
            🏥 {tr('brand_name')}
        </h2>
        <p style='color: rgba(255,255,255,0.85); margin: 4px 0 0 0; font-size: 11px;
                  position: relative; z-index: 1;'>
            {tr('powered_by')} 8 {tr('ai_agents')} · RAG
        </p>
    </div>
    """, unsafe_allow_html=True)

def sidebar_language_switcher():
    """Language switcher dropdown in the sidebar."""
    current_lang = get_language()
    
    st.markdown("### 🌐 Language / भाषा")
    
    lang_options = []
    lang_map = {}
    for code, info in LANGUAGES.items():
        display = f"{info['flag']} {info['name']}"
        lang_options.append(display)
        lang_map[display] = code
    
    current_display = f"{get_language_flag(current_lang)} {get_language_name(current_lang)}"
    
    # Find index of current language
    try:
        current_index = lang_options.index(current_display)
    except ValueError:
        current_index = 0
    
    selected = st.selectbox(
        "Choose language",
        lang_options,
        index=current_index,
        label_visibility="collapsed",
        key="lang_selector_sidebar",
    )
    
    new_lang = lang_map[selected]
    if new_lang != current_lang:
        set_language(new_lang)
        st.rerun()    


def sidebar_user_card(name, role):
    initial = name[0].upper() if name else "U"
    st.markdown(f"""
    <div class="sidebar-user-card">
        <div class="user-avatar">{initial}</div>
        <p class="user-name">{name}</p>
        <p class="user-role">{role}</p>
    </div>
    """, unsafe_allow_html=True)


def agent_pipeline_card(icon, name, status, badge_type="success"):
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(51, 65, 85, 0.9) 100%);
                border-left: 4px solid #0d9488;
                padding: 14px 18px;
                margin: 8px 0;
                border-radius: 12px;
                display: flex;
                align-items: center;
                gap: 14px;
                transition: all 0.3s;'>
        <div style='width: 40px; height: 40px; min-width: 40px;
                    background: linear-gradient(135deg, #0d9488, #0891b2);
                    border-radius: 10px;
                    display: flex; align-items: center; justify-content: center;
                    font-size: 20px;
                    box-shadow: 0 4px 12px rgba(13, 148, 136, 0.3);'>
            {icon}
        </div>
        <div style='flex: 1; color: #f1f5f9;'>
            <div style='font-weight: 700; font-size: 14px; color: #f8fafc;'>{name}</div>
            <div style='font-size: 13px; color: #cbd5e1; margin-top: 2px;'>{status}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def stat_card(icon, value, label):
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                padding: 20px; border-radius: 14px;
                border: 1px solid rgba(13, 148, 136, 0.2);
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                transition: all 0.3s;'>
        <div style='font-size: 28px; margin-bottom: 6px;'>{icon}</div>
        <div style='font-size: 28px; font-weight: 800; color: #f8fafc;
                    margin: 4px 0;'>{value}</div>
        <div style='color: #94a3b8; font-size: 11px; text-transform: uppercase;
                    font-weight: 600; letter-spacing: 0.5px;'>{label}</div>
    </div>
    """, unsafe_allow_html=True)

def stat_card_alert(icon, value, label, alert=False):
    """Stat card that pulses red when alert=True"""
    alert_class = "pulsing-alert" if alert else ""
    st.markdown(f"""
    <div class="stat-box {alert_class}">
        <div class="stat-icon">{icon}</div>
        <div class="stat-value">{value}</div>
        <div class="stat-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)    


def appointment_card(appt):
    status_map = {
        "confirmed":   ("appt-status-confirmed", f"✓ {tr('status_confirmed')}"),
        "pending":     ("appt-status-rescheduled", f"⏳ {tr('status_pending')}"),
        "cancelled":   ("appt-status-cancelled", f"✕ {tr('status_cancelled')}"),
        "completed":   ("appt-status-confirmed", f"✓ {tr('status_completed')}"),
        "rescheduled": ("appt-status-rescheduled", f"🔄 {tr('status_rescheduled')}"),
    }
    status_class, status_label = status_map.get(
        appt["status"], ("appt-status-confirmed", appt["status"].upper())
    )
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1e293b 0%, #263445 100%);
                border: 1px solid rgba(13, 148, 136, 0.2);
                border-left: 4px solid #0d9488;
                border-radius: 14px; padding: 18px; margin: 12px 0;
                transition: all 0.3s;'>
        <div class="appt-header">
            <div>
                <div class="appt-doctor">👨‍⚕️ {tr_doctor(appt.get('doctor_name', 'Doctor'))}</div>
                <div class="appt-specialty">{tr_spec(appt.get('specialization')) or 'General Consultation'}</div>
            </div>
            <span class="{status_class}">{status_label}</span>
        </div>
        <div class="appt-info-grid">
            <div class="appt-info-item">
                <div class="appt-info-label">📅 {tr('appt_date')}</div>
                <div class="appt-info-value">{appt.get('date', 'N/A')}</div>
            </div>
            <div class="appt-info-item">
                <div class="appt-info-label">🕐 {tr('appt_time')}</div>
                <div class="appt-info-value">{appt.get('time', 'N/A')}</div>
            </div>
            <div class="appt-info-item">
                <div class="appt-info-label">🆔 {tr('appt_id_label')}</div>
                <div class="appt-info-value">#{appt.get('appointment_id', 'N/A')}</div>
            </div>
            <div class="appt-info-item">
                <div class="appt-info-label">📝 {tr('appt_reason_label')}</div>
                <div class="appt-info-value">{(appt.get('reason') or 'N/A')[:40]}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE (v2 — Split-Screen Judge-Ready Design)
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE (v3 — Fully Multilingual + Judge-Ready)
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE (v4 — Credentials as Left Panel, Judge-Optimized)
# ═══════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# LOGIN PAGE (v5 — Balanced 2-Column Credential Layout)
# ═══════════════════════════════════════════════════════════════

def render_login_page():
    """Judge-optimized layout with balanced credentials on both sides."""
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # ═════════════════════════════════════════════════════════
    # ROW 1: HERO (LEFT) + LOGIN FORM (RIGHT)
    # ═════════════════════════════════════════════════════════
    left_col, right_col = st.columns([1.1, 1], gap="large")
    
    # ── LEFT: HOSPITAL HERO PANEL ──
    with left_col:
        left_html = (
            '<div class="login-hero-panel">'
            '<div class="login-logo-mark">'
            '<div class="login-logo-icon">'
            '<svg width="30" height="30" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">'
            '<path d="M12 2L2 7v10c0 5 4 9 10 9s10-4 10-9V7l-10-5z" stroke="white" stroke-width="1.5" fill="rgba(255,255,255,0.15)"/>'
            '<path d="M12 8v8M8 12h8" stroke="white" stroke-width="2.5" stroke-linecap="round"/>'
            '</svg>'
            '</div>'
            '<div>'
            f'<div class="login-brand-name">{tr("brand_name")}</div>'
            f'<div class="login-brand-sub">{tr("login_brand_sub")}</div>'
            '</div>'
            '</div>'
            f'<h1 class="login-headline">{tr("login_headline_1")}<br><span class="accent">{tr("login_headline_2")}</span></h1>'
            f'<p class="login-tagline">{tr("login_tagline")}</p>'

            '<div class="feature-pill-grid">'
            
            # 🤖 8 AI Agents
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">🤖</div>'
            f'<div class="feature-pill-text">{tr("feature_agents_title")}<br>{tr("feature_agents_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">🤖 8 Specialized Agents</div>'
            '<div class="tooltip-body">Coordinator, Routing, Appointment, Document, Follow-up, Safety, Query & Knowledge — each with unique prompts, tools & responsibilities.</div>'
            '</div>'
            '</div>'
            
            # 🎤 Voice Input
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">🎤</div>'
            f'<div class="feature-pill-text">{tr("feature_voice_title")}<br>{tr("feature_voice_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">🎤 Speech-to-Text AI</div>'
            '<div class="tooltip-body">Speak your request in any language. Groq Whisper-Large-v3 transcribes voice into text instantly for the AI agents.</div>'
            '</div>'
            '</div>'
            
            # 🌐 4 Languages
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">🌐</div>'
            f'<div class="feature-pill-text">{tr("feature_lang_title")}<br>{tr("feature_lang_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">🌐 Truly Multilingual</div>'
            '<div class="tooltip-body">Full UI + AI responses in English, Hindi, Tamil & Telugu. Inclusive healthcare — not English-only.</div>'
            '</div>'
            '</div>'
            
            # 📚 RAG Powered
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">📚</div>'
            f'<div class="feature-pill-text">{tr("feature_rag_title")}<br>{tr("feature_rag_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">📚 Knowledge Retrieval</div>'
            '<div class="tooltip-body">ChromaDB vector store + sentence-transformer embeddings retrieve hospital policies, procedures & department info to ground answers in real data.</div>'
            '</div>'
            '</div>'
            
            # 🛡️ Safety Guard
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">🛡️</div>'
            f'<div class="feature-pill-text">{tr("feature_safety_title")}<br>{tr("feature_safety_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">🛡️ Human-in-the-Loop</div>'
            '<div class="tooltip-body">Blocks diagnosis, prescriptions & emergency requests. Auto-escalates uncertain cases to human staff with email alerts.</div>'
            '</div>'
            '</div>'
            
            # ⚡ Real-Time
            f'<div class="feature-pill">'
            '<div class="feature-pill-header">'
            '<div class="feature-pill-icon">⚡</div>'
            f'<div class="feature-pill-text">{tr("feature_realtime_title")}<br>{tr("feature_realtime_sub")}</div>'
            '</div>'
            '<div class="feature-tooltip">'
            '<div class="tooltip-divider"></div>'
            '<div class="tooltip-title">⚡ Instant Alerts</div>'
            '<div class="tooltip-body">Every escalation triggers immediate email notifications. Staff dashboard pulses red until reviewed & resolved.</div>'
            '</div>'
            '</div>'
            
            '</div>'  # close feature-pill-grid
        )
        st.markdown(left_html, unsafe_allow_html=True)
    
    # ── RIGHT: LOGIN FORM ──
    with right_col:
        # Language selector
        lang_options = []
        lang_map = {}
        for code, info in LANGUAGES.items():
            display = f"{info['flag']} {info['name']}"
            lang_options.append(display)
            lang_map[display] = code
        
        current_lang = get_language()
        current_display = f"{get_language_flag(current_lang)} {get_language_name(current_lang)}"
        try:
            current_index = lang_options.index(current_display)
        except ValueError:
            current_index = 0
        
        col_sp, col_lang = st.columns([2, 1])
        with col_lang:
            selected = st.selectbox(
                "🌐",
                lang_options,
                index=current_index,
                key="login_lang_selector",
                label_visibility="collapsed",
            )
            new_lang = lang_map[selected]
            if new_lang != current_lang:
                set_language(new_lang)
                st.rerun()
        
        tab_login, tab_register = st.tabs([
            f"🔐  {tr('tab_login')}",
            f"✨  {tr('tab_register')}"
        ])
        
        # ═══ LOGIN TAB ═══
        with tab_login:
            st.markdown(f"""
            <div class="form-title">👋 {tr('welcome_back')}</div>
            <div class="form-subtitle">{tr('enter_credentials')}</div>
            """, unsafe_allow_html=True)
            
            with st.form("login_form"):
                email = st.text_input(f"📧 {tr('email')}", placeholder="you@example.com", key="login_email_input")
                password = st.text_input(f"🔒 {tr('password')}", type="password", placeholder="••••••••", key="login_password_input")
                submit = st.form_submit_button(f"🚀  {tr('sign_in')}", use_container_width=True, type="primary")
            
            if submit:
                if not email or not password:
                    st.error("⚠️ Please enter both email and password.")
                else:
                    _perform_login(email, password)
            
            # ═══ ONE-CLICK DEMO ACCESS ═══
            st.markdown(f"""
            <div class="demo-section-title">
                🎯 {tr('instant_demo_access')}
            </div>
            <p style='color: #64748b; font-size: 12px; margin: -8px 0 12px 0;'>
                {tr('click_any_button')}
            </p>
            """, unsafe_allow_html=True)
            
            demo_col1, demo_col2 = st.columns(2)
            
            with demo_col1:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(13, 148, 136, 0.15), rgba(6, 182, 212, 0.1));
                            border: 1px solid rgba(13, 148, 136, 0.3);
                            border-radius: 12px; padding: 14px; margin-bottom: 8px;'>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <div style='width: 32px; height: 32px; background: linear-gradient(135deg, #0d9488, #06b6d4);
                                    border-radius: 50%; display: flex; align-items: center; 
                                    justify-content: center; color: white; font-size: 16px;'>👤</div>
                        <div>
                            <div style='color: #5eead4; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>{tr('patient_portal_label')}</div>
                            <div style='color: #f1f5f9; font-size: 13px; font-weight: 600;'>John Doe</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚀 {tr('login_as_patient')}", key="quick_patient", use_container_width=True):
                    _perform_login("john.doe@example.com", "Patient@123")
            
            with demo_col2:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.1));
                            border: 1px solid rgba(139, 92, 246, 0.3);
                            border-radius: 12px; padding: 14px; margin-bottom: 8px;'>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <div style='width: 32px; height: 32px; background: linear-gradient(135deg, #8b5cf6, #ec4899);
                                    border-radius: 50%; display: flex; align-items: center; 
                                    justify-content: center; color: white; font-size: 16px;'>👨‍⚕️</div>
                        <div>
                            <div style='color: #c4b5fd; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;'>{tr('staff_portal_label')}</div>
                            <div style='color: #f1f5f9; font-size: 13px; font-weight: 600;'>Admin Staff</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🚀 {tr('login_as_staff')}", key="quick_staff", use_container_width=True):
                    _perform_login("staff1@agentcare.com", "Staff@123")
        
        # ═══ REGISTER TAB ═══
        with tab_register:
            st.markdown(f"""
            <div class="form-title">✨ {tr('create_account')}</div>
            <div class="form-subtitle">{tr('join_message')}</div>
            """, unsafe_allow_html=True)
            
            with st.form("register_form"):
                col_a, col_b = st.columns(2)
                with col_a:
                    r_name = st.text_input(f"👤 {tr('full_name')} *")
                    r_phone = st.text_input(f"📱 {tr('phone')}")
                with col_b:
                    r_email = st.text_input(f"📧 {tr('email')} *")
                    r_dob = st.text_input(f"🎂 {tr('dob_format')}")
                
                r_password = st.text_input(f"🔒 {tr('password')} *", type="password")
                
                col_c, col_d = st.columns(2)
                with col_c:
                    r_age = st.number_input(tr("age"), 0, 120, 0)
                with col_d:
                    r_gender = st.selectbox(tr("gender"), ["", "Male", "Female", "Other"])
                
                r_submit = st.form_submit_button(f"✨  {tr('create_account')}", use_container_width=True, type="primary")
            
            if r_submit:
                if not r_name or not r_email or not r_password:
                    st.error("⚠️ Name, email, and password are required.")
                else:
                    with st.spinner("Creating your account..."):
                        result = api_post("/api/auth/register", {
                            "name": r_name, "email": r_email, "password": r_password,
                            "phone": r_phone or None, "age": r_age if r_age > 0 else None,
                            "gender": r_gender or None, "date_of_birth": r_dob or None,
                        })
                    if result["ok"]:
                        st.success("🎉 Registration successful! Please log in.")
                    else:
                        st.error(f"❌ {result['data'].get('detail', 'Registration failed')}")
    
    # ═════════════════════════════════════════════════════════
    # ROW 2: CREDENTIALS SECTION (BALANCED — Left + Right)
    # ═════════════════════════════════════════════════════════
    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
    
    # Section header
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(94, 234, 212, 0.1), rgba(99, 102, 241, 0.1));
                border: 1px solid rgba(94, 234, 212, 0.25);
                border-radius: 16px; padding: 18px 24px; margin-bottom: 16px;
                display: flex; align-items: center; gap: 14px;'>
        <div style='font-size: 32px;'>📋</div>
        <div>
            <div style='color: #f8fafc; font-size: 20px; font-weight: 800; font-family: "Plus Jakarta Sans", sans-serif;'>
                Test Accounts for Judges
            </div>
            <div style='color: #94a3b8; font-size: 13px; margin-top: 2px;'>
                20 pre-seeded accounts · Copy any credential to test any role instantly
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── BALANCED CREDENTIALS: Left (Patients + Staff/Admin) | Right (Doctors) ──
    creds_left, creds_right = st.columns(2, gap="medium")
    
    # ══════════════════════════════════════════════════
    # LEFT COLUMN: PATIENTS + STAFF/ADMIN
    # ══════════════════════════════════════════════════
    with creds_left:
        left_creds_html = (
            # ─── PATIENT ACCOUNTS ───
            '<div style="background: linear-gradient(135deg, rgba(13, 148, 136, 0.15), rgba(6, 182, 212, 0.08));'
            'border: 1px solid rgba(13, 148, 136, 0.3);'
            'border-radius: 14px; padding: 18px 20px; margin-bottom: 14px;">'
            '<div style="color: #5eead4; font-weight: 700; font-size: 12px;'
            'letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px;'
            'display: flex; align-items: center; gap: 8px;">'
            '👤 PATIENTS'
            '<span style="background: rgba(94, 234, 212, 0.2); color: #5eead4;'
            'padding: 2px 8px; border-radius: 10px; font-size: 10px; text-transform: none;">3 accounts · Password: Patient@123</span>'
            '</div>'
            '<table style="width: 100%; color: #f1f5f9; font-size: 13px; border-collapse: separate; border-spacing: 0;">'
            '<tr style="border-bottom: 1px solid rgba(94, 234, 212, 0.15);">'
            '<td style="padding: 8px 12px; width: 35%;"><b>John Doe</b></td>'
            '<td style="padding: 8px 12px;"><code style="color: #5eead4; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">john.doe@example.com</code></td>'
            '</tr>'
            '<tr style="border-bottom: 1px solid rgba(94, 234, 212, 0.15);">'
            '<td style="padding: 8px 12px;"><b>Priya Singh</b></td>'
            '<td style="padding: 8px 12px;"><code style="color: #5eead4; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">priya.singh@example.com</code></td>'
            '</tr>'
            '<tr>'
            '<td style="padding: 8px 12px;"><b>Rahul Verma</b></td>'
            '<td style="padding: 8px 12px;"><code style="color: #5eead4; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">rahul.verma@example.com</code></td>'
            '</tr>'
            '</table>'
            '</div>'
            
            # ─── STAFF & ADMIN ACCOUNTS ───
            '<div style="background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.08));'
            'border: 1px solid rgba(139, 92, 246, 0.3);'
            'border-radius: 14px; padding: 18px 20px;">'
            '<div style="color: #c4b5fd; font-weight: 700; font-size: 12px;'
            'letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px;'
            'display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">'
            '👨‍💼 STAFF & ADMIN'
            '<span style="background: rgba(196, 181, 253, 0.2); color: #c4b5fd;'
            'padding: 2px 8px; border-radius: 10px; font-size: 10px;">3 accounts</span>'
            '</div>'
            
            # Password legend row
            '<div style="display: flex; gap: 16px; margin-bottom: 12px; padding: 8px 10px;'
            'background: rgba(15, 23, 42, 0.4); border-radius: 8px; font-size: 11px;">'
            '<div><span style="color: #94a3b8;">🔑 Admin:</span> '
            '<code style="color: #fbbf24; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">Admin@123</code></div>'
            '<div><span style="color: #94a3b8;">🔑 Staff:</span> '
            '<code style="color: #fbbf24; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">Staff@123</code></div>'
            '</div>'
            
            '<table style="width: 100%; color: #f1f5f9; font-size: 13px; border-collapse: separate; border-spacing: 0;">'
            '<tr style="border-bottom: 1px solid rgba(196, 181, 253, 0.15);">'
            '<td style="padding: 8px 12px; width: 40%;">'
            '<b>Admin User</b> '
            '<span style="background: rgba(236, 72, 153, 0.2); color: #f9a8d4;'
            'padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: 700; margin-left: 4px;">ADMIN</span>'
            '</td>'
            '<td style="padding: 8px 12px;">'
            '<code style="color: #c4b5fd; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">admin@agentcare.com</code>'
            '</td>'
            '</tr>'
            '<tr style="border-bottom: 1px solid rgba(196, 181, 253, 0.15);">'
            '<td style="padding: 8px 12px;"><b>Staff Alice</b></td>'
            '<td style="padding: 8px 12px;">'
            '<code style="color: #c4b5fd; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">staff1@agentcare.com</code>'
            '</td>'
            '</tr>'
            '<tr>'
            '<td style="padding: 8px 12px;"><b>Staff Bob</b></td>'
            '<td style="padding: 8px 12px;">'
            '<code style="color: #c4b5fd; background: rgba(15,23,42,0.6); padding: 3px 8px; border-radius: 4px; font-size: 11px;">staff2@agentcare.com</code>'
            '</td>'
            '</tr>'
            '</table>'
            '</div>'
            
        )
        st.markdown(left_creds_html, unsafe_allow_html=True)
    
    # ══════════════════════════════════════════════════
    # RIGHT COLUMN: DOCTORS (14)
    # ══════════════════════════════════════════════════
    with creds_right:
        right_creds_html = (
            '<div style="background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(16, 185, 129, 0.08));'
            'border: 1px solid rgba(59, 130, 246, 0.3);'
            'border-radius: 14px; padding: 18px 20px;">'
            
            '<div style="color: #93c5fd; font-weight: 700; font-size: 12px;'
            'letter-spacing: 1px; text-transform: uppercase; margin-bottom: 12px;'
            'display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">'
            '👨‍⚕️ DOCTORS'
            '<span style="background: rgba(147, 197, 253, 0.2); color: #93c5fd;'
            'padding: 2px 8px; border-radius: 10px; font-size: 10px; text-transform: none;">14 accounts · Password: Doctor@123</span>'
            
            '<table style="width: 100%; color: #f1f5f9; font-size: 12px; border-collapse: separate; border-spacing: 0; text-transform: none;">'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px; width: 40%;"><b>Dr. Aisha Sharma</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">aisha.sharma@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Rajan Mehta</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">rajan.mehta@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Priya Nair</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">priya.nair@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Kavita Joshi</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">kavita.joshi@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Arjun Patel</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">arjun.patel@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Meena Krishnan</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">meena.krishnan@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Vikram Reddy</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">vikram.reddy@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Sunita Agarwal</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">sunita.agarwal@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Farah Sheikh</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">farah.sheikh@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Rohit Gupta</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">rohit.gupta@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Ananya Pillai</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">ananya.pillai@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Deepa Iyer</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">deepa.iyer@agentcare.com</code></td></tr>'
            '<tr style="border-bottom: 1px solid rgba(147, 197, 253, 0.15);"><td style="padding: 6px 12px;"><b>Dr. Nikhil Bose</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">nikhil.bose@agentcare.com</code></td></tr>'
            '<tr><td style="padding: 6px 12px;"><b>Dr. Samuel D\'souza</b></td><td style="padding: 6px 12px;"><code style="color: #93c5fd; background: rgba(15,23,42,0.6); padding: 2px 6px; border-radius: 4px; font-size: 10px;">samuel.dsouza@agentcare.com</code></td></tr>'
            '</table>'
            '</div>'
        )
        st.markdown(right_creds_html, unsafe_allow_html=True)
    
    # ── Judge Tip Footer ──
    st.markdown("""
    <div style='background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 12px; padding: 14px 18px; margin-top: 16px;'>
        <div style='color: #fbbf24; font-size: 13px; line-height: 1.6;'>
            💡 <b>Judge Tip:</b> Each role gets a completely different portal experience — 
            <b>Patients</b> chat with 8 AI agents to book appointments, upload docs, and ask questions · 
            <b>Doctors</b> view their schedule, patient records, and clinical notes · 
            <b>Staff/Admin</b> access analytics, escalations, workflows, and full system control.
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Final footer ──
    st.markdown(f"""
    <div style='text-align: center; margin-top: 30px; padding: 20px; color: #64748b; font-size: 12px;'>
        <div style='margin-bottom: 8px;'>
            🏥 <b>{tr('brand_name')}</b> · {tr('footer_built_for')}
        </div>
        <div>
            {tr('footer_disclaimer')}
        </div>
    </div>
    """, unsafe_allow_html=True)


def _perform_login(email: str, password: str):
    """Login with clear visual feedback."""
    # Use st.status for a nicer loading indicator
    with st.status("🔒 Signing you in...", expanded=False) as status:
        st.write("Authenticating credentials...")
        result = api_login(email, password)

        if result["ok"]:
            st.write("✅ Loading your portal...")
            data = result["data"]
            st.session_state["token"] = data["access_token"]
            st.session_state["role"] = data["role"]
            st.session_state["user_id"] = data["user_id"]
            st.session_state["name"] = data["name"]
            st.session_state["email"] = data["email"]
            status.update(label="✅ Success! Redirecting...", state="complete")
            time.sleep(0.4)
            st.rerun()
        else:
            status.update(label="❌ Login failed", state="error")
            st.error(f"{result['data'].get('detail', 'Login failed')}")

# ═══════════════════════════════════════════════════════════════
# PATIENT PORTAL
# ═══════════════════════════════════════════════════════════════

def render_patient_portal():
    token = get_token()
    
    # Load user's preferred language on first render
    load_language_from_profile(token)
    
    with st.sidebar:
        sidebar_brand()
        sidebar_user_card(get_user_name(), "Patient")
        
        # NEW: Language switcher
        sidebar_language_switcher()
        
        st.markdown("---")
        st.markdown(f"### 📍 {tr('navigation')}")
        nav_labels = {
            f"🏠 {tr('nav_dashboard')}": "dashboard",
            f"🤖 {tr('nav_ai_assistant')}": "ai_assistant",
            f"📅 {tr('nav_appointments')}": "appointments",
            f"📄 {tr('nav_documents')}": "documents",
            f"🔔 {tr('nav_reminders')}": "reminders",
            f"📬 {tr('nav_notifications')}": "notifications",
            f"👤 {tr('nav_profile')}": "profile",
        }
        
        page_label = st.radio(
            "nav",
            list(nav_labels.keys()),
            label_visibility="collapsed",
            key="patient_nav_radio",
        )
        page = nav_labels[page_label]
        
        st.markdown("---")
        if st.button(f"🚪 {tr('sign_out')}", use_container_width=True):
            logout()
    
    if page == "dashboard":
        render_patient_dashboard(token)
    elif page == "ai_assistant":
        render_submit_request(token)
    elif page == "appointments":
        render_my_appointments(token)
    elif page == "documents":
        render_my_documents(token)
    elif page == "reminders":
        render_my_reminders(token)
    elif page == "notifications":
        render_patient_notifications(token)
    elif page == "profile":
        render_my_profile(token)    


def render_patient_dashboard(token):
    hero_header(f"{tr('dashboard_welcome')}, {get_user_name()}! 👋")
    
    # Fetch data
    appt_result = api_get("/api/appointments/my", token)
    doc_result = api_get("/api/documents/my", token)
    wf_result = api_get("/api/workflow/history", token)
    
    appt_count = len(appt_result["data"].get("appointments", [])) if appt_result["ok"] else 0
    doc_count = len(doc_result["data"].get("documents", [])) if doc_result["ok"] else 0
    wf_count = len(wf_result["data"].get("workflows", [])) if wf_result["ok"] else 0
    
    active_appts = 0
    if appt_result["ok"]:
        active_appts = len([a for a in appt_result["data"].get("appointments", [])
                           if a["status"] in ["confirmed", "pending", "rescheduled"]])
    
    # Stats Grid
    st.markdown(f"### 📊 {tr('your_overview')}")
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("📅", appt_count, tr("total_appointments"))
    with c2: stat_card("✅", active_appts, tr("active_appointments"))
    with c3: stat_card("📄", doc_count, tr("documents_uploaded"))
    with c4: stat_card("🔄", wf_count, tr("ai_requests"))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown(f"### ⚡ {tr('quick_actions')}")
    q1, q2, q3 = st.columns(3)
    with q1:
        st.markdown(f"""
        <div class="stat-box" style="cursor: pointer;">
            <div class="stat-icon">🤖</div>
            <div style="color: #f8fafc; font-weight: 700; font-size: 16px;">{tr('nav_ai_assistant')}</div>
            <div class="stat-label">{tr('ask_anything')}</div>
        </div>
        """, unsafe_allow_html=True)
    with q2:
        st.markdown(f"""
        <div class="stat-box" style="cursor: pointer;">
            <div class="stat-icon">📅</div>
            <div style="color: #f8fafc; font-weight: 700; font-size: 16px;">{tr('book_appointment')}</div>
            <div class="stat-label">{tr('schedule_now')}</div>
        </div>
        """, unsafe_allow_html=True)
    with q3:
        st.markdown(f"""
        <div class="stat-box" style="cursor: pointer;">
            <div class="stat-icon">📄</div>
            <div style="color: #f8fafc; font-weight: 700; font-size: 16px;">{tr('nav_documents')}</div>
            <div class="stat-label">{tr('share_records')}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Recent Appointments
    st.markdown(f"### 📅 {tr('upcoming_appointments')}")
    if appt_result["ok"]:
        appts = appt_result["data"].get("appointments", [])
        upcoming = [a for a in appts if a["status"] in ["confirmed", "pending", "rescheduled"]][:3]
        
        if upcoming:
            for appt in upcoming:
                appointment_card(appt)
        else:
            st.info("💡 No upcoming appointments. Use the AI Assistant to book one!")


def render_submit_request(token):
    """Chat-based AI Assistant interface."""
    
    # Initialize chat history in session state
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    
    # ═══════════════════════════════════════════════════════
    # CHAT HEADER
    # ═══════════════════════════════════════════════════════
        # Get message count for header
    msg_count = len(st.session_state.get("chat_messages", []))
    user_msgs = len([m for m in st.session_state.get("chat_messages", []) if m["role"] == "user"])
    
    col_title, col_new_chat = st.columns([4, 1])
    
    with col_title:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px 24px; border-radius: 16px; margin-bottom: 16px;
                    box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
                    position: relative; overflow: hidden;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <h2 style='color: white; margin: 0; font-weight: 800; display: flex; align-items: center; gap: 10px;'>
                        💬 AI Assistant Chat
                        <span style='background: rgba(255,255,255,0.25); padding: 4px 12px; border-radius: 20px;
                                     font-size: 12px; font-weight: 600;'>
                            🟢 Online
                        </span>
                    </h2>
                    <p style='color: rgba(255,255,255,0.9); margin: 6px 0 0 0; font-size: 13px;'>
                        Powered by 7 AI agents · {user_msgs} message{'s' if user_msgs != 1 else ''} in this conversation
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_new_chat:
        st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 New Chat", use_container_width=True, key="new_chat_btn"):
            st.session_state["chat_messages"] = []
            st.rerun()
    
    # ═══════════════════════════════════════════════════════
    # WELCOME MESSAGE (only if no chat history)
    # ═══════════════════════════════════════════════════════
    if not st.session_state["chat_messages"]:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(f"""
            <div>
                <h4 style='color: #a5b4fc; margin: 0 0 8px 0;'>
                    Hello {get_user_name()}! 👋
                </h4>
                <p style='color: #cbd5e1; margin: 0 0 12px 0;'>
                    I'm your AgentCare assistant. I can help you with:
                </p>
                <ul style='color: #cbd5e1; margin: 0 0 12px 0; padding-left: 20px;'>
                    <li>📅 Booking, rescheduling, or canceling appointments</li>
                    <li>👨‍⚕️ Finding doctors by department</li>
                    <li>🔍 Checking available time slots</li>
                    <li>📄 Managing your medical documents</li>
                </ul>
                <p style='color: #94a3b8; font-size: 13px; margin: 0;'>
                    💡 Try one of the suggestions below or type your own message!
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        # Suggestion buttons
        st.markdown("**💡 Quick suggestions:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💊 Book cardiology for tomorrow at 10 AM", use_container_width=True, key="sug_1"):
                _send_chat_message("Book cardiology for tomorrow at 10 AM", token)
                st.rerun()
        
        with col2:
            if st.button("📅 Show my appointments", use_container_width=True, key="sug_2"):
                _send_chat_message("Show me my appointments", token)
                st.rerun()
        
        with col3:
            if st.button("👨‍⚕️ Show doctors in neurology", use_container_width=True, key="sug_3"):
                _send_chat_message("Show me doctors in neurology", token)
                st.rerun()
        
        col4, col5, col6 = st.columns(3)
        with col4:
            if st.button("🔍 What can you do?", use_container_width=True, key="sug_4"):
                _send_chat_message("What can you do?", token)
                st.rerun()
        with col5:
            if st.button("📄 Show my documents", use_container_width=True, key="sug_5"):
                _send_chat_message("Show me my documents", token)
                st.rerun()
        with col6:
            if st.button("📊 Cardiology slots for July 27", use_container_width=True, key="sug_6"):
                _send_chat_message("Show me cardiology slots for July 27", token)
                st.rerun()
    
    # ═══════════════════════════════════════════════════════
    # CHAT HISTORY DISPLAY
    # ═══════════════════════════════════════════════════════
    for msg_idx, msg in enumerate(st.session_state["chat_messages"]):
        if msg["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(msg["content"])
                if msg.get("timestamp"):
                    st.caption(f"🕐 {msg['timestamp']}")
        else:
            with st.chat_message("assistant", avatar="🤖"):
                # Render the assistant's response with unique msg index
                _render_chat_response(msg.get("data", {}), msg_idx=msg_idx)
                if msg.get("timestamp"):
                    st.caption(f"🕐 {msg['timestamp']}")
    
    # ═══════════════════════════════════════════════════════
    # CHAT INPUT AT BOTTOM
    # ═══════════════════════════════════════════════════════
    

    # ═══════════════════════════════════════════════════════
    # FILE UPLOAD + VOICE INPUT + CHAT INPUT
    # ═══════════════════════════════════════════════════════
    
    # File upload expander
    
    # ═══════════════════════════════════════════════════════
    # WHATSAPP-STYLE CHAT INPUT (Mic + File + Text in one row)
    # ═══════════════════════════════════════════════════════
    
    # Optional file upload (collapsible above input)
    with st.expander("📎 Attach a document (optional)"):
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "jpg", "jpeg", "png", "txt"],
            key="chat_file_uploader",
            label_visibility="collapsed",
        )
        if uploaded_file:
            st.session_state["chat_pending_file"] = {
                "name": uploaded_file.name,
                "content": uploaded_file.getvalue(),
                "type": uploaded_file.type,
            }
            st.success(f"📎 **{uploaded_file.name}** attached to next message")
    
    # ─── Show attached file indicator ─────────────────────────
    if "chat_pending_file" in st.session_state:
        pending = st.session_state["chat_pending_file"]
        col_file, col_remove = st.columns([5, 1])
        with col_file:
            st.info(f"📎 File ready: **{pending['name']}**")
        with col_remove:
            if st.button("❌ Remove", key="remove_file"):
                st.session_state.pop("chat_pending_file", None)
                st.rerun()
    
    # ─── Voice indicator (if user recorded audio) ─────────────
    if "chat_voice_ready" in st.session_state:
        voice_text = st.session_state.get("chat_voice_ready", "")
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, rgba(139, 92, 246, 0.15), rgba(236, 72, 153, 0.15));
                    border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 12px;
                    padding: 12px 16px; margin: 8px 0;'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <div style='font-size: 20px;'>🎤</div>
                <div style='flex: 1;'>
                    <div style='color: #a5b4fc; font-weight: 600; font-size: 12px;'>VOICE MESSAGE</div>
                    <div style='color: #f8fafc; margin-top: 4px;'>{voice_text}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col_send, col_cancel = st.columns([3, 1])
        with col_send:
            if st.button("📤 Send Voice Message", use_container_width=True, type="primary", key="send_voice_msg"):
                pending_file = st.session_state.pop("chat_pending_file", None)
                _send_chat_message(voice_text, token, pending_file)
                st.session_state.pop("chat_voice_ready", None)
                st.rerun()
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True, key="cancel_voice"):
                st.session_state.pop("chat_voice_ready", None)
                st.rerun()
    
    # ─── MAIN INPUT ROW: Text field + Mic button (WhatsApp style) ─────
    # ═══════════════════════════════════════════════════════
    # WHATSAPP-STYLE INPUT ROW (Mic + Text + Send inline)
    # ═══════════════════════════════════════════════════════


    # ═══════════════════════════════════════════════════════
    # WHATSAPP-STYLE INPUT ROW (Mic + Text + Send)
    # ═══════════════════════════════════════════════════════

    
    # ═══════════════════════════════════════════════════════
    # UNIFIED CHAT INPUT (Voice + Text + Send in one clean row)
    # ═══════════════════════════════════════════════════════
    st.markdown("---")
    
    # Nice header
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.08));
                border: 1px solid rgba(99, 102, 241, 0.2); 
                border-radius: 16px; 
                padding: 12px 20px; 
                margin: 12px 0;'>
        <div style='color: #a5b4fc; font-size: 12px; font-weight: 600; 
                    text-transform: uppercase; letter-spacing: 1px;
                    display: flex; align-items: center; gap: 8px;'>
            💬 Send a Message
            <span style='color: #64748b; font-weight: 400; text-transform: none; letter-spacing: 0;'>
                · Type or tap 🎤 to speak
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Row layout: Voice | Text | Send
    col_mic, col_text_wrap, col_send_wrap = st.columns([1.2, 6, 1.5])
    
    # ─── VOICE (Outside form for real-time trigger) ─────
    with col_mic:
        try:
            from streamlit_mic_recorder import mic_recorder
            
            audio = mic_recorder(
                start_prompt="🎤 Voice",
                stop_prompt="⏹️ Stop",
                just_once=True,
                use_container_width=True,
                key="whatsapp_mic",
            )
            
            if audio and audio.get("bytes"):
                st.session_state["pending_voice_audio"] = audio["bytes"]
                st.rerun()
        except ImportError:
            st.button("🎤 Voice", disabled=True, use_container_width=True)
    
    # ─── TEXT + SEND (Inside form for Enter-to-send) ─────
    with col_text_wrap:
        with st.form("whatsapp_chat_form", clear_on_submit=True):
            col_text_inner, col_send_inner = st.columns([5, 1])
            
            with col_text_inner:
                typed_message = st.text_input(
                    "Message",
                    placeholder="💬 Type your message here...",
                    label_visibility="collapsed",
                    key="whatsapp_text_input",
                )
            
            with col_send_inner:
                send_clicked = st.form_submit_button(
                    "➤",
                    use_container_width=True,
                    type="primary",
                )
            
            if send_clicked and typed_message and typed_message.strip():
                pending_file = st.session_state.pop("chat_pending_file", None)
                _send_chat_message(typed_message.strip(), token, pending_file)
                st.rerun()
    
    # ─── HELPER TEXT (Right side) ─────
    with col_send_wrap:
        st.markdown("""
        <div style='height: 42px; display: flex; align-items: center; 
                    justify-content: center; color: #a5b4fc; font-size: 12px;
                    background: rgba(99, 102, 241, 0.05); border-radius: 10px;
                    border: 1px dashed rgba(99, 102, 241, 0.3);'>
            ⌨️ Press Enter
        </div>
        """, unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════
    # PROCESS PENDING VOICE (transcribe → auto-send)
    # ═══════════════════════════════════════════════════════
    if "pending_voice_audio" in st.session_state:
        audio_bytes = st.session_state.pop("pending_voice_audio")
        
        with st.spinner("🎙️ Transcribing your voice with AI..."):
            try:
                from groq import Groq
                from config import settings
                
                groq_client = Groq(api_key=settings.GROQ_API_KEY)
                
                lang_map = {
                    "en": "en",
                    "hi": "hi",
                    "ta": "ta",
                    "te": "te",
                }
                current_lang = lang_map.get(get_language(), "en")
                
                transcription = groq_client.audio.transcriptions.create(
                    file=("voice.wav", audio_bytes, "audio/wav"),
                    model="whisper-large-v3",
                    language=current_lang,
                    response_format="text",
                )
                
                transcribed_text = str(transcription).strip()
                
                if transcribed_text:
                    pending_file = st.session_state.pop("chat_pending_file", None)
                    _send_chat_message(transcribed_text, token, pending_file)
                    st.rerun()
                else:
                    st.error("❌ Could not understand audio. Please try again.")
                    
            except Exception as e:
                st.error(f"❌ Transcription failed: {str(e)}")



def _build_chat_history_for_backend() -> list:
    """Extract previous chat messages as clean text for backend context."""
    history = []
    messages = st.session_state.get("chat_messages", [])
    
    for msg in messages[-10:]:
        if msg["role"] == "user":
            history.append({
                "role": "user",
                "content": str(msg.get("content", ""))[:400]
            })
        elif msg["role"] == "assistant":
            data = msg.get("data", {})
            summary = _summarize_assistant_response(data)
            if summary:
                history.append({
                    "role": "assistant",
                    "content": summary[:400]
                })
    
    return history


def _summarize_assistant_response(data: dict) -> str:
    """Extract short summary from bot's response for LLM context."""
    if not data:
        return ""
    
    if data.get("is_query"):
        query_result = data.get("query_result", {})
        q_type = query_result.get("type", "")
        d = query_result.get("data", {}) or {}
        
        if q_type == "list_slots":
            slots = d.get("slots", [])[:5]
            if slots:
                slot_text = " | ".join(
                    f"{s['doctor_name']} on {s['date']} at {s['time']}"
                    for s in slots
                )
                return f"Showed slots: {slot_text}"
        
        elif q_type == "list_doctors":
            doctors = d.get("doctors", [])[:5]
            if doctors:
                return f"Showed doctors: {', '.join(dd['name'] for dd in doctors)}"
        
        elif q_type == "list_appointments":
            active = d.get("active", [])
            if active:
                first = active[0]
                return f"Showed appointments including: {first.get('doctor_name')} on {first.get('date')} at {first.get('time')}"
        
        return query_result.get("message", "")[:300]
    
    appt = data.get("appointment") or {}
    if appt.get("action") == "slot_unavailable":
        alternatives = appt.get("available_slots", [])[:3]
        if alternatives:
            alt_text = " | ".join(
                f"{a['doctor_name']} at {a['time']}"
                for a in alternatives
            )
            return f"Preferred slot unavailable. Offered alternatives: {alt_text}"
    
    if appt.get("success"):
        a = appt.get("appointment", {})
        if a:
            return f"Booked {a.get('doctor_name')} on {a.get('date')} at {a.get('time')}"
    
    if data.get("blocked"):
        return f"Blocked request. Reason: {data.get('message', '')[:100]}"
    
    if data.get("success"):
        return data.get("summary", "")[:200]
    
    return ""


def _send_chat_message(user_input: str, token: str, pending_file: dict = None):
    """Helper to send a user message and get bot response."""
    from datetime import datetime
    timestamp = datetime.now().strftime("%I:%M %p")
    
    # Add file info to user message if attached
    display_content = user_input
    if pending_file:
        display_content = f"{user_input}\n\n📎 _Attached: {pending_file['name']}_"
    
    # Ensure chat_messages exists
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    
    # Add user message to history
    st.session_state["chat_messages"].append({
        "role": "user",
        "content": display_content,
        "timestamp": timestamp,
    })
    
    # Initialize result BEFORE the status block (prevents UnboundLocalError)
    result = {"ok": False, "data": {"detail": "No response"}}
    
    # Build chat history for context memory
    chat_history_payload = _build_chat_history_for_backend()
    
    form_data = {
        "request_text": user_input,
        "file_description": "",
        "chat_history": json.dumps(chat_history_payload),
    }
    files = None
    if pending_file:
        files = {"file": (pending_file["name"], pending_file["content"], pending_file["type"])}
    
    # Call the API with live status
    with st.status("🤖 AI agents processing your request...", expanded=False) as status:
        st.write("🛡️ Safety Agent · checking...")
        st.write("🗺️ Routing Agent · classifying...")
        st.write("📅 Appointment Agent · processing...")
        if pending_file:
            st.write("📄 Document Agent · analyzing file...")
        st.write("🔔 Follow-up Agent · scheduling...")
        
        try:
            api_response = api_post_form(
                "/api/workflow/submit",
                data=form_data,
                files=files,
                token=token,
            )
            
            if api_response:
                result = api_response
            
            if result.get("ok"):
                status.update(label="✅ Complete!", state="complete")
            else:
                status.update(label="❌ Failed", state="error")
        except Exception as e:
            status.update(label=f"❌ Error: {str(e)}", state="error")
    
    # Add bot response to history
    bot_timestamp = datetime.now().strftime("%I:%M %p")
    
    if result.get("ok"):
        st.session_state["chat_messages"].append({
            "role": "assistant",
            "data": result.get("data", {}),
            "timestamp": bot_timestamp,
        })
    else:
        error_msg = "Something went wrong"
        try:
            if result.get("data"):
                error_msg = result["data"].get("detail", error_msg)
        except Exception:
            pass
        
        st.session_state["chat_messages"].append({
            "role": "assistant",
            "data": {
                "success": False,
                "message": f"❌ {error_msg}",
            },
            "timestamp": bot_timestamp,
        })

        files = None
        if pending_file:
            files = {"file": (pending_file["name"], pending_file["content"], pending_file["type"])}
        
        result = api_post_form(
            "/api/workflow/submit",
            data=form_data,
            files=files,
            token=token,
        )
        
        if result["ok"]:
            status.update(label="✅ Complete!", state="complete")
        else:
            status.update(label="❌ Failed", state="error")
    
    

def _render_chat_response(data: dict, msg_idx: int = 0):
    """
    Renders bot responses in chat format.
    Handles all response types: queries, bookings, alternatives, errors.
    """
    if not data:
        st.markdown("_No response received._")
        return
    
    # ═══ QUERY RESULT ═══
    if data.get("is_query"):
        _render_chat_query(data.get("query_result", {}), msg_idx=msg_idx)
        return
    
    # ═══ KNOWLEDGE RESULT (RAG) ═══
    if data.get("is_knowledge"):
        _render_knowledge_response(data.get("knowledge_result", {}))
        return
    
    # ═══ BLOCKED / SAFETY ═══
    if data.get("blocked"):
        st.markdown(f"""
        <div style='color: #f87171;'>
            <b>🚫 Request Blocked</b><br>
            <span style='color: #fecaca; font-size: 14px;'>{data.get('message', '')}</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # ═══ EMERGENCY ═══
    if data.get("emergency"):
        st.markdown(f"""
        <div style='color: #fbbf24;'>
            <b>⚠️ Emergency Detected</b><br>
            <span style='color: #fde68a; font-size: 14px;'>{data.get('message', '')}</span>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # ═══ MISSING INFO (date/time) ═══
    appt_result = data.get("appointment") or {}
    if appt_result.get("missing_info"):
        missing_labels = {
            "date": "day",
            "time": "time",
            "both": "day and time",
        }
        missing = missing_labels.get(appt_result.get("missing_info"), "details")
        
        st.markdown(f"""
        <div style='color: #fbbf24;'>
            <b>⚠️ I need more information</b><br>
            <span style='color: #fde68a; font-size: 14px;'>
                Please tell me the <b>{missing}</b> for your appointment.
            </span>
        </div>
        
        **💡 Try these examples:**
        - "Book cardiology for **tomorrow at 10 AM**"
        - "Book cardiology for **Wednesday at 3 PM**"
        - "Schedule dermatology **next Monday at 11 AM**"
        """, unsafe_allow_html=True)
        
        sample_slots = appt_result.get("available_slots", [])
        if sample_slots:
            st.markdown("**💡 Some currently available slots:**")
            for slot in sample_slots[:5]:
                st.markdown(
                    f"• 👨‍⚕️ **{slot['doctor_name']}** — {slot['date']} at {slot['time']}"
                )
        return
    
    # ═══ SLOT UNAVAILABLE — SHOW ALTERNATIVES ═══
    if appt_result.get("action") == "slot_unavailable":
        alternatives = appt_result.get("available_slots", [])
        requested_date = appt_result.get("requested_date", "your preferred date")
        requested_time = appt_result.get("requested_time", "")
        
        st.markdown(f"""
        <div style='color: #f87171;'>
            <b>❌ Slot Not Available</b><br>
            <span style='color: #fecaca; font-size: 14px;'>
                Your requested slot on <b>{requested_date}{requested_time}</b> is already booked.
                Here are some alternatives:
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        if alternatives:
            for i in range(0, len(alternatives), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(alternatives):
                        slot = alternatives[i + j]
                        with col:
                            st.markdown(f"""
                            <div style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4);
                                        padding: 12px; border-radius: 10px; margin: 6px 0;'>
                                <div style='color: #f8fafc; font-weight: 700; font-size: 14px;'>
                                    👨‍⚕️ {slot['doctor_name']}
                                </div>
                                <div style='color: #94a3b8; font-size: 12px;'>{slot.get('specialization', 'General')}</div>
                                <div style='color: #a5b4fc; font-size: 13px; margin-top: 4px;'>
                                    📅 {slot['date']} · 🕐 {slot['time']}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Unique key using message count + slot ID
                            btn_key = f"chat_book_{len(st.session_state.get('chat_messages', []))}_{slot['slot_id']}_{i}_{j}"
                            if st.button(f"✅ Book This", key=btn_key, use_container_width=True):
                                with st.spinner("Booking..."):
                                    book_result = api_post(
                                        "/api/appointments/book",
                                        {"slot_id": slot["slot_id"], "reason": "Alternative slot chosen"},
                                        token=get_token(),
                                    )
                                if book_result["ok"]:
                                    appt = book_result["data"].get("appointment", {})
                                    from datetime import datetime as _dt
                                    st.session_state["chat_messages"].append({
                                        "role": "assistant",
                                        "data": {
                                            "success": True,
                                            "summary": f"Booked with {appt.get('doctor_name')} on {appt.get('date')} at {appt.get('time')}",
                                            "safety": {"risk_level": "none", "is_safe": True},
                                            "appointment": {"success": True, "action": "book", "appointment": appt, "message": "Booked"},
                                            "followup": None,
                                            "document": None,
                                        },
                                        "timestamp": _dt.now().strftime("%I:%M %p"),
                                    })
                                    st.rerun()
                                else:
                                    st.error(f"❌ {book_result['data'].get('detail', 'Failed')}")
        return
    
    # ═══ SUCCESSFUL BOOKING ═══
    if data.get("success"):
        st.markdown(f"""
        <div style='color: #34d399;'>
            <b>✅ {data.get('summary', 'Request completed')}</b>
        </div>
        """, unsafe_allow_html=True)
        
        # Show agent pipeline in a compact format
        with st.expander("🤖 View AI Agent Pipeline", expanded=False):
            safety = data.get("safety", {})
            st.markdown(f"🛡️ **Safety Agent** — ✅ Safe (Risk: {safety.get('risk_level', 'none')})")
            
            dept = data.get("department")
            if dept:
                conf = int(dept.get("confidence", 0) * 100)
                st.markdown(f"🗺️ **Routing Agent** — Routed to {dept.get('department_name')} ({conf}%)")
            
            if appt_result and appt_result.get("success"):
                appt = appt_result.get("appointment", {})
                if appt:
                    st.markdown(f"📅 **Appointment Agent** — Booked with {appt.get('doctor_name')} at {appt.get('time')}")
            
            doc_result = data.get("document")
            if doc_result and doc_result.get("success"):
                doc = doc_result.get("document", {})
                st.markdown(f"📄 **Document Agent** — Classified as {doc.get('document_type', 'unknown')}")
            
            fu_result = data.get("followup")
            if fu_result and fu_result.get("success"):
                st.markdown(f"🔔 **Follow-up Agent** — {fu_result.get('total_reminders', 0)} reminders scheduled")
        
        # Show appointment card if booking
        if appt_result and appt_result.get("success"):
            appt = appt_result.get("appointment", {})
            if appt:
                st.markdown(f"""
                <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
                            border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px; margin: 12px 0;'>
                    <div style='color: #34d399; font-weight: 700; font-size: 15px; margin-bottom: 8px;'>
                        📋 Appointment Confirmed
                    </div>
                    <div style='color: #d1fae5; font-size: 14px;'>
                        <div>👨‍⚕️ <b>{appt.get('doctor_name')}</b></div>
                        <div>📅 {appt.get('date')} at {appt.get('time')}</div>
                        <div>🆔 Appointment #{appt.get('appointment_id')}</div>
                    </div>
                </div>
                <div style='color: #6ee7b7; font-size: 13px; margin-top: 8px;'>
                    📧 Confirmation email sent to <b>{get_user_email()}</b>
                </div>
                """, unsafe_allow_html=True)
        return
    
    # ═══ GENERIC FAILURE ═══
    st.markdown(f"""
    <div style='color: #f87171;'>
        <b>❌ Request Failed</b><br>
        <span style='color: #fecaca;'>{data.get('message', 'Unknown error')}</span>
    </div>
    """, unsafe_allow_html=True)

def _build_chat_history_for_backend() -> list:
    """
    Extracts previous chat messages as clean text for backend context.
    Returns list of {"role": "user"/"assistant", "content": "..."}.
    """
    history = []
    messages = st.session_state.get("chat_messages", [])
    
    # Skip the message we're about to send (last user msg is current one being sent)
    for msg in messages[-10:]:  # Only last 10 messages
        if msg["role"] == "user":
            history.append({
                "role": "user",
                "content": str(msg.get("content", ""))[:400]
            })
        elif msg["role"] == "assistant":
            # Extract meaningful text from assistant response
            data = msg.get("data", {})
            summary = _summarize_assistant_response(data)
            if summary:
                history.append({
                    "role": "assistant",
                    "content": summary[:400]
                })
    
    return history


def _summarize_assistant_response(data: dict) -> str:
    """Extracts short summary from bot's response for LLM context."""
    if not data:
        return ""
    
    # Handle query results
    if data.get("is_query"):
        query_result = data.get("query_result", {})
        q_type = query_result.get("type", "")
        d = query_result.get("data", {}) or {}
        
        if q_type == "list_slots":
            slots = d.get("slots", [])[:5]
            if slots:
                slot_text = " | ".join(
                    f"{s['doctor_name']} on {s['date']} at {s['time']}"
                    for s in slots
                )
                return f"Showed slots: {slot_text}"
        
        elif q_type == "list_doctors":
            doctors = d.get("doctors", [])[:5]
            if doctors:
                return f"Showed doctors: {', '.join(d['name'] for d in doctors)}"
        
        elif q_type == "list_appointments":
            active = d.get("active", [])
            if active:
                first = active[0]
                return f"Showed appointments including: {first.get('doctor_name')} on {first.get('date')} at {first.get('time')}"
        
        return query_result.get("message", "")[:300]
    
    # Handle appointment outcomes
    appt = data.get("appointment") or {}
    if appt.get("action") == "slot_unavailable":
        alternatives = appt.get("available_slots", [])[:3]
        if alternatives:
            alt_text = " | ".join(
                f"{a['doctor_name']} at {a['time']}"
                for a in alternatives
            )
            return f"Preferred slot unavailable. Offered alternatives: {alt_text}"
    
    if appt.get("success"):
        a = appt.get("appointment", {})
        if a:
            return f"Booked {a.get('doctor_name')} on {a.get('date')} at {a.get('time')}"
    
    if data.get("blocked"):
        return f"Blocked request. Reason: {data.get('message', '')[:100]}"
    
    if data.get("success"):
        return data.get("summary", "")[:200]
    
    return ""    

def _render_knowledge_response(kr: dict):
    """Renders Knowledge Agent (RAG) responses beautifully in chat."""
    if not kr:
        st.markdown("_No information found._")
        return
    
    answer = kr.get("answer", "I couldn't find an answer.")
    detailed = kr.get("detailed_answer", "")
    sources = kr.get("sources", [])
    chunks = kr.get("chunks_used", [])
    found = kr.get("found_relevant_info", True)
    safety = kr.get("safety_note")
    score = kr.get("top_similarity_score", 0)
    
    # Main answer
    if found and answer:
        st.markdown(f"""
        <div style='color: #f8fafc; font-size: 15px; line-height: 1.6;'>
            {answer}
        </div>
        """, unsafe_allow_html=True)
        
        # Detailed answer (if available)
        if detailed:
            st.markdown(f"""
            <div style='color: #cbd5e1; font-size: 14px; margin-top: 8px; line-height: 1.5;'>
                {detailed}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(f"_{answer}_")
    
    # Safety note
    if safety:
        st.markdown(f"""
        <div style='background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b;
                    padding: 8px 12px; border-radius: 6px; margin-top: 10px;'>
            <span style='color: #fbbf24; font-size: 13px;'>⚠️ {safety}</span>
        </div>
        """, unsafe_allow_html=True)
    
    # Sources citation
    if sources:
        unique_sources = list(set(sources))
        source_text = " · ".join(
            s.replace("\\", "/").split("/")[-1].replace(".txt", "").replace("_", " ").title()
            for s in unique_sources
        )
        
        st.markdown(f"""
        <div style='background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3);
                    border-radius: 10px; padding: 10px 14px; margin-top: 12px;'>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='font-size: 16px;'>📚</div>
                <div>
                    <div style='color: #a5b4fc; font-size: 11px; font-weight: 600; 
                                text-transform: uppercase; letter-spacing: 0.5px;'>
                        SOURCES (RAG Knowledge Base)
                    </div>
                    <div style='color: #cbd5e1; font-size: 13px; margin-top: 2px;'>
                        {source_text}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Expandable — show retrieved chunks
    if chunks:
        with st.expander("🔍 View Retrieved Document Chunks"):
            for i, chunk in enumerate(chunks, 1):
                st.markdown(f"""
                <div style='background: rgba(15, 23, 42, 0.5); border-left: 3px solid #6366f1;
                            padding: 10px 14px; border-radius: 6px; margin: 8px 0;'>
                    <div style='color: #a5b4fc; font-size: 11px; font-weight: 600;'>
                        Chunk {i} · Score: {chunk.get('score', 0):.3f} · {chunk.get('source', 'Unknown')}
                    </div>
                    <div style='color: #cbd5e1; font-size: 13px; margin-top: 4px;'>
                        {chunk.get('preview', '')}
                    </div>
                </div>
                """, unsafe_allow_html=True)


def _render_chat_query(query_result: dict, msg_idx: int = 0):
    """Renders query results in chat format."""
    q_type = query_result.get("type", "general")
    data = query_result.get("data", {}) or {}
    intro = query_result.get("friendly_intro", "")
    
    # Friendly intro
    if intro:
        st.markdown(f"_{intro}_")
    
    # ─── SLOTS ───
    if q_type == "list_slots":
        slots = data.get("slots", [])
        if not slots:
            st.markdown("💡 No slots match your criteria. Try a different date or department.")
            return
        
        dept = data.get("department", "N/A")
        date_filter = data.get("date_filter")
        header = f"**📅 Available slots in {dept}**"
        if date_filter:
            header += f" _(filtered by {date_filter})_"
        st.markdown(header)
        
        # Deduplicate slots by slot_id (in case backend returns duplicates)
        seen_slot_ids = set()
        unique_slots = []
        for s in slots:
            sid = s.get("slot_id")
            if sid and sid not in seen_slot_ids:
                seen_slot_ids.add(sid)
                unique_slots.append(s)
        slots = unique_slots
        
        for i in range(0, len(slots), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                slot_index = i + j
                if slot_index < len(slots):
                    slot = slots[slot_index]
                    with col:
                        st.markdown(f"""
                        <div style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4);
                                    padding: 12px; border-radius: 10px; margin: 6px 0;'>
                            <div style='color: #f8fafc; font-weight: 700; font-size: 14px;'>
                                👨‍⚕️ {tr_doctor(slot['doctor_name'])}
                            </div>
                            <div style='color: #94a3b8; font-size: 12px;'>{tr_spec(slot.get('specialization', ''))}</div>
                            <div style='color: #a5b4fc; font-size: 13px; margin-top: 4px;'>
                                📅 {slot['date']} · 🕐 {slot['time']}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # GUARANTEED UNIQUE KEY using slot_index (position) + slot_id + msg_idx
                        btn_key = f"chat_query_book_msg{msg_idx}_pos{slot_index}_sid{slot['slot_id']}"
                        
                        if st.button(f"✅ Book This", key=btn_key, use_container_width=True):
                            with st.spinner("Booking..."):
                                book_result = api_post(
                                    "/api/appointments/book",
                                    {"slot_id": slot["slot_id"], "reason": "Booked from chat"},
                                    token=get_token(),
                                )
                            if book_result["ok"]:
                                appt = book_result["data"].get("appointment", {})
                                from datetime import datetime as _dt
                                st.session_state["chat_messages"].append({
                                    "role": "assistant",
                                    "data": {
                                        "success": True,
                                        "summary": f"Booked with {appt.get('doctor_name')} on {appt.get('date')} at {appt.get('time')}",
                                        "safety": {"risk_level": "none", "is_safe": True},
                                        "appointment": {"success": True, "action": "book", "appointment": appt, "message": "Booked"},
                                        "followup": None,
                                        "document": None,
                                    },
                                    "timestamp": _dt.now().strftime("%I:%M %p"),
                                })
                                st.rerun()
                            else:
                                st.error(f"❌ {book_result['data'].get('detail', 'Failed')}")
                            with st.spinner("Booking..."):
                                book_result = api_post(
                                    "/api/appointments/book",
                                    {"slot_id": slot["slot_id"], "reason": "Booked from chat"},
                                    token=get_token(),
                                )
                            if book_result["ok"]:
                                appt = book_result["data"].get("appointment", {})
                                from datetime import datetime as _dt
                                st.session_state["chat_messages"].append({
                                    "role": "assistant",
                                    "data": {
                                        "success": True,
                                        "summary": f"Booked with {appt.get('doctor_name')} on {appt.get('date')} at {appt.get('time')}",
                                        "safety": {"risk_level": "none", "is_safe": True},
                                        "appointment": {"success": True, "action": "book", "appointment": appt, "message": "Booked"},
                                        "followup": None,
                                        "document": None,
                                    },
                                    "timestamp": _dt.now().strftime("%I:%M %p"),
                                })
                                st.rerun()
                            else:
                                st.error(f"❌ {book_result['data'].get('detail', 'Failed')}")
    
    # ─── APPOINTMENTS ───
    elif q_type == "list_appointments":
        active = data.get("active", [])
        past = data.get("past", [])
        
        if active:
            st.markdown("**🟢 Upcoming Appointments**")
            for appt in active:
                st.markdown(f"""
                <div style='background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981;
                            padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                    <div style='color: #f8fafc; font-weight: 600;'>
                        👨‍⚕️ {appt.get('doctor_name')} · <span style='color: #34d399;'>{appt['status'].upper()}</span>
                    </div>
                    <div style='color: #cbd5e1; font-size: 13px; margin-top: 4px;'>
                        📅 {appt.get('date')} at {appt.get('time')} · #{appt.get('appointment_id')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if past:
            st.markdown("**📜 Past Appointments**")
            for appt in past[:5]:
                st.markdown(f"""
                <div style='background: rgba(148, 163, 184, 0.1); border-left: 3px solid #64748b;
                            padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                    <div style='color: #cbd5e1; font-size: 14px;'>
                        👨‍⚕️ {appt.get('doctor_name')} · <span style='color: #94a3b8;'>{appt['status'].upper()}</span>
                    </div>
                    <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                        📅 {appt.get('date')} at {appt.get('time')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if not active and not past:
            st.markdown("💡 You don't have any appointments yet.")
    
    # ─── DOCTORS ───
    elif q_type == "list_doctors":
        if data.get("doctors"):
            st.markdown(f"**👨‍⚕️ Doctors in {data.get('department', 'Department')}**")
            for doc in data["doctors"]:
                st.markdown(f"""
                <div style='background: rgba(99, 102, 241, 0.1); border-left: 3px solid #6366f1;
                            padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                    <div style='color: #f8fafc; font-weight: 600;'>👨‍⚕️ {doc['name']}</div>
                    <div style='color: #a5b4fc; font-size: 13px;'>🎓 {doc.get('specialization', 'General')}</div>
                    <div style='color: #94a3b8; font-size: 12px;'>{doc.get('qualification', '')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        elif data.get("all_departments"):
            st.markdown("**🏥 All Departments & Doctors**")
            for dept_info in data["all_departments"]:
                with st.expander(f"🏥 {dept_info['department']} ({len(dept_info['doctors'])} doctors)"):
                    for doc in dept_info["doctors"]:
                        st.markdown(f"👨‍⚕️ **{doc['name']}** · {doc.get('specialization', 'N/A')}")
    
    # ─── DOCUMENTS ───
    elif q_type == "list_documents":
        docs = data.get("documents", [])
        missing = data.get("missing_documents", [])
        
        if missing:
            st.markdown(f"""
            <div style='color: #fbbf24;'>
                <b>📋 Missing Documents:</b> {', '.join(missing)}
            </div>
            """, unsafe_allow_html=True)
        
        if docs:
            st.markdown("**📄 Your Documents**")
            type_icons = {
                "ecg": "❤️", "blood_report": "🩸", "xray": "🦴", "mri": "🧠",
                "ct_scan": "🔬", "prescription": "💊", "identity": "🪪", "other": "📄",
            }
            for doc in docs:
                icon = type_icons.get(doc.get("document_type", "other"), "📄")
                dup = " ⚠️ DUPLICATE" if doc.get("is_duplicate") else ""
                st.markdown(f"""
                <div style='background: rgba(139, 92, 246, 0.1); border-left: 3px solid #8b5cf6;
                            padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                    <div style='color: #f8fafc; font-weight: 600;'>
                        {icon} {doc['original_filename']}{dup}
                    </div>
                    <div style='color: #cbd5e1; font-size: 12px;'>
                        {doc['document_type']} · {doc.get('file_size_kb', 0):.1f} KB
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("💡 You haven't uploaded any documents yet.")
    
    # ─── GENERAL ───
    else:
        st.markdown(query_result.get("message", "Here's what I can help with:"))        


def render_workflow_result(data):

    # ═══════════════════════════════════════════════════════
    # NEW: Handle QUERY results (read-only info responses)
    # ═══════════════════════════════════════════════════════
    if data.get("is_query"):
        render_query_result(data["query_result"])
        return


    # ═══════════════════════════════════════════════════════
    # NEW: Check appointment-specific outcomes FIRST
    # ═══════════════════════════════════════════════════════
    appt_result = data.get("appointment") or {}
    
    # ── Case 1: Missing date/time (validation failed) ─────
    if appt_result.get("missing_info"):
        missing_field = appt_result.get("missing_info", "both")
        
        missing_labels = {
            "date": "📅 Day",
            "time": "🕐 Time",
            "both": "📅 Day and 🕐 Time",
        }
        missing_display = missing_labels.get(missing_field, "details")
        
        st.markdown(f"""
        <div class="warning-hero">
            <h3 style='color: #fbbf24 !important; margin: 0 0 12px 0;'>
                ⚠️ Missing Information: {missing_display}
            </h3>
            <p style='color: #fde68a; font-size: 15px; margin: 0;'>
                To book your appointment, please include a <b>specific day</b> and <b>time</b>.
            </p>
            <div style='background: rgba(0,0,0,0.2); border-radius: 8px; padding: 12px; margin-top: 12px;'>
                <div style='color: #fef3c7; font-size: 13px; font-weight: 600; margin-bottom: 6px;'>
                    💡 Try these examples:
                </div>
                <ul style='color: #fef9c3; font-size: 14px; margin: 0; padding-left: 20px;'>
                    <li>"Book cardiology for <b>tomorrow at 10 AM</b>"</li>
                    <li>"Book cardiology for <b>Wednesday at 3 PM</b>"</li>
                    <li>"Schedule dermatology <b>next Monday at 11 AM</b>"</li>
                </ul>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        sample_slots = appt_result.get("available_slots", [])
        if sample_slots:
            st.markdown("### 💡 Some Currently Available Slots")
            cols = st.columns(min(3, len(sample_slots)))
            for i, slot in enumerate(sample_slots[:6]):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style='background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.4);
                                padding: 14px; border-radius: 10px; margin: 6px 0;'>
                        <div style='color: #f8fafc; font-weight: 700; font-size: 13px;'>
                            👨‍⚕️ {slot['doctor_name']}
                        </div>
                        <div style='color: #cbd5e1; font-size: 12px; margin-top: 4px;'>
                            📅 {slot['date']}
                        </div>
                        <div style='color: #a5b4fc; font-size: 13px; font-weight: 600; margin-top: 2px;'>
                            🕐 {slot['time']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.info(
            "💡 **Tip:** Rewrite your request with a specific date and time.\n\n"
            "Example: *'Book cardiology for tomorrow at 10 AM'* "
            "or *'Book cardiology for Wednesday at 3 PM'*"
        )
        return   # ← Stop here — don't show any other cards
    
    # ── Case 2: Slot unavailable — show alternatives ──────
    if appt_result.get("action") == "slot_unavailable":
        alternatives = appt_result.get("available_slots", [])
        requested_date = appt_result.get("requested_date", "your preferred date")
        requested_time = appt_result.get("requested_time", "")
        
        st.markdown(f"""
        <div class="error-hero">
            <h3 style='color: #f87171 !important;'>❌ Preferred Slot Not Available</h3>
            <p style='color: #fecaca; font-size: 15px;'>
                Your requested slot on <b>{requested_date}{requested_time}</b> is already booked.
                Please choose from the available alternatives below.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        if alternatives:
            st.markdown("### 📅 Available Alternative Slots")
            
            for i in range(0, len(alternatives), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(alternatives):
                        slot = alternatives[i + j]
                        with col:
                            st.markdown(f"""
                            <div class="appt-card" style='border: 2px solid rgba(99, 102, 241, 0.4);'>
                                <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>
                                    👨‍⚕️ {slot.get('doctor_name')}
                                </div>
                                <div style='color: #94a3b8; font-size: 13px; margin-bottom: 12px;'>
                                    {slot.get('specialization', 'General')}
                                </div>
                                <div style='display: flex; gap: 12px; margin-bottom: 12px;'>
                                    <div style='background: rgba(99, 102, 241, 0.15); padding: 8px 12px; border-radius: 8px; flex: 1;'>
                                        <div style='color: #94a3b8; font-size: 11px;'>📅 DATE</div>
                                        <div style='color: #f1f5f9; font-weight: 700;'>{slot.get('date')}</div>
                                    </div>
                                    <div style='background: rgba(99, 102, 241, 0.15); padding: 8px 12px; border-radius: 8px; flex: 1;'>
                                        <div style='color: #94a3b8; font-size: 11px;'>🕐 TIME</div>
                                        <div style='color: #f1f5f9; font-weight: 700;'>{slot.get('time')}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button(
                                f"✅ Book This Slot",
                                key=f"book_alt_{slot['slot_id']}",
                                use_container_width=True,
                            ):
                                with st.spinner("Booking your slot..."):
                                    book_result = api_post(
                                        "/api/appointments/book",
                                        {
                                            "slot_id": slot["slot_id"],
                                            "reason": f"Alternative slot selected by patient",
                                        },
                                        token=get_token(),
                                    )
                                if book_result["ok"]:
                                    # Build a FAKE workflow result so it looks like a success
                                    booked_appt = book_result["data"].get("appointment", {})
                                    st.session_state["workflow_result"] = {
                                        "success": True,
                                        "workflow_id": "N/A (Direct Booking)",
                                        "summary": (
                                            f"Alternative slot booked with "
                                            f"{booked_appt.get('doctor_name')} on "
                                            f"{booked_appt.get('date')} at {booked_appt.get('time')}"
                                        ),
                                        "safety": {"risk_level": "none", "is_safe": True},
                                        "department": {
                                            "department_name": "Same as originally requested",
                                            "confidence": 1.0,
                                        },
                                        "appointment": {
                                            "success": True,
                                            "action": "book",
                                            "appointment": booked_appt,
                                            "message": "Alternative slot booked successfully",
                                        },
                                        "followup": None,
                                        "document": None,
                                    }
                                    st.rerun()
                                else:
                                    st.error(f"❌ {book_result['data'].get('detail', 'Booking failed')}")
        return   # ← Stop here — don't show success card
    
    # ═══════════════════════════════════════════════════════
    # EXISTING LOGIC (blocked, emergency, success) — keep as-is
    # ═══════════════════════════════════════════════════════
    
    if data.get("blocked"):
        st.markdown(f"""
        <div class="error-hero">
            <h3 style='color: #f87171 !important;'>🚫 Request Blocked</h3>
            <p style='color: #fecaca;'>{data.get('message', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if data.get("emergency"):
        st.markdown(f"""
        <div class="warning-hero">
            <h3 style='color: #fbbf24 !important;'>⚠️ Emergency Detected</h3>
            <p style='color: #fde68a;'>{data.get('message', '')}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    if not data.get("success"):
        st.markdown(f"""
        <div class="error-hero">
            <h3 style='color: #f87171 !important;'>❌ Request Failed</h3>
            <p style='color: #fecaca;'>{data.get('message', 'Unknown error')}</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Success
    st.markdown(f"""
    <div class="success-hero">
        <h3>✅ Request Processed Successfully</h3>
        <p style='color: #6ee7b7; margin: 8px 0 0 0;'>Workflow ID: <code>#{data.get('workflow_id')}</code></p>
        <p style='color: #d1fae5; margin: 12px 0 0 0; font-size: 15px;'>{data.get('summary', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Agent Pipeline
    st.markdown("### 🤖 AI Agent Pipeline")
    st.markdown('<div class="agent-pipeline">', unsafe_allow_html=True)
    
    safety = data.get("safety", {})
    risk = safety.get("risk_level", "none")
    agent_pipeline_card("🛡️", "Safety Guardian Agent", f"✅ Verified safe · Risk level: <b>{risk}</b>")
    
    dept = data.get("department")
    if dept:
        conf = int(dept.get("confidence", 0) * 100)
        agent_pipeline_card("🗺️", "Department Routing Agent",
                          f"Routed to <b>{dept.get('department_name', 'N/A')}</b> · Confidence: {conf}%")
    
    if appt_result and appt_result.get("success"):
        appt = appt_result.get("appointment", {})
        if appt:
            agent_pipeline_card("📅", "Appointment Agent",
                              f"Booked with <b>{appt.get('doctor_name')}</b> on {appt.get('date')} at {appt.get('time')}")
    
    doc_result = data.get("document")
    if doc_result and doc_result.get("success"):
        doc = doc_result.get("document", {})
        if doc:
            dup = " (Duplicate detected)" if doc.get("is_duplicate") else ""
            agent_pipeline_card("📄", "Document Agent",
                              f"Classified as <b>{doc.get('document_type')}</b>{dup}")
    
    fu_result = data.get("followup")
    if fu_result and fu_result.get("success"):
        total = fu_result.get("total_reminders", 0)
        agent_pipeline_card("🔔", "Follow-up Agent", f"<b>{total}</b> reminder(s) scheduled")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Appointment Confirmation Card
    if appt_result and appt_result.get("success"):
        appt = appt_result.get("appointment", {})
        if appt:
            st.markdown("### 🎉 Your Appointment is Confirmed")
            appointment_card(appt)
            
            # Email sent confirmation
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(5, 150, 105, 0.15));
                        border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 16px; margin: 16px 0;'>
                <div style='display: flex; align-items: center; gap: 12px;'>
                    <div style='font-size: 28px;'>📧</div>
                    <div>
                        <div style='color: #34d399; font-weight: 700; font-size: 15px;'>
                            Appointment Letter Sent!
                        </div>
                        <div style='color: #d1fae5; font-size: 13px; margin-top: 4px;'>
                            A detailed confirmation has been emailed to <b>{get_user_email()}</b>. 
                            Check your <b>📬 My Notifications</b> page to view it.
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_query_result(query_result):
    """Renders query results based on type."""
    q_type = query_result.get("type", "general")
    data = query_result.get("data", {}) or {}
    intro = query_result.get("friendly_intro", "")
    
    # Header
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
                border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 20px; margin-bottom: 20px;'>
        <h3 style='color: #a5b4fc; margin: 0 0 8px 0;'>💬 Query Result</h3>
        <p style='color: #cbd5e1; margin: 0; font-size: 15px;'>{intro}</p>
        <p style='color: #94a3b8; margin: 4px 0 0 0; font-size: 13px;'>{query_result.get('message', '')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ═══ SLOTS RESULT ═══
    if q_type == "list_slots":
        slots = data.get("slots", [])
        if not slots:
            st.info("💡 No slots match your criteria. Try a different date or department.")
            return
        
        st.markdown(f"### 📅 Available Slots · {data.get('department', 'N/A')}")
        if data.get("date_filter"):
            st.caption(f"📆 Filtered by date: **{data['date_filter']}**")
        
        for i in range(0, len(slots), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(slots):
                    slot = slots[i + j]
                    with col:
                        st.markdown(f"""
                        <div class="appt-card" style='border: 2px solid rgba(99, 102, 241, 0.3);'>
                            <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>
                                👨‍⚕️ {slot['doctor_name']}
                            </div>
                            <div style='color: #94a3b8; font-size: 13px; margin-bottom: 12px;'>
                                {slot.get('specialization', 'General')}
                            </div>
                            <div style='display: flex; gap: 8px;'>
                                <div style='background: rgba(99, 102, 241, 0.15); padding: 8px 12px; border-radius: 8px; flex: 1;'>
                                    <div style='color: #94a3b8; font-size: 11px;'>📅 DATE</div>
                                    <div style='color: #f1f5f9; font-weight: 700;'>{slot['date']}</div>
                                </div>
                                <div style='background: rgba(99, 102, 241, 0.15); padding: 8px 12px; border-radius: 8px; flex: 1;'>
                                    <div style='color: #94a3b8; font-size: 11px;'>🕐 TIME</div>
                                    <div style='color: #f1f5f9; font-weight: 700;'>{slot['time']}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"✅ Book This Slot", key=f"query_book_{slot['slot_id']}", use_container_width=True):
                            with st.spinner("Booking..."):
                                book_result = api_post(
                                    "/api/appointments/book",
                                    {"slot_id": slot["slot_id"], "reason": "Booked from query results"},
                                    token=get_token(),
                                )
                            if book_result["ok"]:
                                appt = book_result["data"].get("appointment", {})
                                st.session_state["workflow_result"] = {
                                    "success": True,
                                    "workflow_id": "N/A",
                                    "summary": f"Booked with {appt.get('doctor_name')} on {appt.get('date')} at {appt.get('time')}",
                                    "safety": {"risk_level": "none", "is_safe": True},
                                    "department": {"department_name": data.get("department"), "confidence": 1.0},
                                    "appointment": {"success": True, "action": "book", "appointment": appt},
                                    "followup": None, "document": None,
                                }
                                st.rerun()
                            else:
                                st.error(f"❌ {book_result['data'].get('detail')}")
    
    # ═══ APPOINTMENTS RESULT ═══
    elif q_type == "list_appointments":
        active = data.get("active", [])
        past = data.get("past", [])
        
        if active:
            st.markdown("### 🟢 Upcoming Appointments")
            for appt in active:
                appointment_card(appt)
        
        if past:
            st.markdown("### 📜 Past Appointments")
            for appt in past[:5]:
                appointment_card(appt)
        
        if not active and not past:
            st.info("💡 You don't have any appointments yet.")
    
    # ═══ DOCTORS RESULT ═══
    elif q_type == "list_doctors":
        if data.get("doctors"):
            st.markdown(f"### 👨‍⚕️ Doctors in {data.get('department', 'Department')}")
            for doc in data["doctors"]:
                st.markdown(f"""
                <div class="appt-card">
                    <div style='display: flex; gap: 16px; align-items: center;'>
                        <div style='width: 56px; height: 56px; background: linear-gradient(135deg, #6366f1, #ec4899);
                                    border-radius: 50%; display: flex; align-items: center; justify-content: center;
                                    color: white; font-size: 24px; font-weight: 700;'>
                            👨‍⚕️
                        </div>
                        <div style='flex: 1;'>
                            <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>{doc['name']}</div>
                            <div style='color: #a5b4fc; font-size: 13px; margin-top: 2px;'>🎓 {doc.get('specialization', 'N/A')}</div>
                            <div style='color: #94a3b8; font-size: 12px; margin-top: 2px;'>{doc.get('qualification', 'N/A')}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        elif data.get("all_departments"):
            st.markdown("### 🏥 All Departments & Doctors")
            for dept_info in data["all_departments"]:
                with st.expander(f"🏥 {dept_info['department']} ({len(dept_info['doctors'])} doctors)"):
                    for doc in dept_info["doctors"]:
                        st.markdown(f"👨‍⚕️ **{doc['name']}** · {doc.get('specialization', 'N/A')}")
    
    # ═══ DOCUMENTS RESULT ═══
    elif q_type == "list_documents":
        docs = data.get("documents", [])
        missing = data.get("missing_documents", [])
        
        if missing:
            st.markdown(f"""
            <div class="warning-hero">
                <h3 style='color: #fbbf24 !important;'>📋 Missing Documents</h3>
                <p style='color: #fde68a;'>You still need to upload: <b>{', '.join(missing)}</b></p>
            </div>
            """, unsafe_allow_html=True)
        
        if docs:
            st.markdown("### 📄 Your Documents")
            for doc in docs:
                type_icons = {
                    "ecg": "❤️", "blood_report": "🩸", "xray": "🦴", "mri": "🧠",
                    "ct_scan": "🔬", "prescription": "💊", "identity": "🪪", "other": "📄",
                }
                icon = type_icons.get(doc.get("document_type", "other"), "📄")
                dup = " ⚠️ DUPLICATE" if doc.get("is_duplicate") else ""
                st.markdown(f"""
                <div class="appt-card">
                    <div style='display: flex; align-items: center; gap: 16px;'>
                        <div style='font-size: 32px;'>{icon}</div>
                        <div style='flex: 1;'>
                            <div style='color: #f8fafc; font-weight: 700;'>{doc['original_filename']}{dup}</div>
                            <div style='color: #94a3b8; font-size: 13px;'>
                                {doc['document_type']} · {doc.get('file_size_kb', 0):.1f} KB · 
                                {doc.get('created_at', '')[:10] if doc.get('created_at') else 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("💡 You haven't uploaded any documents yet.")
    
    # ═══ GENERAL RESULT ═══
    elif q_type == "general":
        st.markdown(f"""
        <div class="appt-card">
            <div style='color: #cbd5e1; font-size: 15px; white-space: pre-line;'>{query_result.get('message', '')}</div>
        </div>
        """, unsafe_allow_html=True)


def render_my_appointments(token):
    hero_header(f"📅 {tr('nav_appointments')}")
    
    status_filter = st.selectbox(
        tr("filter_by_status"),
        ["All", "confirmed", "pending", "cancelled", "completed", "rescheduled"]
    )
    
    params = {}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    result = api_get("/api/appointments/my", token, params)
    
    if not result["ok"]:
        st.error("Could not load appointments.")
        return
    
    appointments = result["data"].get("appointments", [])
    
    if not appointments:
        st.info(f"💡 {tr('no_appointments_yet')}. {tr('book_first_appt')}")
        return
    
    st.markdown(f"**{tr('showing_appointments')} {len(appointments)} {tr('appointments_count')}**")
    
    for appt in appointments:
        appointment_card(appt)
        
        if appt["status"] in ["confirmed", "pending", "rescheduled"]:
            cols = st.columns([3, 1])
            with cols[1]:
                if st.button(f"❌ {tr('cancel_appt')}", key=f"cancel_{appt['appointment_id']}"):
                    with st.spinner("Cancelling..."):
                        cancel_result = api_delete(
                            "/api/appointments/cancel",
                            {"appointment_id": appt["appointment_id"], "reason": "Patient request"},
                            token=token
                        )
                    if cancel_result["ok"]:
                        st.success("Appointment cancelled")
                        time.sleep(0.5)
                        st.rerun()


def render_my_documents(token):
    hero_header("My Medical Documents")
    
    # Upload section
    st.markdown("### ⬆️ Upload New Document")
    
    with st.form("doc_upload_form"):
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader(
                "Choose file", type=["pdf", "jpg", "jpeg", "png", "txt"]
            )
        with col2:
            dept_name = st.selectbox("For which department?", [
                "", "Cardiology", "Neurology", "Orthopedics",
                "General Medicine", "Radiology", "Dermatology",
                "Ophthalmology", "Pediatrics", "Gynecology",
                "Gastroenterology"
            ])
        
        description = st.text_input("Description", placeholder="e.g., Blood test from Jan 2024")
        upload_submit = st.form_submit_button("📤 Upload Document", use_container_width=True)
    
    if upload_submit:
        if not uploaded_file:
            st.error("Please select a file.")
        else:
            with st.spinner("🤖 Document Agent processing..."):
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                form_data = {"description": description or "", "department_name": dept_name or ""}
                result = api_post_form("/api/documents/upload", data=form_data, files=files, token=token)
            
            if result["ok"]:
                data = result["data"]
                doc = data.get("document", {})
                
                if doc.get("is_duplicate"):
                    st.warning(f"⚠️ Duplicate document detected: **{doc.get('document_type')}**")
                else:
                    st.success(f"✅ Uploaded as **{doc.get('document_type')}** ({doc.get('file_size_kb', 0):.1f} KB)")
                
                missing = data.get("missing_documents", [])
                if missing:
                    st.warning(f"📋 Still need: **{', '.join(missing)}**")
            else:
                st.error(f"❌ {result['data'].get('detail', 'Upload failed')}")
    
    # Documents list
    st.markdown("---")
    st.markdown("### 📋 Your Documents")
    
    result = api_get("/api/documents/my", token)
    if not result["ok"]:
        st.error("Could not load documents.")
        return
    
    documents = result["data"].get("documents", [])
    if not documents:
        st.info("💡 No documents uploaded yet.")
        return
    
    st.markdown(f"**{len(documents)} document(s) on file**")
    
    for doc in documents:
        type_icons = {
            "ecg": "❤️", "blood_report": "🩸", "xray": "🦴", "mri": "🧠",
            "ct_scan": "🔬", "prescription": "💊", "discharge_summary": "📋",
            "insurance": "📜", "identity": "🪪", "other": "📄",
        }
        icon = type_icons.get(doc.get("document_type", "other"), "📄")
        dup_badge = " ⚠️ DUPLICATE" if doc.get("is_duplicate") else ""
        
        # Get document ID (handle different key names)
        _doc_id = doc.get('id') or doc.get('document_id') or doc.get('doc_id')
        
        col_doc, col_delete = st.columns([5, 1])
        
        with col_doc:
            st.markdown(f"""
            <div class="appt-card">
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='display: flex; align-items: center; gap: 16px;'>
                        <div style='font-size: 36px;'>{icon}</div>
                        <div>
                            <div style='color: #f8fafc; font-size: 16px; font-weight: 700;'>
                                {doc['original_filename']}{dup_badge}
                            </div>
                            <div style='color: #94a3b8; font-size: 13px;'>
                                {doc['document_type']} · {doc.get('file_size_kb', 0):.1f} KB · 
                                {doc.get('created_at', '')[:10] if doc.get('created_at') else 'N/A'}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_delete:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            if _doc_id:
                if st.button("🗑️ Delete", key=f"del_doc_{_doc_id}", use_container_width=True):
                    st.session_state[f"confirm_delete_{_doc_id}"] = True
                    st.rerun()
        
        # Confirmation dialog
        if _doc_id and st.session_state.get(f"confirm_delete_{_doc_id}", False):
            st.warning(f"⚠️ Are you sure you want to delete **{doc['original_filename']}**?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Yes, Delete", key=f"yes_del_{_doc_id}", use_container_width=True):
                    with st.spinner("Deleting..."):
                        result = api_delete(
                            f"/api/documents/{_doc_id}",
                            token=token,
                        )
                    if result["ok"]:
                        st.success("✅ Document deleted!")
                        st.session_state.pop(f"confirm_delete_{_doc_id}", None)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"❌ {result['data'].get('detail', 'Delete failed')}")
            with c2:
                if st.button("❌ Cancel", key=f"no_del_{_doc_id}", use_container_width=True):
                    st.session_state.pop(f"confirm_delete_{_doc_id}", None)
                    st.rerun()
        


def render_my_reminders(token):
    hero_header("Reminders & Request History")
    
    tab1, tab2 = st.tabs(["🔔 Upcoming Appointments", "📜 Request History"])
    
    with tab1:
        result = api_get("/api/appointments/my", token, {"status_filter": "confirmed"})
        if result["ok"]:
            appts = result["data"].get("appointments", [])
            if appts:
                st.success(f"🔔 You have **{len(appts)}** upcoming appointment(s). Reminders are auto-scheduled.")
                for appt in appts:
                    appointment_card(appt)
            else:
                st.info("No upcoming appointments.")
    
    with tab2:
        wf_result = api_get("/api/workflow/history", token)
        if wf_result["ok"]:
            workflows = wf_result["data"].get("workflows", [])
            if workflows:
                for wf in workflows:
                    icons = {
                        "completed": "✅", "escalated": "⚠️",
                        "failed": "❌", "in_progress": "🔄", "started": "▶️"
                    }
                    icon = icons.get(wf["status"], "⚪")
                    
                    st.markdown(f"""
                    <div class="appt-card">
                        <div style='display: flex; align-items: center; gap: 16px;'>
                            <div style='font-size: 28px;'>{icon}</div>
                            <div style='flex: 1;'>
                                <div style='color: #f8fafc; font-weight: 700; font-size: 15px;'>
                                    Request #{wf['workflow_id']} · {wf['status'].upper()}
                                </div>
                                <div style='color: #cbd5e1; font-size: 14px; margin-top: 4px;'>
                                    {wf.get('request_text', '')[:100]}
                                </div>
                                <div style='color: #64748b; font-size: 12px; margin-top: 4px;'>
                                    {wf.get('created_at', '')[:19] if wf.get('created_at') else ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No request history.")


def render_patient_notifications(token):
    hero_header("📬 My Notifications · Email History")
    
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15)); 
                padding: 20px; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.3); margin-bottom: 20px;'>
        <h4 style='margin: 0 0 8px 0; color: #f8fafc;'>💡 Your Email Records</h4>
        <p style='color: #cbd5e1; margin: 0; font-size: 14px;'>
            All communications sent to <b>{get_user_email()}</b> are logged here. 
            Click "View Email" to see the full content anytime.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    result = api_get("/api/patients/notifications", token)
    if not result["ok"]:
        st.error("Could not load notifications.")
        return
    
    notifications = result["data"].get("notifications", [])
    if not notifications:
        st.info("📭 No notifications yet. Book an appointment or upload a document to receive your first email!")
        return
    
    # Summary
    c1, c2, c3 = st.columns(3)
    with c1: stat_card("📬", len(notifications), "Total Emails")
    with c2:
        confirmations = len([n for n in notifications if 'appointment' in n['notification_type']])
        stat_card("✅", confirmations, "Appointments")
    with c3:
        docs = len([n for n in notifications if 'document' in n['notification_type']])
        stat_card("📄", docs, "Documents")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### 📋 Recent Emails ({len(notifications)})")
    
    type_icons = {
        "appointment_confirm":    "📅",
        "escalation_alert":       "⚠️",
        "document_confirm":       "📄",
        "reminder":               "🔔",
        "followup":               "🔄",
    }
    
    for n in notifications:
        type_icon = type_icons.get(n["notification_type"], "📧")
        status_color = "#10b981" if n["status"] == "sent" else "#f59e0b"
        
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; gap: 16px; align-items: center;'>
                <div style='font-size: 32px;'>{type_icon}</div>
                <div style='flex: 1;'>
                    <div style='color: #f8fafc; font-weight: 700; font-size: 15px;'>
                        {n['subject']}
                    </div>
                    <div style='color: #94a3b8; font-size: 12px; margin-top: 4px;'>
                        {n['notification_type']} · Sent: {n.get('sent_at', 'N/A')[:19] if n.get('sent_at') else 'Pending'}
                    </div>
                </div>
                <div>
                    <span style='background: {status_color}; color: white; padding: 4px 12px; 
                                 border-radius: 12px; font-size: 11px; font-weight: 700;'>
                        {n['status'].upper()}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"👁️ View Email", key=f"view_patient_{n['id']}"):
            with st.spinner("Loading..."):
                detail = api_get(f"/api/patients/notifications/{n['id']}", token)
            if detail["ok"]:
                d = detail["data"]
                st.markdown("### 📧 Email Preview")
                st.markdown(f"**To:** {d['recipient_email']}")
                st.markdown(f"**Subject:** {d['subject']}")
                st.markdown("**Body:**")
                components.html(d.get('body_html', ''), height=800, scrolling=True)


def render_my_profile(token):
    hero_header("My Profile")
    
    result = api_get("/api/patients/profile", token)
    if not result["ok"]:
        st.error("Could not load profile.")
        return
    
    profile = result["data"]
    
    # Profile Overview Card
    st.markdown(f"""
    <div class="appt-card">
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div style='width: 80px; height: 80px; background: linear-gradient(135deg, #6366f1, #ec4899);
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 32px; font-weight: 700;'>
                {profile.get('name', 'U')[0].upper()}
            </div>
            <div>
                <div style='color: #f8fafc; font-size: 24px; font-weight: 800;'>
                    {profile.get('name', 'N/A')}
                </div>
                <div style='color: #94a3b8; font-size: 14px;'>{profile.get('email', 'N/A')}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### ✏️ Update Profile")
    
    with st.form("profile_form"):
        col1, col2 = st.columns(2)
        with col1:
            u_phone = st.text_input("📱 Phone", value=profile.get("phone") or "")
            u_age = st.number_input("🎂 Age", 0, 120, profile.get("age") or 0)
            u_gender = st.selectbox("Gender", ["", "Male", "Female", "Other"],
                                    index=["", "Male", "Female", "Other"].index(profile.get("gender") or "") if profile.get("gender") in ["", "Male", "Female", "Other"] else 0)
            u_blood = st.selectbox("🩸 Blood Group",
                                   ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                                   index=["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(profile.get("blood_group") or "") if profile.get("blood_group") in ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] else 0)
        with col2:
            u_dob = st.text_input("🎂 DOB (YYYY-MM-DD)", value=profile.get("date_of_birth") or "")
            u_lang = st.selectbox("🗣️ Language", ["English", "Hindi", "Tamil", "Telugu", "Bengali"])
            u_emergency = st.text_input("🚨 Emergency Contact", value=profile.get("emergency_contact") or "")
            u_address = st.text_area("🏠 Address", value=profile.get("address") or "", height=80)
        
        submit = st.form_submit_button("💾 Save Changes", use_container_width=True)
    
    if submit:
        with st.spinner("Updating..."):
            result = api_put("/api/patients/profile", {
                "phone": u_phone or None, "age": u_age if u_age > 0 else None,
                "gender": u_gender or None, "date_of_birth": u_dob or None,
                "address": u_address or None, "blood_group": u_blood or None,
                "emergency_contact": u_emergency or None, "preferred_language": u_lang,
            }, token=token)
        
        if result["ok"]:
            st.success("✅ Profile updated!")
            time.sleep(0.5)
            st.rerun()
        else:
            st.error(f"❌ {result['data'].get('detail', 'Update failed')}")


# ═══════════════════════════════════════════════════════════════
# STAFF PORTAL
# ═══════════════════════════════════════════════════════════════

def render_staff_portal():
    token = get_token()
    role = get_role()
    
    with st.sidebar:
        sidebar_brand()
        sidebar_user_card(get_user_name(), role.title())

         # NEW: Language switcher
        sidebar_language_switcher()
        
        st.markdown("---")
        
        st.markdown(f"### 📍 {tr('navigation')}")

        esc_result = api_get("/api/escalations/open", token)
        esc_count = len(esc_result["data"].get("escalations", [])) if esc_result["ok"] else 0
        
        notif_result = api_get("/api/staff/notifications", token, {"limit": 100})
        notif_count = 0
        if notif_result["ok"]:
            notifs = notif_result["data"].get("notifications", [])
            notif_count = len([n for n in notifs if n.get("status") == "sent"])
        
        esc_label = f"⚠️ Escalations{'  🔴' if esc_count > 0 else ''}"
        notif_label = f"📬 Notifications"
        page = st.radio(
            "nav",
            [
                "🏠 Dashboard",
                "📈 Analytics",
                "🔍 Search & Filter",       # ← NEW
                "📅 All Appointments",
                "🎯 Slot Utilization",
                esc_label,
                notif_label,
                "📋 Workflows",
                "👥 Patients",
                "🏥 Departments",
                "📊 Audit Log",
            ],
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        if st.button(f"🚪 {tr('sign_out')}", use_container_width=True):
            logout()
    
    if page == "🏠 Dashboard":
        render_staff_dashboard(token)
    elif page == "📈 Analytics":
        render_analytics_dashboard(token)
    elif page == "🔍 Search & Filter":         # ← NEW
        render_search_page(token)                # ← NEW
    elif page == "📅 All Appointments":
        render_all_appointments(token)
    elif page == "🎯 Slot Utilization":
        render_slot_statistics(token)
    elif "Escalations" in page:
        render_escalations(token)
    elif "Notifications" in page:
        render_notifications(token)
    elif page == "📋 Workflows":
        render_all_workflows(token)
    elif page == "👥 Patients":
        render_patients_list(token)
    elif page == "🏥 Departments":
        render_departments(token)
    elif page == "📊 Audit Log":
        render_audit_log(token)


def render_staff_dashboard(token):
    hero_header(f"Staff Command Center · {get_user_name()}")
    
    result = api_get("/api/staff/dashboard", token)
    if not result["ok"]:
        st.error("Could not load dashboard.")
        return
    
    stats = result["data"].get("stats", {})
    open_esc = stats.get("open_escalations", 0)
    
    # Stats Grid
    st.markdown("### 📊 System Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: stat_card("👥", stats.get("total_patients", 0), "Patients")
    with c2: stat_card("🔄", stats.get("total_workflows", 0), "Workflows")
    with c3: stat_card("📅", stats.get("total_appointments", 0), "Appointments")
    with c4: stat_card("✅", stats.get("active_appointments", 0), "Active Appts")
    with c5:
        # PULSING RED when open escalations > 0
        stat_card_alert("⚠️", open_esc, "Open Escalations", alert=(open_esc > 0))
    
    if open_esc > 0:
        st.markdown(f"""
        <div class="warning-hero" style="animation: pulse-red 2s infinite;">
            <h3 style='color: #f87171 !important;'>🚨 URGENT: Escalations Awaiting Review</h3>
            <p style='color: #fecaca; font-size: 16px;'>
                You have <b>{open_esc}</b> escalation(s) that require immediate review.
                Email notifications have been sent to all staff.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏥 Department Overview")
    
    dept_result = api_get("/api/staff/departments", token)
    if dept_result["ok"]:
        departments = dept_result["data"].get("departments", [])
        cols = st.columns(5)
        for i, dept in enumerate(departments[:10]):
            with cols[i % 5]:
                st.markdown(f"""
                <div class="stat-box">
                    <div class="stat-icon">🏥</div>
                    <div style='color: #f8fafc; font-weight: 700; font-size: 14px;'>{dept['name']}</div>
                    <div class="stat-label">{dept.get('doctor_count', 0)} doctors</div>
                </div>
                """, unsafe_allow_html=True)
    
    # Auto-refresh every 15 seconds
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("🔄 Dashboard auto-refreshes every 15 seconds")
    time.sleep(15)
    st.rerun()

# ═══════════════════════════════════════════════════════════════
# SEARCH & FILTER PAGE (Feature #4)
# ═══════════════════════════════════════════════════════════════

def render_search_page(token: str):
    """Universal search & filter page for staff."""
    hero_header("🔍 Search & Filter · Find Anything Fast")
    
    # ═══ UNIVERSAL SEARCH BAR ═══
    st.markdown("### 🌐 Global Search")
    st.caption("Search across patients, doctors, and departments instantly")
    
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        global_query = st.text_input(
            "Search",
            placeholder="Type a name, email, department...",
            label_visibility="collapsed",
            key="global_search_input",
        )
    with col_btn:
        do_search = st.button("🔍 Search", use_container_width=True)
    
    if global_query and (do_search or len(global_query) >= 3):
        with st.spinner("Searching..."):
            result = api_get(
                "/api/staff/search/global",
                token,
                {"q": global_query},
            )
        
        if result["ok"]:
            data = result["data"]
            total = data.get("total_results", 0)
            
            if total == 0:
                st.info(f"🔍 No results found for **{global_query}**")
            else:
                st.markdown(f"### 📋 {total} Result(s) Found")
                
                # Patients
                patients = data.get("patients", [])
                if patients:
                    st.markdown(f"**👥 Patients ({len(patients)})**")
                    for p in patients:
                        st.markdown(f"""
                        <div style='background: rgba(99, 102, 241, 0.1); 
                                    border-left: 3px solid #6366f1;
                                    padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                            <div style='color: #f8fafc; font-weight: 600;'>👤 {p['name']}</div>
                            <div style='color: #cbd5e1; font-size: 12px;'>
                                📧 {p.get('email', 'N/A')} · 📞 {p.get('phone', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Doctors
                doctors = data.get("doctors", [])
                if doctors:
                    st.markdown(f"**👨‍⚕️ Doctors ({len(doctors)})**")
                    for d in doctors:
                        st.markdown(f"""
                        <div style='background: rgba(236, 72, 153, 0.1); 
                                    border-left: 3px solid #ec4899;
                                    padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                            <div style='color: #f8fafc; font-weight: 600;'>👨‍⚕️ {d['name']}</div>
                            <div style='color: #cbd5e1; font-size: 12px;'>
                                🎓 {d.get('specialization', 'N/A')} · 🏥 {d.get('department', 'N/A')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Departments
                depts = data.get("departments", [])
                if depts:
                    st.markdown(f"**🏥 Departments ({len(depts)})**")
                    for d in depts:
                        st.markdown(f"""
                        <div style='background: rgba(16, 185, 129, 0.1); 
                                    border-left: 3px solid #10b981;
                                    padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                            <div style='color: #f8fafc; font-weight: 600;'>🏥 {d['name']}</div>
                            <div style='color: #cbd5e1; font-size: 12px;'>{d.get('description', 'N/A')}</div>
                        </div>
                        """, unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("---")
    
    # ═══ ADVANCED SEARCH TABS ═══
    st.markdown("### 🎯 Advanced Filters")
    
    tab_patients, tab_appts, tab_docs = st.tabs([
        "👥 Patient Search",
        "📅 Appointment Search",
        "👨‍⚕️ Doctor Search"
    ])
    
    # ─────────────────────────────────────────────
    # TAB 1: PATIENT SEARCH
    # ─────────────────────────────────────────────
    with tab_patients:
        st.markdown("#### Filter Patients")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            p_search = st.text_input(
                "Name / Email / Phone",
                placeholder="e.g., John or 9876",
                key="p_search",
            )
        with col2:
            p_gender = st.selectbox(
                "Gender",
                ["All", "Male", "Female", "Other"],
                key="p_gender",
            )
        with col3:
            p_blood = st.selectbox(
                "Blood Group",
                ["All", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                key="p_blood",
            )
        
        col4, col5 = st.columns(2)
        with col4:
            p_min_age = st.number_input("Min Age", 0, 120, 0, key="p_min_age")
        with col5:
            p_max_age = st.number_input("Max Age", 0, 120, 120, key="p_max_age")
        
        if st.button("🔍 Search Patients", use_container_width=True, key="p_search_btn"):
            params = {"limit": 50}
            if p_search: params["q"] = p_search
            if p_gender != "All": params["gender"] = p_gender
            if p_blood != "All": params["blood_group"] = p_blood
            if p_min_age > 0: params["min_age"] = p_min_age
            if p_max_age < 120: params["max_age"] = p_max_age
            
            with st.spinner("Searching..."):
                result = api_get("/api/staff/search/patients", token, params)
            
            if result["ok"]:
                patients = result["data"].get("patients", [])
                st.markdown(f"### 📊 Found {len(patients)} patient(s)")
                
                if patients:
                    for p in patients:
                        with st.expander(f"👤 {p['name']} · {p.get('email', 'N/A')}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f"**📧 Email:** {p.get('email', 'N/A')}")
                                st.markdown(f"**📞 Phone:** {p.get('phone', 'N/A')}")
                                st.markdown(f"**🎂 Age:** {p.get('age', 'N/A')}")
                                st.markdown(f"**👤 Gender:** {p.get('gender', 'N/A')}")
                            with c2:
                                st.markdown(f"**🩸 Blood:** {p.get('blood_group', 'N/A')}")
                                st.markdown(f"**🏠 Address:** {p.get('address', 'N/A')}")
                                st.markdown(f"**🚨 Emergency:** {p.get('emergency_contact', 'N/A')}")
                else:
                    st.info("🔍 No patients match your filters")
    
    # ─────────────────────────────────────────────
    # TAB 2: APPOINTMENT SEARCH
    # ─────────────────────────────────────────────
    with tab_appts:
        st.markdown("#### Filter Appointments")
        
        # Fetch departments for dropdown
        dept_result = api_get("/api/staff/departments", token)
        departments = dept_result["data"].get("departments", []) if dept_result["ok"] else []
        dept_options = ["All"] + [d["name"] for d in departments]
        dept_id_map = {d["name"]: d["id"] for d in departments}
        
        col1, col2 = st.columns(2)
        with col1:
            a_search = st.text_input(
                "Patient/Doctor Name",
                placeholder="e.g., John or Sharma",
                key="a_search",
            )
        with col2:
            a_dept = st.selectbox("Department", dept_options, key="a_dept")
        
        col3, col4 = st.columns(2)
        with col3:
            a_status = st.selectbox(
                "Status",
                ["All", "confirmed", "pending", "completed", "cancelled", "rescheduled"],
                key="a_status",
            )
        with col4:
            a_limit = st.number_input("Results Limit", 10, 500, 100, key="a_limit")
        
        col5, col6 = st.columns(2)
        with col5:
            a_from = st.date_input("From Date", value=None, key="a_from")
        with col6:
            a_to = st.date_input("To Date", value=None, key="a_to")
        
        if st.button("🔍 Search Appointments", use_container_width=True, key="a_search_btn"):
            params = {"limit": a_limit}
            if a_search: params["q"] = a_search
            if a_dept != "All": params["department_id"] = dept_id_map.get(a_dept)
            if a_status != "All": params["status_filter"] = a_status
            if a_from: params["from_date"] = a_from.isoformat()
            if a_to: params["to_date"] = a_to.isoformat()
            
            with st.spinner("Searching..."):
                result = api_get("/api/staff/search/appointments", token, params)
            
            if result["ok"]:
                appts = result["data"].get("appointments", [])
                st.markdown(f"### 📊 Found {len(appts)} appointment(s)")
                
                if appts:
                    # Summary stats
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: stat_card("🟢", len([a for a in appts if a["status"] == "confirmed"]), "Confirmed")
                    with c2: stat_card("✅", len([a for a in appts if a["status"] == "completed"]), "Completed")
                    with c3: stat_card("🔴", len([a for a in appts if a["status"] == "cancelled"]), "Cancelled")
                    with c4: stat_card("🔵", len([a for a in appts if a["status"] == "rescheduled"]), "Rescheduled")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    for a in appts:
                        status_color = {
                            "confirmed": "#10b981",
                            "completed": "#6366f1",
                            "cancelled": "#ef4444",
                            "rescheduled": "#3b82f6",
                            "pending": "#f59e0b",
                        }.get(a["status"], "#94a3b8")
                        
                        st.markdown(f"""
                        <div class="appt-card">
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div style='flex: 1;'>
                                    <div style='color: #f8fafc; font-weight: 700;'>
                                        👤 {a.get('patient_name')} → 👨‍⚕️ {a.get('doctor_name')}
                                    </div>
                                    <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                                        🏥 {a.get('department')} · 📅 {a.get('date')} at {a.get('time')}
                                    </div>
                                    <div style='color: #cbd5e1; font-size: 12px; margin-top: 4px;'>
                                        {(a.get('reason') or 'No reason')[:100]}
                                    </div>
                                </div>
                                <span style='background: {status_color}; color: white; 
                                             padding: 5px 12px; border-radius: 12px; 
                                             font-size: 11px; font-weight: 700;'>
                                    {a['status'].upper()}
                                </span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("🔍 No appointments match your filters")
    
    # ─────────────────────────────────────────────
    # TAB 3: DOCTOR SEARCH
    # ─────────────────────────────────────────────
    with tab_docs:
        st.markdown("#### Filter Doctors")
        
        col1, col2 = st.columns(2)
        with col1:
            d_search = st.text_input(
                "Doctor Name / Specialization",
                placeholder="e.g., Sharma or Cardiology",
                key="d_search",
            )
        with col2:
            d_dept = st.selectbox("Department", dept_options, key="d_dept")
        
        if st.button("🔍 Search Doctors", use_container_width=True, key="d_search_btn"):
            params = {"limit": 50}
            if d_search: params["q"] = d_search
            if d_dept != "All": params["department_id"] = dept_id_map.get(d_dept)
            
            with st.spinner("Searching..."):
                result = api_get("/api/staff/search/doctors", token, params)
            
            if result["ok"]:
                docs = result["data"].get("doctors", [])
                st.markdown(f"### 📊 Found {len(docs)} doctor(s)")
                
                if docs:
                    for i in range(0, len(docs), 2):
                        cols = st.columns(2)
                        for j, col in enumerate(cols):
                            if i + j < len(docs):
                                d = docs[i + j]
                                with col:
                                    st.markdown(f"""
                                    <div class="appt-card" style='border-left: 3px solid #ec4899;'>
                                        <div style='display: flex; align-items: center; gap: 16px;'>
                                            <div style='width: 56px; height: 56px; 
                                                        background: linear-gradient(135deg, #6366f1, #ec4899);
                                                        border-radius: 50%; display: flex; 
                                                        align-items: center; justify-content: center;
                                                        color: white; font-size: 24px;'>
                                                👨‍⚕️
                                            </div>
                                            <div style='flex: 1;'>
                                                <div style='color: #f8fafc; font-weight: 700; font-size: 15px;'>
                                                    {d['name']}
                                                </div>
                                                <div style='color: #a5b4fc; font-size: 12px;'>
                                                    🎓 {d.get('specialization', 'N/A')}
                                                </div>
                                                <div style='color: #94a3b8; font-size: 11px;'>
                                                    🏥 {d.get('department', 'N/A')}
                                                </div>
                                                <div style='color: #64748b; font-size: 11px;'>
                                                    {d.get('qualification', 'N/A')}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                else:
                    st.info("🔍 No doctors match your filters")


def render_all_appointments(token):
    hero_header("All Appointments · System-Wide View")
    
    status_filter = st.selectbox("Filter",
        ["All", "confirmed", "pending", "cancelled", "completed", "rescheduled"])
    
    params = {"limit": 100}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    result = api_get("/api/staff/appointments", token, params)
    if not result["ok"]:
        st.error("Could not load appointments.")
        return
    
    appointments = result["data"].get("appointments", [])
    if not appointments:
        st.info("No appointments found.")
        return
    
    # Summary
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("🟢", len([a for a in appointments if a["status"] == "confirmed"]), "Confirmed")
    with c2: stat_card("🟡", len([a for a in appointments if a["status"] == "pending"]), "Pending")
    with c3: stat_card("✅", len([a for a in appointments if a["status"] == "completed"]), "Completed")
    with c4: stat_card("🔴", len([a for a in appointments if a["status"] == "cancelled"]), "Cancelled")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### 📋 Total: {len(appointments)} Appointment(s)")
    
    for appt in appointments:
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='color: #f8fafc; font-size: 17px; font-weight: 700;'>
                        👤 {appt.get('patient_name', 'Unknown')} → 👨‍⚕️ {appt.get('doctor_name', 'Unknown')}
                    </div>
                    <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                        {appt.get('specialization', 'N/A')} · {appt.get('patient_email', '')}
                    </div>
                    <div style='color: #cbd5e1; margin-top: 12px;'>
                        📅 <b>{appt.get('date')}</b> at <b>{appt.get('time')}</b> · 
                        Reason: {appt.get('reason', 'N/A')[:80]}
                    </div>
                </div>
                <div>
                    <span class="appt-status-{appt['status']}" style='background: #6366f1; color: white; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 700;'>
                        {appt['status'].upper()}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
# ANALYTICS DASHBOARD (Feature #3)
# ═══════════════════════════════════════════════════════════════

def render_analytics_dashboard(token: str):
    """Beautiful analytics dashboard with charts."""
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    
    hero_header("📈 Analytics Dashboard · Real-Time Hospital Insights")
    
    # ─── Fetch all analytics data ────────────────────────────
    overview = api_get("/api/staff/analytics/overview", token)
    trends = api_get("/api/staff/analytics/appointment-trends", token, {"days": 7})
    dept_util = api_get("/api/staff/analytics/department-utilization", token)
    doctor_wl = api_get("/api/staff/analytics/doctor-workload", token, {"limit": 10})
    status = api_get("/api/staff/analytics/appointment-status", token)
    peak = api_get("/api/staff/analytics/peak-hours", token)
    growth = api_get("/api/staff/analytics/patient-growth", token, {"days": 30})
    
    if not overview["ok"]:
        st.error("❌ Could not load analytics data.")
        return
    
    ov = overview["data"]
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 1: KEY METRICS
    # ═══════════════════════════════════════════════════════════
    st.markdown("### 🎯 Key Metrics")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        stat_card("👥", ov["totals"]["patients"], "Total Patients")
    with c2:
        stat_card("👨‍⚕️", ov["totals"]["doctors"], "Active Doctors")
    with c3:
        stat_card("🏥", ov["totals"]["departments"], "Departments")
    with c4:
        stat_card("📅", ov["totals"]["appointments"], "Total Appts")
    with c5:
        stat_card("🔄", ov["totals"]["workflows"], "AI Workflows")
    with c6:
        stat_card("⚠️", ov["recent"]["open_escalations"], "Open Escalations")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Second row of metrics
    st.markdown("### 📊 Recent Activity")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        stat_card("📅", ov["recent"]["appointments_last_7_days"], "Bookings Last 7 Days")
    with m2:
        stat_card("📆", ov["recent"]["appointments_last_30_days"], "Bookings Last 30 Days")
    with m3:
        stat_card("🤖", ov["recent"]["workflows_last_7_days"], "AI Workflows (7d)")
    with m4:
        stat_card("📈", ov["averages"]["appointments_per_day"], "Avg Bookings/Day")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 2: APPOINTMENT TRENDS (Line Chart)
    # ═══════════════════════════════════════════════════════════
    st.markdown("### 📈 Appointment Trends (Last 7 Days)")
    
    if trends["ok"]:
        trend_data = trends["data"].get("trend", [])
        if trend_data:
            df_trends = pd.DataFrame(trend_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_trends["date"],
                y=df_trends["count"],
                mode='lines+markers',
                name='Bookings',
                line=dict(color='#6366f1', width=3),
                marker=dict(size=10, color='#8b5cf6'),
                fill='tozeroy',
                fillcolor='rgba(99, 102, 241, 0.15)',
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(30, 41, 59, 0.5)',
                plot_bgcolor='rgba(15, 23, 42, 0.5)',
                height=350,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis=dict(title="Date", gridcolor='rgba(148, 163, 184, 0.1)'),
                yaxis=dict(title="Bookings", gridcolor='rgba(148, 163, 184, 0.1)'),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No appointment data available for trends.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 3: DEPARTMENT + STATUS (Two columns)
    # ═══════════════════════════════════════════════════════════
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 🏥 Department Utilization")
        if dept_util["ok"]:
            depts = dept_util["data"].get("departments", [])
            if depts:
                df_depts = pd.DataFrame(depts)
                fig = px.bar(
                    df_depts,
                    x="appointments",
                    y="department",
                    orientation='h',
                    color="appointments",
                    color_continuous_scale=[[0, '#6366f1'], [1, '#ec4899']],
                )
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(30, 41, 59, 0.5)',
                    plot_bgcolor='rgba(15, 23, 42, 0.5)',
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    coloraxis_showscale=False,
                    xaxis_title="Appointments",
                    yaxis_title="",
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 No department data yet.")
    
    with col_right:
        st.markdown("### 🎯 Appointment Status")
        if status["ok"]:
            breakdown = status["data"].get("breakdown", [])
            if breakdown and any(b["count"] > 0 for b in breakdown):
                df_status = pd.DataFrame(breakdown)
                
                color_map = {
                    "confirmed": "#10b981",
                    "pending": "#f59e0b",
                    "cancelled": "#ef4444",
                    "completed": "#6366f1",
                    "rescheduled": "#3b82f6",
                }
                
                fig = go.Figure(data=[go.Pie(
                    labels=df_status["status"],
                    values=df_status["count"],
                    hole=0.5,
                    marker=dict(colors=[color_map.get(s, "#94a3b8") for s in df_status["status"]]),
                    textinfo='label+percent',
                    textfont_size=14,
                )])
                fig.update_layout(
                    template='plotly_dark',
                    paper_bgcolor='rgba(30, 41, 59, 0.5)',
                    plot_bgcolor='rgba(15, 23, 42, 0.5)',
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    showlegend=True,
                    legend=dict(orientation="v", yanchor="middle", y=0.5),
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📭 No status data yet.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 4: DOCTOR WORKLOAD
    # ═══════════════════════════════════════════════════════════
    st.markdown("### 👨‍⚕️ Top 10 Busiest Doctors")
    if doctor_wl["ok"]:
        doctors = doctor_wl["data"].get("doctors", [])
        if doctors:
            df_docs = pd.DataFrame(doctors)
            
            fig = px.bar(
                df_docs,
                x="appointments",
                y="doctor",
                orientation='h',
                color="department",
                hover_data=["specialization"],
                labels={"doctor": "Doctor", "appointments": "Appointments"},
            )
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(30, 41, 59, 0.5)',
                plot_bgcolor='rgba(15, 23, 42, 0.5)',
                height=500,
                margin=dict(l=20, r=20, t=30, b=20),
                yaxis={'categoryorder': 'total ascending'},
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No doctor workload data yet.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 5: PEAK HOURS
    # ═══════════════════════════════════════════════════════════
    st.markdown("### 🕐 Peak Booking Hours")
    if peak["ok"]:
        hours = peak["data"].get("hours", [])
        peak_hour = peak["data"].get("peak_hour", "N/A")
        peak_count = peak["data"].get("peak_count", 0)
        
        if hours and any(h["count"] > 0 for h in hours):
            df_hours = pd.DataFrame(hours)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_hours["hour"],
                y=df_hours["count"],
                marker=dict(
                    color=df_hours["count"],
                    colorscale=[[0, '#1e293b'], [1, '#ec4899']],
                    showscale=False,
                ),
                text=df_hours["count"],
                textposition='outside',
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(30, 41, 59, 0.5)',
                plot_bgcolor='rgba(15, 23, 42, 0.5)',
                height=350,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis=dict(title="Hour of Day", gridcolor='rgba(148, 163, 184, 0.1)'),
                yaxis=dict(title="Bookings", gridcolor='rgba(148, 163, 184, 0.1)'),
                showlegend=False,
            )
            st.plotly_chart(fig, use_container_width=True)
            
            st.info(f"🌟 **Peak Hour:** {peak_hour} with {peak_count} bookings")
        else:
            st.info("📭 No booking data yet to show peak hours.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # SECTION 6: PATIENT GROWTH
    # ═══════════════════════════════════════════════════════════
    st.markdown("### 📈 Patient Growth (Last 30 Days)")
    if growth["ok"]:
        growth_data = growth["data"].get("growth", [])
        total_new = growth["data"].get("total_new_last_period", 0)
        current_total = growth["data"].get("current_total", 0)
        
        c1, c2 = st.columns(2)
        with c1:
            stat_card("👥", current_total, "Total Patients")
        with c2:
            stat_card("➕", total_new, "New Signups (30d)")
        
        if growth_data:
            df_growth = pd.DataFrame(growth_data)
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df_growth["date"],
                y=df_growth["cumulative"],
                mode='lines',
                name='Total Patients',
                line=dict(color='#10b981', width=3),
                fill='tozeroy',
                fillcolor='rgba(16, 185, 129, 0.15)',
            ))
            fig.add_trace(go.Bar(
                x=df_growth["date"],
                y=df_growth["new_signups"],
                name='New Signups',
                marker=dict(color='#6366f1'),
                yaxis='y2',
            ))
            fig.update_layout(
                template='plotly_dark',
                paper_bgcolor='rgba(30, 41, 59, 0.5)',
                plot_bgcolor='rgba(15, 23, 42, 0.5)',
                height=400,
                margin=dict(l=20, r=20, t=30, b=20),
                xaxis=dict(title="Date", gridcolor='rgba(148, 163, 184, 0.1)'),
                yaxis=dict(title="Cumulative Patients", gridcolor='rgba(148, 163, 184, 0.1)'),
                yaxis2=dict(title="Daily Signups", overlaying='y', side='right', showgrid=False),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ═══════════════════════════════════════════════════════════
    # FOOTER — Refresh + Info
    # ═══════════════════════════════════════════════════════════
    col_info, col_refresh = st.columns([3, 1])
    with col_info:
        st.caption("📊 Data refreshed on page load · All metrics computed from live database")
    with col_refresh:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()        


def render_slot_statistics(token):
    hero_header("Slot Utilization Analytics")
    
    result = api_get("/api/staff/slots/stats", token)
    if not result["ok"]:
        st.error("Could not load slot statistics.")
        return
    
    data = result["data"]
    overall = data.get("overall", {})
    
    st.markdown("### 📈 Overall Utilization")
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("📅", overall.get("total", 0), "Total Slots")
    with c2: stat_card("🟢", overall.get("available", 0), "Available")
    with c3: stat_card("🔴", overall.get("booked", 0), "Booked")
    with c4: stat_card("📊", f"{overall.get('utilization', 0)}%", "Utilization")
    
    utilization = overall.get("utilization", 0)
    st.progress(min(utilization / 100, 1.0))
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🏥 Department Breakdown")
    
    for dept in data.get("by_department", []):
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div style='flex: 2;'>
                    <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>🏥 {dept['department']}</div>
                    <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                        {dept['available']} available · {dept['booked']} booked · {dept['total']} total
                    </div>
                </div>
                <div style='flex: 3;'>
                    <div style='background: rgba(15, 23, 42, 0.5); height: 12px; border-radius: 10px; overflow: hidden;'>
                        <div style='background: linear-gradient(90deg, #6366f1, #ec4899); height: 100%; width: {dept['utilization']}%; border-radius: 10px;'></div>
                    </div>
                    <div style='color: #cbd5e1; font-size: 12px; margin-top: 4px; text-align: right;'>
                        {dept['utilization']}% utilized
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_notifications(token):
    hero_header("📬 System Notifications · Email Audit Trail")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15)); 
                padding: 20px; border-radius: 16px; border: 1px solid rgba(99, 102, 241, 0.3); margin-bottom: 20px;'>
        <h4 style='margin: 0 0 8px 0; color: #f8fafc;'>💡 About Notifications</h4>
        <p style='color: #cbd5e1; margin: 0; font-size: 14px;'>
            Every escalation automatically triggers email notifications to all staff members.
            This page shows all notifications sent by the system with delivery status.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filter
    col1, col2 = st.columns([1, 3])
    with col1:
        status_filter = st.selectbox("Status", ["All", "sent", "pending", "failed"])
    
    params = {"limit": 100}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    result = api_get("/api/staff/notifications", token, params)
    
    if not result["ok"]:
        st.error("Could not load notifications.")
        return
    
    notifications = result["data"].get("notifications", [])
    
    if not notifications:
        st.info("💡 No notifications sent yet. Trigger an escalation to see notifications here.")
        return
    
    # Summary stats
    sent = len([n for n in notifications if n["status"] == "sent"])
    failed = len([n for n in notifications if n["status"] == "failed"])
    pending = len([n for n in notifications if n["status"] == "pending"])
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("📬", len(notifications), "Total Sent")
    with c2: stat_card("✅", sent, "Delivered")
    with c3: stat_card("⏳", pending, "Pending")
    with c4: stat_card("❌", failed, "Failed")
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"### 📋 Notification Log ({len(notifications)} records)")
    
    for n in notifications:
        status_colors = {
            "sent":    ("✅", "#10b981"),
            "pending": ("⏳", "#f59e0b"),
            "failed":  ("❌", "#ef4444"),
        }
        icon, color = status_colors.get(n["status"], ("⚪", "#94a3b8"))
        
        type_icons = {
            "escalation_alert":    "🚨",
            "appointment_confirm": "📅",
            "reminder":            "🔔",
            "document_confirm":    "📄",
            "followup":            "🔄",
        }
        type_icon = type_icons.get(n["notification_type"], "📧")
        
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; gap: 16px; align-items: center;'>
                <div style='font-size: 32px;'>{type_icon}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div style='color: #f8fafc; font-weight: 700; font-size: 15px;'>
                            {n['subject']}
                        </div>
                        <span style='background: {color}; color: white; padding: 4px 12px; 
                                     border-radius: 12px; font-size: 11px; font-weight: 700;'>
                            {icon} {n['status'].upper()}
                        </span>
                    </div>
                    <div style='color: #94a3b8; font-size: 13px; margin-top: 6px;'>
                        📧 To: <b>{n['recipient_email']}</b> ({n.get('recipient_name', 'N/A')})
                    </div>
                    <div style='color: #64748b; font-size: 12px; margin-top: 4px;'>
                        Type: {n['notification_type']} · 
                        Sent: {n.get('sent_at', 'N/A')[:19] if n.get('sent_at') else 'Not sent'} · 
                        Escalation: #{n.get('escalation_id', 'N/A')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Preview button
        if st.button(f"👁️ View Email Content", key=f"view_{n['id']}"):
            with st.spinner("Loading email preview..."):
                detail_result = api_get(f"/api/staff/notifications/{n['id']}", token)
            
            if detail_result["ok"]:
                detail = detail_result["data"]
                
                st.markdown("### 📧 Email Preview")
                st.markdown(f"**To:** {detail['recipient_email']}")
                st.markdown(f"**Subject:** {detail['subject']}")
                st.markdown("**Body:**")
                
                # Render the HTML email in an iframe-like container   
                components.html(detail.get('body_html', ''), height=800, scrolling=True)     


def render_escalations(token):
    hero_header("Escalation Management")
    
    tab1, tab2 = st.tabs(["🔴 Open Escalations", "📜 All History"])
    
    with tab1:
        result = api_get("/api/escalations/open", token)
        if not result["ok"]:
            st.error("Could not load escalations.")
            return
        
        escalations = result["data"].get("escalations", [])
        if not escalations:
            st.markdown("""
            <div class="success-hero">
                <h3>✅ All Clear!</h3>
                <p style='color: #6ee7b7;'>No open escalations at this time.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"### ⚠️ {len(escalations)} escalation(s) require your attention")
            
            for esc in escalations:
                with st.expander(f"🔴 Escalation #{esc['escalation_id']} — {esc.get('reason', '')[:60]}"):
                    st.markdown(f"**Reason:** {esc['reason']}")
                    st.markdown(f"**Details:** {esc.get('details', 'N/A')}")
                    st.markdown(f"**Workflow:** #{esc.get('workflow_run_id', 'N/A')}")
                    st.markdown(f"**Created:** {esc.get('created_at', '')[:19]}")
                    
                    with st.form(f"resolve_{esc['escalation_id']}"):
                        note = st.text_area("Resolution Note *")
                        status = st.selectbox("Status", ["resolved", "reviewed"])
                        if st.form_submit_button("✅ Resolve"):
                            if not note:
                                st.error("Please add a note.")
                            else:
                                r = api_post(f"/api/escalations/{esc['escalation_id']}/resolve",
                                             {"resolution_note": note, "new_status": status}, token=token)
                                if r["ok"]:
                                    st.success("Resolved!")
                                    time.sleep(0.5)
                                    st.rerun()
    
    with tab2:
        result = api_get("/api/escalations/all", token, {"limit": 50})
        if result["ok"]:
            for esc in result["data"].get("escalations", []):
                icons = {"open": "🔴", "reviewed": "🟡", "resolved": "✅"}
                icon = icons.get(esc["status"], "⚪")
                st.markdown(f"{icon} **#{esc['escalation_id']}** · `{esc['status']}` · {esc['reason'][:70]}")


def render_all_workflows(token):
    hero_header("All Workflows")
    
    status_filter = st.selectbox("Filter",
        ["All", "completed", "escalated", "failed", "in_progress", "started"])
    
    params = {"limit": 50}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    result = api_get("/api/staff/workflows", token, params)
    if not result["ok"]:
        return
    
    workflows = result["data"].get("workflows", [])
    st.markdown(f"**{len(workflows)} workflow(s)**")
    
    for wf in workflows:
        icons = {"completed": "✅", "escalated": "⚠️", "failed": "❌", "in_progress": "🔄", "started": "▶️"}
        icon = icons.get(wf["status"], "⚪")
        
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; gap: 16px;'>
                <div style='font-size: 28px;'>{icon}</div>
                <div style='flex: 1;'>
                    <div style='color: #f8fafc; font-weight: 700;'>
                        Workflow #{wf['workflow_id']} · Patient #{wf['patient_id']}
                    </div>
                    <div style='color: #cbd5e1; margin-top: 4px;'>{wf.get('request_text', '')[:150]}</div>
                    <div style='color: #64748b; font-size: 12px; margin-top: 4px;'>
                        Step: {wf.get('current_step')} · Status: {wf['status']} · {wf.get('created_at', '')[:19]}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_patients_list(token):
    hero_header("Patient Records")
    
    result = api_get("/api/staff/patients", token, {"limit": 50})
    if not result["ok"]:
        return
    
    patients = result["data"].get("patients", [])
    st.markdown(f"**{len(patients)} patient(s)**")
    
    for p in patients:
        st.markdown(f"""
        <div class="appt-card">
            <div style='display: flex; align-items: center; gap: 16px;'>
                <div style='width: 56px; height: 56px; background: linear-gradient(135deg, #6366f1, #ec4899);
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            color: white; font-size: 22px; font-weight: 700;'>
                    {p['name'][0].upper()}
                </div>
                <div style='flex: 1;'>
                    <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>{p['name']}</div>
                    <div style='color: #94a3b8; font-size: 13px;'>{p['email']}</div>
                    <div style='color: #cbd5e1; font-size: 13px; margin-top: 4px;'>
                        📱 {p.get('phone', 'N/A')} · 🎂 {p.get('age', 'N/A')} · 
                        {p.get('gender', 'N/A')} · 🩸 {p.get('blood_group', 'N/A')}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_departments(token):
    hero_header("Departments & Doctors")
    
    result = api_get("/api/staff/departments", token)
    if not result["ok"]:
        return
    
    for dept in result["data"].get("departments", []):
        with st.expander(f"🏥 {dept['name']} · {dept.get('doctor_count', 0)} doctors"):
            st.markdown(f"*{dept.get('description', 'N/A')}*")
            
            doc_result = api_get(f"/api/staff/departments/{dept['id']}/doctors", token)
            if doc_result["ok"]:
                for d in doc_result["data"].get("doctors", []):
                    st.markdown(f"👨‍⚕️ **{d['name']}** · {d.get('specialization')} · {d.get('qualification')}")


def render_audit_log(token):
    hero_header("System Audit Log")
    
    result = api_get("/api/staff/audit-log", token, {"limit": 100})
    if not result["ok"]:
        return
    
    events = result["data"].get("events", [])
    action_filter = st.selectbox("Filter",
        ["All", "login_success", "login_failed", "appointment_booked",
         "appointment_cancelled", "document_uploaded", "escalation_created",
         "workflow_started", "workflow_completed"])
    
    filtered = events if action_filter == "All" else [e for e in events if e["action"] == action_filter]
    st.markdown(f"**Showing {len(filtered)} events**")
    
    icons = {
        "login_success": "🔐", "login_failed": "🚫",
        "appointment_booked": "📅", "appointment_cancelled": "❌",
        "appointment_rescheduled": "🔄", "document_uploaded": "📄",
        "escalation_created": "⚠️", "escalation_resolved": "✅",
        "workflow_started": "▶️", "workflow_completed": "✅",
        "patient_registered": "👤", "reminder_created": "🔔",
    }
    
    for event in filtered:
        icon = icons.get(event["action"], "📝")
        st.markdown(f"""
        <div style='background: rgba(30, 41, 59, 0.6); padding: 12px 16px; border-radius: 10px;
                    margin: 6px 0; border-left: 3px solid #6366f1;'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <div style='font-size: 20px;'>{icon}</div>
                <div style='flex: 1;'>
                    <span style='color: #f1f5f9; font-weight: 600;'>{event['action']}</span>
                    <span style='color: #94a3b8; font-size: 12px; margin-left: 12px;'>
                        Actor: #{event.get('actor_id', 'sys')} · 
                        {event.get('entity_type', 'N/A')}#{event.get('entity_id', '')} · 
                        {event.get('created_at', '')[:19]}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# DOCTOR PORTAL
# ═══════════════════════════════════════════════════════════════

def render_doctor_portal():
    token = get_token()
    
    with st.sidebar:
        sidebar_brand()
        sidebar_user_card(get_user_name(), "Doctor")

        sidebar_language_switcher()
        
        st.markdown("---")
        
        st.markdown(f"### 📍 {tr('navigation')}")
        page = st.radio(
            "nav",
            [
                "🏠 Dashboard",
                "📅 Today's Schedule",
                "🗓️ Upcoming",
                "👥 My Patients",
                "📋 All Appointments",
            ],
            label_visibility="collapsed",
        )
        
        st.markdown("---")
        if st.button(f"🚪 {tr('sign_out')}", use_container_width=True):
            logout()
    
    if page == "🏠 Dashboard":
        render_doctor_dashboard(token)
    elif page == "📅 Today's Schedule":
        render_doctor_today(token)
    elif page == "🗓️ Upcoming":
        render_doctor_upcoming(token)
    elif page == "👥 My Patients":
        render_doctor_patients(token)
    elif page == "📋 All Appointments":
        render_doctor_all_appointments(token)


def render_doctor_dashboard(token):
    """Doctor's home dashboard with stats."""
    hero_header(f"Welcome, {get_user_name()}! 🩺")
    
    result = api_get("/api/doctor/dashboard", token)
    if not result["ok"]:
        st.error("Could not load dashboard.")
        return
    
    data = result["data"]
    doctor = data.get("doctor", {})
    today = data.get("today", {})
    week = data.get("this_week", {})
    
    # Doctor Info Card
    st.markdown(f"""
    <div class="appt-card" style='background: linear-gradient(135deg, rgba(99, 102, 241, 0.15), rgba(139, 92, 246, 0.15));
                border: 1px solid rgba(99, 102, 241, 0.3);'>
        <div style='display: flex; align-items: center; gap: 20px;'>
            <div style='width: 80px; height: 80px; background: linear-gradient(135deg, #6366f1, #ec4899);
                        border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        color: white; font-size: 36px;'>
                👨‍⚕️
            </div>
            <div>
                <div style='color: #f8fafc; font-size: 24px; font-weight: 800;'>
                    {doctor.get('name', 'Doctor')}
                </div>
                <div style='color: #a5b4fc; font-size: 15px; margin-top: 4px;'>
                    🎓 {doctor.get('specialization', 'General')}
                </div>
                <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                    {doctor.get('qualification', 'N/A')}
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Today's Stats
    st.markdown("### 📅 Today's Overview")
    c1, c2, c3 = st.columns(3)
    with c1: stat_card("📋", today.get("total", 0), "Total Today")
    with c2: stat_card("✅", today.get("completed", 0), "Completed")
    with c3: stat_card("⏳", today.get("pending", 0), "Pending")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # This Week's Stats
    st.markdown("### 📊 This Week")
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("📅", week.get("total", 0), "Total")
    with c2: stat_card("✅", week.get("completed", 0), "Completed")
    with c3: stat_card("🗓️", week.get("upcoming", 0), "Upcoming")
    with c4: stat_card("❌", week.get("cancelled", 0), "Cancelled")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # All-time stats
    st.markdown("### 🏆 Career Stats")
    c1, c2 = st.columns(2)
    with c1: stat_card("👥", data.get("total_patients_seen", 0), "Total Patients Seen")
    with c2: stat_card("🩺", doctor.get("id", "N/A"), "Doctor ID")
    
    # Today's appointments preview
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🕐 Today's Appointments")
    
    today_result = api_get("/api/doctor/appointments/today", token)
    if today_result["ok"]:
        appts = today_result["data"].get("appointments", [])
        if not appts:
            st.info("📭 No appointments scheduled for today. Enjoy your day!")
        else:
            for appt in appts[:5]:
                status_color = {
                    "confirmed": "#10b981",
                    "completed": "#6366f1",
                    "cancelled": "#ef4444",
                    "rescheduled": "#3b82f6",
                }.get(appt["status"], "#94a3b8")
                
                st.markdown(f"""
                <div class="appt-card">
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='color: #f8fafc; font-weight: 700; font-size: 16px;'>
                                👤 {appt.get('patient_name', 'Unknown')}
                            </div>
                            <div style='color: #a5b4fc; font-size: 14px; margin-top: 4px;'>
                                🕐 {appt.get('time', 'N/A')} · 
                                {appt.get('patient_age', 'N/A')} yrs · 
                                {appt.get('patient_gender', 'N/A')}
                            </div>
                            <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                                {(appt.get('reason') or 'No reason provided')[:80]}
                            </div>
                        </div>
                        <span style='background: {status_color}; color: white; 
                                     padding: 6px 14px; border-radius: 20px; 
                                     font-size: 12px; font-weight: 700;'>
                            {appt['status'].upper()}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


def render_doctor_today(token):
    """Detailed view of today's schedule."""
    hero_header("📅 Today's Schedule")
    
    result = api_get("/api/doctor/appointments/today", token)
    if not result["ok"]:
        st.error("Could not load today's appointments.")
        return
    
    appts = result["data"].get("appointments", [])
    date_str = result["data"].get("date", "")
    
    st.markdown(f"### {date_str}")
    
    if not appts:
        st.info("📭 No appointments scheduled for today.")
        return
    
    st.markdown(f"**Total: {len(appts)} appointment(s)**")
    
    for appt in appts:
        status_color = {
            "confirmed": "#10b981",
            "completed": "#6366f1",
            "cancelled": "#ef4444",
            "rescheduled": "#3b82f6",
            "pending": "#f59e0b",
        }.get(appt["status"], "#94a3b8")
        
        with st.expander(
            f"🕐 {appt.get('time', 'N/A')} — 👤 {appt.get('patient_name', 'Unknown')} — {appt['status'].upper()}"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**👤 Patient Info**")
                st.markdown(f"- Name: **{appt.get('patient_name', 'N/A')}**")
                st.markdown(f"- Age: {appt.get('patient_age', 'N/A')}")
                st.markdown(f"- Gender: {appt.get('patient_gender', 'N/A')}")
                st.markdown(f"- Phone: {appt.get('patient_phone', 'N/A')}")
                st.markdown(f"- Email: {appt.get('patient_email', 'N/A')}")
            with c2:
                st.markdown("**📅 Appointment**")
                st.markdown(f"- Time: **{appt.get('time', 'N/A')}**")
                st.markdown(f"- Status: `{appt['status']}`")
                st.markdown(f"- Appt ID: #{appt['appointment_id']}")
                st.markdown(f"- Reason: {appt.get('reason', 'N/A')[:100]}")
            
            st.markdown("---")
            
            # Existing notes
            if appt.get("doctor_notes"):
                st.markdown("**📝 Existing Clinical Notes:**")
                st.info(appt["doctor_notes"])
            
            if appt.get("consultation_summary"):
                st.markdown("**📋 Consultation Summary:**")
                st.info(appt["consultation_summary"])
            
            # Add/Update notes form
            st.markdown("**✍️ Add/Update Notes**")
            with st.form(f"notes_form_{appt['appointment_id']}"):
                notes = st.text_area(
                    "Clinical Notes",
                    value=appt.get("doctor_notes") or "",
                    height=100,
                    placeholder="Patient presented with... Vitals normal... Recommended follow-up..."
                )
                summary = st.text_area(
                    "Consultation Summary (short)",
                    value=appt.get("consultation_summary") or "",
                    height=60,
                    placeholder="Routine checkup completed. Patient stable."
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    save = st.form_submit_button("💾 Save Notes", use_container_width=True)
                with col_b:
                    complete = st.form_submit_button(
                        "✅ Save & Mark Completed",
                        use_container_width=True,
                    )
            
            if save or complete:
                with st.spinner("Saving..."):
                    save_result = api_put(
                        f"/api/doctor/appointments/{appt['appointment_id']}/notes",
                        {
                            "doctor_notes": notes,
                            "consultation_summary": summary,
                            "mark_completed": complete,
                        },
                        token=token,
                    )
                if save_result["ok"]:
                    st.success("✅ " + save_result["data"].get("message", "Saved!"))
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error(f"❌ {save_result['data'].get('detail', 'Failed')}")


def render_doctor_upcoming(token):
    """Upcoming appointments (next 7 days)."""
    hero_header("🗓️ Upcoming Appointments")
    
    days = st.selectbox("Show appointments for next:", [3, 7, 14, 30], index=1)
    
    result = api_get("/api/doctor/appointments/upcoming", token, {"days": days})
    if not result["ok"]:
        st.error("Could not load appointments.")
        return
    
    appts = result["data"].get("appointments", [])
    
    if not appts:
        st.info(f"📭 No upcoming appointments in the next {days} days.")
        return
    
    st.markdown(f"**Total: {len(appts)} appointment(s) in next {days} days**")
    
    # Group by date
    from collections import defaultdict
    by_date = defaultdict(list)
    for appt in appts:
        by_date[appt.get("date", "Unknown")].append(appt)
    
    for date, day_appts in sorted(by_date.items()):
        st.markdown(f"### 📅 {date}")
        for appt in day_appts:
            status_color = {
                "confirmed": "#10b981",
                "rescheduled": "#3b82f6",
                "pending": "#f59e0b",
            }.get(appt["status"], "#94a3b8")
            
            st.markdown(f"""
            <div class="appt-card">
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div style='flex: 1;'>
                        <div style='color: #f8fafc; font-weight: 700; font-size: 15px;'>
                            🕐 {appt.get('time')} — 👤 {appt.get('patient_name')}
                        </div>
                        <div style='color: #94a3b8; font-size: 13px; margin-top: 4px;'>
                            📞 {appt.get('patient_phone', 'N/A')} · 
                            {(appt.get('reason') or 'No reason')[:80]}
                        </div>
                    </div>
                    <span style='background: {status_color}; color: white; 
                                 padding: 5px 12px; border-radius: 12px; 
                                 font-size: 11px; font-weight: 700;'>
                        {appt['status'].upper()}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_doctor_patients(token):
    """List of unique patients doctor has seen."""
    hero_header("👥 My Patients")
    
    result = api_get("/api/doctor/patients", token)
    if not result["ok"]:
        st.error("Could not load patients.")
        return
    
    patients = result["data"].get("patients", [])
    
    if not patients:
        st.info("📭 No patients yet.")
        return
    
    st.markdown(f"**Total: {len(patients)} unique patient(s)**")
    
    for p in patients:
        with st.expander(
            f"👤 {p['name']} · {p.get('total_appointments', 0)} visit(s)"
        ):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**👤 Basic Info**")
                st.markdown(f"- Name: **{p['name']}**")
                st.markdown(f"- Email: {p.get('email', 'N/A')}")
                st.markdown(f"- Phone: {p.get('phone', 'N/A')}")
            with c2:
                st.markdown("**📊 Stats**")
                st.markdown(f"- Age: {p.get('age', 'N/A')}")
                st.markdown(f"- Gender: {p.get('gender', 'N/A')}")
                st.markdown(f"- Total visits: **{p.get('total_appointments', 0)}**")
                st.markdown(f"- Last visit: {p.get('last_visit', 'N/A')}")
            
            if st.button(f"🔍 View Full History", key=f"view_pat_{p['patient_id']}"):
                with st.spinner("Loading..."):
                    detail = api_get(f"/api/doctor/patients/{p['patient_id']}", token)
                if detail["ok"]:
                    d = detail["data"]
                    st.markdown("---")
                    st.markdown("### 📋 Patient History")
                    
                    st.markdown("**Past Appointments:**")
                    past = d.get("past_appointments", [])
                    if past:
                        for pa in past:
                            st.markdown(f"""
                            <div style='background: rgba(99, 102, 241, 0.1); 
                                        border-left: 3px solid #6366f1;
                                        padding: 10px 14px; border-radius: 8px; margin: 6px 0;'>
                                <div style='color: #f8fafc; font-weight: 600;'>
                                    {pa['date']} at {pa['time']} · {pa['status'].upper()}
                                </div>
                                <div style='color: #cbd5e1; font-size: 13px; margin-top: 4px;'>
                                    {(pa.get('doctor_notes') or 'No notes')[:200]}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.info("No past appointments.")
                    
                    st.markdown("**Documents:**")
                    docs = d.get("documents", [])
                    if docs:
                        for doc in docs:
                            st.markdown(f"📄 {doc['original_filename']} — {doc['document_type']}")
                    else:
                        st.info("No documents.")


def render_doctor_all_appointments(token):
    """All appointments with filters."""
    hero_header("📋 All Appointments")
    
    status_filter = st.selectbox(
        "Filter by status",
        ["All", "confirmed", "pending", "completed", "cancelled", "rescheduled"]
    )
    
    params = {"limit": 100}
    if status_filter != "All":
        params["status_filter"] = status_filter
    
    result = api_get("/api/doctor/appointments/all", token, params)
    if not result["ok"]:
        st.error("Could not load appointments.")
        return
    
    appts = result["data"].get("appointments", [])
    st.markdown(f"**Total: {len(appts)} appointment(s)**")
    
    for appt in appts:
        status_color = {
            "confirmed": "#10b981",
            "completed": "#6366f1",
            "cancelled": "#ef4444",
            "rescheduled": "#3b82f6",
            "pending": "#f59e0b",
        }.get(appt["status"], "#94a3b8")
        
        with st.expander(
            f"👤 {appt.get('patient_name')} · {appt.get('date')} at {appt.get('time')} · {appt['status'].upper()}"
        ):
            st.markdown(f"**Patient:** {appt.get('patient_name')}")
            st.markdown(f"**Email:** {appt.get('patient_email', 'N/A')}")
            st.markdown(f"**Date:** {appt.get('date')} at {appt.get('time')}")
            st.markdown(f"**Status:** `{appt['status']}`")
            st.markdown(f"**Reason:** {appt.get('reason', 'N/A')}")
            if appt.get("doctor_notes"):
                st.markdown("**Clinical Notes:**")
                st.info(appt["doctor_notes"])        


# ═══════════════════════════════════════════════════════════════
# MAIN ROUTER
# ═══════════════════════════════════════════════════════════════

def main():
    
    # ═══════════════════════════════════════════════════════════
    # ROUTING
    # ═══════════════════════════════════════════════════════════
    if not is_logged_in():
        render_login_page()
        return
    
    role = get_role()
    
    if role == "patient":
        render_patient_portal()
    elif role == "doctor":
        render_doctor_portal()
    elif role in ["staff", "admin"]:
        render_staff_portal()
    else:
        st.error(f"Unknown role: {role}")
        if st.button("Logout"):
            logout()       


if __name__ == "__main__":
    main()