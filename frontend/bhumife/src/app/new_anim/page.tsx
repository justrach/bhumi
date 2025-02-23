'use client'
import { motion, useAnimation } from "framer-motion";
import { useEffect, useState } from "react";

export default function BufferAnimation() {
  const packetCount = 8;
  const coralRed = "#FF6F61";
  const [isPlaying, setIsPlaying] = useState(true);

  // Animation controls
  const serverControls = useAnimation();
  const resetAnimation = async () => {
    setIsPlaying(false);
    await Promise.all([serverControls.stop()]);
    // Reset all animations
    setTimeout(() => setIsPlaying(true), 100);
  };

  return (
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#f5f5f5",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "40px",
      fontFamily: "system-ui, -apple-system, sans-serif",
    }}>
      <h1 style={{
        color: coralRed,
        fontSize: "2.5rem",
        marginBottom: "20px",
      }}>
        Bhumi: Accelerated LLM Inference
      </h1>
      
      <div style={{
        display: "flex",
        gap: "20px",
        marginBottom: "40px",
      }}>
        <button
          onClick={resetAnimation}
          style={{
            padding: "10px 20px",
            backgroundColor: coralRed,
            color: "white",
            border: "none",
            borderRadius: "5px",
            cursor: "pointer",
          }}
        >
          Replay Animation
        </button>
      </div>

      {/* Main Animation Container */}
      <div style={{
        position: "relative",
        width: "1000px",
        height: "500px",
        backgroundColor: "#fff",
        borderRadius: "15px",
        boxShadow: "0 4px 20px rgba(0,0,0,0.1)",
        padding: "20px",
        overflow: "visible",
      }}>
        {/* System Components */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          height: "100%",
          padding: "20px",
        }}>
          {/* LLM Server (e.g., Grok) */}
          <div style={{
            width: "150px",
            height: "400px",
            border: "2px solid #444",
            borderRadius: "10px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "10px",
          }}>
            <h3>LLM Server</h3>
            <div style={{
              marginTop: "10px",
              width: "100%",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}>
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={`gpu-${i}`}
                  style={{
                    backgroundColor: "#2a2a2a",
                    color: "white",
                    padding: "5px",
                    borderRadius: "5px",
                    textAlign: "center",
                    fontSize: "0.8rem",
                  }}
                >
                  H100 GPU
                </div>
              ))}
            </div>
          </div>

          {/* Traditional vs Bhumi Comparison */}
          <div style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            gap: "40px",
            margin: "0 40px",
          }}>
            {/* Traditional Buffer */}
            <div style={{
              position: "relative",
              height: "150px",
              border: "2px solid #1E90FF",
              borderRadius: "10px",
              padding: "10px",
            }}>
              <h3 style={{ color: "#1E90FF" }}>Traditional Buffer</h3>
              <div style={{
                position: "absolute",
                left: "50%",
                top: "50%",
                transform: "translate(-50%, -50%)",
                width: "200px",
                height: "60px",
                border: "2px dashed #1E90FF",
                borderRadius: "5px",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}>
                Fixed Buffer Size
              </div>
            </div>

            {/* Bhumi Buffer */}
            <div style={{
              position: "relative",
              height: "150px",
              border: `2px solid ${coralRed}`,
              borderRadius: "10px",
              padding: "10px",
            }}>
              <h3 style={{ color: coralRed }}>Bhumi Buffer</h3>
              <motion.div
                animate={{
                  width: ["100px", "300px", "150px"],
                  x: [0, -100, -25],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "50%",
                  transform: "translate(-50%, -50%)",
                  height: "60px",
                  border: `2px dashed ${coralRed}`,
                  borderRadius: "5px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                }}
              >
                Dynamic Buffer Size
              </motion.div>
            </div>
          </div>

          {/* Client */}
          <div style={{
            width: "150px",
            height: "400px",
            border: "2px solid #444",
            borderRadius: "10px",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            padding: "10px",
          }}>
            <h3>Client</h3>
            <div style={{
              marginTop: "20px",
              width: "80%",
              height: "150px",
              backgroundColor: "#f0f0f0",
              borderRadius: "5px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.8rem",
            }}>
              Receiving...
            </div>
          </div>
        </div>

        {/* Packets Animation */}
        {isPlaying && (
          <>
            {/* Traditional Packets */}
            {Array.from({ length: packetCount }).map((_, i) => (
              <motion.div
                key={`trad-${i}`}
                initial={{ x: 150, y: 125 }}
                animate={{
                  x: [
                    150,  // Start from LLM server
                    350,  // Move to traditional buffer
                    350,  // Wait in buffer
                    650   // Move to client
                  ],
                  y: 125, // Keep y constant
                }}
                transition={{
                  duration: 4,
                  times: [0, 0.2, 0.7, 1],
                  delay: i * 0.3 + (i > 0 ? 2 : 0),
                  ease: "linear",
                }}
                style={{
                  position: "absolute",
                  width: "12px",
                  height: "12px",
                  backgroundColor: "#1E90FF",
                  borderRadius: "50%",
                  zIndex: 10,
                  boxShadow: "0 0 10px rgba(30, 144, 255, 0.5)",
                }}
              />
            ))}

            {/* Bhumi Packets */}
            {Array.from({ length: packetCount }).map((_, i) => (
              <motion.div
                key={`bhumi-${i}`}
                initial={{ x: 150, y: 225 }}
                animate={{
                  x: [
                    150,  // Start from LLM server
                    350,  // Move to Bhumi buffer
                    650   // Move to client quickly
                  ],
                  y: 225, // Keep y constant
                }}
                transition={{
                  duration: 2,
                  times: [0, 0.3, 1],
                  delay: i * 0.15,
                  ease: "linear",
                }}
                style={{
                  position: "absolute",
                  width: "12px",
                  height: "12px",
                  backgroundColor: coralRed,
                  borderRadius: "50%",
                  zIndex: 10,
                  boxShadow: `0 0 10px ${coralRed}80`,
                }}
              />
            ))}

            {/* Packet Generation Effect at LLM Server */}
            <motion.div
              animate={{
                scale: [1, 1.5, 1],
                opacity: [0.8, 0, 0.8],
              }}
              transition={{
                duration: 1,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              style={{
                position: "absolute",
                left: "140px",
                top: "175px",
                width: "16px",
                height: "16px",
                backgroundColor: coralRed,
                borderRadius: "50%",
                opacity: 0.5,
              }}
            />
          </>
        )}

        {/* Performance Metrics */}
        <div style={{
          position: "absolute",
          bottom: "20px",
          left: "50%",
          transform: "translateX(-50%)",
          display: "flex",
          gap: "40px",
        }}>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            style={{ color: "#1E90FF" }}
          >
            Traditional TTFT: ~2.5s
          </motion.div>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            style={{ color: coralRed }}
          >
            Bhumi TTFT: ~0.5s
          </motion.div>
        </div>
      </div>

      {/* Description */}
      <div style={{
        maxWidth: "800px",
        margin: "40px auto",
        textAlign: "center",
        lineHeight: "1.6",
      }}>
        <p>
          Bhumi optimizes LLM inference by implementing intelligent streaming buffers and 
          leveraging Rust's concurrency features. The dynamic buffer sizing algorithm 
          adapts in real-time to reduce Time to First Token (TTFT) while maintaining 
          optimal throughput.
        </p>
      </div>
    </div>
  );
}