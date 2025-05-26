import React from "react";
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

const LandingPage = () => {
  return (
    <div className="min-h-screen bg-black text-white flex flex-col justify-center items-center">
      {/* Main Content Container */}
      <div className="container mx-auto max-w-5xl flex flex-col items-center justify-center py-16 px-4">
        {/* CLASH Title */}
        <h1 className="text-7xl md:text-9xl font-black mb-12 text-red-500 tracking-tighter italic">
          CLASH
        </h1>

        {/* Subtitle */}
        <p className="text-xl md:text-2xl text-white mb-16 tracking-wide font-normal text-center helvetica-neue">
          Go head-to-head with Universe's greatest intelligence...
        </p>

        {/* Video Placeholders */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 w-full max-w-4xl">
          <div className="bg-gray-800/80 rounded-lg aspect-video flex items-center justify-center">
            <p className="text-gray-400">Video Placeholder</p>
          </div>
          <div className="bg-gray-800/80 rounded-lg aspect-video flex items-center justify-center">
            <p className="text-gray-400">Video Placeholder</p>
          </div>
          <div className="bg-gray-800/80 rounded-lg aspect-video flex items-center justify-center">
            <p className="text-gray-400">Video Placeholder</p>
          </div>
        </div>

        {/* Description Text */}
        <p className="text-gray-300 mb-12 text-center max-w-2xl helvetica-neue">
          Sharpen your confidence, influence, and patience debating legendary
          opponents
        </p>

        {/* CTA Button */}
        <Link to="/debate" className="mb-16">
          <Button className="bg-transparent hover:bg-red-600/20 text-red-500 border-2 border-red-500 rounded-full py-6 px-12 text-lg font-medium transition-all duration-300">
            ENTER WITH CAUTION
          </Button>
        </Link>

        {/* Copyright */}
        <p className="text-gray-500 text-sm">
          © 2025 Clash. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default LandingPage;
