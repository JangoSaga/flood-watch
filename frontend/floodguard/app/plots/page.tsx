"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { useEffect, useState } from "react"
import dynamic from 'next/dynamic'

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
}

export default function PlotsPage() {
  const [plotData, setPlotData] = useState<PlotData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPlotData()
  }, [])

  const fetchPlotData = async () => {
    try {
      // Replace with your Flask backend URL
      const response = await fetch('http://localhost:5000/api/plots')
      if (!response.ok) {
        throw new Error('Failed to fetch plot data')
      }
      const data = await response.json()
      setPlotData(data)
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

  const safeAreas = plotData.filter(item => item.prediction === 0).length
  const riskAreas = plotData.filter(item => item.prediction === 1).length

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

        <div className="grid md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Safe Areas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Low flood risk regions</span>
                </div>
                <span className="text-2xl font-bold text-green-600">{safeAreas}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">High Risk Areas</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-4 h-4 bg-red-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">High flood risk zones</span>
                </div>
                <span className="text-2xl font-bold text-red-600">{riskAreas}</span>
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
