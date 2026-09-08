import { useState, useEffect, useRef, useCallback } from 'react';
import type { Socket } from 'socket.io-client';
import client from '../api/client';
import type { SpeechTranscriptItem } from '../types/ai';

export interface UseSpeechToTextOptions {
  socket: Socket | null;
  roomCode: string;
  speakerName: string;
}

export const useSpeechToText = ({ socket, roomCode, speakerName }: UseSpeechToTextOptions) => {
  const [isListening, setIsListening] = useState(false);
  const [captions, setCaptions] = useState<SpeechTranscriptItem[]>([]);
  const [activeSubtitle, setActiveSubtitle] = useState<SpeechTranscriptItem | null>(null);

  const recognitionRef = useRef<any>(null);
  const debounceTimerRef = useRef<any>(null);
  const lastLoggedTextRef = useRef<string>('');

  useEffect(() => {
    // Listen for remote subtitles via Socket.IO
    if (!socket) return;

    const handleRemoteSpeech = (data: { sender_sid: string; speaker_name: string; text: string; is_final: boolean }) => {
      const trimmedText = (data.text || '').trim();
      if (!trimmedText) return;

      const item: SpeechTranscriptItem = {
        id: Math.random().toString(36).substring(2, 9),
        speaker_name: data.speaker_name || 'Speaker',
        text: trimmedText,
        is_final: data.is_final,
        timestamp: new Date().toISOString(),
      };

      setActiveSubtitle(item);
      if (data.is_final) {
        setCaptions((prev) => [...prev.slice(-10), item]);
      }
    };

    socket.on('speech_transcript_event', handleRemoteSpeech);
    return () => {
      socket.off('speech_transcript_event', handleRemoteSpeech);
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [socket]);

  const startListening = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn('WebSpeech API is not supported in this browser.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += transcript;
          } else {
            interim += transcript;
          }
        }

        const text = (final || interim).trim();
        // Guard 1: Reject empty or whitespace-only inputs
        if (!text) return;

        const item: SpeechTranscriptItem = {
          id: Math.random().toString(36).substring(2, 9),
          speaker_name: speakerName,
          text,
          is_final: !!final,
          timestamp: new Date().toISOString(),
        };

        setActiveSubtitle(item);

        if (socket) {
          socket.emit('speech_transcript_event', {
            room_code: roomCode,
            speaker_name: speakerName,
            text,
            is_final: !!final,
          });
        }

        const cleanedFinal = final.trim();
        if (cleanedFinal) {
          // Guard 2: Consecutive deduplication check
          if (cleanedFinal === lastLoggedTextRef.current) {
            return;
          }

          setCaptions((prev) => [...prev.slice(-10), item]);
          lastLoggedTextRef.current = cleanedFinal;

          // Guard 3: Debounce REST API logging to prevent 50K+ request flooding
          if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
          }

          debounceTimerRef.current = setTimeout(() => {
            client.post('/api/summaries/transcript', {
              meeting_code: roomCode,
              speaker_name: speakerName,
              transcript_text: cleanedFinal,
            }).catch((err) => console.warn('Failed logging transcript line:', err));
          }, 600);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition error:', event.error);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
      recognitionRef.current = recognition;
      setIsListening(true);
    } catch (err) {
      console.warn('Failed starting speech recognition:', err);
    }
  }, [socket, roomCode, speakerName]);

  const stopListening = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, []);

  return {
    isListening,
    captions,
    activeSubtitle,
    startListening,
    stopListening,
  };
};

