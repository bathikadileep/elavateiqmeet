import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import GlassCard from '../components/common/GlassCard';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import BrandLogo from '../components/common/BrandLogo';
import { KeyRound, ArrowLeft, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';
import type { ForgotPasswordResponseData } from '../api/auth';

export const ForgotPassword: React.FC = () => {
  const { forgotPassword, error, clearError } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [result, setResult] = useState<ForgotPasswordResponseData | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!email.trim()) {
      setLocalError('Please enter your email address.');
      return;
    }

    setLoading(true);
    try {
      const res = await forgotPassword({ email: email.trim() });
      setResult(res);
    } catch {
      // Handled via AuthContext error
    } finally {
      setLoading(false);
    }
  };

  const displayError = localError || error;

  return (
    <GlassCard variant="glow" className="w-full max-w-md p-8">
      {/* Header */}
      <div className="flex flex-col items-center text-center mb-6">
        <BrandLogo size="xl" className="mb-3" />
        <h2 className="text-2xl font-extrabold text-white">Forgot Password</h2>
        <p className="text-xs text-gray-400 mt-1">
          Enter your email to receive password reset instructions
        </p>
      </div>

      {/* Success Notification */}
      {result && (
        <div className="mb-6 space-y-3">
          <div className="p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-start gap-3 text-emerald-300 text-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">{result.message}</p>
              {result.reset_token && (
                <p className="mt-1 text-[11px] text-gray-300">
                  Password reset link has been generated.
                </p>
              )}
            </div>
          </div>

          {/* Dev Mode Shortcut Button */}
          {result.reset_token && (
            <Button
              type="button"
              variant="secondary"
              fullWidth
              size="sm"
              onClick={() => navigate(`/reset-password?token=${result.reset_token}`)}
              rightIcon={<ExternalLink className="w-3.5 h-3.5" />}
            >
              Proceed to Reset Page (Dev Test)
            </Button>
          )}
        </div>
      )}

      {/* Error Alert */}
      {displayError && !result && (
        <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      {/* Form */}
      {!result && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Email Address"
            type="email"
            placeholder="registered@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            required
          />

          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={loading}
            rightIcon={<KeyRound className="w-4 h-4" />}
            className="mt-2"
          >
            Send Reset Link
          </Button>
        </form>
      )}

      {/* Back to Login */}
      <div className="mt-6 text-center">
        <Link
          to="/login"
          className="inline-flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Sign In
        </Link>
      </div>
    </GlassCard>
  );
};

export default ForgotPassword;
