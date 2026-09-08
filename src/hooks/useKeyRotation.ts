import { useState, useCallback } from 'react';

export const useKeyRotation = () => {
  const [isRotating, setIsRotating] = useState(false);
  const [activeKeyId, setActiveKeyId] = useState<string | null>('kid_jwt_v2');

  const rotateKeys = useCallback(async (keyType: string = 'JWT_RS256') => {
    setIsRotating(true);
    try {
      const newKeyId = `kid_${keyType.toLowerCase()}_v${Date.now()}`;
      setActiveKeyId(newKeyId);
      return { success: true, keyId: newKeyId };
    } finally {
      setIsRotating(false);
    }
  }, []);

  return { activeKeyId, isRotating, rotateKeys };
};
