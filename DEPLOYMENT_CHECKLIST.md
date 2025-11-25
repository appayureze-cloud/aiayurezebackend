# 🚀 DEPLOYMENT CHECKLIST - HuggingFace Space

**Error:** `ModuleNotFoundError: No module named 'app.medicine_reminders.webhook_handler'`

**Cause:** New email authentication files not uploaded yet to HF Space.

---

## ✅ **STEP-BY-STEP DEPLOYMENT GUIDE**

### **Step 1: Upload NEW Files First** ⚠️ **DO THIS FIRST**

Go to: `https://huggingface.co/spaces/ayureze/aibackends/tree/main/app/medicine_reminders`

**Click "Add file" → "Upload files"**

Upload these **3 NEW files** (they don't exist on HF Space yet):

1. ✅ `hf_space_deploy/app/medicine_reminders/email_auth_service.py`
2. ✅ `hf_space_deploy/app/medicine_reminders/email_auth_handlers.py`
3. ✅ `hf_space_deploy/app/medicine_reminders/order_tracking_whatsapp.py` ← **NEW FOR ORDER TRACKING**

**Then go to:** `https://huggingface.co/spaces/ayureze/aibackends/tree/main/app`

Upload this **1 NEW file**:

4. ✅ `hf_space_deploy/app/ai_content_filter.py`

**⚠️ IMPORTANT:** Wait for these uploads to complete before proceeding!

---

### **Step 2: Update EXISTING Files**

Now update these existing files:

**Go to:** `https://huggingface.co/spaces/ayureze/aibackends/tree/main/app/medicine_reminders`

Replace these files by clicking on each file and using "Edit file":

1. ✅ `webhook_handler.py` → Upload from `hf_space_deploy/app/medicine_reminders/webhook_handler.py`

**Go to:** `https://huggingface.co/spaces/ayureze/aibackends/tree/main/app`

Replace these files:

2. ✅ `shopify_client.py` → Upload from `hf_space_deploy/app/shopify_client.py` ← **UPDATED FOR ORDER TRACKING**
3. ✅ `firebase_patient_service.py` → Upload from `hf_space_deploy/app/firebase_patient_service.py`
4. ✅ `ayureze_backend_client.py` → Upload from `hf_space_deploy/app/ayureze_backend_client.py`

---

### **Step 3: Verify Environment Variables**

Go to: Settings → Secrets

Make sure these are set:

- ✅ `FIREBASE_SERVICE_ACCOUNT` - Firebase JSON credentials
- ✅ `AYUREZE_BACKEND_URL` - Should be `https://ayureze.org` (NOT with `/login`)
- ✅ `AYUREZE_BACKEND_EMAIL` - Admin email
- ✅ `AYUREZE_BACKEND_PASSWORD` - Admin password
- ✅ `CUSTOM_WA_API_BASE_URL` - WhatsApp API base URL
- ✅ `CUSTOM_WA_BEARER_TOKEN` - WhatsApp API bearer token
- ✅ `CUSTOM_WA_VENDOR_UID` - WhatsApp vendor UID

---

### **Step 4: Restart HF Space**

1. Go to: **Settings** → **Factory reboot**
2. Click "Factory reboot" button
3. Wait 2-3 minutes for the space to restart
4. Check the **Logs** tab for any errors

---

### **Step 5: Verify Deployment**

Check the logs for these success messages:

```
✅ Server started
✅ Database tables created
✅ Shopify sync completed
✅ AI model loaded
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:7860
```

If you see errors, check the logs and let me know!

---

## 📂 **File Upload Summary**

### **NEW Files to Upload (4 files):**

```
app/medicine_reminders/
  ├── email_auth_service.py           ← NEW FILE (Email auth)
  ├── email_auth_handlers.py          ← NEW FILE (Email auth)
  └── order_tracking_whatsapp.py      ← NEW FILE (Order tracking) 📦

app/
  └── ai_content_filter.py            ← NEW FILE (AI safety)
```

### **EXISTING Files to Replace (4 files):**

```
app/medicine_reminders/
  └── webhook_handler.py              ← REPLACE (Updated for order tracking)
  
app/
  ├── shopify_client.py               ← REPLACE (Added tracking methods) 📦
  ├── firebase_patient_service.py     ← REPLACE
  └── ayureze_backend_client.py       ← REPLACE
```

---

## 🔍 **Common Issues & Solutions**

### **Issue 1: "ModuleNotFoundError: No module named 'app.medicine_reminders.email_auth_service'"**

**Cause:** New files not uploaded yet  
**Solution:** Upload `email_auth_service.py` and `email_auth_handlers.py` FIRST

---

### **Issue 2: "ModuleNotFoundError: No module named 'app.ai_content_filter'"**

**Cause:** AI content filter file not uploaded  
**Solution:** Upload `ai_content_filter.py` to `app/` directory

---

### **Issue 3: "Backend login failed: 403 Forbidden"**

**Cause:** Wrong backend URL  
**Solution:** Change `AYUREZE_BACKEND_URL` to `https://ayureze.org` (remove `/login`)

---

### **Issue 4: "Firebase service account error"**

**Cause:** Invalid or missing Firebase credentials  
**Solution:** Verify `FIREBASE_SERVICE_ACCOUNT` is set correctly in Secrets

---

## 📋 **Upload Order (CRITICAL)**

**❌ WRONG ORDER:**
1. Update webhook_handler.py first
2. Upload new files later
3. **Result:** ERROR - webhook_handler can't import missing modules!

**✅ CORRECT ORDER:**
1. Upload NEW files first (`email_auth_service.py`, `email_auth_handlers.py`, `ai_content_filter.py`)
2. Then update EXISTING files (`webhook_handler.py`, etc.)
3. **Result:** SUCCESS - all imports work!

---

## 🧪 **After Deployment Testing**

Send WhatsApp messages to test:

**Test 1: Welcome Message**
```
You: "hi"
Bot: Welcome message with login instructions
```

**Test 2: Email Login**
```
You: "patient@example.com"
Bot: OTP sent message with 6-digit code
```

**Test 3: OTP Verification**
```
You: "123456" (the OTP you received)
Bot: "Login Successful! ✅"
```

**Test 4: AI Query**
```
You: "tell me about ayurveda"
Bot: Personalized AI response
```

**Test 5: Logout**
```
You: "LOGOUT"
Bot: "Logged Out Successfully"
```

---

## 📞 **Need Help?**

If you encounter any errors:

1. **Check HF Space Logs** - Look for error messages
2. **Verify all files uploaded** - Make sure all 6 files are present
3. **Check environment variables** - Verify all secrets are set correctly
4. **Try factory reboot** - Sometimes a fresh restart helps

**Share the error message and I'll help you fix it!** 🚀

---

## ✅ **Success Indicators**

You'll know deployment was successful when:

- ✅ No errors in HF Space logs
- ✅ Server starts on port 7860
- ✅ AI model loads successfully
- ✅ WhatsApp bot responds to messages
- ✅ Email login works correctly
- ✅ AI responses are appropriate and on-topic

---

**Ready to deploy? Start with Step 1: Upload NEW files first!** 🎉
