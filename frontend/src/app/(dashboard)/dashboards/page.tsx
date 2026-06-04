"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, BarChart3, Globe, Lock, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Dashboard } from "@/types";
import { formatDate } from "@/lib/utils";

export default function DashboardsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data: dashboards, isLoading } = useQuery({
    queryKey: ["dashboards"],
    queryFn: async (): Promise<Dashboard[]> => {
      const res = await api.get("/dashboards");
      return res.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      api.post("/dashboards", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      setShowCreate(false);
      setName("");
      setDescription("");
      toast.success("Dashboard created");
    },
    onError: () => toast.error("Failed to create dashboard"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/dashboards/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      toast.success("Dashboard deleted");
    },
  });

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboards</h1>
          <p className="text-gray-500 mt-1">Manage your analytics dashboards</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Dashboard
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">Create Dashboard</h2>
          <div className="space-y-3">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Dashboard name"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
            />
            <div className="flex gap-2">
              <button
                onClick={() => createMutation.mutate({ name, description })}
                disabled={!name || createMutation.isPending}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-60"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse h-40"
            />
          ))}
        </div>
      ) : dashboards?.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No dashboards yet</p>
          <p className="text-sm">Create your first dashboard to get started</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {dashboards?.map((dash) => (
            <div
              key={dash.id}
              className="bg-white rounded-xl border border-gray-200 hover:shadow-md transition-shadow group"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <BarChart3 className="w-4 h-4 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 truncate max-w-[150px]">
                        {dash.name}
                      </h3>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(dash.id)}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                {dash.description && (
                  <p className="text-sm text-gray-500 mb-3 line-clamp-2">
                    {dash.description}
                  </p>
                )}

                <div className="flex items-center gap-3 text-xs text-gray-400 mb-4">
                  {dash.is_public ? (
                    <span className="flex items-center gap-1">
                      <Globe className="w-3 h-3" /> Public
                    </span>
                  ) : (
                    <span className="flex items-center gap-1">
                      <Lock className="w-3 h-3" /> Private
                    </span>
                  )}
                  {dash.refresh_interval && (
                    <span className="flex items-center gap-1">
                      <RefreshCw className="w-3 h-3" /> {dash.refresh_interval}s
                    </span>
                  )}
                </div>

                <Link
                  href={`/dashboards/${dash.id}`}
                  className="block w-full text-center py-2 border border-primary text-primary rounded-lg text-sm font-medium hover:bg-primary hover:text-white transition-colors"
                >
                  Open Dashboard
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
