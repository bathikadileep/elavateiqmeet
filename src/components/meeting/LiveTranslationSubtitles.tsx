import React, { useState, useEffect, useCallback } from 'react';

interface Subtitle {
  id: string;
  speaker: string;
  text: string;
  startMs: number;
  endMs: number;
  language: string;
  translatedText?: string;
  confidence: number;
  isFinal: boolean;
}

interface LiveTranslationSubtitlesProps {
  subtitles: Subtitle[];
  targetLanguage?: string;
  showOriginal?: boolean;
  showSpeakerName?: boolean;
  maxVisible?: number;
  position?: 'bottom' | 'top';
  fontSize?: 'sm' | 'md' | 'lg';
  onLanguageChange?: (lang: string) => void;
  className?: string;
}

interface LanguageOption {
  code: string;
  label: string;
  flag: string;
}

const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
  { code: 'fr', label: 'Français', flag: '🇫🇷' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', label: '中文', flag: '🇨🇳' },
  { code: 'ja', label: '日本語', flag: '🇯🇵' },
  { code: 'ko', label: '한국어', flag: '🇰🇷' },
  { code: 'ar', label: 'العربية', flag: '🇸🇦' },
  { code: 'hi', label: 'हिन्दी', flag: '🇮🇳' },
  { code: 'pt', label: 'Português', flag: '🇧🇷' },
];

const FONT_SIZES: { [key: string]: string } = {
  sm: '13px',
  md: '15px',
  lg: '18px',
};

const SPEAKER_COLORS = [
  '#818cf8', '#34d399', '#fb923c', '#a78bfa',
  '#60a5fa', '#f472b6', '#facc15', '#2dd4bf',
];

function getSpeakerColor(speaker: string): string {
  let hash = 0;
  for (let i = 0; i < speaker.length; i++) {
    hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
  }
  return SPEAKER_COLORS[Math.abs(hash) % SPEAKER_COLORS.length];
}

const ConfidenceDot: React.FC<{ confidence: number }> = ({ confidence }) => {
  const color = confidence > 0.85 ? '#22c55e' : confidence > 0.65 ? '#f59e0b' : '#ef4444';
  return (
    <span
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: color,
        marginRight: 4,
        verticalAlign: 'middle',
      }}
      title={`Confidence: ${(confidence * 100).toFixed(0)}%`}
    />
  );
};

const SubtitleLine: React.FC<{
  subtitle: Subtitle;
  showOriginal: boolean;
  showSpeakerName: boolean;
  fontSize: string;
  targetLanguage: string;
}> = ({ subtitle, showOriginal, showSpeakerName, fontSize, targetLanguage }) => {
  const speakerColor = getSpeakerColor(subtitle.speaker);
  const displayText =
    subtitle.translatedText && targetLanguage !== subtitle.language
      ? subtitle.translatedText
      : subtitle.text;

  return (
    <div
      style={{
        padding: '6px 14px',
        marginBottom: 4,
        opacity: subtitle.isFinal ? 1 : 0.75,
        transition: 'opacity 0.2s',
        display: 'flex',
        flexDirection: 'column',
        gap: 2,
      }}
    >
      {showSpeakerName && (
        <div style={{ fontSize: 11, color: speakerColor, fontWeight: 600, letterSpacing: '0.02em' }}>
          {subtitle.speaker}
        </div>
      )}
      <div
        style={{
          fontSize,
          color: '#f8fafc',
          lineHeight: 1.5,
          fontStyle: subtitle.isFinal ? 'normal' : 'italic',
          display: 'flex',
          alignItems: 'flex-start',
          gap: 4,
        }}
      >
        <ConfidenceDot confidence={subtitle.confidence} />
        <span>{displayText}</span>
        {!subtitle.isFinal && (
          <span style={{ color: '#94a3b8', fontSize: 10, marginLeft: 4 }}>…</span>
        )}
      </div>
      {showOriginal && subtitle.translatedText && targetLanguage !== subtitle.language && (
        <div style={{ fontSize: 11, color: '#64748b', fontStyle: 'italic' }}>
          {subtitle.text}
        </div>
      )}
    </div>
  );
};

const LiveTranslationSubtitles: React.FC<LiveTranslationSubtitlesProps> = ({
  subtitles,
  targetLanguage = 'en',
  showOriginal = false,
  showSpeakerName = true,
  maxVisible = 3,
  position = 'bottom',
  fontSize = 'md',
  onLanguageChange,
  className = '',
}) => {
  const [selectedLang, setSelectedLang] = useState(targetLanguage);
  const [showSettings, setShowSettings] = useState(false);
  const [enabled, setEnabled] = useState(true);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const visibleSubtitles = subtitles.slice(-maxVisible);
  const fontSizeValue = FONT_SIZES[fontSize] || FONT_SIZES.md;

  const handleLanguageChange = useCallback((lang: string) => {
    setSelectedLang(lang);
    onLanguageChange?.(lang);
    setShowSettings(false);
  }, [onLanguageChange]);

  const selectedLangOption = LANGUAGES.find(l => l.code === selectedLang);

  return (
    <div
      className={`live-translation-subtitles ${className}`}
      style={{
        position: 'relative',
        width: '100%',
        pointerEvents: 'auto',
      }}
    >
      {/* Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '4px 8px',
          background: 'rgba(15, 23, 42, 0.7)',
          borderRadius: '8px 8px 0 0',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 11, color: '#94a3b8', fontWeight: 500 }}>
            🌐 Live Translation
          </span>
          {enabled && (
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 3,
              background: '#16a34a20',
              color: '#22c55e',
              fontSize: 10,
              padding: '2px 6px',
              borderRadius: 4,
              fontWeight: 600,
            }}>
              <span style={{ width: 5, height: 5, borderRadius: '50%', background: '#22c55e', display: 'inline-block' }} />
              LIVE
            </span>
          )}
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {/* Language picker */}
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowSettings(s => !s)}
              style={{
                background: 'rgba(99, 102, 241, 0.2)',
                border: '1px solid #4f46e5',
                color: '#818cf8',
                borderRadius: 6,
                padding: '3px 8px',
                fontSize: 11,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              {selectedLangOption?.flag} {selectedLangOption?.label} ▾
            </button>
            {showSettings && (
              <div
                style={{
                  position: 'absolute',
                  bottom: '100%',
                  right: 0,
                  background: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: 8,
                  padding: 4,
                  zIndex: 999,
                  minWidth: 150,
                  boxShadow: '0 4px 20px rgba(0,0,0,0.4)',
                }}
              >
                {LANGUAGES.map(lang => (
                  <div
                    key={lang.code}
                    onClick={() => handleLanguageChange(lang.code)}
                    style={{
                      padding: '6px 12px',
                      cursor: 'pointer',
                      borderRadius: 6,
                      fontSize: 12,
                      color: lang.code === selectedLang ? '#818cf8' : '#94a3b8',
                      background: lang.code === selectedLang ? 'rgba(99,102,241,0.15)' : 'transparent',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                    }}
                  >
                    {lang.flag} {lang.label}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Toggle enabled */}
          <button
            onClick={() => setEnabled(e => !e)}
            style={{
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              fontSize: 14,
              color: enabled ? '#22c55e' : '#475569',
            }}
            title={enabled ? 'Disable subtitles' : 'Enable subtitles'}
          >
            {enabled ? '👁' : '👁‍🗨'}
          </button>
        </div>
      </div>

      {/* Subtitles container */}
      {enabled && (
        <div
          ref={containerRef}
          style={{
            background: 'rgba(3, 7, 18, 0.85)',
            backdropFilter: 'blur(8px)',
            borderRadius: '0 0 8px 8px',
            minHeight: 80,
            maxHeight: 200,
            overflow: 'hidden',
            padding: '8px 0',
          }}
        >
          {visibleSubtitles.length === 0 ? (
            <div style={{
              padding: '16px',
              textAlign: 'center',
              color: '#475569',
              fontSize: 12,
              fontStyle: 'italic',
            }}>
              Waiting for speech…
            </div>
          ) : (
            visibleSubtitles.map(subtitle => (
              <SubtitleLine
                key={subtitle.id}
                subtitle={subtitle}
                showOriginal={showOriginal}
                showSpeakerName={showSpeakerName}
                fontSize={fontSizeValue}
                targetLanguage={selectedLang}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default LiveTranslationSubtitles;
