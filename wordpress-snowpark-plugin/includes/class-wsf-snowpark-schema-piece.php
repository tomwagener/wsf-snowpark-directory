<?php
/**
 * Yoast SEO Schema Piece for Snowpark Post Type
 */

if (!defined('ABSPATH')) exit;

use Yoast\WP\SEO\Generators\Schema\Abstract_Schema_Piece;

class WSF_Snowpark_Schema_Piece extends Abstract_Schema_Piece {

    public function is_needed() {
        return is_singular('snowpark');
    }

    public function generate() {
        $post_id = $this->context->id;

        $resort_name  = get_field('resort_name', $post_id) ?: get_the_title($post_id);
        $website_url  = get_field('website_url', $post_id) ?: get_permalink($post_id);
        $lat          = get_field('latitude', $post_id);
        $lng          = get_field('longitude', $post_id);
        $pipe_type    = get_field('pipe_type', $post_id);
        $has_pipe     = get_field('has_pipe', $post_id);
        $has_night    = get_field('has_nightpark', $post_id);
        $has_lift     = get_field('has_park_lift', $post_id);
        $stars        = get_field('overall_wspl_stars', $post_id);
        $crew         = get_field('shaper_crew', $post_id);

        $schema = [
            '@type'            => ['SportsActivityLocation', 'SkiResort'],
            '@id'              => $this->context->canonical . '#snowpark',
            'name'             => get_the_title($post_id),
            'url'              => $this->context->canonical,
            'description'      => get_the_excerpt($post_id) ?: sprintf('%s freestyle snowpark located at %s.', get_the_title($post_id), $resort_name),
            'mainEntityOfPage' => $this->context->main_schema_id,
        ];

        // Geo Coordinates
        if (!empty($lat) && !empty($lng)) {
            $schema['geo'] = [
                '@type'     => 'GeoCoordinates',
                'latitude'  => (float) $lat,
                'longitude' => (float) $lng,
            ];
        }

        // Amenity Features List
        $amenities = [];

        if ($has_pipe && $pipe_type && $pipe_type !== 'None') {
            $amenities[] = [
                '@type' => 'LocationFeatureSpecification',
                'name'  => 'Halfpipe / Superpipe',
                'value' => $pipe_type,
            ];
        }

        if ($has_night) {
            $amenities[] = [
                '@type' => 'LocationFeatureSpecification',
                'name'  => 'Night Lighting / Night Sessions',
                'value' => true,
            ];
        }

        if ($has_lift) {
            $amenities[] = [
                '@type' => 'LocationFeatureSpecification',
                'name'  => 'Dedicated Terrain Park Lift',
                'value' => true,
            ];
        }

        if (!empty($amenities)) {
            $schema['amenityFeature'] = $amenities;
        }

        // Aggregate Rating
        if ($stars && is_numeric($stars)) {
            $schema['aggregateRating'] = [
                '@type'       => 'AggregateRating',
                'ratingValue' => (float) $stars,
                'bestRating'  => 5,
                'worstRating' => 1,
                'ratingCount' => 1,
            ];
        }

        return $schema;
    }
}
