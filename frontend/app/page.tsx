"use client";

import { useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useVoiceAssistant,
  useLocalParticipant,
} from "@livekit/components-react";

const translations = {
  en: {
    title: "AshaAssist Voice",
    subtitle: "AI Assistant for ASHA Health Workers",
    connectBtn: "Start Talking",
    statusDisconnected: "Tap below to begin voice intake session",
    speakingAgent: "Agent Speaking...",
    speakingUser: "Your turn — Speak now",
    idleState: "Listening...",
  },
  hi: {
    title: "आशाअसिस्ट वॉयस",
    subtitle: "आशा कार्यकर्ताओं के लिए AI वॉयस सहायक",
    connectBtn: "बातचीत शुरू करें",
    statusDisconnected: "वॉयस सेशन शुरू करने के लिए नीचे टैप करें",
    speakingAgent: "एजेंट बोल रहा है...",
    speakingUser: "आपकी बारी — अब बोलें",
    idleState: "सुन रहा है...",
  },
};

export default function Home() {
  const [lang, setLang] = useState<"en" | "hi">("en");
  const [token, setToken] = useState<string>("");
  const [url, setUrl] = useState<string>("");
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const t = translations[lang];

  const handleConnect = async () => {
    try {
      const response = await fetch(`/api/token?room=asha-room&username=asha-worker`);
      if (!response.ok) {
        console.error("Failed to fetch token.");
        return;
      }

      const data = await response.json();
      if (data.token) {
        setToken(data.token);
        setUrl(data.url || process.env.NEXT_PUBLIC_LIVEKIT_URL || "");
        setIsConnected(true);
      }
    } catch (error) {
      console.error("Failed to connect:", error);
    }
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    setToken("");
  };

  return (
    <main style={styles.container}>
      <div style={styles.card}>
        {/* Header */}
        <header style={styles.header}>
          <div>
            <h1 style={styles.title}>{t.title}</h1>
            <p style={styles.subtitle}>{t.subtitle}</p>
          </div>

          <div style={styles.langToggle}>
            <button
              style={{
                ...styles.langBtn,
                ...(lang === "en" ? styles.langBtnActive : {}),
              }}
              onClick={() => setLang("en")}
            >
              English
            </button>
            <button
              style={{
                ...styles.langBtn,
                ...(lang === "hi" ? styles.langBtnActive : {}),
              }}
              onClick={() => setLang("hi")}
            >
              हिंदी
            </button>
          </div>
        </header>

        {/* Stage */}
        <div style={styles.stage}>
          {!isConnected ? (
            <div style={styles.idleBox}>
              <p style={styles.idleText}>{t.statusDisconnected}</p>
              <button onClick={handleConnect} style={styles.startBtn}>
                <span style={{ fontSize: "20px" }}>🎙️</span> {t.connectBtn}
              </button>
            </div>
          ) : (
            <LiveKitRoom
              serverUrl={url}
              token={token}
              connect={true}
              onDisconnected={handleDisconnect}
              data-lk-theme="default"
              style={styles.activeRoom}
            >
              {/* Minimalist Speaking Indicator */}
              <ActiveVoiceStage lang={lang} />

              {/* Microphone Mute Toggle & Disconnect */}
              <VoiceAssistantControlBar controls={{ leave: true, microphone: true }} />
              
              <RoomAudioRenderer />
            </LiveKitRoom>
          )}
        </div>
      </div>
    </main>
  );
}

function ActiveVoiceStage({ lang }: { lang: "en" | "hi" }) {
  const t = translations[lang];
  const { state: agentState } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();

  const isAgentSpeaking = agentState === "speaking";
  const isUserSpeaking = localParticipant.isSpeaking;

  let badgeText = t.idleState;
  let badgeStyle = styles.badgeIdle;

  if (isAgentSpeaking) {
    badgeText = t.speakingAgent;
    badgeStyle = styles.badgeAgentSpeaking;
  } else if (isUserSpeaking) {
    badgeText = t.speakingUser;
    badgeStyle = styles.badgeUserSpeaking;
  }

  return (
    <div style={styles.stageInner}>
      <div style={{ ...styles.activeBadge, ...badgeStyle }}>
        <span style={styles.pulseDot}></span>
        {badgeText}
      </div>
    </div>
  );
}

// Styling
const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: "100vh",
    backgroundColor: "#0B0F17",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    padding: "20px",
  },
  card: {
    width: "100%",
    maxWidth: "520px",
    backgroundColor: "#131924",
    border: "1px solid #1F293D",
    borderRadius: "24px",
    padding: "32px",
    boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.5)",
    display: "flex",
    flexDirection: "column",
    gap: "24px",
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "16px",
  },
  title: {
    margin: 0,
    fontSize: "24px",
    fontWeight: 700,
    color: "#F8FAFC",
  },
  subtitle: {
    margin: "4px 0 0 0",
    fontSize: "14px",
    color: "#94A3B8",
  },
  langToggle: {
    display: "flex",
    backgroundColor: "#0F172A",
    borderRadius: "12px",
    padding: "4px",
    border: "1px solid #1E293B",
  },
  langBtn: {
    padding: "8px 16px",
    border: "none",
    borderRadius: "8px",
    backgroundColor: "transparent",
    color: "#64748B",
    fontWeight: 600,
    fontSize: "14px",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  langBtnActive: {
    backgroundColor: "#6366F1",
    color: "#FFFFFF",
    boxShadow: "0 2px 10px rgba(99, 102, 241, 0.4)",
  },
  stage: {
    minHeight: "220px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#090D16",
    borderRadius: "16px",
    border: "1px solid #1A2333",
    padding: "24px",
  },
  stageInner: {
    width: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "20px 0",
  },
  idleBox: {
    textAlign: "center",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "20px",
  },
  idleText: {
    margin: 0,
    color: "#64748B",
    fontSize: "14px",
  },
  startBtn: {
    backgroundColor: "#6366F1",
    backgroundImage: "linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)",
    color: "#FFFFFF",
    border: "none",
    padding: "16px 36px",
    borderRadius: "14px",
    fontSize: "18px",
    fontWeight: 600,
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "10px",
    boxShadow: "0 8px 20px rgba(99, 102, 241, 0.35)",
  },
  activeRoom: {
    width: "100%",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    gap: "32px",
  },
  activeBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "10px",
    fontSize: "16px",
    fontWeight: 600,
    padding: "10px 24px",
    borderRadius: "30px",
    transition: "all 0.3s ease",
  },
  badgeIdle: {
    color: "#94A3B8",
    backgroundColor: "rgba(148, 163, 184, 0.1)",
    border: "1px solid rgba(148, 163, 184, 0.2)",
  },
  badgeUserSpeaking: {
    color: "#22C55E",
    backgroundColor: "rgba(34, 197, 94, 0.15)",
    border: "1px solid rgba(34, 197, 94, 0.3)",
  },
  badgeAgentSpeaking: {
    color: "#38BDF8",
    backgroundColor: "rgba(56, 189, 248, 0.15)",
    border: "1px solid rgba(56, 189, 248, 0.3)",
  },
  pulseDot: {
    width: "10px",
    height: "10px",
    backgroundColor: "currentColor",
    borderRadius: "50%",
  },
};