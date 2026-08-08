'use client';

import { LiveKitRoom, RoomAudioRenderer, StartAudio, useVoiceAssistant } from '@livekit/components-react';
import { useState } from 'react';

export default function Home() {
  const [shouldConnect, setShouldConnect] = useState(false);
  const [token, setToken] = useState<string>('');
  const [url, setUrl] = useState<string>('');
  const [micError, setMicError] = useState<string>('');
  
  // Default language set to English ('en')
  const [lang, setLang] = useState<'en' | 'hi'>('en');

  const handleStartCall = async () => {
    try {
      setMicError('');
      await navigator.mediaDevices.getUserMedia({ audio: true });

      const res = await fetch('/api/token', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to get token');

      const data = await res.json();
      setToken(data.participantToken);
      setUrl(data.serverUrl);
      setShouldConnect(true);
    } catch (err: any) {
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setMicError(
          lang === 'hi'
            ? 'माइक्रोफोन की अनुमति नहीं मिली। कृपया ब्राउज़र सेटिंग्स में माइक्रोफोन को चालू करें।'
            : 'Microphone permission blocked. Please enable mic access in your browser settings.'
        );
      } else {
        setMicError(
          lang === 'hi'
            ? 'कनेक्शन विफल रहा। कृपया अपना इंटरनेट कनेक्शन या सर्वर जांचें।'
            : 'Connection failed. Please check your internet connection or backend server.'
        );
      }
    }
  };

  const handleDisconnect = () => {
    setShouldConnect(false);
    setToken('');
  };

  return (
    <main className="min-h-screen bg-[#f8fafc] text-slate-800 flex flex-col justify-between p-6 font-sans relative">
      {/* 1. Header with Logo & Dynamic Language Toggle */}
      <header className="w-full max-w-6xl mx-auto flex items-center justify-between py-2">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sky-700 text-white font-bold text-lg flex items-center justify-center shadow-sm">
            AA
          </div>
          <div>
            <h1 className="text-base font-bold text-sky-950 tracking-tight leading-none">
              ASHA ASSIST
            </h1>
            <p className="text-xs text-sky-700 font-medium mt-0.5">
              {lang === 'hi' ? 'स्वास्थ्य सेवा डिजिटल साथी' : 'Healthcare Field Assistant'}
            </p>
          </div>
        </div>

        {/* Dynamic Language Switcher */}
        <div className="bg-white border border-slate-200 p-1 rounded-full text-xs font-semibold text-slate-600 shadow-sm flex items-center gap-1">
          <button
            onClick={() => setLang('en')}
            className={`px-3 py-0.5 rounded-full transition-all ${
              lang === 'en'
                ? 'bg-sky-100 text-sky-800 font-bold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            English
          </button>
          <span className="text-slate-300">|</span>
          <button
            onClick={() => setLang('hi')}
            className={`px-3 py-0.5 rounded-full transition-all ${
              lang === 'hi'
                ? 'bg-sky-100 text-sky-800 font-bold'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            हिन्दी
          </button>
        </div>
      </header>

      {/* 2. Main Central Card */}
      <div className="w-full max-w-md mx-auto my-auto">
        <div className="bg-white border border-slate-200/80 rounded-2xl p-8 shadow-sm text-center flex flex-col items-center gap-5">
          
          {/* Medical Icon */}
          <div className="w-12 h-12 rounded-xl bg-sky-50 text-sky-600 border border-sky-100 flex items-center justify-center text-xl shadow-xs">
            🩺
          </div>

          <div>
            <h2 className="text-xl font-bold text-slate-900">
              AshaAssist Voice Agent
            </h2>
            <p className="text-xs text-slate-500 mt-1.5 leading-relaxed max-w-xs">
              {lang === 'hi'
                ? 'मरीज़ की जानकारी, लक्षण और प्राथमिक जांच में आपका डिजिटल साथी।'
                : 'Your digital assistant for patient intake, symptom collection, and triage.'}
            </p>
          </div>

          {!shouldConnect ? (
            /* Ready / Disconnected State */
            <div className="w-full flex flex-col items-center gap-3 mt-2">
              <button
                onClick={handleStartCall}
                className="w-full bg-sky-700 hover:bg-sky-800 text-white font-medium py-3 px-6 rounded-xl shadow-sm transition-all flex items-center justify-center gap-2 text-sm active:scale-95"
              >
                <span>🎙️</span>
                <span>{lang === 'hi' ? 'बातचीत शुरू करें' : 'Start Talking'}</span>
              </button>

              <div className="flex items-center gap-1.5 text-xs text-emerald-600 font-medium mt-1">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{lang === 'hi' ? 'वॉयस असिस्टेंट ऑनलाइन है' : 'Voice Assistant Online'}</span>
              </div>

              {micError && (
                <div className="w-full bg-red-50 border border-red-200 text-red-600 text-xs p-3 rounded-xl mt-2 text-left">
                  {micError}
                </div>
              )}
            </div>
          ) : (
            /* Connected State */
            <LiveKitRoom
              serverUrl={url}
              token={token}
              connect={shouldConnect}
              onDisconnected={handleDisconnect}
              audio={true}
              video={false}
              className="w-full"
            >
              <ActiveAssistantUI onDisconnect={handleDisconnect} lang={lang} />
              <RoomAudioRenderer />
              <StartAudio label="Audio enabled" />
            </LiveKitRoom>
          )}
        </div>
      </div>

      {/* 3. Bottom Shortcut Buttons */}
      <div className="w-full max-w-xl mx-auto flex items-center justify-center gap-3 pb-2 text-xs">
        <button className="bg-white border border-slate-200/90 hover:border-sky-300 text-slate-700 px-4 py-2 rounded-xl shadow-2xs transition-all flex items-center gap-2">
          <span>📋</span>
          <span>{lang === 'hi' ? 'मरीज़ रजिस्ट्रेशन' : 'Patient Intake'}</span>
        </button>

        <button className="bg-white border border-slate-200/90 hover:border-sky-300 text-slate-700 px-4 py-2 rounded-xl shadow-2xs transition-all flex items-center gap-2">
          <span>🩺</span>
          <span>{lang === 'hi' ? 'लक्षण जांच' : 'Symptom Check'}</span>
        </button>

        <button className="bg-white border border-slate-200/90 hover:border-sky-300 text-slate-700 px-4 py-2 rounded-xl shadow-2xs transition-all flex items-center gap-2">
          <span>📅</span>
          <span>{lang === 'hi' ? 'फॉलो-अप शेड्यूल' : 'Follow-up Plan'}</span>
        </button>
      </div>
    </main>
  );
}

/* Active State Badge Component */
function ActiveAssistantUI({ onDisconnect, lang }: { onDisconnect: () => void; lang: 'en' | 'hi' }) {
  const { state } = useVoiceAssistant();

  const getStatusText = () => {
    switch (state) {
      case 'connecting':
        return lang === 'hi' ? 'कनेक्ट हो रहा है...' : 'Connecting...';
      case 'listening':
        return lang === 'hi' ? 'आपकी बात सुन रहे हैं...' : 'Listening to you...';
      case 'speaking':
        return lang === 'hi' ? 'एजेंट जवाब दे रहा है...' : 'AshaAssist is speaking...';
      default:
        return lang === 'hi' ? 'कनेक्टेड' : 'Connected';
    }
  };

  return (
    <div className="w-full flex flex-col items-center gap-4 mt-2">
      <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sky-50 border border-sky-200 text-sky-800 text-xs font-semibold animate-pulse">
        <span className="w-2 h-2 rounded-full bg-sky-600" />
        <span>{getStatusText()}</span>
      </div>

      <div className="w-20 h-20 rounded-full bg-sky-50 border border-sky-200 flex items-center justify-center text-2xl relative my-1">
        {state === 'speaking' && (
          <div className="absolute inset-0 rounded-full bg-sky-400/20 animate-ping" />
        )}
        <span>{state === 'speaking' ? '🗣️' : state === 'listening' ? '🎙️' : '⏳'}</span>
      </div>

      <button
        onClick={onDisconnect}
        className="w-full bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 font-medium py-2.5 px-4 rounded-xl text-xs transition-all"
      >
        {lang === 'hi' ? 'कॉल समाप्त करें' : 'End Call'}
      </button>
    </div>
  );
}