"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import { Thermometer, Wind, Cloud, Droplets, Eye, TrendingUp } from 'lucide-react'
import { api, fallbackData, handleApiError } from "@/lib/api"

export default function PredictPage() {
  const [selectedCity, setSelectedCity] = useState("")
  const [prediction, setPrediction] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [cities, setCities] = useState<string[]>([])
  const [citiesLoading, setCitiesLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCities()
  }, [])

  const fetchCities = async () => {
    try {
      const response = await api.getCities()
      if (response.success && response.data) {
        setCities(response.data)
      } else {
        console.warn('Using fallback cities:', response.error)
        setCities(fallbackData.cities)
      }
    } catch (err) {
      console.error('Error fetching cities:', err)
      setCities(fallbackData.cities)
    } finally {
      setCitiesLoading(false)
    }
  }

  const handlePredict = async () => {
    if (!selectedCity) return

    setLoading(true)
    setError(null)

    try {
      const response = await api.getPrediction(selectedCity)

      if (response.success && response.data) {
        setPrediction({
          city: selectedCity,
          status: response.data.prediction === "Safe" ? "Safe" : "Unsafe",
          temperature: response.data.temp || 0,
          maxTemperature: response.data.maxt || 0,
          windSpeed: response.data.wspd || 0,
          cloudCover: response.data.cloudcover || 0,
          precipitation: response.data.percip || 0,
          humidity: response.data.humidity || 0
        })
      } else {
        setError(handleApiError(response.error))
        // Use fallback data
        setPrediction({
          city: selectedCity,
          status: selectedCity === "Mumbai" ? "Unsafe" : "Safe",
          temperature: fallbackData.prediction.temperature,
          maxTemperature: fallbackData.prediction.maxTemperature,
          windSpeed: fallbackData.prediction.windSpeed,
          cloudCover: fallbackData.prediction.cloudCover,
          precipitation: fallbackData.prediction.precipitation,
          humidity: fallbackData.prediction.humidity
        })
      }
    } catch (err) {
      console.error('Error getting prediction:', err)
      setError(handleApiError(err))
      // Use fallback data
      setPrediction({
        city: selectedCity,
        status: selectedCity === "Mumbai" ? "Unsafe" : "Safe",
        temperature: fallbackData.prediction.temperature,
        maxTemperature: fallbackData.prediction.maxTemperature,
        windSpeed: fallbackData.prediction.windSpeed,
        cloudCover: fallbackData.prediction.cloudCover,
        precipitation: fallbackData.prediction.precipitation,
        humidity: fallbackData.prediction.humidity
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Flood Predictions</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Get real-time flood predictions for specific cities based on current weather conditions and ML analysis.
          </p>
        </div>

        <div className="max-w-2xl mx-auto mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Select City for Prediction</CardTitle>
              <CardDescription>
                Choose a city to get detailed weather analysis and flood risk assessment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedCity} onValueChange={setSelectedCity}>
                <SelectTrigger>
                  <SelectValue placeholder={citiesLoading ? "Loading cities..." : "Choose a city"} />
                </SelectTrigger>
                <SelectContent>
                  {cities.map((city) => (
                    <SelectItem key={city} value={city}>
                      {city}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                onClick={handlePredict}
                disabled={!selectedCity || loading}
                className="w-full"
              >
                {loading ? "Analyzing..." : "Get Prediction"}
              </Button>
            </CardContent>
          </Card>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6 max-w-2xl mx-auto">
            <p className="text-sm">
              <strong>Warning:</strong> {error} Using fallback data for demonstration.
            </p>
          </div>
        )}

        {prediction && (
          <div className="max-w-4xl mx-auto space-y-6">
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-2xl">
                  Information about {prediction.city}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-center mb-8">
                  <div className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${prediction.status === "Safe" ? "bg-green-100" : "bg-red-100"
                    }`}>
                    {prediction.status === "Safe" ? (
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
                      </svg>
                    )}
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Flood Prediction</h3>
                  <div className={`text-3xl font-bold mb-4 ${prediction.status === "Safe" ? "text-green-600" : "text-red-600"
                    }`}>
                    {prediction.status}
                  </div>
                  {prediction.status === "Unsafe" && (
                    <p className="text-gray-600 max-w-2xl mx-auto">
                      According to our ML model, this area has potential risk of flooding within the next 15 days.
                      Please take emergency measures.
                    </p>
                  )}
                  {prediction.status === "Safe" && (
                    <p className="text-gray-600 max-w-2xl mx-auto">
                      According to our ML model, this area has low risk of flooding in the next 15 days.
                      Continue monitoring weather conditions.
                    </p>
                  )}
                </div>

                <div className="grid md:grid-cols-3 gap-6">
                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <Thermometer className="w-6 h-6 text-red-600" />
                      </div>
                      <CardTitle className="text-lg">Temperature (°F)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.temperature}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <TrendingUp className="w-6 h-6 text-orange-600" />
                      </div>
                      <CardTitle className="text-lg">Max Temperature (°F)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.maxTemperature}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <Wind className="w-6 h-6 text-blue-600" />
                      </div>
                      <CardTitle className="text-lg">Windspeed (mph)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.windSpeed}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <Cloud className="w-6 h-6 text-gray-600" />
                      </div>
                      <CardTitle className="text-lg">Cloud Cover (%)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.cloudCover}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <Droplets className="w-6 h-6 text-blue-600" />
                      </div>
                      <CardTitle className="text-lg">Precipitation (mm)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.precipitation}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader className="text-center pb-2">
                      <div className="w-12 h-12 bg-teal-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                        <Eye className="w-6 h-6 text-teal-600" />
                      </div>
                      <CardTitle className="text-lg">Humidity (%)</CardTitle>
                    </CardHeader>
                    <CardContent className="text-center">
                      <div className="text-3xl font-bold text-gray-900">
                        {prediction.humidity}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
