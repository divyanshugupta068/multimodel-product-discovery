import React from 'react'
import { Link } from 'react-router-dom'
import { StarIcon, ShoppingCartIcon } from '@heroicons/react/24/solid'
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline'

const ProductCard = ({ product, matchScore, matchReason }) => {
  const { id, name, description, images, category, features } = product.product || product
  const bestPrice = product.product?.best_price || product.best_price
  
  const renderRating = (rating) => {
    const stars = []
    for (let i = 1; i <= 5; i++) {
      stars.push(
        i <= rating ? (
          <StarIcon key={i} className="h-4 w-4 text-yellow-400" />
        ) : (
          <StarOutlineIcon key={i} className="h-4 w-4 text-gray-300" />
        )
      )
    }
    return stars
  }

  return (
    <div className="card group hover:shadow-xl transition-all duration-200">
      {/* Image */}
      <div className="relative overflow-hidden rounded-lg bg-gray-200 h-48 mb-4">
        {images && images.length > 0 ? (
          <img
            src={images[0]}
            alt={name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            onError={(e) => {
              e.target.src = 'https://via.placeholder.com/300x200?text=No+Image'
            }}
          />
        ) : (
          <div className="flex items-center justify-center h-full">
            <span className="text-gray-400">No image</span>
          </div>
        )}
        
        {matchScore && (
          <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-bold">
            {Math.round(matchScore * 100)}% match
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1">
        {/* Category & Brand */}
        <div className="flex items-center gap-2 mb-2">
          <span className="badge badge-info text-xs">{category}</span>
          {features?.brand && (
            <span className="text-xs text-gray-500">{features.brand}</span>
          )}
        </div>

        {/* Title */}
        <Link to={`/product/${id}`}>
          <h3 className="font-semibold text-gray-900 mb-2 hover:text-blue-600 transition-colors line-clamp-2">
            {name}
          </h3>
        </Link>

        {/* Description */}
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{description}</p>

        {/* Match Reason */}
        {matchReason && (
          <p className="text-xs text-blue-600 mb-3 italic">{matchReason}</p>
        )}

        {/* Rating */}
        <div className="flex items-center gap-1 mb-3">
          {renderRating(4)}
          <span className="text-xs text-gray-500 ml-1">(128)</span>
        </div>

        {/* Price & Actions */}
        <div className="flex items-center justify-between">
          <div>
            {bestPrice && (
              <>
                <p className="text-2xl font-bold text-gray-900">
                  ${bestPrice.amount?.toFixed(2) || bestPrice.toFixed(2)}
                </p>
                {bestPrice.retailer && (
                  <p className="text-xs text-gray-500">at {bestPrice.retailer}</p>
                )}
              </>
            )}
          </div>
          
          <button className="p-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <ShoppingCartIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ProductCard
