import React from 'react';
import { Link } from 'react-router-dom';

/**
 * About component that displays information about CLASH AI
 */
const About: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <div className="bg-gray-800 rounded-lg p-8 shadow-lg">
          <h1 className="text-3xl font-bold mb-6">About CLASH AI</h1>
          
          {/* New blurb added here */}
          <p className="text-lg mb-8">
            Debate highly nuanced and fine-tuned AI characters to practice your debating, influence, 
            communication, patience... and have a lot of fun while you're at it. CLASH provides a 
            safe environment to develop and refine your persuasion skills with challenging opponents.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-gray-700 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <span className="text-yellow-400 mr-2">⚡</span> How Minutes Work
              </h2>
              <p className="mb-4 text-gray-300">
                Understanding CLASH AI's minute-based system
              </p>

              <div className="bg-gray-800 rounded p-4 mb-4">
                <h3 className="font-semibold mb-2">Purchasing Minutes</h3>
                <p className="text-sm text-gray-300">
                  Buy minute packages through our secure payment system. Choose from 10, 30, or 60 minute bundles.
                </p>
              </div>

              <div className="bg-gray-800 rounded p-4 mb-4">
                <h3 className="font-semibold mb-2">Usage Tracking</h3>
                <p className="text-sm text-gray-300">
                  Minutes are consumed during active conversations with AI characters. The timer at the top shows your current session length.
                </p>
              </div>

              <div className="bg-gray-800 rounded p-4">
                <h3 className="font-semibold mb-2">Minute Balance</h3>
                <p className="text-sm text-gray-300">
                  Your remaining minutes are displayed at the top of the screen. You'll need to purchase more when your balance reaches zero.
                </p>
              </div>
            </div>

            <div className="bg-gray-700 rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4 flex items-center">
                <span className="text-blue-400 mr-2">ℹ️</span> How To
              </h2>
              <p className="mb-4 text-gray-300">
                Getting the most out of your experience
              </p>

              <div className="bg-gray-800 rounded p-4 mb-4">
                <h3 className="font-semibold mb-2">Select a Character</h3>
                <p className="text-sm text-gray-300">
                  Choose from our diverse cast of AI characters, each with unique perspectives and expertise.
                </p>
              </div>

              <div className="bg-gray-800 rounded p-4 mb-4">
                <h3 className="font-semibold mb-2">Voice Interaction</h3>
                <p className="text-sm text-gray-300">
                  Speak naturally with your chosen character. Our advanced voice recognition understands natural conversation.
                </p>
              </div>

              <div className="bg-gray-800 rounded p-4">
                <h3 className="font-semibold mb-2">Call Duration</h3>
                <p className="text-sm text-gray-300">
                  The timer at the top tracks your current conversation length. Your minutes are deducted based on actual usage time.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 text-center">
            <Link 
              to="/" 
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-6 rounded transition duration-300"
            >
              Back to Dashboard
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default About;
