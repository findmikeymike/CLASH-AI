import React from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Calendar, Clock, User } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { BlogPost } from "@/data/blogPosts";

interface BlogPostDetailProps {
  post: BlogPost;
  onBack: () => void;
}

const BlogPostDetail: React.FC<BlogPostDetailProps> = ({ post, onBack }) => {
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
          <h1 className="text-xl md:text-2xl font-bold text-white">CLASH Blog</h1>
        </div>
      </header>

      {/* Main content */}
      <main className="relative z-10 container mx-auto px-4 py-8 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="bg-gradient-to-br from-gray-900 to-black border border-gray-800 rounded-2xl overflow-hidden"
        >
          {/* Featured image */}
          <div className="relative h-96">
            <img 
              src={post.imageUrl} 
              alt={post.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent"></div>
            
            {/* Categories */}
            <div className="absolute top-4 left-4 z-20 flex flex-wrap gap-2">
              {post.categories.map((category, index) => (
                <Badge 
                  key={index}
                  className="bg-red-600/80 hover:bg-red-700 text-white border-none"
                >
                  {category}
                </Badge>
              ))}
            </div>
            
            {/* Title overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-8">
              <h1 className="text-3xl md:text-4xl font-bold text-white mb-4">{post.title}</h1>
              
              <div className="flex flex-wrap items-center text-sm text-gray-300 gap-y-2">
                <div className="flex items-center mr-6">
                  <User className="h-4 w-4 mr-2" />
                  <span>{post.author}</span>
                </div>
                <div className="flex items-center mr-6">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span>{post.date}</span>
                </div>
                <div className="flex items-center">
                  <Clock className="h-4 w-4 mr-2" />
                  <span>{post.readTime} min read</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Article content */}
          <div className="p-8">
            {/* Article excerpt */}
            <div className="mb-8 pb-4 border-b border-gray-800">
              <div className="text-lg text-gray-300 italic">
                {post.excerpt}
              </div>
            </div>
            
            {/* Article body - render markdown content */}
            <div className="prose prose-invert prose-red max-w-none">
              {post.isMarkdown ? (
                <div dangerouslySetInnerHTML={{ __html: post.content || '' }} />
              ) : (
                <>
                  <p>
                    {post.content || `This is a placeholder for the full content of "${post.title}". In a real implementation, this would be a rich text field with proper formatting, images, and other elements.`}
                  </p>
                  
                  <h2>Why This Matters</h2>
                  <p>
                    Debate skills are essential in today's polarized world. Whether you're discussing politics, ethics, or simply trying to make your point in a meeting, the ability to articulate your thoughts clearly and respond to counterarguments effectively is invaluable.
                  </p>
                  
                  <h2>How CLASH AI Can Help</h2>
                  <p>
                    CLASH AI provides a safe environment to practice debate skills with a variety of AI personas, each with their own unique perspectives and debate styles. By engaging with these diverse viewpoints, you can:
                  </p>
                  
                  <ul>
                    <li>Strengthen your argumentation skills</li>
                    <li>Learn to anticipate counterpoints</li>
                    <li>Develop greater empathy for opposing viewpoints</li>
                    <li>Build confidence in expressing your ideas</li>
                  </ul>
                  
                  <blockquote>
                    "The ability to understand and effectively respond to different perspectives is not just a debate skill—it's a life skill that enhances critical thinking and emotional intelligence."
                  </blockquote>
                  
                  <h2>Key Takeaways</h2>
                  <p>
                    As you continue to engage with CLASH AI, remember that the goal isn't always to "win" but to expand your understanding and improve your communication. The most powerful debaters are those who can genuinely understand multiple perspectives, even when they disagree with them.
                  </p>
                </>
              )}
            </div>
          </div>
          

        </motion.div>
      </main>
    </div>
  );
};

export default BlogPostDetail;
