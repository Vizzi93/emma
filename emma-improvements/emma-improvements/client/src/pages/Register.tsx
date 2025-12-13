import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, UserPlus, AlertCircle, Check } from 'lucide-react';

import { useAuthStore } from '@/stores/authStore';

const registerSchema = z
  .object({
    fullName: z.string().min(2, 'Name muss mindestens 2 Zeichen haben').optional(),
    email: z.string().email('Ungültige E-Mail-Adresse'),
    password: z
      .string()
      .min(8, 'Passwort muss mindestens 8 Zeichen haben')
      .regex(/[A-Z]/, 'Mindestens ein Großbuchstabe erforderlich')
      .regex(/[a-z]/, 'Mindestens ein Kleinbuchstabe erforderlich')
      .regex(/[0-9]/, 'Mindestens eine Zahl erforderlich'),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwörter stimmen nicht überein',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerSchema>;

const passwordRequirements = [
  { regex: /.{8,}/, label: 'Mindestens 8 Zeichen' },
  { regex: /[A-Z]/, label: 'Ein Großbuchstabe' },
  { regex: /[a-z]/, label: 'Ein Kleinbuchstabe' },
  { regex: /[0-9]/, label: 'Eine Zahl' },
];

export function Register() {
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const navigate = useNavigate();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    mode: 'onChange',
  });

  const password = watch('password', '');

  const onSubmit = async (data: RegisterFormData) => {
    try {
      await registerUser(data.email, data.password, data.fullName);
      navigate('/dashboard', { replace: true });
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4 py-8">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emma-400 to-emma-600 mb-4">
            <span className="text-white font-bold text-2xl">eM</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Konto erstellen</h1>
          <p className="text-gray-400 mt-2">Registriere dich bei eMMA</p>
        </div>

        {/* Form Card */}
        <div className="card p-8">
          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-4 rounded-lg bg-red-900/30 border border-red-700 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm text-red-300">{error}</p>
                <button
                  onClick={clearError}
                  className="text-xs text-red-400 hover:text-red-300 mt-1"
                >
                  Ausblenden
                </button>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Full Name */}
            <div>
              <label htmlFor="fullName" className="block text-sm font-medium text-gray-300 mb-2">
                Name (optional)
              </label>
              <input
                id="fullName"
                type="text"
                autoComplete="name"
                {...register('fullName')}
                className={`input ${errors.fullName ? 'input-error' : ''}`}
                placeholder="Max Mustermann"
              />
              {errors.fullName && (
                <p className="mt-1 text-sm text-red-400">{errors.fullName.message}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                E-Mail-Adresse
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                {...register('email')}
                className={`input ${errors.email ? 'input-error' : ''}`}
                placeholder="name@example.com"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
                Passwort
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  {...register('password')}
                  className={`input pr-10 ${errors.password ? 'input-error' : ''}`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>

              {/* Password Requirements */}
              <div className="mt-3 space-y-1">
                {passwordRequirements.map((req, index) => {
                  const isValid = req.regex.test(password);
                  return (
                    <div
                      key={index}
                      className={`flex items-center gap-2 text-xs ${
                        isValid ? 'text-green-400' : 'text-gray-500'
                      }`}
                    >
                      <Check size={14} className={isValid ? 'opacity-100' : 'opacity-30'} />
                      <span>{req.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Confirm Password */}
            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-300 mb-2"
              >
                Passwort bestätigen
              </label>
              <div className="relative">
                <input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  {...register('confirmPassword')}
                  className={`input pr-10 ${errors.confirmPassword ? 'input-error' : ''}`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                >
                  {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.confirmPassword && (
                <p className="mt-1 text-sm text-red-400">{errors.confirmPassword.message}</p>
              )}
            </div>

            {/* Terms */}
            <p className="text-xs text-gray-500">
              Mit der Registrierung akzeptierst du unsere{' '}
              <a href="#" className="text-emma-400 hover:text-emma-300">
                Nutzungsbedingungen
              </a>{' '}
              und{' '}
              <a href="#" className="text-emma-400 hover:text-emma-300">
                Datenschutzrichtlinie
              </a>
              .
            </p>

            {/* Submit */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Registrieren...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <UserPlus size={18} />
                  Konto erstellen
                </span>
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="mt-6 text-center text-sm text-gray-400">
            Bereits ein Konto?{' '}
            <Link to="/login" className="text-emma-400 hover:text-emma-300 font-medium">
              Jetzt anmelden
            </Link>
          </p>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-gray-500">
          © 2024 DojaFlow AI. Alle Rechte vorbehalten.
        </p>
      </div>
    </div>
  );
}
