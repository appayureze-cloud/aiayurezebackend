# ⏰ HOW ASTRA AI AGENT AUTOMATICALLY WAKES UP

## 🤖 **Automatic Wake-Up System Explained**

Your backend has an **intelligent scheduling system** that automatically wakes up Astra AI Agent to send reminders, check-ins, and interventions **without any manual intervention**.

---

## 🔄 **Complete Automatic Flow**

```
┌──────────────────────────────────────────────┐
│  1. BACKGROUND SCHEDULER STARTS              │
│     (Runs 24/7 in the background)            │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  2. SCHEDULED TIMES TRIGGER                  │
│     • 8:00 AM - Morning reminders            │
│     • 8:00 PM - Evening reminders            │
│     • Every 6 hours - Shopify sync           │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  3. ASTRA WAKES UP                           │
│     Checks database for patients             │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  4. SENDS REMINDERS VIA WHATSAPP             │
│     To all patients with active schedules    │
└──────────────────────────────────────────────┘
                    ↓
┌──────────────────────────────────────────────┐
│  5. GOES BACK TO SLEEP                       │
│     Waits for next scheduled time            │
└──────────────────────────────────────────────┘
```

---

## 📅 **Automatic Schedule**

### **Daily Medicine Reminders:**

| Time | What Happens | Astra Action |
|------|--------------|--------------|
| **8:00 AM** | Morning wake-up | Send morning medicine reminders |
| **8:00 PM** | Evening wake-up | Send evening medicine reminders |

### **Other Automatic Tasks:**

| Task | Frequency | Purpose |
|------|-----------|---------|
| **Shopify Sync** | Every 6 hours | Update product catalog |
| **Check-ins** | Daily (with reminders) | Ask patients how they feel |
| **Symptom Tracking** | Weekly | Assess progress |

---

## ⚙️ **How It Works (Technical)**

### **1. Background Scheduler**

**File:** `app/background_tasks.py`

```python
# Schedule medicine reminders
schedule.every().day.at("08:00").do(
    lambda: asyncio.run(run_medicine_reminders())
)
schedule.every().day.at("20:00").do(
    lambda: asyncio.run(run_medicine_reminders())
)

# Schedule Shopify sync
schedule.every(6).hours.do(
    lambda: asyncio.run(run_shopify_sync())
)

# Main loop - checks every minute
while True:
    schedule.run_pending()
    time.sleep(60)  # Wake up every minute to check
```

**What This Does:**
- ✅ Runs 24/7 in the background
- ✅ Wakes up every minute to check if it's time
- ✅ When time matches (8:00 AM or 8:00 PM), triggers reminder function
- ✅ Goes back to sleep until next minute

---

### **2. Medicine Reminder Function**

**File:** `app/background_tasks.py`

```python
async def run_medicine_reminders():
    """
    Send medicine reminders to all patients
    Runs at 8 AM and 8 PM daily
    """
    logger.info("🔔 Starting medicine reminder service...")
    
    # Import reminder service
    from app.medicine_reminder_service import send_all_reminders
    
    # Send all reminders
    result = await send_all_reminders()
    
    logger.info(f"✅ Medicine reminders sent: {result.get('sent', 0)} patients")
```

**What This Does:**
1. ✅ Wakes up at scheduled time
2. ✅ Fetches all active medicine schedules from database
3. ✅ For each patient, calculates which medicines are due
4. ✅ Sends WhatsApp reminder to each patient
5. ✅ Logs results
6. ✅ Finishes and waits for next scheduled time

---

### **3. Reminder Engine**

**File:** `app/medicine_reminders/reminder_engine.py`

```python
class ReminderEngine:
    def __init__(self):
        # Initialize WhatsApp client
        self.whatsapp_client = CustomWhatsAppClient()
        
        # Default reminder times
        self.default_times = {
            'morning': time(8, 0),    # 8:00 AM
            'afternoon': time(13, 0), # 1:00 PM
            'evening': time(20, 0)    # 8:00 PM
        }
    
    async def send_pending_reminders(self):
        """Find and send all pending reminders"""
        # Get current time
        current_time = datetime.now()
        
        # Query database for reminders due at this time
        db = SessionLocal()
        
        reminders = db.query(MedicineReminder).filter(
            MedicineReminder.scheduled_time <= current_time,
            MedicineReminder.status == 'pending'
        ).all()
        
        # Send each reminder via WhatsApp
        for reminder in reminders:
            await self.send_reminder(reminder)
```

**What This Does:**
1. ✅ Queries database for all pending reminders
2. ✅ Checks if reminder time has arrived
3. ✅ Sends WhatsApp message to patient
4. ✅ Updates reminder status to "sent"
5. ✅ Tracks delivery status

---

## 📱 **WhatsApp Message Flow**

### **Example: 8:00 AM Wake-Up**

**Time: 8:00 AM**

**Step 1: Scheduler Triggers**
```
[Background Scheduler]
⏰ Time is 8:00 AM
✅ Triggering run_medicine_reminders()
```

**Step 2: Database Query**
```
[Reminder Engine]
🔍 Querying database...
Found 45 patients with morning medicines due
```

**Step 3: Generate Messages**
```
[Message Generator]
Patient 1: Rajesh Kumar
  • Ashwagandha Churna (8 AM)
  • Triphala Powder (8 AM)
  
Patient 2: Priya Sharma
  • Abhayarishtam (8 AM)
  
... (43 more patients)
```

**Step 4: Send via WhatsApp**
```
[WhatsApp Client]
📤 Sending to +916380176373...
✅ Message sent successfully

📤 Sending to +919876543210...
✅ Message sent successfully

... (sending to all 45 patients)
```

**Step 5: Log Results**
```
[Background Scheduler]
✅ Medicine reminders sent: 45 patients
📊 Success: 45, Failed: 0
⏰ Next run: 8:00 PM
```

---

## 🔍 **Example WhatsApp Messages**

### **Morning Reminder (8:00 AM):**

```
☀️ Good Morning, Rajesh!

⏰ Time to take your morning medicines:

1️⃣ Ashwagandha Churna
   📏 1 teaspoon
   🥛 Mix with warm milk
   ⏱️ Before breakfast

2️⃣ Triphala Powder
   📏 1/2 teaspoon
   💧 Mix with warm water
   ⏱️ Empty stomach

Reply:
✅ TAKEN - If you took them
❌ SKIP - If you missed
⏰ LATER - Remind in 30 min

Your Progress:
📊 Day 15 of 60 (25% complete)
✅ Adherence: 93%

Stay healthy! 🌿
```

### **Evening Reminder (8:00 PM):**

```
🌙 Good Evening, Rajesh!

⏰ Time for your evening medicine:

💊 Ashwagandha Churna
📏 1 teaspoon
🥛 Mix with warm milk
⏱️ After dinner

Reply:
✅ TAKEN
❌ SKIP
⏰ LATER

Today's Progress:
✅ Morning: Taken
✅ Afternoon: Taken
⏰ Evening: Pending

Keep it up! 💪
```

---

## 🗓️ **Daily Schedule Example**

**For a typical day:**

```
00:00 AM - Scheduler running (sleeping)
  ↓
08:00 AM - 🚨 WAKE UP! Send morning reminders
           📤 Send to 45 patients
           ✅ Done! Go back to sleep
  ↓
09:00 AM - Scheduler running (sleeping)
  ↓
14:00 PM - Shopify sync (every 6 hours)
           📦 Update 250 products
           ✅ Done! Go back to sleep
  ↓
20:00 PM - 🚨 WAKE UP! Send evening reminders
           📤 Send to 45 patients
           ✅ Done! Go back to sleep
  ↓
20:00 PM - Shopify sync (6 hours after last)
           📦 Update products
           ✅ Done! Go back to sleep
  ↓
23:59 PM - Scheduler running (sleeping)
```

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────┐
│  Background Worker Process (24/7)           │
│  ├── Schedule Library                       │
│  ├── Timer (checks every 60 seconds)        │
│  └── Task Queue                             │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  Scheduled Tasks                             │
│  ├── 08:00 AM → Medicine Reminders          │
│  ├── 20:00 PM → Medicine Reminders          │
│  └── Every 6h → Shopify Sync                │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  Reminder Engine                             │
│  ├── Query Database                          │
│  ├── Get Active Schedules                    │
│  ├── Calculate Due Medicines                 │
│  └── Generate Messages                       │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  WhatsApp Client                             │
│  ├── Format Messages                         │
│  ├── Send via Custom API                     │
│  └── Track Delivery                          │
└─────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────┐
│  Patient's WhatsApp                          │
│  └── Receives Reminder ✅                   │
└─────────────────────────────────────────────┘
```

---

## 🚀 **How to Start Background Worker**

### **Option 1: Railway / Cloud Deployment**

**Create a Worker Service:**

1. **Add to `Procfile`:**
   ```
   worker: python -m app.background_tasks
   ```

2. **Railway will run it automatically** as a separate worker process

3. **Logs:**
   ```
   🤖 Background Tasks Worker Started
   📅 Scheduling background tasks...
   ✅ Medicine reminders scheduled: 8:00 AM, 8:00 PM
   ✅ Shopify sync scheduled: Every 6 hours
   ⏰ Scheduler running...
   ```

---

### **Option 2: HuggingFace Space**

**Run in background using `asyncio`:**

**File:** `main_enhanced.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Start background scheduler
    asyncio.create_task(start_background_scheduler())
    
    yield
    
async def start_background_scheduler():
    """Start scheduler in background"""
    while True:
        await asyncio.sleep(60)  # Check every minute
        
        current_time = datetime.now().time()
        
        # Check if it's 8:00 AM
        if current_time.hour == 8 and current_time.minute == 0:
            await run_medicine_reminders()
        
        # Check if it's 8:00 PM
        if current_time.hour == 20 and current_time.minute == 0:
            await run_medicine_reminders()
```

---

### **Option 3: External Cron Service (EasyCron)**

**Use external service to trigger endpoints:**

**Setup:**
1. Create cron job on EasyCron.com
2. Schedule: `0 8,20 * * *` (8 AM and 8 PM)
3. URL: `https://your-backend.com/api/cron/reminders`
4. Method: POST

**Endpoint in backend:**
```python
@router.post("/api/cron/reminders")
async def trigger_reminders():
    """Endpoint for external cron to trigger"""
    result = await run_medicine_reminders()
    return {"success": True, "sent": result.get('sent', 0)}
```

---

## 📊 **Database Tables Used**

### **1. medicine_schedules**
```sql
CREATE TABLE medicine_schedules (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR,
    medicine_name VARCHAR,
    morning_time TIME,      -- e.g., "08:00"
    afternoon_time TIME,    -- e.g., "13:00"
    evening_time TIME,      -- e.g., "20:00"
    is_active BOOLEAN,
    start_date TIMESTAMP,
    end_date TIMESTAMP
);
```

### **2. medicine_reminders**
```sql
CREATE TABLE medicine_reminders (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER,
    patient_id VARCHAR,
    scheduled_time TIMESTAMP,  -- e.g., "2025-11-08 08:00:00"
    status VARCHAR,             -- 'pending', 'sent', 'taken', 'skipped'
    sent_at TIMESTAMP,
    response_at TIMESTAMP,
    response_type VARCHAR       -- 'taken', 'skipped', 'later'
);
```

---

## 🔄 **Complete Automatic Cycle**

### **Day 1:**

**8:00 AM:**
```
Scheduler: Wake up!
Database: 45 patients need reminders
WhatsApp: Send 45 messages
Patients: Receive reminders
Scheduler: Done! Sleep until 8:00 PM
```

**8:00 PM:**
```
Scheduler: Wake up!
Database: 45 patients need evening reminders
WhatsApp: Send 45 messages
Patients: Receive reminders
Scheduler: Done! Sleep until tomorrow 8:00 AM
```

### **Day 2:**

**Repeat same cycle...**

### **Day 60:**

**Last day of treatment:**
```
8:00 AM: Send final reminder
System: Mark case as "RESOLVED"
Astra: Send congratulations message
Scheduler: Stop reminders for this patient
```

---

## ⚡ **Smart Features**

### **1. Skip Sent Reminders:**
```python
# Don't send duplicate reminders
reminders = db.query(MedicineReminder).filter(
    MedicineReminder.status == 'pending',  # Only pending
    MedicineReminder.scheduled_time <= now
).all()
```

### **2. Respect Patient Timezone:**
```python
# Convert to patient's local time
patient_timezone = get_patient_timezone(patient_id)
reminder_time = scheduled_time.astimezone(patient_timezone)
```

### **3. Handle Failures:**
```python
try:
    await whatsapp_client.send_message(...)
except Exception as e:
    # Log error
    # Retry after 5 minutes
    schedule_retry(reminder_id, retry_after=5)
```

### **4. Track Responses:**
```python
# When patient replies "TAKEN"
update_reminder_status(reminder_id, status='taken')
update_adherence_score(patient_id, +1)
```

---

## 🎯 **Benefits of Automatic System**

| Feature | Benefit |
|---------|---------|
| **24/7 Operation** | Never misses a reminder |
| **Precision Timing** | Exact 8 AM and 8 PM delivery |
| **No Manual Work** | Fully automated |
| **Scalable** | Handles 1000s of patients |
| **Reliable** | Continues even if server restarts |
| **Trackable** | Complete logs of all sends |

---

## 🔍 **Monitoring & Logs**

### **Check if scheduler is running:**

**Logs will show:**
```
2025-11-08 07:59:59 - 📅 Scheduling background tasks...
2025-11-08 08:00:00 - 🔔 Starting medicine reminder service...
2025-11-08 08:00:15 - 📤 Sending reminder to +916380176373
2025-11-08 08:00:16 - ✅ Message sent successfully
2025-11-08 08:00:45 - ✅ Medicine reminders sent: 45 patients
2025-11-08 08:01:00 - ⏰ Scheduler running... (sleeping)
```

---

## 📋 **Setup Checklist**

For automatic wake-up to work, ensure:

- ✅ Background worker process running
- ✅ Database connection active
- ✅ WhatsApp API credentials set
- ✅ Medicine schedules created in database
- ✅ Patient phone numbers verified
- ✅ Timezone configured correctly
- ✅ Scheduler started on server boot

---

## 🚨 **Troubleshooting**

### **Reminders not sending?**

**Check:**
1. ✅ Is background worker running?
   ```bash
   ps aux | grep background_tasks
   ```

2. ✅ Are there pending reminders in database?
   ```sql
   SELECT * FROM medicine_reminders WHERE status = 'pending';
   ```

3. ✅ Is WhatsApp API working?
   ```python
   whatsapp_client.test_connection()
   ```

4. ✅ Check scheduler logs:
   ```
   tail -f /var/log/background_tasks.log
   ```

---

## ✨ **Summary**

**Your Astra AI Agent wakes up automatically using:**

1. ✅ **Background Scheduler** - Runs 24/7
2. ✅ **Python `schedule` library** - Manages timing
3. ✅ **Automatic triggers at 8 AM & 8 PM** - Daily
4. ✅ **Database queries** - Gets active schedules
5. ✅ **WhatsApp API** - Sends messages
6. ✅ **Status tracking** - Logs everything
7. ✅ **Retry mechanism** - Handles failures
8. ✅ **Patient responses** - Updates adherence

**No manual intervention needed - Astra works 24/7 automatically!** ⏰🤖🌿
