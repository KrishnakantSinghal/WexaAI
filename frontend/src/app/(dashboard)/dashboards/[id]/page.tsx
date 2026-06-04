"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  Plus,
  RefreshCw,
  Maximize2,
  Settings,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import Link from "next/link";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useDashboardStore } from "@/store/dashboardStore";
import { useAuthStore } from "@/store/authStore";
import type { Dashboard, Widget } from "@/types";
import { cn } from "@/lib/utils";

const COLORS = ["#3B82F6", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#06B6D4"];

function WidgetCard({ widget }: { widget: Widget }) {
  const { data: queryData, isLoading } = useQuery({
    queryKey: ["widget-data", widget.id, widget.saved_query_id],
    queryFn: async () => {
      if (!widget.saved_query_id) return null;
      // Get the saved query to know what to query
      const qRes = await api.get(`/dashboards/queries/saved`);
      const queries = qRes.data as Array<{
        id: string;
        query_config: Record<string, unknown>;
      }>;
      const savedQuery = queries.find((q) => q.id === widget.saved_query_id);
      if (!savedQuery) return null;

      // --- translate seeded query_config -> backend EventQueryRequest ---
      const cfg = savedQuery.query_config || {};
      // time_range like "7d" / "24h" → start_time/end_time
      const parseRange = (r: unknown): number => {
        if (typeof r !== "string") return 14 * 24 * 3600 * 1000;
        const m = /^(\d+)([dhm])$/.exec(r);
        if (!m) return 14 * 24 * 3600 * 1000;
        const n = Number(m[1]);
        const unit = m[2];
        const mult =
          unit === "d" ? 86400_000 : unit === "h" ? 3600_000 : 60_000;
        return n * mult;
      };
      const rangeMs = parseRange(cfg.time_range);
      const endTime = new Date().toISOString();
      const startTime = new Date(Date.now() - rangeMs).toISOString();

      // group_by: "day"/"hour" → time_bucket; otherwise it's a property → keep
      const gb = cfg.group_by as string | undefined;
      const timeBucketMap: Record<string, string> = {
        minute: "1m",
        hour: "1h",
        day: "1d",
        week: "1w",
      };
      const isTimeGroup = gb && gb in timeBucketMap;
      const time_bucket = isTimeGroup ? timeBucketMap[gb!] : "1d";
      const group_by = isTimeGroup ? undefined : gb;

      // filters: backend wants dict, seed uses []
      const rawFilters = cfg.filters;
      const filters =
        rawFilters && !Array.isArray(rawFilters) &&
        typeof rawFilters === "object"
          ? rawFilters
          : {};

      const eventName = cfg.event_name as string | undefined;
      const body: Record<string, unknown> = {
        start_time: startTime,
        end_time: endTime,
        aggregation: (cfg.aggregation as string) || "count",
        time_bucket,
        filters,
      };
      if (eventName && eventName !== "*") body.event_name = eventName;
      if (group_by) body.group_by = group_by;
      if (cfg.aggregation_field)
        body.property_name = cfg.aggregation_field as string;

      const res = await api.post("/events/query", body);
      return res.data as {
        data: Array<{ bucket: string; value: number }>;
        total: number;
      };
    },
    enabled: !!widget.saved_query_id,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  const chartData = queryData?.data ?? [];

  switch (widget.widget_type) {
    case "kpi_card":
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <p className="text-4xl font-bold text-gray-900">
            {queryData?.total ?? 0}
          </p>
          <p className="text-sm text-gray-500 mt-1">{widget.title}</p>
        </div>
      );

    case "line_chart":
      return (
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      );

    case "bar_chart":
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="bucket" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );

    case "pie_chart":
      return (
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={chartData} dataKey="value" nameKey="bucket" cx="50%" cy="50%">
              {chartData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      );

    case "table":
      return (
        <div className="overflow-auto h-full">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left p-2 font-medium text-gray-500">Time</th>
                <th className="text-right p-2 font-medium text-gray-500">Value</th>
              </tr>
            </thead>
            <tbody>
              {chartData.map((row, i) => (
                <tr key={i} className="border-b border-gray-100">
                  <td className="p-2 text-gray-700">{row.bucket}</td>
                  <td className="p-2 text-right font-mono">{row.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );

    default:
      return <div className="text-gray-400 text-sm">Unknown widget type</div>;
  }
}

export default function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { isFullscreen, setFullscreen } = useDashboardStore();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  const { data: dashboard, isLoading, refetch } = useQuery({
    queryKey: ["dashboard", id],
    queryFn: async (): Promise<Dashboard> => {
      const res = await api.get(`/dashboards/${id}`);
      return res.data;
    },
    enabled: !!id,
  });

  // Real-time updates via WebSocket
  const { status: wsStatus } = useWebSocket({
    path: `/ws/dashboard/${id}`,
    enabled: isAuthenticated && !!id,
    onMessage: useCallback(
      (msg: unknown) => {
        const data = msg as { type?: string };
        if (data?.type === "data_updated") {
          refetch();
        }
      },
      [refetch]
    ),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>Dashboard not found.</p>
        <Link href="/dashboards" className="text-primary hover:underline mt-2 inline-block">
          Back to dashboards
        </Link>
      </div>
    );
  }

  return (
    <div className={cn("p-8", isFullscreen && "fixed inset-0 bg-white z-50 overflow-auto")}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          {!isFullscreen && (
            <Link
              href="/dashboards"
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <ArrowLeft className="w-5 h-5" />
            </Link>
          )}
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{dashboard.name}</h1>
            {dashboard.description && (
              <p className="text-gray-500 text-sm mt-0.5">{dashboard.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              wsStatus === "connected" ? "bg-green-500" : "bg-gray-300"
            )}
            title={`WebSocket: ${wsStatus}`}
          />
          <button
            onClick={() => refetch()}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
          <button
            onClick={() => setFullscreen(!isFullscreen)}
            className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <Maximize2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Widgets Grid */}
      {!dashboard.widgets || dashboard.widgets.length === 0 ? (
        <div className="text-center py-24 text-gray-400">
          <Settings className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p className="text-lg font-medium">No widgets yet</p>
          <p className="text-sm">Add widgets to start visualizing your data</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4">
          {dashboard.widgets.map((widget) => {
            const pos = widget.position as {
              x: number;
              y: number;
              w: number;
              h: number;
            };
            const spanW = Math.min(Math.max(pos.w || 6, 1), 12);
            // Static class map so Tailwind picks these up during build.
            const lgColSpan = {
              1: "lg:col-span-1",
              2: "lg:col-span-2",
              3: "lg:col-span-3",
              4: "lg:col-span-4",
              5: "lg:col-span-5",
              6: "lg:col-span-6",
              7: "lg:col-span-7",
              8: "lg:col-span-8",
              9: "lg:col-span-9",
              10: "lg:col-span-10",
              11: "lg:col-span-11",
              12: "lg:col-span-12",
            }[spanW];
            const heightPx = Math.max((pos.h || 4) * 80, 240);
            return (
              <div
                key={widget.id}
                className={cn(
                  "bg-white rounded-xl border border-gray-200 p-4",
                  "col-span-1 sm:col-span-2",
                  lgColSpan
                )}
                style={{ height: `${heightPx}px` }}
              >
                <p className="text-sm font-medium text-gray-700 mb-3">
                  {widget.title}
                </p>
                <div className="h-[calc(100%-2rem)]">
                  <WidgetCard widget={widget} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
