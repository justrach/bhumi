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
          background: 'linear-gradient(135deg, #fff7ed 0%, #ffffff 50%, #fef3e2 100%)',
          padding: '60px 40px',
          position: 'relative',
        }}
      >
        {/* Background decorative elements */}
        <div
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background: 'rgba(255, 154, 72, 0.1)',
            filter: 'blur(40px)',
          }}
        />
        <div
          style={{
            position: 'absolute',
            bottom: '40px',
            left: '40px',
            width: '80px',
            height: '80px',
            borderRadius: '50%',
            background: 'rgba(255, 154, 72, 0.15)',
            filter: 'blur(30px)',
          }}
        />

        {/* Main content */}
        <div 
          style={{
            display: 'flex',
            fontSize: 88,
            fontWeight: 900,
            letterSpacing: '-0.06em',
            lineHeight: 0.9,
            marginBottom: 16,
            alignItems: 'center',
            gap: '16px',
            textAlign: 'center',
          }}
        >
          <span style={{ color: '#1f2937' }}>Meet</span>
          <span 
            style={{ 
              color: 'hsl(15, 85%, 62%)',
              background: 'linear-gradient(135deg, hsl(15, 85%, 62%) 0%, hsl(15, 85%, 55%) 100%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            Bhumi
          </span>
        </div>
        
        <div style={{ 
          display: 'flex',
          color: 'hsl(15, 85%, 60%)',
          fontSize: 54,
          fontWeight: 700,
          marginBottom: 32,
          letterSpacing: '-0.02em',
        }}>
          भूमि
        </div>

        <div style={{
          display: 'flex',
          fontSize: 32,
          color: '#4b5563',
          textAlign: 'center',
          maxWidth: '900px',
          justifyContent: 'center',
          marginBottom: 40,
          lineHeight: 1.2,
          fontWeight: 500,
        }}>
          The <span style={{ color: 'hsl(15, 85%, 55%)', fontWeight: 700 }}>blazing-fast</span> AI inference client for Python
        </div>

        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
        }}>
          {/* Install command */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '16px 32px',
            backgroundColor: '#f9fafb',
            border: '2px solid #e5e7eb',
            borderRadius: '12px',
            fontFamily: 'monospace',
            fontSize: 28,
            fontWeight: 600,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}>
            <span style={{ color: '#9ca3af' }}>$</span>
            <span style={{ color: '#374151' }}>pip install bhumi</span>
          </div>

          {/* Stats */}
          <div style={{
            display: 'flex',
            gap: '40px',
            alignItems: 'center',
          }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: 'hsl(15, 85%, 55%)' }}>3x</span>
              <span style={{ fontSize: 16, color: '#6b7280' }}>Faster</span>
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: 'hsl(15, 85%, 55%)' }}>60%</span>
              <span style={{ fontSize: 16, color: '#6b7280' }}>Less Memory</span>
            </div>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
            }}>
              <span style={{ fontSize: 28, fontWeight: 700, color: 'hsl(15, 85%, 55%)' }}>4+</span>
              <span style={{ fontSize: 16, color: '#6b7280' }}>AI Providers</span>
            </div>
          </div>
        </div>

        {/* Bottom attribution */}
        <div style={{
          position: 'absolute',
          bottom: '24px',
          right: '40px',
          fontSize: 18,
          color: '#9ca3af',
          fontWeight: 500,
        }}>
          Built by Trilok.ai
        </div>
      </div>
    ),
    {
      width: 1200,
      height: 630,
    }
  )
}