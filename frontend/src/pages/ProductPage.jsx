import React from 'react'
import { useParams } from 'react-router-dom'

const ProductPage = () => {
  const { id } = useParams()

  return (
    <div className="max-w-6xl mx-auto">
      <div className="card">
        <h1 className="text-3xl font-bold mb-4">Product Details</h1>
        <p className="text-gray-600">Product ID: {id}</p>
        <p className="mt-4 text-gray-500">
          Detailed product page coming soon...
        </p>
      </div>
    </div>
  )
}

export default ProductPage
