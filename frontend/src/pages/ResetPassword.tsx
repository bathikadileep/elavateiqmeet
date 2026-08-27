import React, { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import GlassCard from '../components/common/GlassCard';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import BrandLogo from '../components/common/BrandLogo';
import { Lock, CheckCircle2, AlertCircle, Eye, EyeOff } from 'lucide-react';

export const ResetPassword: React.FC = () => {
  const { resetPassword, error, clearError } = useAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get('token') || '';

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    clearError();

    if (!token) {
      setLocalError('Missing password reset token. Please check your reset link.');
      return;
    }

    if (!newPassword) {
      setLocalError('Please enter a new password.');
      return;
    }

    if (newPassword.length < 6) {
      setLocalError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await resetPassword({ token, new_password: newPassword });
      setSuccess(true);
      setTimeout(() => {
        navigate('/login');
      }, 2500);
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
        <h2 className="text-2xl font-extrabold text-white">Reset Password</h2>
        <p className="text-xs text-gray-400 mt-1">Enter your new account password</p>
      </div>

      {/* Missing Token Alert */}
      {!token && (
        <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>No reset token provided in URL. Please request a new reset link.</span>
        </div>
      )}

      {/* Success Notification */}
      {success && (
        <div className="mb-6 p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-300 text-xs animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Password reset successfully! Redirecting to login...</span>
        </div>
      )}

      {/* Error Alert */}
      {displayError && !success && token && (
        <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      {/* Form */}
      {token && !success && (
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
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

          <Input
            label="Confirm New Password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            disabled={loading}
            required
          />

          <Button
            type="submit"
            variant="primary"
            fullWidth
            isLoading={loading}
            rightIcon={<Lock className="w-4 h-4" />}
            className="mt-2"
          >
            Reset Password
          </Button>
        </form>
      )}

      {/* Back to Login */}
      <div className="mt-6 text-center">
        <Link to="/login" className="text-xs text-cyan-400 hover:text-cyan-300 font-semibold hover:underline transition-colors">
          Back to Sign In
        </Link>
      </div>
    </GlassCard>
  );
};

export default ResetPassword;
