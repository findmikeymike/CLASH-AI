# CLASH Blog Deployment

This directory contains a deployment-ready version of the CLASH blog, optimized for hosting on Netlify or any static site hosting service.

## Directory Structure

- `index.html` - Main blog listing page
- `styles.css` - Global styles for the blog
- `posts/` - Directory containing individual blog post HTML files
- `netlify.toml` - Configuration file for Netlify deployment

## Deployment Instructions

### Option 1: Deploy to Netlify (Recommended)

1. Create a new site on Netlify (https://app.netlify.com/start)
2. Connect your GitHub repository or drag and drop this `blog-deploy` folder
3. Netlify will automatically detect the configuration in `netlify.toml`
4. Your blog will be deployed and available at a Netlify subdomain (e.g., `clash-blog.netlify.app`)
5. You can configure a custom domain in the Netlify settings

### Option 2: Deploy to GitHub Pages

1. Create a new GitHub repository
2. Push the contents of this `blog-deploy` directory to the repository
3. Enable GitHub Pages in the repository settings
4. Your blog will be available at `https://[username].github.io/[repository-name]`

### Option 3: Deploy to Any Static Hosting

The blog is built with plain HTML, CSS, and no JavaScript dependencies, making it compatible with any static hosting service:

1. Upload the contents of this directory to your hosting service
2. Ensure the directory structure is maintained
3. Configure your domain to point to the hosting service

## Adding New Blog Posts

To add a new blog post:

1. Create a new HTML file in the `posts/` directory (e.g., `posts/new-article.html`)
2. Copy the structure from an existing post and update the content
3. Add a link to the new post on the main `index.html` page

## Customization

- Update `styles.css` to change the appearance of the blog
- Modify the header and footer in each HTML file to update navigation or site information
- Replace placeholder images with your own images

## SEO Optimization

Each page includes:
- Descriptive title tags
- Meta descriptions
- Semantic HTML structure
- Responsive design for mobile devices

## Nuclear Debugging

If you encounter any issues with the deployment:

1. Verify all file paths are correct (especially for CSS and image references)
2. Check that all HTML files are properly formatted
3. Ensure the `netlify.toml` file is in the root of the deployed directory
4. Review the deployment logs from your hosting provider for specific errors

## Contact

For any questions or issues, please contact the CLASH team.
