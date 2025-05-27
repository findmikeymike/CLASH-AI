import { MarkdownArticle, getAllArticles } from '@/utils/markdownLoader';

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  author: string;
  date: string;
  readTime: number;
  excerpt: string;
  content?: string;
  imageUrl: string;
  categories: string[];
  isMarkdown?: boolean;
}

// Static blog posts that will be combined with markdown articles
export const staticBlogPosts: BlogPost[] = [
  {
    id: "1",
    title: "What Zeek the Nihilist Would Say About Trump vs Biden 2024",
    slug: "zeek-nihilist-trump-biden-2024",
    author: "CLASH Team",
    date: "May 26, 2025",
    readTime: 8,
    excerpt: "Dive into the mind of Zeek, our resident nihilist, as he deconstructs the upcoming presidential election and why it might not matter in the grand cosmic scheme.",
    imageUrl: "https://images.unsplash.com/photo-1540910419892-4a36d2c3266c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Politics", "Character Analysis", "Hot Takes"]
  },
  {
    id: "2",
    title: "How to Destroy a Liberal in 5 Moves — According to Chad the Alpha",
    slug: "chad-alpha-destroy-liberal-debate",
    author: "CLASH Team",
    date: "May 23, 2025",
    readTime: 6,
    excerpt: "Chad, our most confident debate persona, breaks down his top strategies for dismantling progressive arguments. Learn his tactics whether you agree with him or not.",
    imageUrl: "https://images.unsplash.com/photo-1494059980473-813e73ee784b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2069&q=80",
    categories: ["Debate Tactics", "Character Analysis", "Political Discourse"]
  },
  {
    id: "3",
    title: "Why Debating a Hippy is Harder Than Debating a Priest",
    slug: "debating-hippy-vs-priest",
    author: "CLASH Team",
    date: "May 20, 2025",
    readTime: 7,
    excerpt: "Contrary to popular belief, spiritual but non-religious opponents present unique challenges in debate. We analyze why these conversations require different approaches.",
    imageUrl: "https://images.unsplash.com/photo-1529253355930-ddbe423a2ac7?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2001&q=80",
    categories: ["Debate Psychology", "Spiritual Discourse", "Strategy"]
  },
  {
    id: "4",
    title: "How to Get Better at Debating Controversial Topics",
    slug: "improve-controversial-topic-debates",
    author: "CLASH Team",
    date: "May 18, 2025",
    readTime: 9,
    excerpt: "Tackling sensitive subjects requires special skills. Learn how to navigate emotional landmines while still making compelling arguments on divisive issues.",
    imageUrl: "https://images.unsplash.com/photo-1517245386807-bb43f82c33c4?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Debate Skills", "Controversial Topics", "Communication"]
  },
  {
    id: "5",
    title: "Best AI Debate Tools in 2025",
    slug: "best-ai-debate-tools-2025",
    author: "CLASH Team",
    date: "May 15, 2025",
    readTime: 10,
    excerpt: "CLASH leads the pack, but we're honest about the competition. Here's our comprehensive review of all AI platforms helping people become better debaters.",
    imageUrl: "https://images.unsplash.com/photo-1677442135968-6144fc1c8d04?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["AI Tools", "Product Reviews", "Technology"]
  },
  {
    id: "6",
    title: "What is Steelmanning and Why CLASH Trains It Better Than College",
    slug: "steelmanning-clash-vs-college",
    author: "CLASH Team",
    date: "May 12, 2025",
    readTime: 8,
    excerpt: "The art of strengthening your opponent's argument before countering it is essential for intellectual honesty. See how AI practice makes this skill accessible to everyone.",
    imageUrl: "https://images.unsplash.com/photo-1523240795612-9a054b0db644?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Debate Techniques", "Education", "Critical Thinking"]
  },
  {
    id: "7",
    title: "Israel-Palestine, Explained Like You're Arguing with Karen",
    slug: "israel-palestine-karen-debate",
    author: "CLASH Team",
    date: "May 10, 2025",
    readTime: 12,
    excerpt: "Complex geopolitical issues meet everyday debate scenarios. Learn how to discuss the Middle East conflict with someone who has strong opinions but limited nuance.",
    imageUrl: "https://images.unsplash.com/photo-1569209067215-e2a52b55c8fb?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Geopolitics", "Difficult Conversations", "Hot Takes"]
  },
  {
    id: "8",
    title: "Practice Public Speaking with AI: Why It Works",
    slug: "ai-public-speaking-practice",
    author: "CLASH Team",
    date: "May 8, 2025",
    readTime: 7,
    excerpt: "The science behind why practicing with AI opponents can dramatically improve your real-world speaking confidence and performance.",
    imageUrl: "https://images.unsplash.com/photo-1475721027785-f74eccf877e2?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Public Speaking", "AI Training", "Personal Development"]
  },
  {
    id: "9",
    title: "Debating Liberals vs Conservatives: What Changes?",
    slug: "liberal-conservative-debate-differences",
    author: "CLASH Team",
    date: "May 5, 2025",
    readTime: 11,
    excerpt: "Different political ideologies require different debate approaches. Discover the psychological and rhetorical adjustments that make cross-political conversations more productive.",
    imageUrl: "https://images.unsplash.com/photo-1529107386315-e1a2ed48a620?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Political Discourse", "Debate Psychology", "Communication"]
  },
  {
    id: "10",
    title: "Why Debate Makes You Smarter Than Therapy",
    slug: "debate-vs-therapy-intelligence",
    author: "CLASH Team",
    date: "May 3, 2025",
    readTime: 9,
    excerpt: "Controversial take: structured argumentation develops cognitive flexibility and emotional resilience in ways traditional therapy might miss. We explore the evidence.",
    imageUrl: "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=2070&q=80",
    categories: ["Mental Health", "Cognitive Development", "Controversial Takes"]
  }
];

// This function will load all blog posts, combining static ones with markdown articles
export async function loadAllBlogPosts(): Promise<BlogPost[]> {
  try {
    // Load markdown articles
    const markdownArticles = await getAllArticles();
    
    // Convert markdown articles to BlogPost format
    const markdownPosts: BlogPost[] = markdownArticles.map(article => ({
      ...article,
      isMarkdown: true
    }));
    
    // Combine both sources, with markdown posts first (they're newer)
    return [...markdownPosts, ...staticBlogPosts];
  } catch (error) {
    console.error('Error loading blog posts:', error);
    return staticBlogPosts; // Fallback to static posts if there's an error
  }
}

// For backward compatibility, export the static posts as blogPosts
export const blogPosts = staticBlogPosts;