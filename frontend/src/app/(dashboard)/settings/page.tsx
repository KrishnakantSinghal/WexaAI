"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Key, Plus, Trash2, Copy, Eye, EyeOff, Users, Building } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useAuth } from "@/hooks/useAuth";
import type { ApiKey, Member } from "@/types";
import { formatDate } from "@/lib/utils";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"api-keys" | "members" | "org">("api-keys");
  const [showKey, setShowKey] = useState<string | null>(null);
  const [newKeyName, setNewKeyName] = useState("");
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("viewer");
  const { user } = useAuth();

  const { data: apiKeys, isLoading: loadingKeys } = useQuery({
    queryKey: ["api-keys"],
    queryFn: async (): Promise<ApiKey[]> => {
      const res = await api.get("/organizations/current/api-keys");
      return res.data;
    },
  });

  const { data: members } = useQuery({
    queryKey: ["members"],
    queryFn: async (): Promise<Member[]> => {
      const res = await api.get("/organizations/current/members");
      return res.data;
    },
  });

  const { data: org } = useQuery({
    queryKey: ["org"],
    queryFn: async () => {
      const res = await api.get("/organizations/current");
      return res.data;
    },
  });

  const createKeyMutation = useMutation({
    mutationFn: (name: string) =>
      api.post<ApiKey & { full_key: string }>("/organizations/current/api-keys", {
        name,
        scopes: "ingest",
      }),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key created");
      setNewKeyName("");
      setShowKey(res.data.full_key);
    },
  });

  const revokeKeyMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/organizations/current/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
      toast.success("API key revoked");
    },
  });

  const inviteMutation = useMutation({
    mutationFn: ({ email, role }: { email: string; role: string }) =>
      api.post("/organizations/current/members/invite", { email, role }),
    onSuccess: () => {
      toast.success("Invitation sent");
      setInviteEmail("");
    },
  });

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your organization settings</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
        {[
          { id: "api-keys" as const, label: "API Keys", icon: Key },
          { id: "members" as const, label: "Members", icon: Users },
          { id: "org" as const, label: "Organization", icon: Building },
        ].map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === id
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* API Keys Tab */}
      {activeTab === "api-keys" && (
        <div className="max-w-2xl">
          {showKey && (
            <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm font-medium text-yellow-800 mb-2">
                Save this key — it won't be shown again!
              </p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm bg-white px-3 py-2 rounded border border-yellow-200">
                  {showKey}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(showKey);
                    toast.success("Copied!");
                  }}
                  className="p-2 text-yellow-700 hover:text-yellow-900"
                >
                  <Copy className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={() => setShowKey(null)}
                className="text-xs text-yellow-700 mt-2 hover:underline"
              >
                I've saved it, dismiss
              </button>
            </div>
          )}

          <div className="flex gap-2 mb-6">
            <input
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              placeholder="Key name (e.g. Production)"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
            />
            <button
              onClick={() => createKeyMutation.mutate(newKeyName)}
              disabled={!newKeyName || createKeyMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg disabled:opacity-60"
            >
              <Plus className="w-4 h-4" />
              Create
            </button>
          </div>

          <div className="space-y-3">
            {apiKeys?.map((key) => (
              <div
                key={key.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-4"
              >
                <div>
                  <p className="font-medium text-gray-900">{key.name}</p>
                  <p className="text-sm text-gray-500">
                    <code>{key.key_prefix}...</code> · {key.scopes}
                  </p>
                  {key.last_used_at && (
                    <p className="text-xs text-gray-400">
                      Last used: {formatDate(key.last_used_at)}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs ${
                      key.is_active
                        ? "bg-green-100 text-green-700"
                        : "bg-gray-100 text-gray-500"
                    }`}
                  >
                    {key.is_active ? "Active" : "Revoked"}
                  </span>
                  {key.is_active && (
                    <button
                      onClick={() => revokeKeyMutation.mutate(key.id)}
                      className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>
            ))}
            {apiKeys?.length === 0 && (
              <p className="text-center text-gray-400 py-8">No API keys yet</p>
            )}
          </div>
        </div>
      )}

      {/* Members Tab */}
      {activeTab === "members" && (
        <div className="max-w-2xl">
          <div className="flex gap-2 mb-6">
            <input
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
              placeholder="colleague@company.com"
              type="email"
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
            />
            <select
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="viewer">Viewer</option>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
            </select>
            <button
              onClick={() => inviteMutation.mutate({ email: inviteEmail, role: inviteRole })}
              disabled={!inviteEmail || inviteMutation.isPending}
              className="px-4 py-2 bg-primary text-white rounded-lg disabled:opacity-60"
            >
              Invite
            </button>
          </div>

          <div className="space-y-3">
            {members?.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-4"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                    <span className="text-sm font-medium text-gray-600">
                      {m.user_full_name?.charAt(0) ?? m.user_email?.charAt(0)}
                    </span>
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{m.user_full_name ?? m.user_email}</p>
                    <p className="text-xs text-gray-500">{m.user_email}</p>
                  </div>
                </div>
                <span className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full capitalize">
                  {m.role}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Organization Tab */}
      {activeTab === "org" && (
        <div className="max-w-2xl bg-white border border-gray-200 rounded-xl p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Organization Details</h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm text-gray-500">Name</dt>
              <dd className="font-medium text-gray-900">{(org as { name?: string })?.name}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Slug</dt>
              <dd className="font-mono text-sm text-gray-900">{(org as { slug?: string })?.slug}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">ID</dt>
              <dd className="font-mono text-xs text-gray-500">{(org as { id?: string })?.id}</dd>
            </div>
          </dl>
        </div>
      )}
    </div>
  );
}
