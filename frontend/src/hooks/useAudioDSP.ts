import { useState, useCallback } from 'react';

export const useAudioDSP = () => {
  const [dspEnabled, setDspEnabled] = useState(false);

  const processAudioStream = useCallback((inputStream: MediaStream): MediaStream => {
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return inputStream;

      const audioTrack = inputStream.getAudioTracks()[0];
      if (!audioTrack) return inputStream;

      const ctx = new AudioContextClass();
      const source = ctx.createMediaStreamSource(inputStream);

      // High-pass filter to eliminate low frequency rumble (< 80Hz)
      const highPassFilter = ctx.createBiquadFilter();
      highPassFilter.type = 'highpass';
      highPassFilter.frequency.value = 80;

      // Peak equalizer to clean voice clarity (2.5kHz boost)
      const eqFilter = ctx.createBiquadFilter();
      eqFilter.type = 'peaking';
      eqFilter.frequency.value = 2500;
      eqFilter.Q.value = 1.0;
      eqFilter.gain.value = 3.0;

      // Dynamics Compressor for acoustic noise compression
      const compressor = ctx.createDynamicsCompressor();
      compressor.threshold.value = -24;
      compressor.knee.value = 12;
      compressor.ratio.value = 4;
      compressor.attack.value = 0.003;
      compressor.release.value = 0.25;

      const destination = ctx.createMediaStreamDestination();

      source.connect(highPassFilter);
      highPassFilter.connect(eqFilter);
      eqFilter.connect(compressor);
      compressor.connect(destination);

      setDspEnabled(true);

      const processedTrack = destination.stream.getAudioTracks()[0];
      const outputStream = new MediaStream([processedTrack]);

      // Copy video tracks if present
      inputStream.getVideoTracks().forEach((vt) => outputStream.addTrack(vt));

      return outputStream;
    } catch (err) {
      console.warn('WebAudio DSP error:', err);
      return inputStream;
    }
  }, []);

  return {
    dspEnabled,
    processAudioStream,
  };
};
