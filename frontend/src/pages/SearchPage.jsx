import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import SearchInput from '../components/SearchInput'
import { queryText } from '../services/api'
import Skeleton from 'react-loading-skeleton'
import 'react-loading-skeleton/dist/skeleton.css'

const SearchPage = () => {
  const location = useLocation()
  const [results, setResults] = useState(location.state?.results || null)
  const [query, setQuery] = useState(location.state?.query || '')
  const [loading, setLoading] = useState(false)

  const handleSearch = async (newQuery) => {
    setLoading(true)
    setQuery(newQuery)
    try {
      const data = await queryText(newQuery)
      setResults(data)
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      {/* Search Bar */}
      <div className="mb-8">
        <SearchInput
          onSearch={handleSearch}
          placeholder="Refine your search..."
          loading={loading}
        />
      </div>

      {/* Results Info */}
      {results && (
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Search Results</h2>
          <p className="text-gray-600 mt-1">
            Found {results.products?.length || 0} products
            {query && ` for "${query}"`}
            {results.processing_time_ms && (
              <span className="text-gray-400 ml-2">
                ({(results.processing_time_ms / 1000).toFixed(2)}s)
              </span>
            )}
          </p>
          {results.message && (
            <p className="mt-2 text-blue-600 italic">{results.message}</p>
          )}
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="card">
              <Skeleton height={200} />
              <Skeleton count={3} className="mt-4" />
            </div>
          ))}
        </div>
      )}

      {/* Results Grid */}
      {!loading && results && results.products && results.products.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.products.map((product, index) => (
            <ProductCard
              key={product.product?.id || index}
              product={product}
              matchScore={product.match_score}
              matchReason={product.match_reason}
            />
          ))}
        </div>
      )}

      {/* No Results */}
      {!loading && results && results.products?.length === 0 && (
        <div className="text-center py-12">
          <p className="text-xl text-gray-600">No products found</p>
          <p className="text-gray-500 mt-2">Try a different search term</p>
        </div>
      )}
    </div>
  )
}

export default SearchPage
