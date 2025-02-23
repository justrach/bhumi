import { ImageResponse } from 'next/og'

// Route segment config
export const runtime = 'edge'

export const contentType = 'image/png'

// Image metadata
export const size = {
  width: 32,
  height: 32,
}

// Image generation
export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          background: 'hsl(15, 85%, 70%)',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          fontSize: 20,
        }}
      >
        🌍
      </div>
    ),
    size
  )
} 