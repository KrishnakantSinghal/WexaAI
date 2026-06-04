"use client";

import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Activity,
  Bell,
  TrendingUp,
  Users,
  Zap,
} from "lucide-react";
import api from "@/lib/api";
import { formatNumber } from "@/lib/utils";
import Link from "next/link";

function KpiCard({
  title,
  value,
  icon: Icon,
  color,
  href,
}: {
  title: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  href?: string;
}) {
  const content = (
    <div className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

export default function OverviewPage() {
  const { data: dashboards } = useQuery({
    queryKey: ["dashboards"],
    queryFn: async () => {
      const res = await api.get("/dashboards");
      return res.data as unknown[];
    },
  });

  const { data: alerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: async () => {
      const res = await api.get("/alerts");
      return res.data as Array<{ status: string }>;
    },
  });

  const { data: eventNames } = useQuery({
    queryKey: ["event-names"],
    queryFn: async () => {
      const res = await api.get("/events/names");
      return res.data as string[];
    },
  });

  const triggeredAlerts = alerts?.filter((a) => a.status === "triggered").length ?? 0;

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Overview</h1>
        <p className="text-gray-500 mt-1">
          Welcome to your analytics platform
        </p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <KpiCard
          title="Dashboards"
          value={dashboards?.length ?? 0}
          icon={BarChart3}
          color="bg-blue-500"
          href="/dashboards"
        />
        <KpiCard
          title="Event Types"
          value={eventNames?.length ?? 0}
          icon={Activity}
          color="bg-green-500"
          href="/events"
        />
        <KpiCard
          title="Triggered Alerts"
          value={triggeredAlerts}
          icon={Bell}
          color={triggeredAlerts > 0 ? "bg-red-500" : "bg-gray-400"}
          href="/alerts"
        />
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            href="/dashboards"
            className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
          >
            <BarChart3 className="w-5 h-5 text-primary" />
            <div>
              <p className="font-medium text-gray-900">New Dashboard</p>
              <p className="text-xs text-gray-500">Create a custom dashboard</p>
            </div>
          </Link>
          <Link
            href="/events"
            className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
          >
            <Zap className="w-5 h-5 text-primary" />
            <div>
              <p className="font-medium text-gray-900">Ingest Events</p>
              <p className="text-xs text-gray-500">Send data to the platform</p>
            </div>
          </Link>
          <Link
            href="/alerts"
            className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-primary hover:bg-primary/5 transition-colors"
          >
            <Bell className="w-5 h-5 text-primary" />
            <div>
              <p className="font-medium text-gray-900">Create Alert</p>
              <p className="text-xs text-gray-500">Set up threshold alerts</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
