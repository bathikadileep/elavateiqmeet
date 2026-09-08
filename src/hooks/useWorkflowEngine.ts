import { useState, useCallback } from 'react';

export const useWorkflowEngine = () => {
  const [workflows, setWorkflows] = useState<any[]>([]);

  const triggerEvent = useCallback(async (eventName: string, data: any) => {
    console.log(`Triggered workflow event: ${eventName}`, data);
  }, []);

  return { workflows, triggerEvent };
};
