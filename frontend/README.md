# Frontend - Multimodal Product Discovery

React frontend for the multimodal product discovery system.

## Setup

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

## Build for Production

```bash
npm run build
```

## Features

- **Text Search**: Type queries naturally
- **Image Upload**: Drag and drop or click to upload product images
- **Voice Recording**: Click-to-record voice commands
- **Product Cards**: Display search results with pricing and details
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- React 18
- Vite
- Tailwind CSS
- React Router
- Axios
- Heroicons
- React Toastify
- React Dropzone

## Project Structure

```
frontend/
├── src/
│   ├── components/       # Reusable components
│   ├── pages/           # Page components
│   ├── services/        # API services
│   ├── hooks/           # Custom React hooks
│   ├── utils/           # Utility functions
│   ├── App.jsx          # Main app component
│   └── main.jsx         # Entry point
├── public/              # Static assets
└── package.json
```
