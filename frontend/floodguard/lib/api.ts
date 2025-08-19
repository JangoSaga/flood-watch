// API utility functions for connecting to Flask backend

const API_BASE_URL = "http://localhost:5000";

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  success: boolean;
}

export async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<ApiResponse<T>> {
  try {
    const url = `${API_BASE_URL}${endpoint}`;

    // Avoid forcing Content-Type on GET to prevent preflight
    const isGet = !options.method || options.method === "GET";
    const headers = {
      ...(isGet ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    } as HeadersInit;

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      return {
        success: false,
        error: `HTTP ${response.status}: ${errorText}`,
      };
    }

    const data = await response.json();
    return {
      success: true,
      data,
    };
  } catch (error) {
    console.error("API call failed:", error);
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error occurred",
    };
  }
}

// Specific API functions
export const api = {
  // Get list of cities (Flask: /api/data/cities)
  getCities: () => apiCall<any>("/api/data/cities"),

  // Get plotting data for maps (Flask: /api/data/plotting)
  getPlotsData: () => apiCall<any>("/api/data/plotting"),

  // Get risk zones data (Flask: /api/data/risk-zones)
  getHeatmapsData: () => apiCall<any>("/api/data/risk-zones"),

  // Get available dates and summaries (Flask: /api/data/dates)
  getAvailableDates: () => apiCall<any>("/api/data/dates"),

  // Forecast endpoints (available if needed by UI)
  get7DayForecast: () => apiCall<any>("/api/forecast/7day"),
  getDailySummary: () => apiCall<any>("/api/forecast/daily-summary"),
  getCitySummary: () => apiCall<any>("/api/forecast/city-summary"),
  // City forecast: /api/forecast/city/<city_name>
  getCityForecast: (city: string) => apiCall<any>(`/api/forecast/city/${encodeURIComponent(city)}`),
  // Date forecast: /api/forecast/date/<date>
  getDateForecast: (date: string) => apiCall<any>(`/api/forecast/date/${encodeURIComponent(date)}`),

  // Analysis endpoints (available if needed by UI)
  getAnalysisOverview: () => apiCall<any>("/api/analysis/overview"),
  getRiskDistribution: () => apiCall<any>("/api/analysis/risk-distribution"),

  // Health check
  healthCheck: () => apiCall<any>("/api/health"),
};

// Error handling utilities
export function handleApiError(error: any): string {
  if (typeof error === "string") {
    return error;
  }

  if (error?.message) {
    return error.message;
  }

  if (error?.error) {
    return error.error;
  }

  return "An unexpected error occurred";
}

// Fallback data for when API is unavailable
export const fallbackData = {
  cities: ["Delhi", "Mumbai", "Kolkata", "Bangalore", "Chennai"],
  prediction: {
    city: "Mumbai",
    status: "Unsafe",
    temperature: 85.5,
    maxTemperature: 83.4,
    windSpeed: 14.87,
    cloudCover: 45.2,
    precipitation: 12.3,
    humidity: 78.9,
  },
  plots: [
    {
      city: "Delhi",
      lat: 28.6139,
      lon: 77.209,
      precipitation: 25.5,
      prediction: 1,
    },
    {
      city: "Mumbai",
      lat: 19.076,
      lon: 72.8777,
      precipitation: 45.2,
      prediction: 1,
    },
    {
      city: "Kolkata",
      lat: 22.5726,
      lon: 88.3639,
      precipitation: 15.8,
      prediction: 0,
    },
    {
      city: "Bangalore",
      lat: 12.9716,
      lon: 77.5946,
      precipitation: 12.3,
      prediction: 0,
    },
    {
      city: "Chennai",
      lat: 13.0827,
      lon: 80.2707,
      precipitation: 35.7,
      prediction: 1,
    },
  ],
  heatmaps: [
    {
      city: "Delhi",
      lat: 28.6139,
      lon: 77.209,
      damage: 150000,
      prediction: 1,
      precipitation: 25.5,
    },
    {
      city: "Mumbai",
      lat: 19.076,
      lon: 72.8777,
      damage: 250000,
      prediction: 1,
      precipitation: 45.2,
    },
    {
      city: "Kolkata",
      lat: 22.5726,
      lon: 88.3639,
      damage: 80000,
      prediction: 0,
      precipitation: 15.8,
    },
    {
      city: "Bangalore",
      lat: 12.9716,
      lon: 77.5946,
      damage: 50000,
      prediction: 0,
      precipitation: 12.3,
    },
    {
      city: "Chennai",
      lat: 13.0827,
      lon: 80.2707,
      damage: 180000,
      prediction: 1,
      precipitation: 35.7,
    },
  ],
  satellite: {
    city: "Delhi",
    month: "July",
    precipitation: 24.5,
    cloudCover: 67,
    risk_category: "Moderate",
  },
};

