import { useState, useCallback } from 'react';

export interface DLPScanResult {
  isBlocked: boolean;
  redactedText: string;
  offenses: Array<{ policyName: string; snippet: string }>;
}

export const useDLPScanner = () => {
  const [isScanning, setIsScanning] = useState(false);

  const scanText = useCallback(async (text: string, context: string = 'chat'): Promise<DLPScanResult> => {
    setIsScanning(true);
    try {
      // Local client pattern evaluation for instant feedback
      const ssnPattern = /\b\d{3}-\d{2}-\d{4}\b/g;
      const ccPattern = /\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14})\b/g;

      let blocked = false;
      let redacted = text;
      const offenses: Array<{ policyName: string; snippet: string }> = [];

      if (ssnPattern.test(text)) {
        blocked = true;
        offenses.push({ policyName: 'SSN', snippet: '***-**-****' });
        redacted = redacted.replace(ssnPattern, '[REDACTED_SSN]');
      }

      if (ccPattern.test(text)) {
        blocked = true;
        offenses.push({ policyName: 'CREDIT_CARD', snippet: '****-****-****-****' });
        redacted = redacted.replace(ccPattern, '[REDACTED_CC]');
      }

      return { isBlocked: blocked, redactedText: redacted, offenses };
    } finally {
      setIsScanning(false);
    }
  }, []);

  return { scanText, isScanning };
};
