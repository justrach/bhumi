'use client'
import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type BufferConfig = {
  label: string;
  blocks: number;
};

const bufferConfigs: BufferConfig[] = [
  { label: "16 KB", blocks: 5 },
  { label: "128 KB (Optimal)", blocks: 10 },
  { label: "512 KB", blocks: 20 },
];

const BufferAnimation: React.FC = () => {
  const [selectedBufferIndex, setSelectedBufferIndex] = useState<number>(1);
  const [filledBlocks, setFilledBlocks] = useState<number>(0);
  const [isSending, setIsSending] = useState<boolean>(false);

  const currentBuffer = bufferConfigs[selectedBufferIndex];

  // Reset buffer fill when buffer size changes
  useEffect(() => {
    setFilledBlocks(0);
    setIsSending(false);
  }, [selectedBufferIndex]);

  // Simulate filling the buffer and then sending it
  useEffect(() => {
    if (isSending) return; // Do not fill while sending
    if (filledBlocks < currentBuffer.blocks) {
      const timer = setTimeout(() => {
        setFilledBlocks((prev) => prev + 1);
      }, 500); // Increase fill every 500ms
      return () => clearTimeout(timer);
    } else {
      // Buffer full; simulate sending the data
      setIsSending(true);
      const timer = setTimeout(() => {
        setFilledBlocks(0);
        setIsSending(false);
      }, 1000); // 1 second sending delay
      return () => clearTimeout(timer);
    }
  }, [filledBlocks, currentBuffer.blocks, isSending]);

  return (
    <div className="max-w-2xl mx-auto mt-8 text-center">
      <h1 className="text-2xl font-bold mb-4">
        Buffer Animation with Framer Motion
      </h1>
      <div className="mb-4">
        <p>
          Buffer Size: <strong>{currentBuffer.label}</strong>
        </p>
        <p>
          Filling: {filledBlocks} / {currentBuffer.blocks}
        </p>
      </div>

      {/* Buffer visualization */}
      <div className="flex justify-center items-center my-8">
        {Array.from({ length: currentBuffer.blocks }).map((_, index) => (
          <div
            key={index}
            className="w-8 h-8 border-2 border-gray-300 m-1 relative"
          >
            <AnimatePresence>
              {index < filledBlocks && (
                <motion.div
                  className="w-full h-full bg-green-500 absolute top-0 left-0 rounded"
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  transition={{ duration: 0.3 }}
                />
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>

      {/* Sending message */}
      <AnimatePresence>
        {isSending && (
          <motion.div
            className="text-xl text-red-500 mb-4"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            SENDING...
          </motion.div>
        )}
      </AnimatePresence>

      {/* Buffer selection buttons */}
      <div className="flex justify-center space-x-4">
        {bufferConfigs.map((buffer, index) => (
          <button
            key={buffer.label}
            onClick={() => setSelectedBufferIndex(index)}
            className={`px-4 py-2 rounded transition-colors duration-300 ${
              selectedBufferIndex === index
                ? "bg-green-500 text-white"
                : "bg-gray-200 text-gray-800 hover:bg-gray-300"
            }`}
          >
            {buffer.label}
          </button>
        ))}
      </div>
    </div>
  );
};

export default BufferAnimation;