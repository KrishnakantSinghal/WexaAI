"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useAuthStore } from "@/store/authStore";
import type { TokenResponse, User } from "@/types";

export function useAuth() {
  const router = useRouter();
  const { isAuthenticated, user, setAccessToken, setUser, clearAuth } = useAuthStore();

  const meQuery = useQuery({
    queryKey: ["me"],
    queryFn: async (): Promise<User> => {
      const res = await api.get("/users/me");
      return res.data;
    },
    enabled: isAuthenticated,
    staleTime: 5 * 60 * 1000,
  });

  const signInMutation = useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      const res = await api.post<TokenResponse>("/auth/signin", data);
      return res.data;
    },
    onSuccess: async (data) => {
      setAccessToken(data.access_token);
      const userRes = await api.get<User>("/users/me");
      setUser(userRes.data);
      router.push("/overview");
    },
  });

  const signUpMutation = useMutation({
    mutationFn: async (data: {
      email: string;
      password: string;
      full_name: string;
      organization_name: string;
    }) => {
      const res = await api.post<TokenResponse>("/auth/signup", data);
      return res.data;
    },
    onSuccess: async (data) => {
      setAccessToken(data.access_token);
      const userRes = await api.get<User>("/users/me");
      setUser(userRes.data);
      router.push("/overview");
    },
  });

  const signOutMutation = useMutation({
    mutationFn: () => api.post("/auth/signout"),
    onSettled: () => {
      clearAuth();
      queryClient.clear();
      router.push("/login");
    },
  });

  return {
    isAuthenticated,
    user: meQuery.data ?? user,
    isLoadingUser: meQuery.isLoading,
    signIn: signInMutation.mutate,
    signUp: signUpMutation.mutate,
    signOut: signOutMutation.mutate,
    signInError: signInMutation.error,
    signUpError: signUpMutation.error,
    isSigningIn: signInMutation.isPending,
    isSigningUp: signUpMutation.isPending,
  };
}
