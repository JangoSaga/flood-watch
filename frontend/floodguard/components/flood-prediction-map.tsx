"use client"

import { useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'

// Import Leaflet dynamically to avoid SSR issues
const MapComponent = dynamic(() => import('./map-component'), {
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

interface FloodPredictionMapProps {
  data: PlotData[]
}

export default function FloodPredictionMap({ data }: FloodPredictionMapProps) {
  return <MapComponent data={data} type="prediction" />
}
