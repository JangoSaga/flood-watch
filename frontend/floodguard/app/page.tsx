import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TrendingUp, AlertTriangle, BarChart3 } from 'lucide-react'
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Flood Prediction & Analysis System
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Advanced machine learning-powered flood prediction system providing real-time analysis, 
            damage assessment, and evacuation planning for disaster management across India.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="w-6 h-6 text-blue-600" />
              </div>
              <CardTitle>Interactive Plots</CardTitle>
              <CardDescription>
                Visualize flood predictions across cities with interactive scatter plots
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/plots">
                <Button className="w-full">View Plots</Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <TrendingUp className="w-6 h-6 text-red-600" />
              </div>
              <CardTitle>Heatmaps</CardTitle>
              <CardDescription>
                Explore damage analysis and flood risk intensity across regions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/heatmaps">
                <Button className="w-full">View Heatmaps</Button>
              </Link>
            </CardContent>
          </Card>


          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader className="text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
              <CardTitle>Predictions</CardTitle>
              <CardDescription>
                Get real-time flood predictions for specific cities and regions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/predict">
                <Button className="w-full">Get Predictions</Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Advanced ML-Powered Analysis
              </h2>
              <p className="text-gray-600 mb-6">
                Our system analyzes weather patterns, precipitation data, temperature, humidity,
                and historical flood data to provide accurate predictions for 56 cities across Maharashtra.
              </p>
              <div className="space-y-3">
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Real-time weather data integration</span>
                </div>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Machine learning flood classification</span>
                </div>
                
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-red-500 rounded-full mr-3"></div>
                  <span className="text-gray-700">Emergency response planning</span>
                </div>
              </div>
            </div>
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-8 text-white">
              <h3 className="text-2xl font-bold mb-4">System Coverage</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-3xl font-bold">56</div>
                  <div className="text-blue-100">Cities Covered</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">24/7</div>
                  <div className="text-blue-100">Monitoring</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">95%</div>
                  <div className="text-blue-100">Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">7</div>
                  <div className="text-blue-100">Day Forecast</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
