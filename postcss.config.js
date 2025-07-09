// postcss.config.js
module.exports = {
  plugins: [
    // Other PostCSS plugins you might use (e.g., autoprefixer for browser prefixes)
    require('autoprefixer'),

    // PurgeCSS plugin
    require('@fullhuman/postcss-purgecss')({
      // Paths to all your files that contain class names or IDs
      content: [
        './templates/**/*.html', // Scans HTML files in your 'templates' directory
        './static/js/**/*.js',   // If you dynamically add classes with JavaScript
        // Add other template files if you use them (e.g., Flask/Jinja2, React, Vue, etc.)
      ],

      // Paths to your CSS files that need purging
      css: [
        './static/css/style.css', // Your main stylesheet
      ],

      // Optional: Safelist classes/selectors to prevent removal (e.g., classes added by JavaScript)
      safelist: {
          standard: [], // Example: ['some-class-added-by-js', 'another-dynamic-class']
          deep: [],     // For more complex nested selectors
          greedy: [],   // For keeping all classes starting with a certain prefix, e.g., ['fa-'] for Font Awesome
          keyframes: [], // If you have specific keyframe animations you want to preserve
          variables: [], // If you have CSS variables you want to preserve
      },

      // Optional: You usually don't need 'output' here as PostCSS CLI handles output
      // However, if you were using PurgeCSS directly without PostCSS-CLI, you might use it.
    }),
  ],
};