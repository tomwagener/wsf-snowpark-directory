<?php
/**
 * Simple Auto-Setup for Directory Page
 */

if (!defined('ABSPATH')) exit;

add_action('init', function() {
    // Check if directory page exists
    $page = get_page_by_path('snowparks-guide');
    if (!$page) {
        wp_insert_post([
            'post_title'   => 'WSF Snowpark Guide',
            'post_name'    => 'snowparks-guide',
            'post_content' => '<!-- wp:shortcode -->[wsf_snowpark_directory]<!-- /wp:shortcode -->',
            'post_status'  => 'publish',
            'post_type'    => 'page',
        ]);
    }
});
