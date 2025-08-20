"use client";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";

const FloodHeatmap = dynamic(() => import("@/components/flood-heatmap"), {
  ssr: false,
  loading: () => (
    <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  ),
});

interface HeatmapData {
  city: string;
  lat: number;
  lon: number;
  prediction: number; // reuse as probability 0..1 for risk intensity
  precipitation: number;
  riskCategory?: string;
  explanation?: string;
  reservoirFill?: number; // percent 0..100
}

export default function HeatmapsPage() {
  const [heatmapData, setHeatmapData] = useState<HeatmapData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [grouped, setGrouped] = useState<any[]>([]);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>("");

  useEffect(() => {
    fetchHeatmapData();
  }, []);

  // Parse percent values that could be like "85%", 85, or 0.85
  const parsePercent = (v: any): number => {
    if (v === null || v === undefined) return 0;
    if (typeof v === 'string') {
      const trimmed = v.trim();
      const noPct = trimmed.endsWith('%') ? trimmed.slice(0, -1) : trimmed;
      const num = Number(noPct);
      if (!isNaN(num)) return num;
      return 0;
    }
    const num = Number(v);
    if (isNaN(num)) return 0;
    // if looks like 0..1, convert to 0..100
    if (num <= 1 && num >= 0) return num * 100;
    return num;
  };

  const fetchHeatmapData = async () => {
    try {
      const { success, data, error } = await api.getHeatmapsData();
      if (!success || !data)
        throw new Error(error || "Failed to fetch heatmap data");

      const payload = data as any;
      const zones = Array.isArray(payload.risk_zones) ? payload.risk_zones : [];
      if (zones.length === 0) throw new Error("Empty risk zones data");
      console.log(zones[0]);
      // Detect grouped-by-city shape (object with days array)
      const looksGrouped = !!zones[0] && Array.isArray(zones[0].days);

      if (looksGrouped) {
        setGrouped(zones);

        // Collect unique dates
        const dateSet = new Set<string>();
        for (const g of zones) {
          const days = Array.isArray(g.days) ? g.days : [];
          for (const d of days) {
            if (d?.Date) dateSet.add(String(d.Date));
          }
        }
        const sortedDates = Array.from(dateSet).sort();
        setAvailableDates(sortedDates);
        const defaultDate = sortedDates[sortedDates.length - 1];
        setSelectedDate(defaultDate);

        setHeatmapData(buildHeatmapDataForDate(zones, defaultDate));
      } else {
        // Flat list fallback: use latest date
        const latestDate = zones
          .map((d: any) => d.Date)
          .sort()
          .slice(-1)[0];
        const latest = zones.filter((d: any) => d.Date === latestDate);
        const mapped: HeatmapData[] = latest.map((d: any) => ({
          city: String(d.City),
          lat: Number(d.Latitude),
          lon: Number(d.Longitude),
          prediction: Number(d.Flood_Probability ?? d.Probability ?? 0),
          precipitation: Number(
            d.Precipitation_mm ?? d.Precipitation ?? d.Weather_Precip ?? 0
          ),
          riskCategory:
            typeof d.Risk_Level === "string" ? d.Risk_Level : undefined,
          explanation:
            typeof d.explanation === "string"
              ? d.explanation
              : typeof d.Explanation === "string"
              ? d.Explanation
              : undefined,
          reservoirFill: parsePercent(
            d.Max_Reservoir_Fill_Percent ?? d.Max_Reservoir_Fill ?? d.Reservoir_Fill ?? d.Reservoir ?? 0
          ),
        }));
        setHeatmapData(mapped);
        // Minimal dates for selector (single date)
        setAvailableDates([latestDate]);
        setSelectedDate(latestDate);
        setGrouped([]);
      }
    } catch (err) {
      console.error("Error fetching heatmap data:", err);
      setError("Failed to load heatmap data. Using sample data.");
      // Fallback sample data
      setHeatmapData([
        {
          city: "Delhi",
          lat: 28.6139,
          lon: 77.209,
          prediction: 0.8,
          precipitation: 25.5,
        },
        {
          city: "Mumbai",
          lat: 19.076,
          lon: 72.8777,
          prediction: 0.9,
          precipitation: 45.2,
        },
        {
          city: "Kolkata",
          lat: 22.5726,
          lon: 88.3639,
          prediction: 0.2,
          precipitation: 15.8,
        },
        {
          city: "Bangalore",
          lat: 12.9716,
          lon: 77.5946,
          prediction: 0.1,
          precipitation: 12.3,
        },
        {
          city: "Chennai",
          lat: 13.0827,
          lon: 80.2707,
          prediction: 0.7,
          precipitation: 35.7,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const buildHeatmapDataForDate = (
    groups: any[],
    date: string
  ): HeatmapData[] => {
    const out: HeatmapData[] = [];
    for (const g of groups) {
      const days = Array.isArray(g.days) ? g.days : [];
      const day = days.find((d: any) => String(d.Date) === date) || null;
      if (!day) continue;
      out.push({
        city: String(g.City ?? day.City ?? ""),
        lat: Number(day.Latitude),
        lon: Number(day.Longitude),
        prediction: Number(day.Flood_Probability ?? day.Probability ?? 0),
        precipitation: Number(
          day.Precipitation_mm ?? day.Precipitation ?? day.Weather_Precip ?? 0
        ),
        riskCategory: String(day.Risk_Level ?? day.Risk_Category ?? ""),
        explanation:
          typeof day.explanation === "string"
            ? day.explanation
            : typeof day.Explanation === "string"
            ? day.Explanation
            : undefined,
        reservoirFill: parsePercent(
          day.Max_Reservoir_Fill_Percent ?? day.Max_Reservoir_Fill ?? day.Reservoir_Fill ?? day.Reservoir ?? 0
        ),
      });
    }
    return out;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Risk Zones</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Visualize flood risk zones and rainfall intensity across India,
            using probability-driven risk levels and precipitation.
          </p>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Tabs defaultValue="flood" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="flood">Risk Zones</TabsTrigger>
            <TabsTrigger value="rainfall">Rainfall Intensity</TabsTrigger>
            <TabsTrigger value="reservoir">Reservoir Fill</TabsTrigger>
          </TabsList>

          <TabsContent value="flood" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">
                  Risk Zones (by Probability)
                </CardTitle>
                <CardDescription className="text-center">
                  The plot below shows probability-weighted flood risk zones.
                  Higher intensity indicates higher risk probability.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Date selector */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                  <label className="text-sm text-gray-700">Select date:</label>
                  <select
                    className="border rounded px-3 py-2 text-sm w-full md:w-auto"
                    value={selectedDate}
                    onChange={(e) => {
                      const newDate = e.target.value;
                      setSelectedDate(newDate);
                      if (grouped.length > 0) {
                        setHeatmapData(
                          buildHeatmapDataForDate(grouped, newDate)
                        );
                      }
                    }}
                  >
                    {availableDates.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                {loading ? (
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <FloodHeatmap data={heatmapData} />
                )}
                <div className="flex justify-center mt-4">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">
                      Low Probability
                    </span>
                    <div className="w-32 h-4 bg-gradient-to-r from-green-200 to-red-500 rounded"></div>
                    <span className="text-sm text-gray-600">
                      High Probability
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rainfall" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">
                  Rainfall Intensity
                </CardTitle>
                <CardDescription className="text-center">
                  Heavy rainfall predictions and precipitation analysis across
                  different regions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <FloodHeatmap data={heatmapData} type="rainfall" />
                )}
                <div className="flex justify-center mt-4">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">Light Rain</span>
                    <div className="w-32 h-4 bg-gradient-to-r from-yellow-200 to-blue-500 rounded"></div>
                    <span className="text-sm text-gray-600">Heavy Rain</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="reservoir" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">
                  Reservoir Fill
                </CardTitle>
                <CardDescription className="text-center">
                  Visualize reservoir fill levels across regions. Circle size
                  and color reflect fill percentage.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Date selector */}
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
                  <label className="text-sm text-gray-700">Select date:</label>
                  <select
                    className="border rounded px-3 py-2 text-sm w-full md:w-auto"
                    value={selectedDate}
                    onChange={(e) => {
                      const newDate = e.target.value;
                      setSelectedDate(newDate);
                      if (grouped.length > 0) {
                        setHeatmapData(
                          buildHeatmapDataForDate(grouped, newDate)
                        );
                      }
                    }}
                  >
                    {availableDates.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>
                {loading ? (
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <FloodHeatmap data={heatmapData} type="reservoir" />
                )}
                <div className="flex justify-center mt-4">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">Lower Fill</span>
                    <div className="w-32 h-4 bg-gradient-to-r from-green-400 via-amber-500 to-red-600 rounded"></div>
                    <span className="text-sm text-gray-600">Higher Fill</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
