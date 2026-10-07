<?php
/**
 * Auto-populate Snowpark Post Content on Save / Display Fallback
 */

if (!defined('ABSPATH')) exit;

// When Snowpark is saved or viewed, ensure it has the layout markup or template output
add_filter('default_content', function($content, $post) {
    if ($post->post_type === 'snowpark') {
        return '[wsf_snowpark_single]';
    }
    return $content;
}, 10, 2);

// Direct Content Filter without complex conditionals
add_filter('the_content', function($content) {
    if (is_singular('snowpark')) {
        return do_shortcode('[wsf_snowpark_single]');
    }
    return $content;
}, 1);
