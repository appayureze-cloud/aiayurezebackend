# 🎨 Frontend AI Companion Components

## **React Components for AyurEze AI Companion**

Beautiful, production-ready React components that sync seamlessly between your app and WhatsApp.

---

## 📁 **Files Included**

1. **`AIChatInterface.tsx`** - Main chat component
2. **`AIChatInterface.css`** - Styles with Ayurvedic theme
3. **README.md** - This file

---

## 🚀 **Quick Start**

### **1. Install in Your React App:**

```bash
cd your-react-app

# Copy files
cp AIChatInterface.tsx src/components/
cp AIChatInterface.css src/components/

# Install dependencies
npm install axios
```

### **2. Configure Environment:**

Create `.env` file:
```env
REACT_APP_API_URL=https://your-backend-api.com
```

### **3. Use Component:**

```tsx
// App.tsx or any parent component
import AIChatInterface from './components/AIChatInterface';
import './components/AIChatInterface.css';

function App() {
  // Set user authentication
  React.useEffect(() => {
    const user = getCurrentUser(); // Your auth logic
    localStorage.setItem('user_id', user.id);
    localStorage.setItem('journey_id', user.journeyId);
  }, []);
  
  return (
    <div className="App">
      <AIChatInterface />
    </div>
  );
}

export default App;
```

### **4. Start Development Server:**

```bash
npm start
```

Visit `http://localhost:3000` and you'll see the chat interface!

---

## ✨ **Features**

### **🔄 Real-Time Sync**
- Polls backend every 5 seconds for new messages
- Shows messages from both app and WhatsApp
- Platform badges on each message (💻 App / 📱 WhatsApp)

### **🎨 Beautiful UI**
- Ayurvedic green theme
- Smooth animations
- Responsive design (mobile-friendly)
- Professional layout

### **📊 Journey Tracking**
- Progress percentage in header
- Adherence score display
- Health concern shown
- Real-time updates

### **⭐ Rating System**
- "End Journey" button
- Star rating (1-5)
- Optional text feedback
- Beautiful modal UI

### **⚡ Quick Actions**
- View Progress
- Medicine Schedule
- Diet Plan

---

## 🔧 **Customization**

### **Change Colors:**

Edit `AIChatInterface.css`:

```css
/* Primary green color */
background: linear-gradient(135deg, #2e7d32 0%, #43a047 100%);

/* Change to blue */
background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%);
```

### **Change Logo:**

Replace avatar image:
```tsx
<img src="/astra-avatar.png" alt="Astra" />
```

### **Change Polling Interval:**

Default is 5 seconds. To change:
```tsx
const interval = setInterval(loadConversation, 3000); // 3 seconds
```

---

## 📱 **API Endpoints Used**

The component uses these backend endpoints:

1. **GET** `/api/unified-chat/conversations/{user_id}`
   - Fetches unified conversation (app + WhatsApp)
   - Polls every 5 seconds

2. **POST** `/api/unified-chat/send`
   - Sends message from app
   - Gets AI response

3. **GET** `/api/companion/journey/{journey_id}`
   - Fetches journey progress
   - Gets health concern, adherence, etc.

4. **POST** `/api/companion/journey/complete`
   - Completes journey
   - Submits rating & feedback

---

## 🎯 **User Flow**

```
1. User opens app
   ↓
2. Sees chat interface with history
   ↓
3. Messages include both app & WhatsApp
   ↓
4. Types message "How are you?"
   ↓
5. Gets AI response instantly
   ↓
6. Sees progress in header
   ↓
7. Clicks "End Journey" when healed
   ↓
8. Rates experience (1-5 stars)
   ↓
9. Submits feedback
   ↓
10. Gets PDF report via email ✅
```

---

## 🔐 **Authentication**

Component reads from `localStorage`:

```javascript
const USER_ID = localStorage.getItem('user_id');
const JOURNEY_ID = localStorage.getItem('journey_id');
```

**Set these before using the component!**

---

## 📱 **Responsive Design**

Component is fully responsive:

- **Desktop:** Full width, 3-column layout
- **Tablet:** 2-column layout, smaller padding
- **Mobile:** Single column, touch-optimized

---

## 🎨 **Design System**

### **Colors:**
- **Primary Green:** `#2e7d32` (Ayurvedic theme)
- **Light Green:** `#e8f5e9` (backgrounds)
- **White:** `#ffffff` (message bubbles)
- **Gray:** `#666666` (timestamps)

### **Fonts:**
- **Primary:** Inter, -apple-system, sans-serif
- **Size:** 15px (body), 13px (small)

### **Spacing:**
- **Padding:** 20px (desktop), 15px (mobile)
- **Message Gap:** 15px
- **Border Radius:** 18px (messages), 24px (inputs)

---

## 🐛 **Troubleshooting**

### **"Cannot read property 'user_id' of null"**
**Solution:** Set user_id in localStorage before loading component

### **"Network Error" when sending messages**
**Solution:** Check REACT_APP_API_URL is correct and backend is running

### **Messages not syncing**
**Solution:** Verify backend `/unified-chat/conversations` endpoint works

### **Rating modal not appearing**
**Solution:** Check console for errors, verify journey_id exists

---

## 📚 **Dependencies**

```json
{
  "dependencies": {
    "react": "^18.0.0",
    "axios": "^1.6.0"
  }
}
```

---

## 🚀 **Production Deployment**

### **Build for Production:**

```bash
npm run build
```

### **Environment Variables:**

```env
REACT_APP_API_URL=https://api.ayureze.com
```

### **Deploy to:**
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any React hosting

---

## ✅ **Checklist**

Before deploying:

- [ ] Set `REACT_APP_API_URL` environment variable
- [ ] Test user authentication (user_id, journey_id)
- [ ] Test message sending
- [ ] Test message receiving
- [ ] Test rating modal
- [ ] Test on mobile devices
- [ ] Test WhatsApp sync
- [ ] Optimize bundle size
- [ ] Add error boundaries
- [ ] Add analytics tracking

---

## 💡 **Tips**

1. **Use WebSocket for Real-Time:**
   - Polling works but WebSocket is better
   - See `APP_WHATSAPP_SYNC_GUIDE.md` for WebSocket setup

2. **Add Push Notifications:**
   - Use Firebase Cloud Messaging
   - Notify users of new WhatsApp messages

3. **Add Offline Support:**
   - Use IndexedDB for local message cache
   - Sync when connection restored

4. **Add Typing Indicators:**
   - Show "Astra is typing..." when AI is generating

---

## 📖 **Documentation**

**Full Integration Guide:** `../APP_WHATSAPP_SYNC_GUIDE.md`

**Backend API:** `../app/unified_conversation_api.py`

**Journey System:** `../ASTRA_AI_COMPANION_JOURNEY.md`

---

## 🎉 **You're All Set!**

Your React app now has:
- ✅ Beautiful AI chat interface
- ✅ Real-time app/WhatsApp sync
- ✅ Journey progress tracking
- ✅ Rating & feedback system
- ✅ Production-ready code

**Start building amazing patient experiences!** 🌿💚
