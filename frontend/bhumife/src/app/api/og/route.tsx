import { ImageResponse } from 'next/og'

export const runtime = 'edge'

export async function GET() {
  return new ImageResponse(
    (
      <div
        style={{
          height: '100%',
          width: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'white',
          padding: '40px',
        }}
      >
        <div 
          style={{
            display: 'flex',
            fontSize: 80,
            fontWeight: 800,
            letterSpacing: '-0.05em',
            lineHeight: 0.9,
            marginBottom: 20,
            alignItems: 'center',
            gap: '12px',
          }}
        >
          <span>Meet</span>
          <span style={{ color: 'hsl(15, 85%, 70%)' }}>Bhumi</span>
        </div>
        <div style={{ 
          display: 'flex',
          color: 'hsl(15, 85%, 70%)',
          fontSize: 60,
          fontWeight: 700,
          marginBottom: 20,
        }}>
          भूमि
        </div>
        <div style={{
          display: 'flex',
          fontSize: 28,
          color: '#666',
          textAlign: 'center',
          maxWidth: '800px',
          justifyContent: 'center',
          marginBottom: 32,
        }}>
          The fastest and most efficient AI inference client for Python
        </div>
        <div style={{
          display: 'flex',
          gap: '8px',
          padding: '12px 24px',
          backgroundColor: '#f1f1f1',
          borderRadius: '8px',
          fontFamily: 'monospace',
          fontSize: 24,
        }}>
          <span style={{ color: '#888' }}>$</span>
          <span>pip install bhumi</span>
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  )
} 