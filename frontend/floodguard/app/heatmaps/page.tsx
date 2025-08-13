"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useEffect, useState } from "react"
import dynamic from 'next/dynamic'

const DamageHeatmap = dynamic(() => import('@/components/damage-heatmap'), {
  ssr: false,
  loading: () => (
    <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  )
})

const FloodHeatmap = dynamic(() => import('@/components/flood-heatmap'), {
  ssr: false,
  loading: () => (
    <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
    </div>
  )
})

interface HeatmapData {
  city: string
  lat: number
  lon: number
  damage: number
  prediction: number
  precipitation: number
}

export default function HeatmapsPage() {
  const [heatmapData, setHeatmapData] = useState<HeatmapData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchHeatmapData()
  }, [])

  const fetchHeatmapData = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/heatmaps')
      if (!response.ok) {
        throw new Error('Failed to fetch heatmap data')
      }
      const data = await response.json()
      setHeatmapData(data)
    } catch (err) {
      console.error('Error fetching heatmap data:', err)
      setError('Failed to load heatmap data. Using sample data.')
      // Fallback sample data
      setHeatmapData([
        { city: "Delhi", lat: 28.6139, lon: 77.2090, damage: 150000, prediction: 1, precipitation: 25.5 },
        { city: "Mumbai", lat: 19.0760, lon: 72.8777, damage: 250000, prediction: 1, precipitation: 45.2 },
        { city: "Kolkata", lat: 22.5726, lon: 88.3639, damage: 80000, prediction: 0, precipitation: 15.8 },
        { city: "Bangalore", lat: 12.9716, lon: 77.5946, damage: 50000, prediction: 0, precipitation: 12.3 },
        { city: "Chennai", lat: 13.0827, lon: 80.2707, damage: 180000, prediction: 1, precipitation: 35.7 },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Interactive Heatmaps</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            The heatmaps show flood predictions, damage predictions, and heavy rainfall predictions across India, 
            taking in factors such as precipitation, wind speed, humidity, temperature, cloud cover, as well as previous data history.
          </p>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Tabs defaultValue="damage" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="damage">Damage Analysis</TabsTrigger>
            <TabsTrigger value="flood">Flood Prediction</TabsTrigger>
            <TabsTrigger value="rainfall">Rainfall Intensity</TabsTrigger>
          </TabsList>

          <TabsContent value="damage" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">Damage Analysis</CardTitle>
                <CardDescription className="text-center">
                  The plot below shows cost and damage analysis, based on the flood risk prediction. 
                  The colorscale of the heatmap indicates the extent of predicted monetary damage, measured in USD.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <DamageHeatmap data={heatmapData} />
                )}
                <div className="flex justify-center mt-4">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">Low Damage</span>
                    <div className="w-32 h-4 bg-gradient-to-r from-blue-200 to-red-500 rounded"></div>
                    <span className="text-sm text-gray-600">High Damage</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="flood" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">Flood Prediction</CardTitle>
                <CardDescription className="text-center">
                  The plot below shows our ML-powered prediction of where a flood is going to occur, 
                  marked by red areas with higher intensity indicating higher risk.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                  </div>
                ) : (
                  <FloodHeatmap data={heatmapData} />
                )}
                <div className="flex justify-center mt-4">
                  <div className="flex items-center space-x-4">
                    <span className="text-sm text-gray-600">Safe</span>
                    <div className="w-32 h-4 bg-gradient-to-r from-green-200 to-red-500 rounded"></div>
                    <span className="text-sm text-gray-600">High Risk</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="rainfall" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl text-center">Rainfall Intensity</CardTitle>
                <CardDescription className="text-center">
                  Heavy rainfall predictions and precipitation analysis across different regions.
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
        </Tabs>
      </div>
    </div>
  )
}
