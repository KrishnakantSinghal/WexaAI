"use client";

import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";

const schema = z.object({
  email: z.string().email("Invalid email"),
  password: z
    .string()
    .min(8, "At least 8 characters")
    .regex(/[A-Z]/, "Must contain uppercase letter")
    .regex(/[0-9]/, "Must contain a digit"),
  full_name: z.string().min(1, "Name required"),
  organization_name: z.string().min(2, "Organization name required"),
});

type FormData = z.infer<typeof schema>;

export default function RegisterPage() {
  const { signUp, isSigningUp } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({ resolver: zodResolver(schema) });

  const onSubmit = (data: FormData) => {
    signUp(data, {
      onError: (err: unknown) => {
        const msg =
          (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
          "Registration failed";
        toast.error(msg);
      },
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-12 h-12 bg-primary rounded-xl mb-4">
              <span className="text-white font-bold text-xl">W</span>
            </div>
            <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
            <p className="text-gray-500 mt-1">Start with WexaAI Analytics</p>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {[
              {
                name: "full_name" as const,
                label: "Full name",
                type: "text",
                placeholder: "Jane Smith",
              },
              {
                name: "organization_name" as const,
                label: "Organization name",
                type: "text",
                placeholder: "Acme Corp",
              },
              {
                name: "email" as const,
                label: "Work email",
                type: "email",
                placeholder: "you@company.com",
              },
              {
                name: "password" as const,
                label: "Password",
                type: "password",
                placeholder: "••••••••",
              },
            ].map(({ name, label, type, placeholder }) => (
              <div key={name}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {label}
                </label>
                <input
                  {...register(name)}
                  type={type}
                  className={cn(
                    "w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50",
                    errors[name] ? "border-red-500" : "border-gray-300"
                  )}
                  placeholder={placeholder}
                />
                {errors[name] && (
                  <p className="text-red-500 text-xs mt-1">{errors[name]?.message}</p>
                )}
              </div>
            ))}

            <button
              type="submit"
              disabled={isSigningUp}
              className="w-full py-2.5 px-4 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-60 transition-colors"
            >
              {isSigningUp ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{" "}
            <Link href="/login" className="text-primary font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
