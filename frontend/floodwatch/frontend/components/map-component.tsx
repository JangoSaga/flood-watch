"use client";

import { useEffect, useRef } from "react";

interface MapData {
  city: string;
  lat: number;
  lon: number;
  precipitation?: number;
  prediction?: number;
  damage?: number;
}

interface MapComponentProps {
  data: MapData[];
  type: "prediction" | "damage" | "flood" | "rainfall";
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
      .then((mod) => {
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
      .then((mod) => {
        const L = (mod as any).default || (mod as any);
        // Clear existing layers
        mapInstanceRef.current.eachLayer((layer: any) => {
          if (layer instanceof L.Marker || layer instanceof L.Circle) {
            mapInstanceRef.current.removeLayer(layer);
          }
        });

        addDataToMap(L, mapInstanceRef.current, data, type);
      })
      .catch((error) => {
        console.error("Error updating map:", error);
      });
  }, [data, type]);

  const addDataToMap = (L: any, map: any, data: MapData[], type: string) => {
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

  const addPredictionMarker = (L: any, map: any, item: MapData) => {
    const isHighRisk = item.prediction === 1;

    const icon = L.divIcon({
      className: "custom-marker",
      html: `<div style="
				width: 12px;
				height: 12px;
				border-radius: 50%;
				background-color: ${isHighRisk ? "#ef4444" : "#22c55e"};
				border: 2px solid white;
				box-shadow: 0 2px 4px rgba(0,0,0,0.3);
			"></div>`,
      iconSize: [12, 12],
      iconAnchor: [6, 6],
    });

    const marker = L.marker([item.lat, item.lon], { icon })
      .bindPopup(
        `
				<div style="padding: 8px;">
					<h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${item.city
        }</h3>
					<p style="font-size: 14px; margin: 2px 0;">
						<strong>Status:</strong> 
						<span style="font-weight: 500; color: ${isHighRisk ? "#dc2626" : "#16a34a"
        };">
							${isHighRisk ? "High Risk" : "Safe"}
						</span>
					</p>
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
				<h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${item.city
        }</h3>
				<p style="font-size: 14px; margin: 2px 0;"><strong>Estimated Damage:</strong> $${(
          item.damage || 0
        ).toLocaleString()}</p>
				<p style="font-size: 14px; margin: 2px 0;"><strong>Risk Level:</strong> ${item.prediction === 1 ? "High" : "Low"
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
    const getValue = (item: MapData) => {
      return type === "rainfall"
        ? item.precipitation || 0
        : item.prediction || 0;
    };

    const value = getValue(item);
    const maxValue =
      type === "rainfall"
        ? Math.max(...allData.map((d) => d.precipitation || 0))
        : 1;

    const intensity = type === "rainfall" ? value / maxValue : value;

    const getColor = (intensity: number, type: string) => {
      if (type === "rainfall") {
        if (intensity > 0.8) return "#1e40af";
        if (intensity > 0.6) return "#2563eb";
        if (intensity > 0.4) return "#3b82f6";
        if (intensity > 0.2) return "#60a5fa";
        return "#dbeafe";
      } else {
        return intensity > 0.5 ? "#dc2626" : "#22c55e";
      }
    };

    const radius =
      type === "rainfall"
        ? Math.max(intensity * 30000, 8000)
        : item.prediction === 1
          ? 25000
          : 15000;

    const circle = L.circle([item.lat, item.lon], {
      color: getColor(intensity, type),
      fillColor: getColor(intensity, type),
      fillOpacity: type === "rainfall" ? 0.7 : 0.6,
      radius: radius,
    })
      .bindPopup(
        `
			<div style="padding: 8px;">
				<h3 style="font-weight: bold; font-size: 16px; margin-bottom: 4px;">${item.city
        }</h3>
				${type === "rainfall"
          ? `<p style="font-size: 14px; margin: 2px 0;"><strong>Precipitation:</strong> ${(
            item.precipitation || 0
          ).toFixed(1)}mm</p>`
          : `<p style=\"font-size: 14px; margin: 2px 0;\"><strong>Flood Risk:</strong> ${item.prediction === 1 ? "High" : "Low"
          }</p>`
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
                <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                <span>Safe Areas</span>
              </div>
              <div className="flex items-center text-xs">
                <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
                <span>High Risk Areas</span>
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
          {(type === "flood" || type === "rainfall") && (
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
        </div>
      </div>
    </div>
  );
}
