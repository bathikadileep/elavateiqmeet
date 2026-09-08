import { useState, useCallback } from 'react';

export const useLiveTranslation = (targetLanguage: string = 'es') => {
  const [translatedSubtitles, setTranslatedSubtitles] = useState<Array<{ id: string; speaker: string; text: string }>>([]);

  const translateChunk = useCallback(async (speaker: string, originalText: string) => {
    const translated = `[${targetLanguage.toUpperCase()}] ${originalText}`;
    const newEntry = { id: Math.random().toString(), speaker, text: translated };
    setTranslatedSubtitles(prev => [...prev.slice(-20), newEntry]);
  }, [targetLanguage]);

  return { translatedSubtitles, translateChunk };
};
