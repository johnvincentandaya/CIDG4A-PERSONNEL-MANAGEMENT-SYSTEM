import React, { useState, useMemo, useContext } from 'react';
import { api } from '../api';
import { AuthContext } from '../contexts/AuthContext';

const strengthLabels = [
  'Very Weak',
  'Weak',
  'Fair',
  'Good',
  'Strong',
  'Very Strong',
];

function calculatePasswordStrength(password) {
  let score = 0;
  if (password.length >= 8) score += 1;
  if (password.length >= 12) score += 1;
  if (/[A-Z]/.test(password)) score += 1;
  if (/[a-z]/.test(password)) score += 1;
  if (/\d/.test(password)) score += 1;
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
  return Math.min(score, 5);
}

function formatRequirement(label, isValid) {
  return (
    <div className={`requirement-row ${isValid ? 'valid' : 'invalid'}`}>
      <span className="requirement-icon">{isValid ? '✓' : '•'}</span>
      <span>{label}</span>
    </div>
  );
}

export default function ChangePassword() {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [statusType, setStatusType] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { authReady } = useContext(AuthContext);

  const strengthScore = useMemo(() => calculatePasswordStrength(newPassword), [newPassword]);
  const strengthLabel = strengthLabels[strengthScore] || 'Very Weak';

  const requirements = useMemo(() => ({
    length: newPassword.length >= 8,
    uppercase: /[A-Z]/.test(newPassword),
    lowercase: /[a-z]/.test(newPassword),
    number: /\d/.test(newPassword),
    special: /[!@#$%^&*(),.?":{}|<>]/.test(newPassword),
  }), [newPassword]);

  async function handleSubmit(event) {
    event.preventDefault();
    setStatusMessage('');
    setStatusType('');

    if (!newPassword || !confirmPassword || !currentPassword) {
      setStatusMessage('Please complete every password field.');
      setStatusType('error');
      return;
    }

    if (newPassword !== confirmPassword) {
      setStatusMessage('New password and confirmation do not match.');
      setStatusType('error');
      return;
    }

    if (strengthScore < 4) {
      setStatusMessage('Password strength is too weak. Please follow the secure password requirements.');
      setStatusType('error');
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await api.post('/api/auth/change-password', {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_new_password: confirmPassword,
      });
      if (response?.data?.ok) {
        setStatusMessage('Password changed successfully.');
        setStatusType('success');
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
      } else {
        setStatusMessage('Password update failed. Please try again.');
        setStatusType('error');
      }
    } catch (error) {
      const detail = error?.response?.data?.detail;
      setStatusMessage(detail || 'Unable to change password.');
      setStatusType('error');
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!authReady) {
    return null;
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title-block">
          <div className="page-eyebrow">Account Security</div>
          <h1 className="page-title">Change Password</h1>
          <p className="page-subtitle">
            Update your CIDG RFU4A password securely. Current password verification is required.
          </p>
        </div>
      </div>

      <div className="card-section p-4" style={{ maxWidth: 640 }}>
        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label">Current Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              className="form-control"
              value={currentPassword}
              onChange={e => setCurrentPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label">New Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              className="form-control"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>

          <div className="mb-3">
            <label className="form-label">Confirm New Password</label>
            <input
              type={showPassword ? 'text' : 'password'}
              className="form-control"
              value={confirmPassword}
              onChange={e => setConfirmPassword(e.target.value)}
              autoComplete="new-password"
              required
            />
          </div>

          <div className="form-text mb-3 d-flex align-items-center gap-2">
            <button
              type="button"
              className="btn btn-sm btn-outline-secondary"
              onClick={() => setShowPassword(prev => !prev)}
            >
              {showPassword ? 'Hide passwords' : 'Show passwords'}
            </button>
            <span className="text-muted">Keep your password secure and unique.</span>
          </div>

          <div className="password-strength-panel mb-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <div>
                <strong>Password Strength</strong>
                <div className="small text-muted">Use a long, mixed-case password with numbers and symbols.</div>
              </div>
              <div className={`strength-badge strength-${strengthScore}`}>
                {strengthLabel}
              </div>
            </div>
            <div className="strength-meter">
              {[0, 1, 2, 3, 4].map((value) => (
                <div key={value} className={`strength-step ${strengthScore > value ? 'active' : ''}`} />
              ))}
            </div>
          </div>

          <div className="password-requirements mb-4">
            {formatRequirement('At least 8 characters', requirements.length)}
            {formatRequirement('Uppercase and lowercase letters', requirements.uppercase && requirements.lowercase)}
            {formatRequirement('At least one number', requirements.number)}
            {formatRequirement('At least one special character', requirements.special)}
          </div>

          {statusMessage && (
            <div className={`alert ${statusType === 'success' ? 'alert-success' : 'alert-danger'}`} role="alert">
              {statusMessage}
            </div>
          )}

          <div className="d-grid gap-2">
            <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Updating password…' : 'Change Password'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
