"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import Image from "next/image"

const cities = ["Delhi", "Mumbai", "Kolkata", "Bangalore", "Chennai"]
const months = ["May", "June", "July"]

interface SatelliteData {
  city: string
  month: string
  precipitation: number
  cloudCover: number
  riskLevel: string
  temperature?: number
  humidity?: number
  reservoir_fill?: number
  reservoir_risk_score?: number
  reservoirs_above_danger?: number
  prediction?: number
  confidence?: number
  satelliteImage?: string
}

export default function SatellitePage() {
  const [selectedCity, setSelectedCity] = useState("Delhi")
  const [selectedMonth, setSelectedMonth] = useState("July")
  const [satelliteData, setSatelliteData] = useState<SatelliteData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFetchSatelliteData = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('http://localhost:5000/api/satellite', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city: selectedCity,
          month: selectedMonth
        })
      })

      if (!response.ok) {
        throw new Error('Failed to fetch satellite data')
      }

      const data = await response.json()
      // Normalize to UI-friendly shape using enhanced API fields
      setSatelliteData({
        city: selectedCity,
        month: selectedMonth,
        precipitation: data.precipitation ?? data.weather?.precipitation ?? 0,
        cloudCover: data.cloudCover ?? data.weather?.cloud_cover ?? 0,
        riskLevel: data.risk_category ?? data.riskLevel ?? 'Unknown',
        temperature: data.temperature ?? data.weather?.temp_avg,
        humidity: data.humidity ?? data.weather?.humidity,
        reservoir_fill: data.reservoir_fill,
        reservoir_risk_score: data.reservoir_risk_score,
        reservoirs_above_danger: data.reservoirs_above_danger,
        prediction: data.prediction,
        confidence: data.confidence,
        satelliteImage: data.satelliteImage,
      })
    } catch (err) {
      console.error('Error fetching satellite data:', err)
      setError('Failed to load satellite data from Flask backend')
      // Set fallback data
      setSatelliteData({
        city: selectedCity,
        month: selectedMonth,
        precipitation: 24.5,
        cloudCover: 67,
        riskLevel: 'Moderate'
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Satellite Data Analysis</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Access satellite imagery and precipitation data analysis for different cities and time periods.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Select City</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedCity} onValueChange={setSelectedCity}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a city" />
                </SelectTrigger>
                <SelectContent>
                  {cities.map((city) => (
                    <SelectItem key={city} value={city}>
                      {city}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Select Month</CardTitle>
            </CardHeader>
            <CardContent>
              <Select value={selectedMonth} onValueChange={setSelectedMonth}>
                <SelectTrigger>
                  <SelectValue placeholder="Choose a month" />
                </SelectTrigger>
                <SelectContent>
                  {months.map((month) => (
                    <SelectItem key={month} value={month}>
                      {month}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Load Data</CardTitle>
            </CardHeader>
            <CardContent>
              <Button
                onClick={handleFetchSatelliteData}
                disabled={loading}
                className="w-full"
              >
                {loading ? "Loading..." : "Fetch Satellite Data"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6">
            <p className="text-sm">{error}</p>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-2xl text-center">
              {selectedCity} in {selectedMonth} 2020
            </CardTitle>
            <CardDescription className="text-center">
              Satellite imagery showing precipitation patterns and weather conditions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {satelliteData?.satelliteImage ? (
              <div className="flex justify-center">
                <Image
                  src={`data:image/png;base64,${satelliteData.satelliteImage}`}
                  alt={`Satellite image of ${selectedCity}`}
                  width={600}
                  height={400}
                  className="rounded-lg"
                />
              </div>
            ) : (
              <div className="bg-gradient-to-br from-blue-100 to-green-100 rounded-lg p-8 min-h-[600px] flex items-center justify-center">
                <div className="text-center">
                  <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                    <svg className="w-10 h-10 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">
                    Satellite Data for {selectedCity}
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Processed satellite imagery for {selectedMonth} 2020
                  </p>
                  <p className="text-sm text-gray-500">
                    {satelliteData ? 'Satellite image not available for this city/month combination' : 'Click "Fetch Satellite Data" to load satellite information'}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {satelliteData && (
          <div className="grid md:grid-cols-3 gap-6 mt-8">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Precipitation Data</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600 mb-2">
                  {satelliteData.precipitation?.toFixed(1) || 'N/A'}mm
                </div>
                <p className="text-sm text-gray-600">Average rainfall for selected period</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Cloud Coverage</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-600 mb-2">
                  {satelliteData.cloudCover?.toFixed(0) || 'N/A'}%
                </div>
                <p className="text-sm text-gray-600">Average cloud cover percentage</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold mb-2 ${satelliteData.riskLevel === 'High' ? 'text-red-600' :
                    satelliteData.riskLevel === 'Moderate' ? 'text-orange-600' : 'text-green-600'
                  }`}>
                  {satelliteData.riskLevel || 'N/A'}
                </div>
                <p className="text-sm text-gray-600">Flood risk level for this region</p>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
