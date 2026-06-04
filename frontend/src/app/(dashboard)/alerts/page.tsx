"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Plus, Bell, BellOff, Trash2, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Alert, AlertStatus } from "@/types";
import { formatDate } from "@/lib/utils";
import { cn } from "@/lib/utils";

const statusConfig: Record<AlertStatus, { label: string; color: string; icon: React.ElementType }> = {
  active: { label: "Active", color: "bg-blue-100 text-blue-700", icon: CheckCircle },
  triggered: { label: "Triggered", color: "bg-red-100 text-red-700", icon: AlertTriangle },
  resolved: { label: "Resolved", color: "bg-green-100 text-green-700", icon: CheckCircle },
  muted: { label: "Muted", color: "bg-gray-100 text-gray-600", icon: BellOff },
};

export default function AlertsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    event_name: "",
    aggregation: "count",
    condition: "gt",
    threshold: "",
    time_window_minutes: "10",
    evaluation_interval_minutes: "5",
  });

  const { data: alerts, isLoading } = useQuery({
    queryKey: ["alerts"],
    queryFn: async (): Promise<Alert[]> => {
      const res = await api.get("/alerts");
      return res.data;
    },
    refetchInterval: 30000,
  });

  const createMutation = useMutation({
    mutationFn: (data: object) => api.post("/alerts", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      setShowCreate(false);
      toast.success("Alert created");
    },
    onError: () => toast.error("Failed to create alert"),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/alerts/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      toast.success("Alert deleted");
    },
  });

  const muteMutation = useMutation({
    mutationFn: ({ id, until }: { id: string; until: string }) =>
      api.post(`/alerts/${id}/mute`, { mute_until: until }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      toast.success("Alert muted for 1 hour");
    },
  });

  const handleCreate = () => {
    createMutation.mutate({
      name: form.name,
      metric_query: {
        event_name: form.event_name,
        aggregation: form.aggregation,
        time_window_minutes: parseInt(form.time_window_minutes),
      },
      condition: form.condition,
      threshold: parseFloat(form.threshold),
      evaluation_interval_minutes: parseInt(form.evaluation_interval_minutes),
      notification_channels: [],
    });
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alerts</h1>
          <p className="text-gray-500 mt-1">Monitor your metrics with threshold alerts</p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Alert
        </button>
      </div>

      {/* Create Form */}
      {showCreate && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="font-semibold text-gray-900 mb-4">Create Alert Rule</h2>
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Alert Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="High error rate"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Event Name</label>
              <input
                value={form.event_name}
                onChange={(e) => setForm({ ...form, event_name: e.target.value })}
                placeholder="error"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Aggregation</label>
              <select
                value={form.aggregation}
                onChange={(e) => setForm({ ...form, aggregation: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="count">Count</option>
                <option value="unique">Unique users</option>
                <option value="sum">Sum</option>
                <option value="avg">Average</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Condition</label>
              <select
                value={form.condition}
                onChange={(e) => setForm({ ...form, condition: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              >
                <option value="gt">&gt; Greater than</option>
                <option value="gte">&gt;= Greater or equal</option>
                <option value="lt">&lt; Less than</option>
                <option value="lte">&lt;= Less or equal</option>
                <option value="eq">= Equal to</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Threshold</label>
              <input
                type="number"
                value={form.threshold}
                onChange={(e) => setForm({ ...form, threshold: e.target.value })}
                placeholder="100"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Time Window (min)</label>
              <input
                type="number"
                value={form.time_window_minutes}
                onChange={(e) => setForm({ ...form, time_window_minutes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Eval Interval (min)</label>
              <input
                type="number"
                value={form.evaluation_interval_minutes}
                onChange={(e) => setForm({ ...form, evaluation_interval_minutes: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
            </div>
          </div>
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleCreate}
              disabled={!form.name || !form.event_name || !form.threshold || createMutation.isPending}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-60"
            >
              Create Alert
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Alerts List */}
      {isLoading ? (
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-6 animate-pulse h-24" />
          ))}
        </div>
      ) : alerts?.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <Bell className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No alerts yet</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts?.map((alert) => {
            const cfg = statusConfig[alert.status] ?? statusConfig.active;
            const Icon = cfg.icon;
            return (
              <div
                key={alert.id}
                className="bg-white rounded-xl border border-gray-200 p-6 flex items-center justify-between"
              >
                <div className="flex items-start gap-4">
                  <div className={cn("p-2 rounded-lg", cfg.color)}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{alert.name}</h3>
                    <p className="text-sm text-gray-500 mt-0.5">
                      {(alert.metric_query as { event_name?: string }).event_name} {alert.condition}{" "}
                      {alert.threshold} over{" "}
                      {(alert.metric_query as { time_window_minutes?: number }).time_window_minutes}m
                    </p>
                    {alert.last_triggered_at && (
                      <p className="text-xs text-gray-400 mt-1">
                        Last triggered: {formatDate(alert.last_triggered_at)}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={cn("px-2 py-1 rounded-full text-xs font-medium", cfg.color)}>
                    {cfg.label}
                  </span>
                  {alert.status !== "muted" && (
                    <button
                      onClick={() => {
                        const until = new Date(Date.now() + 3600 * 1000).toISOString();
                        muteMutation.mutate({ id: alert.id, until });
                      }}
                      className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg"
                      title="Mute for 1 hour"
                    >
                      <BellOff className="w-4 h-4" />
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(alert.id)}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
