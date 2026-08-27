import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import GlassCard from '../components/common/GlassCard';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import BrandLogo from '../components/common/BrandLogo';
import { LogIn, AlertCircle, Eye, EyeOff } from 'lucide-react';

export const Login: React.FC = () => {
  const { login, error, clearError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const fromPath = (location.state as { from?: { pathname?: string } })?.from?.pathname || '/dashboard';

  const [identity, setIdentity] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!identity.trim() || !password) {
      setLocalError('Please enter both email/username and password.');
      return;
    }

    setLoading(true);
    try {
      await login({ identity: identity.trim(), password });
      navigate(fromPath, { replace: true });
    } catch {
      // Error is caught and set in AuthContext
    } finally {
      setLoading(false);
    }
  };

  const displayError = localError || error;

  return (
    <GlassCard variant="glow" className="w-full max-w-md p-8">
      {/* Header */}
      <div className="flex flex-col items-center text-center mb-8">
        <BrandLogo size="xl" className="mb-3" />
        <h2 className="text-2xl font-extrabold text-white">Welcome Back</h2>
        <p className="text-xs text-gray-400 mt-1">Sign in to access your ElevateIQ meeting dashboard</p>
      </div>

      {/* Error Alert */}
      {displayError && (
        <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email or Username"
          type="text"
          placeholder="username or email@example.com"
          value={identity}
          onChange={(e) => setIdentity(e.target.value)}
          disabled={loading}
          required
        />

        <Input
          label="Password"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={loading}
          required
          rightIcon={
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="hover:text-white transition-colors cursor-pointer"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          }
        />

        <div className="flex justify-end pt-1">
          <Link
            to="/forgot-password"
            className="text-xs text-indigo-400 hover:text-indigo-300 hover:underline transition-colors"
          >
            Forgot Password?
          </Link>
        </div>

        <Button
          type="submit"
          variant="primary"
          fullWidth
          isLoading={loading}
          rightIcon={<LogIn className="w-4 h-4" />}
          className="mt-2"
        >
          Sign In
        </Button>
      </form>

      {/* Footer Link */}
      <div className="mt-6 text-center text-xs text-gray-400">
        Don't have an account?{' '}
        <Link to="/register" className="text-cyan-400 hover:text-cyan-300 font-semibold hover:underline transition-colors">
          Create Account
        </Link>
      </div>
    </GlassCard>
  );
};

export default Login;
