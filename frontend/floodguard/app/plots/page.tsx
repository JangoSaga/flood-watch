"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useEffect, useState } from "react"
import dynamic from 'next/dynamic'
import { api } from '@/lib/api'

// Dynamically import the map component to avoid SSR issues
const FloodPredictionMap = dynamic(() => import('@/components/flood-prediction-map'), {
  ssr: false,
  loading: () => (
    <div className="bg-gray-100 rounded-lg p-4 min-h-[600px] flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading map...</p>
      </div>
    </div>
  )
})

interface PlotData {
  city: string
  lat: number
  lon: number
  precipitation: number
  prediction: number
  riskCategory?: string
  probability?: number
  explanation?: string
}

export default function PlotsPage() {
  const [plotData, setPlotData] = useState<PlotData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [grouped, setGrouped] = useState<any[]>([])
  const [availableDates, setAvailableDates] = useState<string[]>([])
  const [selectedDate, setSelectedDate] = useState<string>("")

  useEffect(() => {
    fetchPlotData()
  }, [])

  const fetchPlotData = async () => {
    try {
      const { success, data, error } = await api.getPlotsData()
      if (!success || !data) throw new Error(error || 'Failed to fetch plot data')

      // With grouped-by-city default, backend returns { plotting_data: [{ City, coordinates?, days: [...] }], grouped: true }
      const groups = Array.isArray((data as any).plotting_data) ? (data as any).plotting_data : []
      if (groups.length === 0) throw new Error('Empty plotting data')

      setGrouped(groups)

      // Collect unique available dates from the grouped days
      const dateSet = new Set<string>()
      for (const g of groups) {
        const days = Array.isArray(g.days) ? g.days : []
        for (const d of days) {
          if (d?.Date) dateSet.add(String(d.Date))
        }
      }
      const sortedDates = Array.from(dateSet).sort()
      setAvailableDates(sortedDates)

      // Pick latest by default
      const defaultDate = sortedDates[sortedDates.length - 1]
      setSelectedDate(defaultDate)

      // Build plot data for the default date
      const mapped: PlotData[] = buildPlotDataForDate(groups, defaultDate)
      setPlotData(mapped)
    } catch (err) {
      console.error('Error fetching plot data:', err)
      setError('Failed to load plot data. Using sample data.')
      // Fallback sample data
      setPlotData([
        { city: "Delhi", lat: 28.6139, lon: 77.2090, precipitation: 25.5, prediction: 1 },
        { city: "Mumbai", lat: 19.0760, lon: 72.8777, precipitation: 45.2, prediction: 1 },
        { city: "Kolkata", lat: 22.5726, lon: 88.3639, precipitation: 15.8, prediction: 0 },
        { city: "Bangalore", lat: 12.9716, lon: 77.5946, precipitation: 12.3, prediction: 0 },
        { city: "Chennai", lat: 13.0827, lon: 80.2707, precipitation: 35.7, prediction: 1 },
      ])
    } finally {
      setLoading(false)
    }
  }

  const buildPlotDataForDate = (groups: any[], date: string): PlotData[] => {
    const out: PlotData[] = []
    for (const g of groups) {
      const days = Array.isArray(g.days) ? g.days : []
      const day = days.find((d: any) => String(d.Date) === date) || null
      if (!day) continue
      out.push({
        city: String(g.City ?? day.City ?? ''),
        lat: Number(day.Latitude),
        lon: Number(day.Longitude),
        precipitation: Number(day.Precipitation ?? day.Weather_Precip ?? 0),
        prediction: Number(day.Flood_Risk ?? day.Predicted_Flood_Risk ?? 0),
        riskCategory: String(day.Risk_Category ?? ''),
        probability: Number(day.Flood_Probability ?? 0),
        explanation: typeof day.explanation === 'string' ? day.explanation : undefined,
      })
    }
    return out
  }

  const categorize = (rc?: string, pred?: number) => {
    const v = (rc || '').toString().trim().toLowerCase()
    if (v) return v
    // fallback from binary prediction
    return pred === 1 ? 'high' : 'low'
  }
  const counts = plotData.reduce(
    (acc, it) => {
      const c = categorize(it.riskCategory, it.prediction)
      if (c === 'critical') acc.critical++
      else if (c === 'high') acc.high++
      else if (c === 'medium') acc.medium++
      else acc.low++
      return acc
    },
    { low: 0, medium: 0, high: 0, critical: 0 }
  )

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Interactive Plots</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            The visualizations show flood predictions, damage predictions, and heavy rainfall predictions across India, 
            taking in factors such as precipitation, wind speed, humidity, temperature, cloud cover, as well as previous data history.
          </p>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Flood Prediction</CardTitle>
            <CardDescription className="text-center">
              The plot below shows our ML-powered prediction of where a flood is most likely to occur, marked primarily by the red dots.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Date selector */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 mb-4">
              <label className="text-sm text-gray-700">
                Select date:
              </label>
              <select
                className="border rounded px-3 py-2 text-sm w-full md:w-auto"
                value={selectedDate}
                onChange={(e) => {
                  const newDate = e.target.value
                  setSelectedDate(newDate)
                  setPlotData(buildPlotDataForDate(grouped, newDate))
                }}
              >
                {availableDates.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            {loading ? (
              <div className="bg-gray-100 rounded-lg p-4 min-h-[600px] flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Loading flood prediction data...</p>
                </div>
              </div>
            ) : (
              <FloodPredictionMap data={plotData} />
            )}
          </CardContent>
        </Card>

        <div className="grid md:grid-cols-5 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Low</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Low risk regions</span>
                </div>
                <span className="text-2xl font-bold text-green-600">{counts.low}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Medium</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-amber-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Medium risk zones</span>
                </div>
                <span className="text-2xl font-bold text-amber-600">{counts.medium}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">High</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-red-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">High risk zones</span>
                </div>
                <span className="text-2xl font-bold text-red-600">{counts.high}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Critical</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-red-900 rounded-full mr-3"></div>
                  <span className="text-gray-700">Critical risk zones</span>
                </div>
                <span className="text-2xl font-bold text-red-900">{counts.critical}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Total Cities</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-blue-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Cities monitored</span>
                </div>
                <span className="text-2xl font-bold text-blue-600">{plotData.length}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
