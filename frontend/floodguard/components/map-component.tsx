"use client";

import { useEffect, useRef } from "react";

interface MapData {
  city: string;
  lat: number;
  lon: number;
  precipitation?: number;
  prediction?: number;
  riskCategory?: string;
  probability?: number; // Flood_Probability in [0,1]
  explanation?: string;
  damage?: number;
  reservoirFill?: number; // percentage 0..100
}

interface MapComponentProps {
  data: MapData[];
  type: "prediction" | "damage" | "flood" | "rainfall" | "reservoir";
}

export default function MapComponent({ data, type }: MapComponentProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);

  const ensureLeafletCss = () => {
    if (typeof window === "undefined") return;
    if (document.getElementById("leaflet-css")) return;
    const link = document.createElement("link");
    link.id = "leaflet-css";
    link.rel = "stylesheet";
    link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
    link.crossOrigin = "";
    document.head.appendChild(link);
  };

  useEffect(() => {
    if (typeof window === "undefined") return;

    // Ensure Leaflet CSS is present on client
    ensureLeafletCss();

    // Dynamically import Leaflet only on client side
    import("leaflet")
      .then(async (mod) => {
        const L = (mod as any).default || (mod as any);

        // Fix for default markers in Next.js
        delete (L.Icon.Default.prototype as any)._getIconUrl;
        L.Icon.Default.mergeOptions({
          iconRetinaUrl:
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png",
          iconUrl:
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
          shadowUrl:
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
        });

        if (!mapRef.current || mapInstanceRef.current) return;

        // Initialize map centered on India
        const map = L.map(mapRef.current).setView([20.5937, 78.9629], 5);

        // Add tile layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(map);

        mapInstanceRef.current = map;

        // Add data to map
        if (data && data.length > 0) {
          addDataToMap(L, map, data, type);
        }
      })
      .catch((error) => {
        console.error("Error loading Leaflet:", error);
      });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (
      typeof window === "undefined" ||
      !mapInstanceRef.current ||
      !data.length
    )
      return;

    import("leaflet")
      .then(async (mod) => {
        const L = (mod as any).default || (mod as any);
        // Clear existing layers (markers/circles)
        mapInstanceRef.current.eachLayer((layer: any) => {
          if (layer instanceof L.Marker || layer instanceof L.Circle) {
            mapInstanceRef.current.removeLayer(layer);
          }
        });
        // No heat layer used for rainfall; only circles with popups

        addDataToMap(L, mapInstanceRef.current, data, type);
      })
      .catch((error) => {
        console.error("Error updating map:", error);
      });
  }, [data, type]);

  const addDataToMap = (L: any, map: any, data: MapData[], type: string) => {
    if (type === "rainfall") {
      // Circles with popups for rainfall visualization
      data.forEach((item) => addRainfallPopupCircle(L, map, item, data));
      return;
    }
    if (type === "reservoir") {
      data.forEach((item) => addReservoirCircle(L, map, item, data));
      return;
    }
    data.forEach((item) => {
      if (type === "prediction") {
        addPredictionMarker(L, map, item);
      } else if (type === "damage") {
        addDamageCircle(L, map, item, data);
      } else {
        addHeatmapCircle(L, map, item, type, data);
      }
    });
  };

  // Heatmap rendering removed; rainfall uses circles only

  const addRainfallPopupCircle = (
    L: any,
    map: any,
    item: MapData,
    allData: MapData[]
  ) => {
    const maxPrec = Math.max(...allData.map((d) => d.precipitation || 0), 0);
    const intensity = maxPrec > 0 ? (item.precipitation || 0) / maxPrec : 0;
    const color = intensity > 0.6 ? "#2563eb" : "#60a5fa";

    // Linear radius scaling: 8km to 45km based on intensity [0..1]
    const minRadius = 8000; // meters
    const maxRadius = 45000; // meters
    const radius = minRadius + intensity * (maxRadius - minRadius);

    L.circle([item.lat, item.lon], {
      color,
      fillColor: color,
      fillOpacity: 0.7,
      opacity: 0.7,
      radius,
      weight: 1,
    })
      .bindPopup(
        `
        <div style="padding: 8px;">
          <h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${
            item.city
          }</h3>
          <p style="font-size: 14px; margin: 2px 0;"><strong>Precipitation:</strong> ${(
            item.precipitation || 0
          ).toFixed(1)}mm</p>
          ${
            item.explanation
              ? `<p style=\"font-size: 14px; margin: 2px 0;\"><strong>Explanation:</strong> ${item.explanation}</p>`
              : ""
          }
          <p style="font-size: 14px; margin: 2px 0;"><strong>Coordinates:</strong> ${item.lat.toFixed(
            4
          )}, ${item.lon.toFixed(4)}</p>
        </div>
        `
      )
      .addTo(map);
  };

  const addReservoirCircle = (
    L: any,
    map: any,
    item: MapData,
    allData: MapData[]
  ) => {
    // Reuse addHeatmapCircle with type "reservoir"
    addHeatmapCircle(L, map, item, "reservoir", allData);
  };

  const addPredictionMarker = (L: any, map: any, item: MapData) => {
    const categoryRaw = (item.riskCategory || "").toString();
    const category = categoryRaw.trim().toLowerCase();

    const colorByCategory = (cat: string) => {
      switch (cat) {
        case "critical":
          return "#991b1b"; // dark red
        case "high":
          return "#ef4444"; // red
        case "medium":
          return "#f59e0b"; // amber
        case "low":
        default:
          return "#22c55e"; // green
      }
    };

    const displayCategory =
      categoryRaw || (item.prediction === 1 ? "High" : "Low");
    const color = colorByCategory(category);

    const icon = L.divIcon({
      className: "custom-marker",
      html: `<div style="
				width: 12px;
				height: 12px;
				border-radius: 50%;
				background-color: ${color};
				border: 2px solid white;
				box-shadow: 0 2px 4px rgba(0,0,0,0.3);
			"></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    L.marker([item.lat, item.lon], { icon })
      .bindPopup(
        `
                <div style="padding: 8px;">
                    <h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${
                      item.city
                    }</h3>
                    <p style="font-size: 14px; margin: 2px 0;"><strong>Risk Category:</strong> ${displayCategory}</p>
                    ${
                      item.explanation
                        ? `<p style=\"font-size: 14px; margin: 2px 0;\"><strong>Explanation:</strong> ${item.explanation}</p>`
                        : ""
                    }
                    <p style="font-size: 14px; margin: 2px 0;"><strong>Precipitation:</strong> ${(
                      item.precipitation || 0
                    ).toFixed(1)}mm</p>
                    <p style="font-size: 14px; margin: 2px 0;"><strong>Coordinates:</strong> ${item.lat.toFixed(
                      4
                    )}, ${item.lon.toFixed(4)}</p>
                </div>
                `
      )
      .addTo(map);
  };

  const addDamageCircle = (
    L: any,
    map: any,
    item: MapData,
    allData: MapData[]
  ) => {
    const maxDamage = Math.max(...allData.map((d) => d.damage || 0));
    const damageRatio = (item.damage || 0) / maxDamage;
    const radius = Math.max(damageRatio * 50000, 5000);

    const getColor = (ratio: number) => {
      if (ratio > 0.8) return "#dc2626";
      if (ratio > 0.6) return "#ea580c";
      if (ratio > 0.4) return "#d97706";
      if (ratio > 0.2) return "#ca8a04";
      return "#65a30d";
    };

    const circle = L.circle([item.lat, item.lon], {
      color: getColor(damageRatio),
      fillColor: getColor(damageRatio),
      fillOpacity: 0.6,
      radius: radius,
    })
      .bindPopup(
        `
			<div style="padding: 8px;">
				<h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${
          item.city
        }</h3>
				<p style="font-size: 14px; margin: 2px 0;"><strong>Estimated Damage:</strong> $${(
          item.damage || 0
        ).toLocaleString()}</p>
				<p style="font-size: 14px; margin: 2px 0;"><strong>Risk Level:</strong> ${
          item.prediction === 1 ? "High" : "Low"
        }</p>
				<p style="font-size: 14px; margin: 2px 0;"><strong>Precipitation:</strong> ${(
          item.precipitation || 0
        ).toFixed(1)}mm</p>
			</div>
			`
      )
      .addTo(map);
  };

  const addHeatmapCircle = (
    L: any,
    map: any,
    item: MapData,
    type: string,
    allData: MapData[]
  ) => {
    const getValue = (it: MapData) =>
      type === "rainfall"
        ? it.precipitation || 0
        : type === "reservoir"
        ? (it.reservoirFill ?? 0)
        : it.prediction || 0; // probability [0,1]

    const value = getValue(item);
    const maxValue =
      type === "rainfall"
        ? Math.max(...allData.map((d) => d.precipitation || 0))
        : type === "reservoir"
        ? 100
        : 1;

    const intensity =
      type === "rainfall"
        ? (maxValue > 0 ? value / maxValue : 0)
        : type === "reservoir"
        ? Math.max(0, Math.min(1, (value as number) / 100))
        : value;

    const getColor = (intens: number, t: string) => {
      if (t === "rainfall") {
        if (intens > 0.8) return "#1e40af";
        if (intens > 0.6) return "#2563eb";
        if (intens > 0.4) return "#3b82f6";
        if (intens > 0.2) return "#60a5fa";
        return "#dbeafe";
      }
      if (t === "reservoir") {
        // reservoir fill color bands
        const pct = intens * 100;
        if (pct >= 90) return "#dc2626"; // red
        if (pct >= 80) return "#ea580c"; // orange
        if (pct >= 60) return "#f59e0b"; // amber
        return "#22c55e"; // green
      }
      // probability gradient: green -> yellow -> orange -> red
      if (intens > 0.8) return "#dc2626"; // red
      if (intens > 0.6) return "#ea580c"; // orange
      if (intens > 0.4) return "#f59e0b"; // amber
      if (intens > 0.2) return "#84cc16"; // lime
      return "#22c55e"; // green
    };

    // Scale radius consistently: 8km to 45km based on intensity [0..1]
    const minRadius = 8000; // meters
    const maxRadius = 45000; // meters
    const radius = minRadius + intensity * (maxRadius - minRadius);

    L.circle([item.lat, item.lon], {
      color: getColor(intensity, type),
      fillColor: getColor(intensity, type),
      fillOpacity: 0.6,
      radius: radius,
    })
      .bindPopup(
        `
        <div style="padding: 8px;">
          <h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${
            item.city
          }</h3>
          ${
            type === "rainfall"
              ? `<p style="font-size: 14px; margin: 2px 0;"><strong>Precipitation:</strong> ${(
                  item.precipitation || 0
                ).toFixed(1)}mm</p>`
              : type === "reservoir"
              ? `<p style=\"font-size: 14px; margin: 2px 0;\"><strong>Reservoir Fill:</strong> ${Number(
                  item.reservoirFill ?? 0
                ).toFixed(0)}%</p>`
              : `<p style=\"font-size: 14px; margin: 2px 0;\"><strong>Flood Probability:</strong> ${Math.round(
                  (item.prediction || 0) * 100
                )}%</p>`
          }
          ${
            item.explanation
              ? `<p style="font-size: 14px; margin: 2px 0;"><strong>Explanation:</strong> ${item.explanation}</p>`
              : ""
          }
          <p style="font-size: 14px; margin: 2px 0;"><strong>Coordinates:</strong> ${item.lat.toFixed(
            4
          )}, ${item.lon.toFixed(4)}</p>
        </div>
        `
      )
      .addTo(map);
  };

  return (
    <div className="relative">
      <div ref={mapRef} className="w-full h-[600px] rounded-lg border" />
      <div className="absolute top-4 right-4 bg-white p-3 rounded-lg shadow-lg z-[1000]">
        <h4 className="font-semibold text-sm mb-2">Legend</h4>
        <div className="space-y-1">
          {type === "prediction" && (
            <>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#22c55e" }}
                ></div>
                <span>Low</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#f59e0b" }}
                ></div>
                <span>Medium</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#ef4444" }}
                ></div>
                <span>High</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#991b1b" }}
                ></div>
                <span>Critical</span>
              </div>
              <div className="h-px bg-gray-200 my-2" />
              <div className="text-xs font-medium mb-1">Explanations</div>
              <div className="max-h-40 overflow-auto pr-1 space-y-1">
                {data
                  .filter((d) => !!d.explanation)
                  .map((d, idx) => (
                    <div key={idx} className="text-[11px] text-gray-700">
                      <span className="font-semibold">{d.city}:</span>{" "}
                      {d.explanation}
                    </div>
                  ))}
                {data.every((d) => !d.explanation) && (
                  <div className="text-[11px] text-gray-400">
                    No explanations available
                  </div>
                )}
              </div>
            </>
          )}
          {type === "damage" && (
            <>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-red-600 rounded-full mr-2"></div>
                <span>Very High</span>
              </div>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-orange-600 rounded-full mr-2"></div>
                <span>High</span>
              </div>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-lime-600 rounded-full mr-2"></div>
                <span>Low</span>
              </div>
            </>
          )}
          {type === "flood" && (
            <>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#22c55e" }}
                ></div>
                <span>0–20%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#84cc16" }}
                ></div>
                <span>20–40%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#f59e0b" }}
                ></div>
                <span>40–60%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#ea580c" }}
                ></div>
                <span>60–80%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#dc2626" }}
                ></div>
                <span>80–100%</span>
              </div>
            </>
          )}
          {type === "rainfall" && (
            <>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-blue-800 rounded-full mr-2"></div>
                <span>High Intensity</span>
              </div>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-blue-400 rounded-full mr-2"></div>
                <span>Low Intensity</span>
              </div>
            </>
          )}
          {type === "reservoir" && (
            <>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#22c55e" }}
                ></div>
                <span>{"< 60%"}</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#f59e0b" }}
                ></div>
                <span>60–80%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#ea580c" }}
                ></div>
                <span>80–90%</span>
              </div>
              <div className="flex items-center text-xs">
                <div
                  className="w-3 h-3 rounded-full mr-2"
                  style={{ backgroundColor: "#dc2626" }}
                ></div>
                <span>{">= 90%"}</span>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
