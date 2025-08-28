import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, ThinkingStep } from '../types';
import { Send, Mic, MicOff } from 'lucide-react';

interface AIChatProps {
  onThinkingStepsUpdate: (steps: ThinkingStep[]) => void;
}

const AIChat: React.FC<AIChatProps> = ({ onThinkingStepsUpdate }) => {
  // Use a single state for the MediaRecorder instance
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'bot',
      content: 'नमस्ते! मैं आपका कृषि सहायक हूं। आप मुझसे हिंदी में बात कर सकते हैं या अंग्रेजी में लिख सकते हैं। कैसे मदद कर सकता हूं?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  // Consolidate all processing states into a single boolean
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const flaskappRoute = 'http://127.0.0.1:5000';

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const simulateThinkingSteps = () => {
    const steps: ThinkingStep[] = [
      {
        id: '1',
        step: 'Understanding Query',
        description: 'Analyzing the farmer\'s question and context',
        status: 'processing'
      },
      {
        id: '2',
        step: 'Accessing Knowledge Base',
        description: 'Retrieving relevant agricultural information',
        status: 'pending'
      },
      {
        id: '3',
        step: 'Regional Analysis',
        description: 'Considering local climate and soil conditions',
        status: 'pending'
      },
      {
        id: '4',
        step: 'Generating Response',
        description: 'Formulating personalized advice',
        status: 'pending'
      }
    ];

    onThinkingStepsUpdate(steps);

    // Simulate step-by-step processing
    setTimeout(() => {
      steps[0].status = 'completed';
      steps[1].status = 'processing';
      onThinkingStepsUpdate([...steps]);
    }, 1000);

    setTimeout(() => {
      steps[1].status = 'completed';
      steps[2].status = 'processing';
      onThinkingStepsUpdate([...steps]);
    }, 2000);

    setTimeout(() => {
      steps[2].status = 'completed';
      steps[3].status = 'processing';
      onThinkingStepsUpdate([...steps]);
    }, 3000);

    setTimeout(() => {
      steps[3].status = 'completed';
      onThinkingStepsUpdate([...steps]);
    }, 4000);
  };

  // Refactored to accept the message content as an argument
  const handleSendMessage = async (content: string, lang: string) => {
    if (!content.trim()) return;

    // Add user message to chat immediately
    if (lang == 'eng') {
      const newUserMessage: ChatMessage = {
        id: Date.now().toString(),
        type: 'user',
        content: content,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, newUserMessage]);
    }
    
    // Clear input box
    setInputMessage('');
    
    // Set processing state to true
    setIsProcessing(true);
    simulateThinkingSteps();

    try {
      const res = await fetch(`${flaskappRoute}/api/submit_query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: content, lang: lang })
      });

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const result = await res.json();

      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: result.message,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botResponse]);

    } catch (error) {
      console.error('Error submitting query:', error);
      const botError: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: 'Sorry, I am unable to process your request at the moment.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, botError]);

    } finally {
      setIsProcessing(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      // Pass the current input value to the handler
      handleSendMessage(inputMessage, 'eng');
    }
  };

  const toggleRecording = async () => {
    // If we're already recording, stop
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
      mediaRecorderRef.current.stop();
      return;
    }
    
    // If not, start recording
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      let audioChunks: BlobPart[] = [];
      setIsProcessing(true); // Show loader for recording and upload

      mediaRecorder.ondataavailable = e => {
        audioChunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunks, { type: 'audio/webm' });
        // The rest of the process is now handled in a single flow
        await handleAudioUploadAndQuery(blob);
      };

      mediaRecorder.start();
      
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setIsProcessing(false);
    }
  };

  // Combines the audio upload and query submission into one function
  const handleAudioUploadAndQuery = async (blob: Blob) => {
      const formData = new FormData();
      formData.append("audio", blob, "recording.webm");

      try {
          const uploadResponse = await fetch(`${flaskappRoute}/api/upload_audio`, {
              method: "POST",
              body: formData
          });

          if (!uploadResponse.ok) {
              throw new Error(`Upload failed with status: ${uploadResponse.status}`);
          }

          const data = await uploadResponse.json();
          const hindi_msg = data.hindi_text;
          const english_msg = data.english_text;
          const audioUrl = URL.createObjectURL(blob);

          // Add a new user message for the transcribed text
          const newUserMessage: ChatMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: hindi_msg,
            timestamp: new Date(),
            audioUrl: audioUrl
          };
          setMessages(prev => [...prev, newUserMessage]);
          
          // Submit the query with the English transcription
          await handleSendMessage(english_msg, 'hi');

      } catch (error) {
          console.error("Error uploading audio:", error);
          const errorMessage: ChatMessage = {
            id: (Date.now() + 1).toString(),
            type: 'bot',
            content: 'Sorry, I couldn\'t process that audio.',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsProcessing(false);
      }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-green-100 flex flex-col h-[600px]">
      <div className="flex items-center space-x-3 p-6 border-b border-gray-100">
        <div className="w-10 h-10 bg-green-100 rounded-xl flex items-center justify-center">
          <span className="text-green-600 text-lg">🤖</span>
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">General Queries</h2>
          <p className="text-sm text-gray-600">AI Assistant for farmers</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div key={message.id} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-3 rounded-lg ${
              message.type === 'user' 
                ? 'bg-green-600 text-white' 
                : 'bg-gray-100 text-gray-900'
            }`}>
              {message.audioUrl && (
                  <audio controls src={message.audioUrl} className="w-full mb-2" />
              )}
              <p className="text-sm">{message.content}</p>
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <span className="text-sm">Thinking</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="p-6 border-t border-gray-100">
        <div className="flex space-x-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your question..."
              className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
            />
            <button
              onClick={toggleRecording}
              className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 rounded-full transition-colors ${
                isProcessing && mediaRecorderRef.current?.state === 'recording' ? 'text-red-500 bg-red-100' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              {isProcessing && mediaRecorderRef.current?.state === 'recording' ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => handleSendMessage(inputMessage, 'eng')}
              disabled={!inputMessage.trim() || isProcessing}
              className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
