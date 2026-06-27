import React, { useEffect, useState, useRef } from 'react';
import { chatAPI } from '../services/api';
import { ChatHistoryEntry } from '../types';
import { 
  Send, Mic, MicOff, Volume2, VolumeX, ArrowLeft, Bot, User, HeartPulse
} from 'lucide-react';

interface ChatProps {
  onBack: () => void;
}

export const Chat: React.FC<ChatProps> = ({ onBack }) => {
  const [history, setHistory] = useState<ChatHistoryEntry[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [speakingMsgId, setSpeakingMsgId] = useState<number | null>(null);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  const fetchChatHistory = async () => {
    try {
      const data = await chatAPI.getHistory();
      setHistory(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  useEffect(() => {
    // Scroll chat to bottom
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history]);

  const handleSend = async (msgToSend?: string) => {
    const text = msgToSend || input;
    if (!text.trim()) return;

    setLoading(true);
    setInput('');
    
    // Add optimistic user message to history
    const tempUserMsg: ChatHistoryEntry = {
      id: Date.now(),
      message: text,
      response: '...',
      sender: 'USER',
      created_at: new Date().toISOString()
    };
    setHistory(prev => [...prev, tempUserMsg]);

    try {
      const result = await chatAPI.send(text);
      // Replace optimistic message and add response
      setHistory(prev => prev.map(m => m.id === tempUserMsg.id ? {
        id: m.id,
        message: text,
        response: result.response,
        sender: 'AI',
        created_at: result.created_at
      } : m));
    } catch (err) {
      console.error(err);
      setHistory(prev => prev.filter(m => m.id !== tempUserMsg.id));
    } finally {
      setLoading(false);
    }
  };

  // --- Voice input: Speech Recognition ---
  const startSpeechRecognition = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Voice input is not supported on this browser.");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.lang = 'en-IN';
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(prev => prev + ' ' + transcript);
    };

    recognition.onerror = () => {
      setListening(false);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognition.start();
  };

  // --- Voice output: Speech Synthesis ---
  const speakResponse = (entry: ChatHistoryEntry) => {
    if ('speechSynthesis' in window) {
      if (speakingMsgId === entry.id) {
        window.speechSynthesis.cancel();
        setSpeakingMsgId(null);
        return;
      }
      
      window.speechSynthesis.cancel(); // Stop active speech
      const textToSpeak = entry.response.replace(/This recommendation is AI-generated and should not replace advice from a qualified healthcare professional./i, '');
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.rate = 0.95;
      
      utterance.onend = () => setSpeakingMsgId(null);
      utterance.onerror = () => setSpeakingMsgId(null);
      
      setSpeakingMsgId(entry.id);
      window.speechSynthesis.speak(utterance);
    } else {
      alert("Speech synthesis is not supported on this browser.");
    }
  };

  const quickQuestions = [
    "What should I eat for diabetes?",
    "Am I drinking enough water?",
    "How to make a healthy ragi porridge?",
    "What foods should I avoid with high blood pressure?"
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header bar */}
      <header className="glass-panel px-6 py-4 flex items-center justify-between shadow-md">
        <button
          onClick={onBack}
          className="py-2 px-4 bg-slate-900 border border-slate-700 text-slate-300 font-bold rounded-xl flex items-center gap-2 hover:bg-slate-850 transition-colors text-sm"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </button>

        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center">
            <Bot className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-200">Dietician Assistant Chat</h1>
            <span className="text-xs text-slate-400">RAG Guidelines-Based Clinical Care</span>
          </div>
        </div>

        <div className="w-20" /> {/* Spacer */}
      </header>

      {/* Chat Area */}
      <div className="flex-1 max-w-4xl w-full mx-auto px-6 py-6 overflow-y-auto flex flex-col space-y-6">
        
        {/* Help introductory panel if history empty */}
        {history.length === 0 && (
          <div className="glass-panel p-6 rounded-3xl border border-slate-800 text-center my-auto space-y-4">
            <div className="w-14 h-14 bg-emerald-500/10 rounded-full flex items-center justify-center mx-auto text-emerald-400">
              <HeartPulse className="w-8 h-8" />
            </div>
            <h2 className="text-2xl font-extrabold text-slate-200">How can I help you today?</h2>
            <p className="text-slate-400 text-elderly-base max-w-md mx-auto">
              Ask about nutrition adjustments, food rules for diabetes or high blood pressure, and recipes.
            </p>
            <div className="flex flex-wrap gap-2.5 justify-center pt-2">
              {quickQuestions.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(q)}
                  className="py-2 px-4 bg-slate-900 hover:bg-slate-850 text-slate-300 text-sm font-semibold rounded-xl border border-slate-800 transition-colors text-left"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message logs */}
        <div className="space-y-6 flex-1">
          {history.map((msg) => (
            <div key={msg.id} className="space-y-2">
              
              {/* User message */}
              <div className="flex items-start gap-3 justify-end">
                <div className="bg-indigo-600 text-white rounded-2xl rounded-tr-none py-3 px-5 max-w-[80%] shadow-md">
                  <p className="text-elderly-base font-medium">{msg.message}</p>
                </div>
                <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-slate-400" />
                </div>
              </div>

              {/* AI message response */}
              {msg.response && (
                <div className="flex items-start gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-emerald-500 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-slate-950" />
                  </div>
                  
                  <div className="glass-panel p-5 rounded-2xl rounded-tl-none border border-slate-800 max-w-[80%] shadow-md relative">
                    <p className="text-elderly-base leading-relaxed text-slate-200 whitespace-pre-wrap">
                      {msg.response}
                    </p>
                    
                    {msg.response !== '...' && (
                      <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3">
                        <span className="text-xs text-rose-400 font-bold max-w-[70%] leading-tight">
                          ⚠️ AI recommendations are helper logs; verify with doctors.
                        </span>
                        
                        <button
                          onClick={() => speakResponse(msg)}
                          className={`p-2 rounded-lg border flex items-center justify-center transition-all ${
                            speakingMsgId === msg.id
                              ? 'bg-rose-500/10 border-rose-500 text-rose-400'
                              : 'bg-slate-900 border-slate-850 text-slate-400 hover:border-slate-700'
                          }`}
                          title="Read response aloud"
                        >
                          {speakingMsgId === msg.id ? <VolumeX className="w-4 h-4 animate-bounce" /> : <Volume2 className="w-4 h-4" />}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input bar */}
      <footer className="glass-panel p-4 sticky bottom-0">
        <div className="max-w-4xl mx-auto flex gap-3 items-center">
          <button
            onClick={startSpeechRecognition}
            className={`p-3.5 rounded-xl border flex items-center justify-center transition-colors shrink-0 ${
              listening 
                ? 'bg-rose-500 border-rose-500 text-white' 
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
            }`}
            title="Voice input"
          >
            {listening ? <MicOff className="w-5 h-5 animate-pulse" /> : <Mic className="w-5 h-5" />}
          </button>
          
          <input
            type="text"
            placeholder="Type your nutrition query here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend();
            }}
            disabled={loading}
            className="flex-1 bg-slate-900/60 border border-slate-800 rounded-xl py-3 px-5 text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 text-elderly-base shadow-inner"
          />

          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className="p-3.5 bg-emerald-500 hover:bg-emerald-450 disabled:bg-slate-900 text-slate-950 disabled:text-slate-600 rounded-xl font-bold transition-all shadow-md shrink-0 active:scale-[0.97]"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </footer>
    </div>
  );
};
