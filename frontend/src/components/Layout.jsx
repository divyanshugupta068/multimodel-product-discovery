import React from 'react'
import { Link } from 'react-router-dom'
import { MagnifyingGlassIcon, HomeIcon, ScaleIcon } from '@heroicons/react/24/outline'

const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center">
                <MagnifyingGlassIcon className="h-8 w-8 text-blue-600" />
                <span className="ml-2 text-xl font-bold text-gray-900">
                  Product Discovery
                </span>
              </Link>
            </div>
            
            <div className="flex items-center space-x-4">
              <Link
                to="/"
                className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600 transition-colors"
              >
                <HomeIcon className="h-5 w-5 mr-1" />
                Home
              </Link>
              <Link
                to="/search"
                className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600 transition-colors"
              >
                <MagnifyingGlassIcon className="h-5 w-5 mr-1" />
                Search
              </Link>
              <Link
                to="/compare"
                className="flex items-center px-3 py-2 text-gray-700 hover:text-blue-600 transition-colors"
              >
                <ScaleIcon className="h-5 w-5 mr-1" />
                Compare
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>© 2025 Multimodal Product Discovery. AI-powered product search.</p>
            <p className="mt-1">
              Powered by GPT-4 Vision, Claude 3.5, and Whisper
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default Layout
