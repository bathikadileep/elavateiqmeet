import { useState, useCallback, useRef } from 'react';
import { E2EEManager } from '../utils/e2ee';

export const useE2EE = () => {
  const [isE2EEEnabled, setIsE2EEEnabled] = useState(false);
  const [e2eeKey, setE2eeKey] = useState<string>('ElevateIQ-Default-E2EE-Key');
  const managerRef = useRef(new E2EEManager());

  const enableE2EE = useCallback(async (passphrase: string) => {
    setE2eeKey(passphrase);
    await managerRef.current.setKey(passphrase);
    setIsE2EEEnabled(true);
  }, []);

  const disableE2EE = useCallback(() => {
    setIsE2EEEnabled(false);
  }, []);

  return {
    isE2EEEnabled,
    e2eeKey,
    enableE2EE,
    disableE2EE,
  };
};
