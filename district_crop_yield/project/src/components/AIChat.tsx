import React, { useState, useRef, useEffect } from 'react';
import { ChatMessage, ThinkingStep } from '../types';
import { Send, Mic, MicOff, Volume2 } from 'lucide-react';

interface AIChatProps {
  onThinkingStepsUpdate: (steps: ThinkingStep[]) => void;
}

const AIChat: React.FC<AIChatProps> = ({ onThinkingStepsUpdate }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'bot',
      content: 'नमस्ते! मैं आपका कृषि सहायक हूं। आप मुझसे हिंदी में बात कर सकते हैं या अंग्रेजी में लिख सकते हैं। कैसे मदद कर सकता हूं?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  const handleSendMessage = () => {
    if (!inputMessage.trim()) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, newMessage]);
    setInputMessage('');
    setIsProcessing(true);

    simulateThinkingSteps();

    // Simulate AI response
    setTimeout(() => {
      const responses = [
        'आपके गेहूं की फसल के लिए, इस समय सिंचाई का विशेष ध्यान रखना जरूरी है। मिट्टी की नमी जांचकर सिंचाई करें।',
        'PMFBY के तहत आप अपनी फसल का बीमा करवा सकते हैं। यह प्राकृतिक आपदाओं से होने वाले नुकसान की भरपाई करता है।',
        'आपकी मासिक EMI ₹3,461 है। वर्तमान आय के अनुसार यह manageable लगती है, लेकिन seasonal planning जरूरी है।'
      ];

      const botResponse: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: responses[Math.floor(Math.random() * responses.length)],
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botResponse]);
      setIsProcessing(false);
    }, 4500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      // Simulate voice recording
      setTimeout(() => {
        setIsRecording(false);
        setInputMessage('फसल की सिंचाई कब करनी चाहिए?');
      }, 3000);
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
              <p className="text-sm">{message.content}</p>
              {message.isAudio && (
                <div className="flex items-center space-x-2 mt-2 opacity-75">
                  <Volume2 size={14} />
                  <span className="text-xs">Audio message</span>
                </div>
              )}
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 p-3 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
                <span className="text-sm">Thinking...</span>
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
                isRecording ? 'text-red-500 bg-red-100' : 'text-gray-400 hover:text-gray-600'
              }`}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleSendMessage}
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