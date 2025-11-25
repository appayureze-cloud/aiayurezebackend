# 🧠 RAG-BASED AI CONVERSATION SYSTEM

## **Retrieval Augmented Generation for Intelligent Responses**

Your AI now uses **all past conversations** from Supabase to provide intelligent, context-aware responses! This makes your AI much smarter by learning from conversation history.

---

## 🎯 **What is RAG?**

**RAG (Retrieval Augmented Generation)** combines:
1. **Retrieval**: Finding relevant past conversations
2. **Augmentation**: Adding this context to the AI prompt
3. **Generation**: AI generates response with full context

**Result:** AI that remembers past conversations and provides personalized responses!

---

## 🚀 **How It Works**

```
User: "What should I eat for breakfast?"
        ↓
RAG System:
├─ 1. Retrieves past conversations about diet
├─ 2. Finds similar queries: "What to eat?"
├─ 3. Builds conversation context
├─ 4. Adds current journey info
└─ 5. Sends to AI model with full context
        ↓
AI Model:
├─ Sees user previously asked about diet
├─ Knows user's health concern
├─ Remembers previous recommendations
└─ Generates personalized response
        ↓
User gets: "Based on our previous conversation about
your acidity, I recommend warm oatmeal with honey..."
```

**AI has FULL CONTEXT from all past conversations!** 📚

---

## 🔧 **System Architecture**

### **Data Storage (Supabase):**

```
chat_messages Table (App conversations)
├─ session_id (journey_id)
├─ user_message
├─ assistant_response
├─ language
├─ metadata (platform, user_id, etc.)
└─ created_at

companion_interactions Table (WhatsApp conversations)
├─ journey_id
├─ interaction_type
├─ content
├─ metadata (platform, user_id, etc.)
└─ created_at
```

### **RAG Flow:**

```
┌─────────────────────────────────────────┐
│  1. User sends message                   │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  2. RAG: Get conversation context       │
│     - Query Supabase for past messages  │
│     - Filter by user_id & journey_id    │
│     - Get last 20 messages               │
│     - Build formatted context string     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  3. RAG: Build enhanced prompt          │
│     [Previous Conversation]             │
│     User: How are you?                  │
│     AI: I'm well, thank you!            │
│                                          │
│     [Current Query]                     │
│     What should I eat?                  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  4. Send to AI model with context       │
│     Model sees full conversation        │
│     Generates personalized response     │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│  5. RAG: Save conversation              │
│     - User message saved                │
│     - AI response saved                 │
│     - Available for future RAG          │
└─────────────────────────────────────────┘
```

---

## 📋 **API Endpoints**

### **1. Send Message with RAG** (Automatic)
```http
POST /api/unified-chat/send
```

**Request:**
```json
{
  "journey_id": "journey_123",
  "user_id": "patient_456",
  "message": "What should I eat?",
  "platform": "app"
}
```

**What Happens:**
1. ✅ RAG retrieves conversation context
2. ✅ AI generates response with context
3. ✅ Conversation saved to Supabase
4. ✅ Available for future RAG queries

**Response:**
```json
{
  "success": true,
  "ai_response": "Based on our previous conversation about your acidity, I recommend...",
  "message_id": "msg_789"
}
```

---

### **2. Get RAG Context**
```http
GET /api/unified-chat/rag/context/{user_id}?journey_id=journey_123&query=diet&max_messages=20
```

**Returns formatted conversation context:**
```json
{
  "user_id": "patient_456",
  "journey_id": "journey_123",
  "context": "[Previous Conversation]\nUser: How are you?\nAssistant: I'm well...",
  "max_messages": 20
}
```

**Use Case:** Manually retrieve conversation context for debugging or custom AI prompts

---

### **3. Find Similar Conversations**
```http
GET /api/unified-chat/rag/similar?query=breakfast diet&user_id=patient_456&limit=5
```

**Returns similar past conversations:**
```json
{
  "query": "breakfast diet",
  "results": [
    {
      "user_message": "What should I eat for breakfast?",
      "assistant_response": "I recommend oatmeal...",
      "created_at": "2025-11-10T08:00:00Z"
    },
    {
      "user_message": "Best diet for acidity?",
      "assistant_response": "Avoid spicy foods...",
      "created_at": "2025-11-09T10:00:00Z"
    }
  ],
  "count": 2
}
```

**Use Case:** Find how AI responded to similar queries in the past

---

### **4. Get Conversation Summary**
```http
GET /api/unified-chat/rag/summary/{user_id}/{journey_id}
```

**Returns conversation summary:**
```json
{
  "user_id": "patient_456",
  "journey_id": "journey_123",
  "summary": "Conversation Summary:\n- Total messages: 45\n- Topics: diet, medicine, symptoms\n- AI has full context"
}
```

**Use Case:** When full conversation is too long, get a summary

---

## 💻 **Code Implementation**

### **Automatic RAG Integration**

RAG is **automatically enabled** in the unified conversation API!

**File:** `app/unified_conversation_api.py`

```python
# When user sends message:

# 1. Get RAG context
conversation_context = await rag_system.get_conversation_context(
    user_id=data.user_id,
    journey_id=data.journey_id,
    current_query=data.message,
    max_messages=20
)

# 2. Build enhanced prompt
enhanced_context = f"""
{conversation_context}

[Current Journey]
Health Concern: {journey['health_concern']}

[Current Query]
{data.message}

Please provide personalized response based on history.
"""

# 3. Generate AI response with context
ai_response = await model_service.generate_response(
    prompt=data.message,
    context=enhanced_context,  # Full conversation history!
    max_length=500
)

# 4. Save conversation for future RAG
await rag_system.save_conversation(
    user_id=data.user_id,
    journey_id=data.journey_id,
    user_message=data.message,
    ai_response=ai_response,
    platform=data.platform
)
```

---

### **Manual RAG Usage**

**Get conversation context:**
```python
from app.rag_conversation_system import rag_system

# Get context for AI
context = await rag_system.get_conversation_context(
    user_id="patient_123",
    journey_id="journey_456",
    current_query="What should I eat?",
    max_messages=20
)

print(context)
# Output:
# [Previous Conversation]
# User: How are you?
# Assistant: I'm well, thank you!
# ...
```

**Save conversation:**
```python
await rag_system.save_conversation(
    user_id="patient_123",
    journey_id="journey_456",
    user_message="Hello Astra",
    ai_response="Namaste! How can I help?",
    platform="whatsapp"
)
```

**Find similar conversations:**
```python
similar = await rag_system.get_similar_conversations(
    query="diet for acidity",
    user_id="patient_123",
    limit=5
)

for conv in similar:
    print(f"Q: {conv['user_message']}")
    print(f"A: {conv['assistant_response']}")
```

---

## 🎨 **Context Format**

RAG builds context in this format:

```
[Previous Conversation History]
User: How are you today?
Assistant: I'm well, thank you! How are you feeling?

User: Much better after following your advice.
Assistant: That's wonderful to hear! Keep up the good work.

User: What should I eat for breakfast?
Assistant: For your acidity, I recommend warm oatmeal with honey...


[Current Context]
Based on the above conversation history, provide a personalized response to the user's current query.
```

**AI sees full conversation before answering!** 🧠

---

## 📊 **RAG Features**

### **1. Conversation Storage** 💾
- ✅ All app messages saved to Supabase
- ✅ All WhatsApp messages saved to Supabase
- ✅ Metadata includes platform, user_id, journey_id
- ✅ Timestamps for chronological ordering

### **2. Context Retrieval** 🔍
- ✅ Get last N messages (default: 20)
- ✅ Filter by user & journey
- ✅ Relevance filtering by keywords
- ✅ Chronological ordering

### **3. Similarity Search** 🎯
- ✅ Find similar past conversations
- ✅ Keyword-based matching
- ✅ Scoring by relevance
- ✅ Top N results

### **4. Summarization** 📝
- ✅ Summary for long conversations
- ✅ Topic extraction
- ✅ Message count
- ✅ Key themes identified

---

## 🚀 **Benefits**

### **For AI:**
- ✅ **Contextual Responses** - AI sees full conversation history
- ✅ **Personalized** - Remembers user's preferences
- ✅ **Consistent** - No contradictory advice
- ✅ **Intelligent** - Learns from past interactions

### **For Patients:**
- ✅ **No Repetition** - AI remembers what you told it
- ✅ **Continuity** - Conversations flow naturally
- ✅ **Personalized Care** - Responses tailored to your history
- ✅ **Better Advice** - AI knows your full health journey

### **For Admin:**
- ✅ **Full History** - All conversations stored in Supabase
- ✅ **Analytics** - Query conversation patterns
- ✅ **Quality Assurance** - Review AI responses
- ✅ **Insights** - Understand patient needs

---

## 🔧 **Configuration**

**File:** `app/rag_conversation_system.py`

### **Adjust Context Size:**
```python
# In RAGConversationSystem.__init__():
self.max_context_messages = 50  # Increase for more context
```

### **Adjust Relevance Threshold:**
```python
self.relevance_threshold = 0.5  # Lower = more results
```

---

## 📈 **Future Enhancements**

### **1. Vector Embeddings** (Advanced)
```python
# Use OpenAI/Hugging Face embeddings
# Store in Supabase with pgvector extension
# Enable true semantic search

from openai import OpenAI

embeddings = openai.Embedding.create(
    input=user_message,
    model="text-embedding-ada-002"
)

# Store in Supabase
# Query with cosine similarity
```

### **2. Conversation Clustering**
- Group similar conversations
- Identify common patterns
- Extract frequently asked questions

### **3. Multi-Language Support**
- Translate queries for search
- Cross-lingual similarity matching

### **4. Conversation Analytics**
- Most discussed topics
- Sentiment analysis
- Patient satisfaction trends

---

## 🧪 **Testing RAG**

### **Test 1: Context Retrieval**
```bash
curl -X GET "http://localhost:5000/api/unified-chat/rag/context/patient_123?journey_id=journey_456&query=diet&max_messages=20"
```

**Expected:** Returns formatted conversation history

### **Test 2: Similar Conversations**
```bash
curl -X GET "http://localhost:5000/api/unified-chat/rag/similar?query=breakfast diet&user_id=patient_123&limit=5"
```

**Expected:** Returns similar past conversations

### **Test 3: Conversation Summary**
```bash
curl -X GET "http://localhost:5000/api/unified-chat/rag/summary/patient_123/journey_456"
```

**Expected:** Returns conversation summary

---

## 📋 **Checklist**

### **Implementation:**
- [x] Created `rag_conversation_system.py`
- [x] Integrated with unified conversation API
- [x] Added RAG context to AI prompts
- [x] Automatic conversation saving
- [x] RAG query endpoints

### **Testing:**
- [ ] Test conversation retrieval
- [ ] Test similarity search
- [ ] Test context building
- [ ] Test AI responses with context
- [ ] Test with long conversations

### **Optimization:**
- [ ] Add vector embeddings (optional)
- [ ] Implement caching for frequent queries
- [ ] Add conversation clustering
- [ ] Create analytics dashboard

---

## 🎉 **You're Ready!**

**Your AI now has:**
- ✅ **Full conversation memory** via Supabase
- ✅ **Context-aware responses** using RAG
- ✅ **Similarity search** for past conversations
- ✅ **Automatic storage** of all messages
- ✅ **Personalized intelligence** for each patient

**AI that remembers everything and gets smarter with every conversation!** 🧠💚

**All conversations stored in Supabase for RAG retrieval!** 📚🚀
