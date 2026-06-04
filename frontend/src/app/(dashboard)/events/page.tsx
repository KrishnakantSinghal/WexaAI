"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Activity, Upload, Zap, Plus, Search } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { formatDate } from "@/lib/utils";
import type { Event } from "@/types";

export default function EventsPage() {
  const [activeTab, setActiveTab] = useState<"stream" | "ingest" | "csv">("stream");
  const [eventName, setEventName] = useState("");
  const [properties, setProperties] = useState("{}");

  const { data: eventNames } = useQuery({
    queryKey: ["event-names"],
    queryFn: async (): Promise<string[]> => {
      const res = await api.get("/events/names");
      return res.data;
    },
  });

  const ingestMutation = useMutation({
    mutationFn: (data: { event_name: string; properties: Record<string, unknown> }) =>
      api.post("/events/ingest", data),
    onSuccess: () => {
      toast.success("Event ingested");
      setEventName("");
      setProperties("{}");
    },
    onError: () => toast.error("Failed to ingest event"),
  });

  const handleIngest = () => {
    let props: Record<string, unknown> = {};
    try {
      props = JSON.parse(properties);
    } catch {
      toast.error("Invalid JSON properties");
      return;
    }
    ingestMutation.mutate({ event_name: eventName, properties: props });
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Events</h1>
        <p className="text-gray-500 mt-1">Ingest and monitor your event data</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 mb-6 w-fit">
        {(["stream", "ingest", "csv"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors capitalize ${
              activeTab === tab
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {tab === "stream" ? "Live Stream" : tab === "ingest" ? "API Ingest" : "CSV Upload"}
          </button>
        ))}
      </div>

      {/* Stream Tab */}
      {activeTab === "stream" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            <h2 className="font-semibold">Live Event Stream</h2>
          </div>
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-2">
              Registered event types ({eventNames?.length ?? 0}):
            </p>
            <div className="flex flex-wrap gap-2">
              {eventNames?.map((name) => (
                <span
                  key={name}
                  className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                >
                  {name}
                </span>
              ))}
              {(!eventNames || eventNames.length === 0) && (
                <span className="text-sm text-gray-400">No events yet</span>
              )}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 h-48 overflow-auto font-mono text-sm text-green-400">
            <p className="opacity-50">{">"} Waiting for events...</p>
          </div>
        </div>
      )}

      {/* Ingest Tab */}
      {activeTab === "ingest" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-2xl">
          <h2 className="font-semibold mb-4">Ingest Single Event</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Event Name
              </label>
              <input
                value={eventName}
                onChange={(e) => setEventName(e.target.value)}
                placeholder="e.g. page_view, purchase, button_click"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Properties (JSON)
              </label>
              <textarea
                value={properties}
                onChange={(e) => setProperties(e.target.value)}
                rows={5}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 font-mono text-sm"
                placeholder='{"url": "/home", "user_id": "abc123"}'
              />
            </div>
            <button
              onClick={handleIngest}
              disabled={!eventName || ingestMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-60"
            >
              <Zap className="w-4 h-4" />
              {ingestMutation.isPending ? "Sending..." : "Send Event"}
            </button>
          </div>

          <div className="mt-6 p-4 bg-gray-50 rounded-lg">
            <p className="text-sm font-medium text-gray-700 mb-2">API Example</p>
            <pre className="text-xs text-gray-600 overflow-auto">
              {`POST /api/v1/events/ingest
Authorization: Bearer <token>

{
  "event_name": "${eventName || "page_view"}",
  "properties": ${properties}
}`}
            </pre>
          </div>
        </div>
      )}

      {/* CSV Tab */}
      {activeTab === "csv" && (
        <div className="bg-white rounded-xl border border-gray-200 p-6 max-w-2xl">
          <h2 className="font-semibold mb-4">Upload CSV</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
            <Upload className="w-8 h-8 text-gray-400 mx-auto mb-3" />
            <p className="font-medium text-gray-700">Drop a CSV file here</p>
            <p className="text-sm text-gray-500 mt-1">
              Required columns: <code>event_name</code>, <code>timestamp</code>
            </p>
            <label className="mt-4 inline-block cursor-pointer">
              <span className="px-4 py-2 bg-primary text-white rounded-lg text-sm hover:bg-primary/90">
                Browse File
              </span>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  const formData = new FormData();
                  formData.append("file", file);
                  try {
                    const res = await api.post("/events/ingest/csv", formData, {
                      headers: { "Content-Type": "multipart/form-data" },
                    });
                    toast.success(`Ingested ${res.data.ingested} events`);
                  } catch {
                    toast.error("CSV upload failed");
                  }
                }}
              />
            </label>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Max file size: 50MB. Up to 10,000 rows per file.
          </p>
        </div>
      )}
    </div>
  );
}
