"use client"

import dynamic from 'next/dynamic'

const MapComponent = dynamic(() => import('./map-component'), {
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
  damage?: number
  prediction: number
  precipitation: number
  reservoirFill?: number
}

interface FloodHeatmapProps {
  data: HeatmapData[]
  type?: 'flood' | 'rainfall' | 'reservoir'
}

export default function FloodHeatmap({ data, type = 'flood' }: FloodHeatmapProps) {
  return <MapComponent data={data} type={type} />
}
