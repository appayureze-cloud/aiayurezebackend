# 🚀 Deploy to HuggingFace Spaces - Complete Package

This folder contains **everything** you need to deploy your AI backend to a fresh HuggingFace Space.

---

## 📦 What's Included

✅ **main_enhanced.py** - Complete FastAPI backend  
✅ **app/** - All modules (WhatsApp, AI, medicine reminders, Storj, etc.)  
✅ **Dockerfile** - GPU-optimized for T4  
✅ **requirements.txt** - All Python dependencies  
✅ **static/** - Empty folder (required by HF Spaces)  
✅ **README.md** - This file  

---

## 🚀 Quick Deploy (5 Minutes)

### **Step 1: Create New HuggingFace Space**

1. Go to: https://huggingface.co/new-space
2. Fill in:
   ```
   Space name: ayureze-backend-v2
   License: Apache 2.0
   Select SDK: Docker
   Space hardware: T4 small (GPU) - $0.60/hour
   ```
3. Click **"Create Space"**

---

### **Step 2: Upload Files**

**Option A: Upload via Web Interface**

1. Click **"Files"** tab in your new Space
2. Click **"Add file"** → **"Upload files"**
3. Drag and drop ALL files from this folder:
   - Dockerfile
   - main_enhanced.py
   - requirements.txt
   - README.md
   - app/ (entire folder)
   - static/ (empty folder)
4. Click **"Commit changes to main"**

**Option B: Use Git (if you prefer)**

```bash
# Clone your new Space
git clone https://huggingface.co/spaces/your-username/ayureze-backend-v2
cd ayureze-backend-v2

# Copy all files from hf_space_deploy
cp -r /path/to/hf_space_deploy/* .

# Push to HuggingFace
git add .
git commit -m "Deploy complete AyurEze AI backend"
git push
```

---

### **Step 3: Add Secrets**

1. Go to your Space → **Settings** → **Repository secrets**
2. Click **"New secret"** and add each one:

```bash
CUSTOM_WA_API_BASE_URL
CUSTOM_WA_BEARER_TOKEN
CUSTOM_WA_VENDOR_UID
FIREBASE_SERVICE_ACCOUNT
STORJ_ACCESS_KEY
STORJ_SECRET_KEY
STORJ_ENDPOINT
SUPABASE_URL
SUPABASE_KEY
SHOPIFY_SHOP_URL
SHOPIFY_ACCESS_TOKEN
DATA_ENCRYPTION_KEY
AYUREZE_WHATSAPP_API_TOKEN (if you use it)
AYUREZE_WHATSAPP_BASE_URL (if you use it)
AYUREZE_WHATSAPP_PHONE_ID (if you use it)
AYUREZE_WHATSAPP_VENDOR_UID (if you use it)
```

**Copy values from your old Space secrets!**

---

### **Step 4: Wait for Build**

HuggingFace will automatically:
1. Build your Docker image (5-10 minutes)
2. Start the container
3. Your Space will be live!

**Watch the build logs** in your Space to see progress.

---

### **Step 5: Get Your New URL**

After build completes:
```
https://your-username-ayureze-backend-v2.hf.space
```

---

### **Step 6: Update WhatsApp Webhook**

Change webhook to your new Space:
```
https://your-username-ayureze-backend-v2.hf.space/webhooks/custom-whatsapp
```

---

### **Step 7: Test**

Send on WhatsApp (6380176373):
```
VERIFY
```

Should work perfectly! ✅

---

## ⚙️ Files Explained

### **Dockerfile**
- Optimized for T4 GPU
- Installs PyTorch with CUDA 12.1
- Sets up all dependencies
- Exposes port 7860 (HF Spaces default)

### **main_enhanced.py**
- Complete FastAPI backend
- Llama 3.1 8B AI agent
- WhatsApp authentication
- Medicine reminders
- Storj document storage
- Shopify integration

### **app/**
- `whatsapp_auth/` - Firebase Phone Auth with OTP
- `medicine_reminders/` - Automated reminder system
- `ai_agent_api.py` - Llama AI integration
- `storj_client.py` - Storj storage
- `shopify_client.py` - Shopify API
- All other modules

### **requirements.txt**
- All Python packages needed
- PyTorch, Transformers, FastAPI, etc.

### **static/**
- Empty folder (required by HF Spaces)
- Can add FCM test page later if needed

---

## 💰 Cost

**HuggingFace Spaces T4 GPU:**
- **Free tier**: NOT available for GPU Spaces
- **T4 small**: $0.60/hour = ~$432/month (24/7)
- **Auto-pause**: You can pause when not in use

**To save money:**
1. Pause Space when not testing
2. Only run when needed
3. Use RunPod serverless instead ($10-30/month)

---

## ⚠️ Important Notes

1. **Don't forget secrets** - Your app won't work without them
2. **Copy exact values** - From your old Space secrets
3. **T4 GPU required** - For Llama 3.1 8B model
4. **Port 7860** - HF Spaces uses this port (already configured)
5. **Build time** - First build takes 5-10 minutes

---

## 🔧 Troubleshooting

### **Build fails?**
- Check Dockerfile syntax
- Verify requirements.txt has all packages
- Check build logs for errors

### **App doesn't start?**
- Check if all secrets are added
- Verify FIREBASE_SERVICE_ACCOUNT is valid JSON
- Check runtime logs

### **WhatsApp doesn't work?**
- Update webhook URL to new Space
- Verify all WhatsApp secrets are added
- Test with VERIFY command

### **AI model doesn't load?**
- Ensure T4 GPU is selected (not CPU)
- Check if Space has enough memory
- Verify model files download correctly

---

## ✅ Checklist

- [ ] Created new HF Space with Docker SDK
- [ ] Selected T4 small GPU
- [ ] Uploaded all files from this folder
- [ ] Added all secrets (copy from old Space)
- [ ] Waited for build to complete
- [ ] Got new Space URL
- [ ] Updated WhatsApp webhook
- [ ] Tested VERIFY command
- [ ] Everything works!

---

## 🎯 What You Get

**Complete AI Healthcare Backend:**
- ✅ Llama 3.1 8B AI agent (Ayurveda)
- ✅ WhatsApp authentication (OTP)
- ✅ Medicine reminder automation
- ✅ Storj document storage (DISHA compliant)
- ✅ Shopify product integration
- ✅ Prescription PDF generation
- ✅ Multilingual support (15+ languages)
- ✅ Android app integration

**All running on fresh HF Space!** 🚀

---

## 📞 Support

**HuggingFace Docs**: https://huggingface.co/docs/hub/spaces-sdks-docker  
**Your old Space**: (pause or delete after new one works)  
**This package**: Ready to upload!

---

**Your complete backend is ready to deploy to a fresh HuggingFace Space!** 🎉
