import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';

// Define the interface for a Markdown Article
export interface MarkdownArticle {
  id: string;
  slug: string;
  title: string;
  date: string;
  author: string;
  readTime: number;
  excerpt: string;
  content: string; // This will be HTML content
  imageUrl: string;
  categories: string[];
}

// Helper function to parse individual article data from raw content and its path
async function parseArticleData(filePath: string, rawContent: string): Promise<MarkdownArticle | null> {
  try {
    const slug = filePath.substring(filePath.lastIndexOf('/') + 1).replace(/\.md$/, '');
    
    // Use gray-matter to parse the post metadata section
    const matterResult = matter(rawContent);
    
    // Extract metadata from the first few lines if not in frontmatter
    const lines = matterResult.content.split('\n');
    const titleLine = lines[0].startsWith('# ') ? lines[0].substring(2) : (matterResult.data.title || 'Untitled');
    
    // Look for date and read time in the format *May 23, 2025 • 6 min read • CLASH Team*
    const metaLine = lines.find(line => line.startsWith('*') && line.includes('min read'))?.slice(1, -1) || '';
    const metaParts = metaLine.split('•').map(part => part.trim());
    
    const dateString = metaParts[0] || matterResult.data.date || '';
    const readTimeStr = metaParts[1] || (matterResult.data.readTime ? `${matterResult.data.readTime} min read` : '');
    const readTime = readTimeStr ? parseInt(readTimeStr.match(/(\d+)/)?.[1] || '8') : (matterResult.data.readTime || 8);
    const author = metaParts[2] || matterResult.data.author || 'CLASH Team';
    
    // Extract image URL from markdown or frontmatter
    const imageMatch = matterResult.content.match(/!\[.*?\]\((.*?)\)\)/);
    const imageUrl = matterResult.data.imageUrl || (imageMatch ? imageMatch[1] : 'https://images.unsplash.com/photo-1557804506-669a67965ba0');
    
    // Extract excerpt from the first paragraph after the image or frontmatter
    const contentAfterImage = matterResult.content.split(/!\[.*?\]\(.*?\)\)/)[1] || matterResult.content;
    const excerptMatch = contentAfterImage.match(/\n([^\n#]+)\n/);
    const excerpt = matterResult.data.excerpt || (excerptMatch ? excerptMatch[1].trim() : '');
    
    // Extract tags from the bottom of the article or frontmatter
    const tagsMatch = matterResult.content.match(/\*Tags:(.*?)\*/);
    const tagsString = tagsMatch ? tagsMatch[1] : (Array.isArray(matterResult.data.categories) ? matterResult.data.categories.join(', ') : '');
    const categories = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    
    // Use remark to convert markdown into HTML string
    const processedContent = await remark()
      .use(html)
      .process(matterResult.content);
    const contentHtml = processedContent.toString();
    
    // Generate a unique ID
    const id = slug;
    
    return {
      id,
      slug,
      title: titleLine,
      date: dateString, // Keep date as string, parsing/formatting can be done in UI
      author,
      readTime,
      excerpt,
      content: contentHtml,
      imageUrl,
      categories: categories.length > 0 ? categories : ['Debate', 'AI', 'CLASH']
    };
  } catch (error) {
    console.error(`Error processing article from path ${filePath}:`, error);
    return null;
  }
}

// Get all articles data using Vite's import.meta.glob
export async function getAllArticles(): Promise<MarkdownArticle[]> {
  // The path for import.meta.glob is relative to the project root.
  // It should point to where your markdown files are within the 'src' directory.
  const markdownModules = import.meta.glob('/src/data/blogArticles/*.md', { as: 'raw', eager: true });
  
  const allArticlesDataPromises: Promise<MarkdownArticle | null>[] = [];

  for (const path in markdownModules) {
    const rawContent = markdownModules[path];
    allArticlesDataPromises.push(parseArticleData(path, rawContent));
  }
  
  const allArticlesData = await Promise.all(allArticlesDataPromises);
  
  // Filter out null values and sort by date
  return allArticlesData
    .filter((article): article is MarkdownArticle => article !== null)
    .sort((a, b) => {
      try {
        // Attempt to parse dates for sorting, provide fallback for invalid dates
        const dateA = new Date(a.date).getTime();
        const dateB = new Date(b.date).getTime();
        if (isNaN(dateA) || isNaN(dateB)) return 0; // Keep original order if dates are invalid
        return dateB - dateA; // Newest first
      } catch (e) {
        return 0; // Keep original order on parsing error
      }
    });
}
