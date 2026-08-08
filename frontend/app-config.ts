export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'AshaAssist Healthcare',
  pageTitle: 'AshaAssist | Voice AI Patient Intake',
  pageDescription: 'Hands-free voice intake assistant for ASHA field health workers',

  supportsChatInput: true,
  supportsVideoInput: false,
  supportsScreenShare: false,
  isPreConnectBufferEnabled: true,

  logo: '/lk-logo.svg',
  accent: '#0284c7',
  logoDark: '/lk-logo-dark.svg',
  accentDark: '#38bdf8',
  startButtonText: 'Start Patient Intake',

  // Audio visualizer setting for Day 3
  audioVisualizerType: 'wave',
  audioVisualizerWaveLineWidth: 3,

  // Connects to your Python agent
  agentName: process.env.AGENT_NAME ?? 'my-agent',

  sandboxId: undefined,
};