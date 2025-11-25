/**
 * AI Companion Chat Interface
 * Syncs seamlessly between App and WhatsApp
 * 
 * Features:
 * - Real-time message sync
 * - Beautiful UI/UX with Ayurvedic theme
 * - Shows messages from both app and WhatsApp
 * - Journey progress tracking
 * - Rating/feedback modal
 */

import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

// TypeScript interfaces
interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  platform: 'app' | 'whatsapp';
  timestamp: string;
  metadata?: any;
}

interface Journey {
  journey_id: string;
  user_id: string;
  health_concern: string;
  status: string;
  progress_percentage: number;
  adherence_score: number;
}

export const AIChatInterface: React.FC = () => {
  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [journey, setJourney] = useState<Journey | null>(null);
  const [showRatingModal, setShowRatingModal] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
  const USER_ID = localStorage.getItem('user_id') || 'demo_user';
  const JOURNEY_ID = localStorage.getItem('journey_id');
  
  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Load conversation on mount
  useEffect(() => {
    loadConversation();
    
    // Poll for new messages every 5 seconds (sync with WhatsApp)
    const interval = setInterval(loadConversation, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  // Load unified conversation (app + WhatsApp)
  const loadConversation = async () => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/api/unified-chat/conversations/${USER_ID}`,
        {
          params: {
            journey_id: JOURNEY_ID,
            limit: 50
          }
        }
      );
      
      setMessages(response.data.messages);
      
      // Load journey data
      if (JOURNEY_ID) {
        const journeyResponse = await axios.get(
          `${API_BASE_URL}/api/companion/journey/${JOURNEY_ID}`
        );
        setJourney(journeyResponse.data);
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    }
  };
  
  // Send message
  const sendMessage = async () => {
    if (!inputMessage.trim() || !JOURNEY_ID) return;
    
    setIsLoading(true);
    
    // Optimistically add user message
    const userMessage: Message = {
      id: `temp_${Date.now()}`,
      content: inputMessage,
      sender: 'user',
      platform: 'app',
      timestamp: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    
    try {
      const response = await axios.post(
        `${API_BASE_URL}/api/unified-chat/send`,
        {
          journey_id: JOURNEY_ID,
          user_id: USER_ID,
          message: inputMessage,
          platform: 'app'
        }
      );
      
      // Add AI response
      const aiMessage: Message = {
        id: response.data.message_id,
        content: response.data.ai_response,
        sender: 'assistant',
        platform: 'app',
        timestamp: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  // Handle Enter key
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };
  
  // Format timestamp
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };
  
  return (
    <div className="ai-chat-container">
      {/* Header with Journey Progress */}
      <div className="chat-header">
        <div className="header-content">
          <div className="avatar">
            <img src="/astra-avatar.png" alt="Astra" />
          </div>
          <div className="header-info">
            <h2>🌿 Astra - Your AI Companion</h2>
            {journey && (
              <div className="journey-stats">
                <span className="stat">
                  📊 Progress: {journey.progress_percentage}%
                </span>
                <span className="stat">
                  ✅ Adherence: {journey.adherence_score}%
                </span>
                <span className="stat">
                  🏥 {journey.health_concern}
                </span>
              </div>
            )}
          </div>
        </div>
        
        <button 
          className="end-journey-btn"
          onClick={() => setShowRatingModal(true)}
        >
          End Journey
        </button>
      </div>
      
      {/* Messages Area */}
      <div className="messages-container" ref={chatContainerRef}>
        {messages.map((message, index) => (
          <div
            key={message.id}
            className={`message ${message.sender} ${message.platform}`}
          >
            <div className="message-content">
              <div className="message-text">{message.content}</div>
              <div className="message-meta">
                <span className="time">{formatTime(message.timestamp)}</span>
                <span className="platform-badge">
                  {message.platform === 'whatsapp' ? '📱 WhatsApp' : '💻 App'}
                </span>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="chat-input-container">
        <div className="platform-sync-notice">
          💬 Messages synced with WhatsApp in real-time
        </div>
        
        <div className="input-wrapper">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Ctrl+Enter to send)"
            className="chat-input"
            rows={1}
          />
          
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="send-button"
          >
            {isLoading ? '⏳' : '📤 Send'}
          </button>
        </div>
        
        <div className="quick-actions">
          <button className="quick-btn">📊 View Progress</button>
          <button className="quick-btn">💊 Medicine Schedule</button>
          <button className="quick-btn">🍽️ Diet Plan</button>
        </div>
      </div>
      
      {/* Rating Modal */}
      {showRatingModal && (
        <RatingModal
          journeyId={JOURNEY_ID!}
          onClose={() => setShowRatingModal(false)}
          onSubmit={() => {
            setShowRatingModal(false);
            alert('Thank you for your feedback! Journey completed.');
          }}
        />
      )}
    </div>
  );
};

// Rating Modal Component
const RatingModal: React.FC<{
  journeyId: string;
  onClose: () => void;
  onSubmit: () => void;
}> = ({ journeyId, onClose, onSubmit }) => {
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  
  const submitRating = async () => {
    try {
      await axios.post('/api/companion/journey/complete', {
        journey_id: journeyId,
        rating,
        feedback
      });
      
      onSubmit();
    } catch (error) {
      console.error('Error submitting rating:', error);
      alert('Failed to submit rating');
    }
  };
  
  return (
    <div className="modal-overlay">
      <div className="rating-modal">
        <h2>🎉 Complete Your Journey</h2>
        <p>How would you rate your experience with Astra?</p>
        
        <div className="star-rating">
          {[1, 2, 3, 4, 5].map(star => (
            <button
              key={star}
              className={`star ${rating >= star ? 'filled' : ''}`}
              onClick={() => setRating(star)}
            >
              ⭐
            </button>
          ))}
        </div>
        
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Share your feedback (optional)"
          className="feedback-input"
          rows={4}
        />
        
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button 
            onClick={submitRating} 
            disabled={rating === 0}
            className="btn-primary"
          >
            Submit & Complete
          </button>
        </div>
      </div>
    </div>
  );
};

export default AIChatInterface;
