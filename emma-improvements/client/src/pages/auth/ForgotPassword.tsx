import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, Mail, Loader2, CheckCircle } from 'lucide-react';

import { api } from '@/lib/api';

const forgotPasswordSchema = z.object({
  email: z.string().email('Ungültige E-Mail-Adresse'),
});

type ForgotPasswordForm = z.infer<typeof forgotPasswordSchema>;

export function ForgotPassword() {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    getValues,
  } = useForm<ForgotPasswordForm>({
    resolver: zodResolver(forgotPasswordSchema),
  });

  const onSubmit = async (data: ForgotPasswordForm) => {
    setIsLoading(true);
    try {
      await api.post('/auth/password-reset/request', { email: data.email });
      setIsSubmitted(true);
    } catch (error: any) {
      // Always show success to prevent email enumeration
      setIsSubmitted(true);
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-900/30 text-green-400 mb-6">
            <CheckCircle size={32} />
          </div>
          <h1 className="text-2xl font-bold text-white mb-4">E-Mail gesendet</h1>
          <p className="text-gray-400 mb-8">
            Falls ein Konto mit <span className="text-white">{getValues('email')}</span> existiert,
            haben wir eine E-Mail mit Anweisungen zum Zurücksetzen des Passworts gesendet.
          </p>
          <Link to="/login" className="btn-primary">
            <ArrowLeft size={18} />
            Zurück zur Anmeldung
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emma-400 to-emma-600 mb-4">
            <Mail size={28} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-white">Passwort vergessen?</h1>
          <p className="text-gray-400 mt-2">
            Gib deine E-Mail-Adresse ein und wir senden dir einen Link zum Zurücksetzen.
          </p>
        </div>

        {/* Form Card */}
        <div className="card p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
                E-Mail
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                className={`input ${errors.email ? 'input-error' : ''}`}
                placeholder="name@example.com"
                {...register('email')}
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-3"
            >
              {isLoading ? (
                <>
                  <Loader2 size={18} className="animate-spin" />
                  Sende E-Mail...
                </>
              ) : (
                <>
                  <Mail size={18} />
                  Link senden
                </>
              )}
            </button>
          </form>

          {/* Back to Login */}
          <Link
            to="/login"
            className="flex items-center justify-center gap-2 mt-6 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft size={16} />
            Zurück zur Anmeldung
          </Link>
        </div>
      </div>
    </div>
  );
}
