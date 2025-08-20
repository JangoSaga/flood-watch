"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useEffect, useMemo, useState } from "react";
import { api, handleApiError } from "@/lib/api";

interface DayForecast {
  City: string;
  Date: string;
  Predicted_Flood_Risk: number;
  Flood_Probability: number;
  Weather_Precip?: number;
  Max_Reservoir_Fill?: number;
  Confidence?: string;
  Risk_Category?: string;
  explanation?: string;
}

// Helpers to color-code cells
function getProbClass(pct: number) {
  if (isNaN(pct)) return "";
  if (pct >= 80) return "bg-red-50 text-red-700";
  if (pct >= 50) return "bg-orange-50 text-orange-700";
  if (pct >= 20) return "bg-yellow-50 text-yellow-700";
  return "bg-green-50 text-green-700";
}

function getPrecipClass(mm: number) {
  if (isNaN(mm)) return "";
  if (mm >= 50) return "bg-red-50 text-red-700";
  if (mm >= 20) return "bg-orange-50 text-orange-700";
  if (mm >= 5) return "bg-yellow-50 text-yellow-700";
  return "bg-green-50 text-green-700";
}

function getReservoirClass(pct: number) {
  if (isNaN(pct)) return "";
  if (pct >= 90) return "bg-red-50 text-red-700";
  if (pct >= 80) return "bg-orange-50 text-orange-700";
  if (pct >= 60) return "bg-yellow-50 text-yellow-700";
  return "bg-green-50 text-green-700";
}

function getConfidenceBadge(conf?: string) {
  const c = (conf || "").toLowerCase();
  if (c === "high") return "bg-green-100 text-green-800";
  if (c === "medium" || c === "moderate") return "bg-yellow-100 text-yellow-800";
  if (c === "low") return "bg-red-100 text-red-800";
  return "bg-gray-100 text-gray-800";
}

function getRiskCategoryBadge(rc?: string) {
  const r = (rc || "").toLowerCase();
  if (r.includes("critical") || r.includes("high")) return "bg-red-100 text-red-800";
  if (r.includes("moderate") || r.includes("medium")) return "bg-yellow-100 text-yellow-800";
  if (r.includes("low")) return "bg-green-100 text-green-800";
  return "bg-gray-100 text-gray-800";
}

export default function PredictPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<DayForecast[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");

  const fetch7Day = async () => {
    setLoading(true);
    setError(null);
    setRows([]);
    try {
      const res = await api.get7DayForecast();
      if (res.success && res.data) {
        let arr: any[] = [];
        const d: any = res.data;
        if (Array.isArray(d)) arr = d;
        else if (Array.isArray(d?.daily_forecasts)) arr = d.daily_forecasts;
        else if (Array.isArray(d?.forecasts)) arr = d.forecasts;
        else if (Array.isArray(d?.predictions)) {
          // Flatten grouped shape: predictions[] each with days[]
          arr = d.predictions.flatMap((p: any) =>
            Array.isArray(p?.days)
              ? p.days.map((day: any) => ({
                  // ensure City present; prefer day.City, fallback to parent City
                  City: day?.City ?? day?.city ?? p?.City ?? p?.city ?? "",
                  ...day,
                }))
              : []
          );
        }

        const normalized: DayForecast[] = (arr || []).map((x: any) => ({
          City: x.City ?? x.city ?? x.name ?? "",
          Date: x.Date ?? x.date ?? x.day ?? "",
          Predicted_Flood_Risk: Number(x.Predicted_Flood_Risk ?? x.predicted ?? x.risk ?? 0),
          Flood_Probability: Number(x.Flood_Probability ?? x.probability ?? 0),
          Weather_Precip: Number(x.Weather_Precip ?? x.precipitation ?? x.precip ?? 0),
          Max_Reservoir_Fill: x.Max_Reservoir_Fill ?? x.max_reservoir_fill ?? undefined,
          Confidence: x.Confidence ?? x.confidence ?? undefined,
          Risk_Category: x.Risk_Category ?? x.risk_category ?? x.riskCategory ?? undefined,
          explanation: x.explanation ?? x.Explanation ?? undefined,
        }));

        // Sort by City then Date
        normalized.sort((a, b) => {
          const c = (a.City || "").localeCompare(b.City || "");
          if (c !== 0) return c;
          return (a.Date || "").localeCompare(b.Date || "");
        });

        setRows(normalized);
        // Initialize selected date to the earliest available if none selected
        const dates = Array.from(new Set(normalized.map((x) => x.Date))).sort();
        setSelectedDate((prev) => prev || (dates.length > 0 ? dates[0] : ""));
      } else {
        setError(handleApiError(res.error));
      }
    } catch (e) {
      console.error("Error fetching 7-day forecast:", e);
      setError(handleApiError(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch7Day();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            7-Day Flood Forecasts
          </h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Forecast details for each city and date.
          </p>
        </div>

        <div className="mb-4 flex items-center gap-3">
          <label className="text-sm font-medium text-gray-700">Select date</label>
          <Select value={selectedDate} onValueChange={setSelectedDate}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="Choose a date" />
            </SelectTrigger>
            <SelectContent>
              {Array.from(new Set(rows.map((r) => r.Date)))
                .sort()
                .map((d) => (
                  <SelectItem key={d} value={String(d)}>
                    {String(d)}
                  </SelectItem>
                ))}
            </SelectContent>
          </Select>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
            <p className="text-sm">
              <strong>Warning:</strong> {error}
            </p>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>All Cities — 7-Day Forecast</CardTitle>
            <CardDescription>
              {loading
                ? "Loading forecasts..."
                : `${rows.length} records`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full border rounded-md text-sm">
                <thead className="bg-gray-100">
                  <tr>
                    <th className="text-left p-2 border">City</th>
                    <th className="text-left p-2 border">Date</th>
                    <th className="text-right p-2 border">Flood Prob (%)</th>
                    <th className="text-right p-2 border">Precip (mm)</th>
                    <th className="text-right p-2 border">Max Reservoir</th>
                    <th className="text-left p-2 border">Confidence</th>
                    <th className="text-left p-2 border">Risk Category</th>
                    <th className="text-left p-2 border">Explanation</th>
                  </tr>
                </thead>
                <tbody>
                  {(rows.filter((r) => !selectedDate || r.Date === selectedDate)).map((r, idx) => (
                    <tr key={`${r.City}-${r.Date}-${idx}`} className="odd:bg-white even:bg-gray-50">
                      <td className="p-2 border">{r.City}</td>
                      <td className="p-2 border">{r.Date}</td>
                      <td className="p-2 border text-right">
                        {(() => {
                          const pct = Math.round((Number(r.Flood_Probability) || 0) * 100);
                          return (
                            <span className={`inline-block rounded px-2 py-0.5 ${getProbClass(pct)}`} title={`${pct}%`}>
                              {pct}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="p-2 border text-right">
                        {(() => {
                          const mm = Number(r.Weather_Precip ?? 0);
                          return (
                            <span className={`inline-block rounded px-2 py-0.5 ${getPrecipClass(mm)}`} title={`${mm} mm`}>
                              {mm}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="p-2 border text-right">
                        {(() => {
                          const mr = r.Max_Reservoir_Fill;
                          if (mr === undefined || mr === null || isNaN(Number(mr))) return "-";
                          const val = Number(mr);
                          return (
                            <span className={`inline-block rounded px-2 py-0.5 ${getReservoirClass(val)}`} title={`${val}%`}>
                              {val}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="p-2 border">
                        <span className={`inline-block rounded px-2 py-0.5 ${getConfidenceBadge(r.Confidence)}`}>
                          {r.Confidence ?? "-"}
                        </span>
                      </td>
                      <td className="p-2 border">
                        <span className={`inline-block rounded px-2 py-0.5 ${getRiskCategoryBadge(r.Risk_Category)}`}>
                          {r.Risk_Category ?? "-"}
                        </span>
                      </td>
                      <td className="p-2 border">{r.explanation ?? "-"}</td>
                    </tr>
                  ))}
                  {!loading && (rows.filter((r) => !selectedDate || r.Date === selectedDate)).length === 0 && (
                    <tr>
                      <td className="p-3 text-center text-gray-500" colSpan={8}>
                        No forecast data available
                      </td>
                    </tr>
                  )}
                  {loading && (
                    <tr>
                      <td className="p-3 text-center text-gray-500" colSpan={8}>
                        Loading...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
