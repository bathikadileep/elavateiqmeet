import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import GlassCard from '../components/common/GlassCard';
import Input from '../components/common/Input';
import Button from '../components/common/Button';
import { ShieldCheck, CheckCircle2, AlertCircle, Eye, EyeOff } from 'lucide-react';

export const ChangePassword: React.FC = () => {
  const { changePassword, error, clearError } = useAuth();

  const [currentPassword, setCurrentPassword] = useState('');
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
    setSuccess(false);

    if (!currentPassword || !newPassword) {
      setLocalError('Please fill in all password fields.');
      return;
    }

    if (newPassword.length < 6) {
      setLocalError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setLocalError('New passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      await changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch {
      // Handled via AuthContext error state
    } finally {
      setLoading(false);
    }
  };

  const displayError = localError || error;

  return (
    <GlassCard variant="default" className="w-full max-w-lg p-6 md:p-8">
      <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
        <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
        </div>
        <div>
          <h3 className="text-lg font-bold text-white">Change Account Password</h3>
          <p className="text-xs text-gray-400">Update your security credentials</p>
        </div>
      </div>

      {/* Success Banner */}
      {success && (
        <div className="mb-6 p-3.5 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center gap-3 text-emerald-300 text-xs animate-in fade-in duration-200">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Password changed successfully! Your session remains active.</span>
        </div>
      )}

      {/* Error Alert */}
      {displayError && (
        <div className="mb-6 p-3.5 bg-rose-500/10 border border-rose-500/20 rounded-xl flex items-center gap-3 text-rose-300 text-xs animate-in fade-in duration-200">
          <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{displayError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Current Password"
          type={showPassword ? 'text' : 'password'}
          placeholder="••••••••"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          disabled={loading}
          required
        />

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

        <div className="pt-2">
          <Button
            type="submit"
            variant="primary"
            isLoading={loading}
            rightIcon={<ShieldCheck className="w-4 h-4" />}
          >
            Update Password
          </Button>
        </div>
      </form>
    </GlassCard>
  );
};

export default ChangePassword;
