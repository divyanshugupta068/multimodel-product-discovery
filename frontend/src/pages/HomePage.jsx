import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import SearchInput from '../components/SearchInput'
import ImageUpload from '../components/ImageUpload'
import VoiceRecorder from '../components/VoiceRecorder'
import { queryText, queryImage, queryVoice } from '../services/api'
import { toast } from 'react-toastify'
import { PhotoIcon, MicrophoneIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'

const HomePage = () => {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('text')

  const handleTextSearch = async (query) => {
    setLoading(true)
    try {
      const results = await queryText(query)
      navigate('/search', { state: { results, query } })
    } catch (error) {
      toast.error('Search failed. Please try again.')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleImageSearch = async (imageFile) => {
    if (!imageFile) return
    setLoading(true)
    try {
      const results = await queryImage(imageFile)
      navigate('/search', { state: { results, query: 'Image search' } })
    } catch (error) {
      toast.error('Image search failed. Please try again.')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleVoiceSearch = async (audioBlob) => {
    setLoading(true)
    try {
      const results = await queryVoice(audioBlob)
      navigate('/search', { state: { results, query: results.message } })
    } catch (error) {
      toast.error('Voice search failed. Please try again.')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Discover Products Naturally
        </h1>
        <p className="text-xl text-gray-600">
          Search using text, images, or voice powered by AI
        </p>
      </div>

      {/* Search Tabs */}
      <div className="card">
        <div className="flex border-b border-gray-200 mb-6">
          <button
            onClick={() => setActiveTab('text')}
            className={`flex items-center px-6 py-3 font-medium transition-colors ${
              activeTab === 'text'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
            Text Search
          </button>
          <button
            onClick={() => setActiveTab('image')}
            className={`flex items-center px-6 py-3 font-medium transition-colors ${
              activeTab === 'image'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <PhotoIcon className="h-5 w-5 mr-2" />
            Image Search
          </button>
          <button
            onClick={() => setActiveTab('voice')}
            className={`flex items-center px-6 py-3 font-medium transition-colors ${
              activeTab === 'voice'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <MicrophoneIcon className="h-5 w-5 mr-2" />
            Voice Search
          </button>
        </div>

        {/* Tab Content */}
        <div className="py-6">
          {activeTab === 'text' && (
            <div>
              <h3 className="text-lg font-medium mb-4">Search by typing</h3>
              <SearchInput onSearch={handleTextSearch} loading={loading} />
              <div className="mt-4">
                <p className="text-sm text-gray-500 mb-2">Try searching for:</p>
                <div className="flex flex-wrap gap-2">
                  {['red leather jacket', 'iPhone 15 Pro', 'wireless headphones', 'running shoes'].map((term) => (
                    <button
                      key={term}
                      onClick={() => handleTextSearch(term)}
                      className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'image' && (
            <div>
              <h3 className="text-lg font-medium mb-4">Upload an image</h3>
              <ImageUpload onImageSelect={handleImageSearch} />
              <p className="mt-4 text-sm text-gray-500 text-center">
                Upload a photo of a product to find similar items
              </p>
            </div>
          )}

          {activeTab === 'voice' && (
            <div>
              <h3 className="text-lg font-medium mb-4 text-center">Speak your query</h3>
              <VoiceRecorder onRecordingComplete={handleVoiceSearch} />
              <p className="mt-4 text-sm text-gray-500 text-center">
                Click the microphone and describe what you're looking for
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Features */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="text-center">
          <div className="bg-blue-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <MagnifyingGlassIcon className="h-8 w-8 text-blue-600" />
          </div>
          <h3 className="font-semibold mb-2">Smart Search</h3>
          <p className="text-sm text-gray-600">AI-powered semantic search understands what you mean</p>
        </div>
        <div className="text-center">
          <div className="bg-purple-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <PhotoIcon className="h-8 w-8 text-purple-600" />
          </div>
          <h3 className="font-semibold mb-2">Visual Recognition</h3>
          <p className="text-sm text-gray-600">Find products by uploading images using GPT-4V</p>
        </div>
        <div className="text-center">
          <div className="bg-green-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <MicrophoneIcon className="h-8 w-8 text-green-600" />
          </div>
          <h3 className="font-semibold mb-2">Voice Commands</h3>
          <p className="text-sm text-gray-600">Search naturally using voice with Whisper AI</p>
        </div>
      </div>
    </div>
  )
}

export default HomePage
