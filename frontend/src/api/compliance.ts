import client from './client';

export interface SOC2Report {
  report_title: string;
  generated_at: string;
  compliance_standards: string[];
  security_controls: Record<string, string>;
  environment_metrics: Record<string, number>;
}

export const getSOC2Report = async (): Promise<SOC2Report> => {
  const response = await client.get('/api/compliance/soc2-report');
  return response.data;
};

export const verifyAuditIntegrity = async (): Promise<any> => {
  const response = await client.get('/api/compliance/audit-integrity');
  return response.data;
};
