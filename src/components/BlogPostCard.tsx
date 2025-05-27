import React from "react";
import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import { Calendar, Clock, User } from "lucide-react";
import { BlogPost } from "@/data/blogPosts";

interface BlogPostCardProps {
  post: BlogPost;
  featured?: boolean;
}

const BlogPostCard: React.FC<BlogPostCardProps> = ({ post, featured = false }) => {
  return (
    <motion.div
      whileHover={{ y: -5, transition: { duration: 0.2 } }}
      className={`group relative overflow-hidden ${
        featured 
          ? "rounded-2xl bg-gradient-to-br from-gray-900 to-black border border-gray-800"
          : "rounded-xl bg-gradient-to-br from-gray-900 to-black border border-gray-800"
      }`}
    >
      <div className="absolute inset-0 bg-gradient-to-t from-black via-black/80 to-transparent opacity-60 group-hover:opacity-70 transition-opacity z-10"></div>
      
      {/* Image */}
      <div className="relative">
        <img 
          src={post.imageUrl} 
          alt={post.title}
          className={`w-full object-cover ${featured ? 'h-96' : 'h-64'}`}
        />
        
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
      </div>
      
      {/* Content */}
      <div className={`relative z-20 p-6 ${featured ? 'pb-8' : ''}`}>
        <h3 className={`${featured ? 'text-2xl' : 'text-xl'} font-bold text-white mb-3 group-hover:text-red-400 transition-colors`}>
          {post.title}
        </h3>
        
        <p className="text-gray-300 mb-4 line-clamp-3">
          {post.excerpt}
        </p>
        
        <div className="flex items-center justify-between text-sm text-gray-400">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              <span>{post.date}</span>
            </div>
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-1" />
              <span>{post.readTime} min read</span>
            </div>
          </div>
          
          <div className="flex items-center">
            <User className="h-4 w-4 mr-1" />
            <span>{post.author}</span>
          </div>
        </div>
      </div>
      
      {/* Hover effect overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-red-600/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity z-0"></div>
      
      {/* Read more link - entire card is clickable */}
      <a href={`/blog/${post.slug}`} className="absolute inset-0 z-30" aria-label={`Read ${post.title}`}></a>
    </motion.div>
  );
};

export default BlogPostCard;
