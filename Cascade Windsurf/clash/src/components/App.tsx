import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Blog from './Blog';
import BlogPostDetail from './BlogPostDetail';
import CharacterSelection from './CharacterSelection';

/**
 * Main App component with routing configuration
 */
const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        {/* Navigation */}
        <nav className="bg-white shadow-md">
          <div className="container mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <Link to="/" className="text-2xl font-bold text-blue-600">CLASH</Link>
              <div className="space-x-6">
                <Link to="/" className="hover:text-blue-600">Home</Link>
                <Link to="/blog" className="hover:text-blue-600">Blog</Link>
                <Link to="/about" className="hover:text-blue-600">About</Link>
                <Link to="/contact" className="hover:text-blue-600">Contact</Link>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main>
          <Routes>
            <Route path="/" element={<CharacterSelection />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:slug" element={<BlogPostDetail />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="bg-gray-800 text-white py-8">
          <div className="container mx-auto px-4">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <div className="mb-4 md:mb-0">
                <h3 className="text-xl font-bold">CLASH</h3>
                <p className="text-gray-400">Improving debate skills through AI practice</p>
              </div>
              <div className="flex space-x-6">
                <Link to="/privacy" className="text-gray-400 hover:text-white">Privacy Policy</Link>
                <Link to="/terms" className="text-gray-400 hover:text-white">Terms of Service</Link>
                <Link to="/contact" className="text-gray-400 hover:text-white">Contact</Link>
              </div>
            </div>
            <div className="mt-8 text-center text-gray-400">
              <p>&copy; {new Date().getFullYear()} CLASH AI. All rights reserved.</p>
            </div>
          </div>
        </footer>
      </div>
    </Router>
  );
};

// Placeholder components for other routes
const Home: React.FC = () => (
  <div className="container mx-auto px-4 py-16 text-center">
    <h1 className="text-4xl font-bold mb-6">Welcome to CLASH</h1>
    <p className="text-xl mb-8">Improve your debate skills through AI-powered practice</p>
    <div className="flex justify-center">
      <Link to="/blog" className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition duration-300">
        Explore Our Blog
      </Link>
    </div>
  </div>
);

const About: React.FC = () => (
  <div className="container mx-auto px-4 py-16">
    <h1 className="text-3xl font-bold mb-6">About CLASH</h1>
    <p className="mb-4">
      CLASH is an AI-powered platform designed to help you improve your debate and critical thinking skills
      through practice with sophisticated AI personas representing different perspectives and debate styles.
    </p>
    <p>
      Our mission is to make high-quality debate practice accessible to everyone, regardless of background
      or resources, and to promote more thoughtful, nuanced discourse in an increasingly polarized world.
    </p>
  </div>
);

const Contact: React.FC = () => (
  <div className="container mx-auto px-4 py-16">
    <h1 className="text-3xl font-bold mb-6">Contact Us</h1>
    <p className="mb-8">
      Have questions, feedback, or suggestions? We'd love to hear from you!
    </p>
    <form className="max-w-lg">
      <div className="mb-4">
        <label htmlFor="name" className="block mb-2">Name</label>
        <input type="text" id="name" className="w-full p-2 border rounded" />
      </div>
      <div className="mb-4">
        <label htmlFor="email" className="block mb-2">Email</label>
        <input type="email" id="email" className="w-full p-2 border rounded" />
      </div>
      <div className="mb-4">
        <label htmlFor="message" className="block mb-2">Message</label>
        <textarea id="message" rows={5} className="w-full p-2 border rounded"></textarea>
      </div>
      <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
        Send Message
      </button>
    </form>
  </div>
);

const NotFound: React.FC = () => (
  <div className="container mx-auto px-4 py-16 text-center">
    <h1 className="text-4xl font-bold mb-6">404 - Page Not Found</h1>
    <p className="text-xl mb-8">The page you're looking for doesn't exist.</p>
    <Link to="/" className="text-blue-600 hover:text-blue-800 font-semibold">
      Return to Home
    </Link>
  </div>
);

export default App;
