/**
 * Adjust the top_img priority for posts
 * 
 * Butterfly default priority: page.top_img > page.cover > theme.default_top_img
 * Adjusted priority: page.top_img > theme.default_top_img > page.cover
 * 
 * How it works: Before post rendering, if the post does not explicitly set top_img
 * and the theme has default_top_img configured, assign default_top_img to page.top_img
 * so that it takes precedence over cover.
 */
hexo.extend.filter.register('before_post_render', function (data) {
  const defaultTopImg = hexo.theme.config.default_top_img;

  // Only handle post layout, where top_img is not explicitly set and default_top_img is configured
  if (data.layout === 'post' && !data.top_img && defaultTopImg) {
    data.top_img = defaultTopImg;
  }

  return data;
});
