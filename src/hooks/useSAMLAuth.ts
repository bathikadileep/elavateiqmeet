import { useState, useCallback } from 'react';

export interface SAMLState {
  isAuthenticated: boolean;
  userEmail: string | null;
  ssoUrl: string | null;
  error: string | null;
}

export const useSAMLAuth = () => {
  const [state, setState] = useState<SAMLState>({
    isAuthenticated: false,
    userEmail: null,
    ssoUrl: null,
    error: null,
  });

  const initiateSSOLogin = useCallback(async (tenantDomain: string) => {
    try {
      const resp = await fetch(`/api/sso/saml/login?domain=${encodeURIComponent(tenantDomain)}`);
      const data = await resp.json();

      if (data.redirect_url) {
        setState(prev => ({ ...prev, ssoUrl: data.redirect_url }));
        window.location.href = data.redirect_url;
      }
    } catch (err: any) {
      setState(prev => ({ ...prev, error: err.message || 'SAML login failed' }));
    }
  }, []);

  return {
    ...state,
    initiateSSOLogin,
  };
};
