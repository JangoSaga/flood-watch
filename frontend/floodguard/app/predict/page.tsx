"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Button } from "@/components/ui/button"
import { useState, useEffect, useMemo } from "react"
import { Thermometer, Wind, Cloud, Droplets, Eye, TrendingUp } from 'lucide-react'
import { api, fallbackData, handleApiError } from "@/lib/api"

interface DayForecast {
  City: string
  Date: string
  Predicted_Flood_Risk: number
  Flood_Probability: number
  Weather_Precip?: number
  Max_Reservoir_Fill?: number
  Temperature?: number
  Humidity?: number
  Wind_Speed?: number
  Cloud_Cover?: number
}

interface UiPrediction {
  city: string
  date: string
  status: "Safe" | "Unsafe"
  probability: number
  temperature: number
  maxTemperature: number
  windSpeed: number
  cloudCover: number
  precipitation: number
  humidity: number
}

export default function PredictPage() {
  const [selectedCity, setSelectedCity] = useState("")
  const [prediction, setPrediction] = useState<UiPrediction | null>(null)
  const [loading, setLoading] = useState(false)
  const [cities, setCities] = useState<string[]>([])
  const [citiesLoading, setCitiesLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [cityForecast, setCityForecast] = useState<DayForecast[]>([])
  const [selectedDate, setSelectedDate] = useState<string>("")

  useEffect(() => {
    fetchCities()
  }, [])

  const fetchCities = async () => {
    try {
      const response = await api.getCities()
      const arr = Array.isArray((response as any)?.data?.cities)
        ? (response as any).data.cities
        : Array.isArray((response as any)?.data)
        ? (response as any).data
        : []
      if (Array.isArray(arr) && arr.length > 0) {
        setCities(arr as string[])
      } else {
        console.warn('Using fallback cities:', (response as any)?.error)
        setCities(fallbackData.cities)
      }
    } catch (err) {
      console.error('Error fetching cities:', err)
      setCities(fallbackData.cities)
    } finally {
      setCitiesLoading(false)
    }
  }

  const availableDates = useMemo(() => {
    const dates = Array.from(new Set(cityForecast.map(d => d.Date))).sort()
    return dates
  }, [cityForecast])

  const fetchCityForecast = async (city: string) => {
    setLoading(true)
    setError(null)
    setPrediction(null)
    setCityForecast([])
    setSelectedDate("")
    try {
      const res = await api.getCityForecast(city)
      if (res.success && res.data && Array.isArray(res.data.daily_forecasts)) {
        const list = res.data.daily_forecasts as DayForecast[]
        setCityForecast(list)
        const firstDate = Array.from(new Set(list.map(d => d.Date))).sort()[0]
        setSelectedDate(firstDate)
      } else {
        setError(handleApiError(res.error))
      }
    } catch (e) {
      console.error('Error fetching city forecast:', e)
      setError(handleApiError(e))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (selectedCity) {
      fetchCityForecast(selectedCity)
    }
  }, [selectedCity])

  useEffect(() => {
    if (!selectedDate || cityForecast.length === 0) return
    const day = cityForecast.find(d => d.Date === selectedDate)
    if (!day) return
    const status = (day.Predicted_Flood_Risk ?? 0) === 1 ? "Unsafe" : "Safe"
    const probability = Number(day.Flood_Probability ?? 0)
    setPrediction({
      city: day.City,
      date: day.Date,
      status,
      probability,
      temperature: Number(day.Temperature ?? 0),
      maxTemperature: Number(day.Temperature ?? 0),
      windSpeed: Number(day.Wind_Speed ?? 0),
      cloudCover: Number(day.Cloud_Cover ?? 0),
      precipitation: Number(day.Weather_Precip ?? 0),
      humidity: Number(day.Humidity ?? 0),
    })
  }, [selectedDate, cityForecast])

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Flood Predictions</h1>
          <p className="text-lg text-gray-600 max-w-3xl mx-auto">
            Explore 7-day forecasts. Select a city and a date to view flood probability and weather metrics.
          </p>
        </div>

        <div className="max-w-2xl mx-auto mb-8">
          <Card>
            <CardHeader>
              <CardTitle>Select City for Prediction</CardTitle>
              <CardDescription>
                Choose a city to get a 7-day forecast and flood risk assessment
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Select value={selectedCity} onValueChange={setSelectedCity}>
                <SelectTrigger>
                  <SelectValue placeholder={citiesLoading ? "Loading cities..." : "Choose a city"} />
                </SelectTrigger>
                <SelectContent>
                  {(cities || []).map((city) => (
                    <SelectItem key={city} value={city}>
                      {city}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedDate} onValueChange={setSelectedDate}>
                <SelectTrigger>
                  <SelectValue placeholder={!selectedCity ? "Select a city first" : (loading ? "Loading dates..." : (availableDates.length ? "Choose a date" : "No dates available"))} />
                </SelectTrigger>
                <SelectContent>
                  {availableDates.map((d) => (
                    <SelectItem key={d} value={d}>
                      {d}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </CardContent>
          </Card>
        </div>

        {error && (
          <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded mb-6 max-w-2xl mx-auto">
            <p className="text-sm">
              <strong>Warning:</strong> {error}
            </p>
          </div>
        )}

        {prediction && (
          <div className="max-w-4xl mx-auto space-y-6">
            <Card>
              <CardHeader className="text-center">
                <CardTitle className="text-2xl">
                  {prediction.city} — {prediction.date}
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
                  <div className={`text-3xl font-bold mb-2 ${prediction.status === "Safe" ? "text-green-600" : "text-red-600"
                    }`}>
                    {prediction.status}
                  </div>
                  <div className="text-gray-700 mb-4">Probability: <span className="font-semibold">{Math.round(prediction.probability * 100)}%</span></div>
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
