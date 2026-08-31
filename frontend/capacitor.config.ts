import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.elevateiq.meet',
  appName: 'ElevateIQ Meet',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
};

export default config;
