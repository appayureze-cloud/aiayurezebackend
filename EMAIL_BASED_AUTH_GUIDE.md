# 📧 EMAIL-BASED AUTHENTICATION SYSTEM

## 🎯 Overview

Your WhatsApp AI assistant now uses **email-based authentication** instead of phone verification. This provides a more secure and user-friendly way for patients to access their medical data.

---

## ✨ **What Changed?**

### **Before (Phone Verification):**
```
User: "VERIFY"
System: "Send OTP to verify phone"
User: [6-digit OTP]
System: "Verified! ✅"
```

### **After (Email-Based Login):**
```
User: "patient@example.com"
System: "🔐 Your OTP: 123456 (via WhatsApp)"
User: "123456"
System: "✅ Logged in as patient@example.com"
```

---

## 🔐 **How It Works:**

### **Step 1: User Sends Email**
```
User sends:
"rajesh.kumar@example.com"
```

### **Step 2: System Validates & Sends OTP**
```
WhatsApp Response:
"✅ Login Started!

📧 Email: rajesh.kumar@example.com
🔐 Your verification code is: 482751

⏱️ Valid for 10 minutes

Reply with the 6-digit code to complete login."
```

### **Step 3: User Sends OTP**
```
User sends:
"482751"
```

### **Step 4: System Verifies & Authenticates**
```
WhatsApp Response:
"🎉 Login Successful!

✅ Authenticated as: rajesh.kumar@example.com

You now have full access to:
📁 Your Medical Documents
💊 Medicine Schedules
🤖 Personalized AI Assistant

What would you like to do?"
```

---

## 📊 **Authentication Flow Diagram:**

```
┌─────────────────────────────────────────┐
│  User Sends Email to WhatsApp          │
│  "rajesh.kumar@example.com"            │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  System Validates Email Format         │
│  ✓ Valid format                         │
│  ✓ Check cooldown (60 sec)             │
│  ✓ Check account not locked            │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Generate 6-Digit OTP                   │
│  Code: 482751                           │
│  Expires: 10 minutes                    │
│  Store in session                       │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Send OTP via WhatsApp                  │
│  (NOT via email - directly in WhatsApp)│
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  User Sends OTP Back                    │
│  "482751"                               │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  System Verifies OTP                    │
│  ✓ Code matches                         │
│  ✓ Not expired                          │
│  ✓ Account not locked                   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│  Authentication Successful! ✅          │
│  Session created                        │
│  Patient data linked                    │
└─────────────────────────────────────────┘
```

---

## 🔒 **Security Features:**

### **1. OTP Cooldown (60 seconds)**
- Prevents spam
- Users must wait 60 seconds between OTP requests

### **2. OTP Expiry (10 minutes)**
- OTP codes expire after 10 minutes
- Must request new OTP if expired

### **3. Account Lockout (5 failed attempts)**
- Max 5 OTP verification attempts
- 24-hour lockout after 5 failures
- Prevents brute force attacks

### **4. Email Validation**
- Strict regex validation: `user@domain.com`
- Case-insensitive matching
- Whitespace trimming

### **5. Session Management**
- In-memory session store (upgrade to database for production)
- Secure session tracking per phone number
- Logout clears all session data

---

## 📱 **User Commands:**

### **Login Commands:**
| Command | Description |
|---------|-------------|
| `user@example.com` | Start login with email |
| `123456` | Verify OTP (6-digit code) |
| `LOGOUT` | Sign out from account |

### **Document Commands (After Login):**
| Command | Description |
|---------|-------------|
| `VIEW DOCS` | List all uploaded documents |
| `GET DOC 1` | Download document #1 |
| Send photo/PDF | Upload new medical document |

### **AI Commands:**
| Command | Description |
|---------|-------------|
| Any health question | Get personalized AI response |
| `HI` / `HELLO` | Welcome message |

---

## 🎨 **Welcome Messages:**

### **For Logged-In Users:**
```
🙏 Namaste, Rajesh!

Welcome back to AyurEze Healthcare! 🌿

✅ Logged in as: rajesh.kumar@example.com

I'm Astra, your personalized AI health assistant.

Quick Commands:
• VIEW DOCS - See your uploaded documents
• Upload photo/PDF - Add medical records
• LOGOUT - Sign out
• Ask any health question!
```

### **For Guest Users:**
```
🙏 Namaste!

Welcome to AyurEze Healthcare! 🌿

I'm Astra, your AI health assistant.

🔐 Login to Access Your Profile:
Send your registered email address to login!

📧 Example:
your.email@example.com

Or ask me any health question! 🌿
```

---

## 🗄️ **Data Integration:**

### **1. Firebase Patient Lookup (by Email):**
```python
# New method added
firebase_service.get_patient_by_email("rajesh@example.com")

# Returns:
{
  "uid": "aacb34f9-8d6c-...",
  "name": "Rajesh Kumar",
  "email": "rajesh@example.com",
  "phone": "916380176373",
  "medicines": [...]
}
```

### **2. Ayureze Backend Lookup (by Email):**
```python
# New method added
backend_client.get_patient_by_email("rajesh@example.com")

# API Call:
# GET /api/admin/patients/search?email=rajesh@example.com
```

### **3. Multi-Tier Fallback:**
```
1. Check if user is authenticated (email session)
   ↓
2. Try Firebase (search by email)
   ↓
3. Try Ayureze Backend (search by email)
   ↓
4. Use guest mode (generic responses)
```

---

## 🛠️ **Implementation Files:**

### **New Files Created:**
1. **`email_auth_service.py`** - Core authentication logic
   - OTP generation
   - Session management
   - Security controls (cooldown, lockout)
   
2. **`email_auth_handlers.py`** - WhatsApp message handlers
   - Email login handler
   - OTP verification handler
   - Logout handler
   - Authenticated patient data retrieval

### **Updated Files:**
1. **`webhook_handler.py`**
   - Replaced phone verification with email login
   - Updated welcome messages
   - Integrated authentication handlers

2. **`firebase_patient_service.py`**
   - Added `get_patient_by_email()` method
   - Email-based patient lookup

3. **`ayureze_backend_client.py`**
   - Added `get_patient_by_email()` method
   - Fixed backend login endpoint URL

---

## 🚀 **Deployment Steps:**

### **Step 1: Upload New Files to HF Space**

Go to: `https://huggingface.co/spaces/ayureze/aibackends/tree/main/app/medicine_reminders`

**Upload these 2 new files:**
1. `email_auth_service.py`
2. `email_auth_handlers.py`

### **Step 2: Update Existing Files**

**Replace these 3 files:**
1. `app/medicine_reminders/webhook_handler.py`
2. `app/firebase_patient_service.py`
3. `app/ayureze_backend_client.py`

### **Step 3: Verify Environment Variables**

Make sure these secrets are set in HF Space:
- ✅ `FIREBASE_SERVICE_ACCOUNT` - Firebase credentials
- ✅ `AYUREZE_BACKEND_URL` - Should be `https://ayureze.org` (NOT `/login`)
- ✅ `AYUREZE_BACKEND_EMAIL` - Admin email
- ✅ `AYUREZE_BACKEND_PASSWORD` - Admin password

### **Step 4: Restart HF Space**

Click "Factory reboot" and wait 2 minutes.

### **Step 5: Test Email Login**

Send WhatsApp message:
```
1. Send: "your.email@example.com"
2. Receive OTP in WhatsApp
3. Send: "123456"
4. Receive: "Login Successful! ✅"
```

---

## 📊 **Session Storage:**

### **Current: In-Memory (Development)**
```python
sessions = {
  "916380176373": {
    "email": "rajesh@example.com",
    "verified": True,
    "otp": "482751",
    "otp_expires": "2025-11-07T17:00:00",
    "attempts": 0,
    "locked_until": None
  }
}
```

### **Recommended: Database (Production)**
```sql
CREATE TABLE auth_sessions (
  phone_number VARCHAR(20) PRIMARY KEY,
  email VARCHAR(255),
  verified BOOLEAN DEFAULT FALSE,
  otp VARCHAR(6),
  otp_expires TIMESTAMP,
  attempts INT DEFAULT 0,
  locked_until TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔍 **Troubleshooting:**

### **Issue: "Invalid Email Format"**
**Cause:** Email doesn't match regex pattern  
**Solution:** Use format: `user@domain.com`

### **Issue: "Please Wait X Seconds"**
**Cause:** OTP cooldown active  
**Solution:** Wait 60 seconds between requests

### **Issue: "Account Locked"**
**Cause:** 5 failed OTP attempts  
**Solution:** Wait 24 hours or contact admin

### **Issue: "OTP Expired"**
**Cause:** OTP older than 10 minutes  
**Solution:** Send email again to get new OTP

### **Issue: "No Patient Found"**
**Cause:** Email not in Firebase/Backend  
**Solution:** Use guest mode or register email in patient database

---

## 📈 **Benefits of Email-Based Auth:**

| Feature | Phone Verification | Email Auth |
|---------|-------------------|------------|
| **Security** | OTP via SMS (cost $$) | OTP via WhatsApp (FREE) |
| **User Experience** | Need phone number | More familiar (email) |
| **Privacy** | Phone number exposed | Email kept private |
| **Cost** | SMS fees | No extra cost |
| **Flexibility** | One device only | Multi-device support |
| **Data Linking** | Phone number match | Email match (more reliable) |

---

## ✅ **Testing Checklist:**

- [ ] User can login with valid email
- [ ] OTP is sent via WhatsApp (not email)
- [ ] OTP verification works correctly
- [ ] Invalid OTP shows error with attempts remaining
- [ ] Account lockout works after 5 failed attempts
- [ ] OTP cooldown prevents spam (60 sec)
- [ ] OTP expires after 10 minutes
- [ ] Logout clears session
- [ ] Authenticated users get personalized responses
- [ ] Guest users get generic responses
- [ ] Firebase patient lookup works by email
- [ ] Backend patient lookup works by email
- [ ] Document commands require authentication

---

## 🎯 **Next Steps (Optional Enhancements):**

1. **Database Storage** - Move sessions from memory to PostgreSQL
2. **Email Templates** - Prettier OTP messages
3. **2FA Option** - Optional SMS as second factor
4. **Session Timeout** - Auto-logout after 24 hours
5. **Audit Logs** - Track all login attempts
6. **Rate Limiting** - IP-based request limits
7. **Push Notifications** - Alert on new login
8. **Biometric** - Fingerprint/FaceID on mobile

---

## 📄 **Summary:**

**Email-based authentication** provides a secure, cost-effective, and user-friendly way for patients to access their medical data via WhatsApp. The system includes OTP verification, account lockout protection, and seamless integration with Firebase and your ayureze.org backend.

**No phone verification needed - just send your email!** 🎉🔐
