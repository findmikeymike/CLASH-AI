import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import BlogPostCard from "./BlogPostCard";
import { BlogPost, staticBlogPosts, loadAllBlogPosts } from "@/data/blogPosts";

interface BlogProps {
  onBack: () => void;
}

const Blog: React.FC<BlogProps> = ({ onBack }) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [posts, setPosts] = useState<BlogPost[]>(staticBlogPosts);
  const [loading, setLoading] = useState(true);
  
  // Load all blog posts including markdown articles
  useEffect(() => {
    const fetchPosts = async () => {
      try {
        setLoading(true);
        const allPosts = await loadAllBlogPosts();
        setPosts(allPosts);
      } catch (error) {
        console.error('Error loading blog posts:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchPosts();
  }, []);
  
  // Filter blog posts based on search query
  const filteredPosts = posts.filter(post => 
    post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.excerpt.toLowerCase().includes(searchQuery.toLowerCase()) ||
    post.categories.some(category => category.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/30 via-black to-pink-900/20 z-10"></div>
        <div className="absolute top-0 left-0 right-0 h-full bg-grid-pattern opacity-15"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/5 via-transparent to-red-600/5"></div>
      </div>

      {/* Header */}
      <header className="relative z-20 flex items-center justify-between p-6">
        <div className="flex items-center space-x-4">
          <Button 
            variant="outline" 
            size="icon" 
            onClick={onBack}
            className="bg-red-600 text-white border-red-600 hover:bg-red-700 hover:border-red-700 rounded-lg transition-colors shadow-xl"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl md:text-4xl font-bold text-white">CLASH Blog</h1>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 container mx-auto px-4 py-8">
        {/* Search bar */}
        <div className="max-w-2xl mx-auto mb-12">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
            <Input 
              type="text"
              placeholder="Search articles..."
              className="pl-10 py-6 bg-gray-900/60 border-gray-700 text-white rounded-xl focus:ring-red-500 focus:border-red-500 w-full"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Loading state */}
        {loading && (
          <div className="flex justify-center items-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-500"></div>
          </div>
        )}
        
        {/* Featured post */}
        {!loading && filteredPosts.length > 0 && !searchQuery && (
          <div className="mb-16">
            <h2 className="text-2xl font-bold text-red-500 mb-6">Featured</h2>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <BlogPostCard 
                post={filteredPosts[0]} 
                featured={true}
              />
            </motion.div>
          </div>
        )}

        {/* Blog post grid */}
        <div className="mb-16">
          <h2 className="text-2xl font-bold text-red-500 mb-6">
            {searchQuery ? `Search Results (${filteredPosts.length})` : "Latest Articles"}
          </h2>
          
          {filteredPosts.length === 0 ? (
            <div className="text-center py-16">
              <h3 className="text-xl text-gray-400">No articles found matching "{searchQuery}"</h3>
              <Button 
                variant="outline" 
                className="mt-4 border-red-500 text-red-500 hover:bg-red-500/10"
                onClick={() => setSearchQuery("")}
              >
                Clear Search
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {filteredPosts.slice(searchQuery ? 0 : 1).map((post, index) => (
                <motion.div
                  key={post.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                >
                  <BlogPostCard post={post} />
                </motion.div>
              ))}
            </div>
          )}
        </div>


      </main>
    </div>
  );
};

export default Blog;