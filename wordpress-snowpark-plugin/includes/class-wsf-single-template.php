<?php
/**
 * Render Kadence-styled Single Snowpark Template via Kadence Hook or the_content
 */

if (!defined('ABSPATH')) exit;

// Hook directly into Kadence Single Content Hook and template_include fallback
add_action('kadence_single_after_entry_header', 'wsf_render_snowpark_kadence_hook', 10);

function wsf_render_snowpark_kadence_hook() {
    if (!is_singular('snowpark')) {
        return;
    }

    $post_id      = get_the_ID();
    $title        = get_the_title($post_id);
    $resort       = get_post_meta($post_id, 'resort_name', true) ?: $title;
    $elev         = get_post_meta($post_id, 'elevation_masl', true);
    $verified     = get_post_meta($post_id, 'wsf_verified', true);
    $stars        = get_post_meta($post_id, 'overall_wspl_stars', true);

    $total_obst   = get_post_meta($post_id, 'total_obstacles', true);
    $jumps        = get_post_meta($post_id, 'jump_count', true);
    $jibs         = get_post_meta($post_id, 'jib_count', true);
    $crew         = get_post_meta($post_id, 'shaper_crew', true);

    $rate_beg     = get_post_meta($post_id, 'rating_beginner', true);
    $rate_int     = get_post_meta($post_id, 'rating_intermediate', true);
    $rate_pro     = get_post_meta($post_id, 'rating_advanced_pro', true);

    $has_pipe     = get_post_meta($post_id, 'has_pipe', true);
    $pipe_type    = get_post_meta($post_id, 'pipe_type', true);

    $has_lift     = get_post_meta($post_id, 'has_park_lift', true);
    $daily_shape  = get_post_meta($post_id, 'daily_shape', true);
    $snowmaking   = get_post_meta($post_id, 'dedicated_snowmaking', true);
    $nightpark    = get_post_meta($post_id, 'has_nightpark', true);
    $groomer      = get_post_meta($post_id, 'dedicated_groomer', true);
    $season       = get_post_meta($post_id, 'season_window', true);

    $transit      = get_post_meta($post_id, 'public_transit_score', true);
    $train        = get_post_meta($post_id, 'nearest_train_station', true);
    $airport      = get_post_meta($post_id, 'nearest_airport', true);

    $insta        = get_post_meta($post_id, 'instagram_handle', true);
    $website      = get_post_meta($post_id, 'website_url', true);
    $events       = get_post_meta($post_id, 'event_calendar_url', true);

    $terms = get_the_terms($post_id, 'snowpark_location');
    $location_str = '';
    if ($terms && !is_wp_error($terms)) {
        $names = wp_list_pluck($terms, 'name');
        $location_str = implode(' &bull; ', array_reverse($names));
    }

    $star_html = function($val) {
        if (!$val) return '';
        $out = '<span style="color:#f59e0b; font-size:1.1rem;">';
        for ($i = 1; $i <= 5; $i++) {
            $out .= ($i <= $val) ? '★' : '☆';
        }
        $out .= '</span>';
        return $out;
    };
    ?>
    <div class="wsf-snowpark-template" style="font-family: inherit; color:#1e293b; line-height: 1.6; margin: 20px auto 40px auto; max-width: 1200px;">
        
        <!-- 1. HERO SECTION -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color:#fff; border-radius:12px; padding:35px 30px; margin-bottom:30px; box-shadow:0 10px 25px -5px rgba(0,0,0,0.1);">
            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:15px; align-items:center;">
                <?php if ($verified): ?>
                    <span style="background:#fbbf24; color:#78350f; font-weight:700; font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; padding:4px 10px; border-radius:9999px;">✓ WSF Verified</span>
                <?php endif; ?>
                <?php if ($location_str): ?>
                    <span style="background:rgba(255,255,255,0.15); color:#fff; font-size:0.85rem; padding:4px 12px; border-radius:9999px;">📍 <?php echo esc_html($location_str); ?></span>
                <?php endif; ?>
                <?php if ($elev): ?>
                    <span style="background:rgba(255,255,255,0.15); color:#fff; font-size:0.85rem; padding:4px 12px; border-radius:9999px;">⛰️ <?php echo esc_html($elev); ?></span>
                <?php endif; ?>
            </div>
            
            <h1 style="color:#fff; font-size:2.4rem; margin:0 0 10px 0; font-weight:800; line-height:1.2;"><?php echo esc_html($title); ?></h1>
            <p style="color:#94a3b8; font-size:1.1rem; margin:0 0 15px 0;">Home Resort: <strong style="color:#e2e8f0;"><?php echo esc_html($resort); ?></strong></p>
            
            <?php if ($stars): ?>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:0.95rem; color:#cbd5e1;">WSPL Overall Rating:</span>
                    <?php echo $star_html($stars); ?>
                    <span style="font-weight:700; color:#fbbf24;"><?php echo esc_html($stars); ?> / 5</span>
                </div>
            <?php endif; ?>
        </div>

        <!-- 2. QUICK STATS BAR -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:15px; margin-bottom:30px;">
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:20px; text-align:center;">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700;">Total Obstacles</div>
                <div style="font-size:2rem; font-weight:800; color:#0f172a; margin-top:5px;"><?php echo esc_html($total_obst ?: '—'); ?></div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:20px; text-align:center;">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700;">Jumps / Kicker</div>
                <div style="font-size:2rem; font-weight:800; color:#2563eb; margin-top:5px;"><?php echo esc_html($jumps ?: '—'); ?></div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:20px; text-align:center;">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700;">Jibs, Rails & Tubes</div>
                <div style="font-size:2rem; font-weight:800; color:#0891b2; margin-top:5px;"><?php echo esc_html($jibs ?: '—'); ?></div>
            </div>
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:20px; text-align:center;">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700;">Shaper Crew</div>
                <div style="font-size:1.1rem; font-weight:700; color:#0f172a; margin-top:10px;"><?php echo esc_html($crew ?: 'Local Crew'); ?></div>
            </div>
        </div>

        <!-- 3. TWO-COLUMN DETAILS MATRIX -->
        <div style="display:grid; grid-template-columns: 1fr 340px; gap:30px;">
            
            <div>
                <!-- RATINGS -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:25px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.25rem; margin-top:0; margin-bottom:15px; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">🎯 Difficulty Level Breakdown</h3>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">Beginner / Easy Lines:</span>
                            <div><?php echo $star_html($rate_beg); ?></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">Intermediate / Medium Lines:</span>
                            <div><?php echo $star_html($rate_int); ?></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600;">Advanced / Pro / XL Lines:</span>
                            <div><?php echo $star_html($rate_pro); ?></div>
                        </div>
                    </div>
                </div>

                <!-- PIPE DETAILS -->
                <?php if ($has_pipe && $pipe_type && $pipe_type !== 'None'): ?>
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; padding:20px; margin-bottom:25px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                            <span style="font-size:1.5rem;">🏂</span>
                            <h3 style="font-size:1.2rem; margin:0; color:#1e40af;">Pipe Specifications</h3>
                        </div>
                        <p style="margin:0; font-size:1.05rem; color:#1e3a8a;"><strong>Pipe Setup:</strong> <?php echo esc_html($pipe_type); ?></p>
                    </div>
                <?php endif; ?>

                <!-- SEASON & EVENTS -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.25rem; margin-top:0; margin-bottom:15px; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">📅 Season & Events</h3>
                    <p style="margin:0 0 15px 0;"><strong>Operating Window:</strong> <?php echo esc_html($season ?: 'Winter Season'); ?></p>
                    <?php if ($events): ?>
                        <a href="<?php echo esc_url($events); ?>" target="_blank" rel="noopener noreferrer" style="display:inline-block; background:#2563eb; color:#fff; font-weight:600; text-decoration:none; padding:10px 18px; border-radius:6px; font-size:0.95rem;">View Event Calendar & Contests ↗</a>
                    <?php endif; ?>
                </div>
            </div>

            <div>
                <!-- INFRASTRUCTURE -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:25px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.15rem; margin-top:0; margin-bottom:15px; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">⚡ Infrastructure</h3>
                    <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:10px; font-size:0.95rem;">
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Park Lift:</span>
                            <strong><?php echo $has_lift ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Daily Shape:</span>
                            <strong><?php echo $daily_shape ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Snowmaking:</span>
                            <strong><?php echo $snowmaking ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Groomer:</span>
                            <strong><?php echo $groomer ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Night Sessions / Floodlight:</span>
                            <strong><?php echo $nightpark ? '✓ Yes' : '—'; ?></strong>
                        </li>
                    </ul>
                </div>

                <!-- TRAVEL & TRANSIT -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:25px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.15rem; margin-top:0; margin-bottom:15px; border-bottom:2px solid #f1f5f9; padding-bottom:10px;">🚆 Travel & Arrival</h3>
                    <?php if ($transit): ?>
                        <p style="margin:0 0 10px 0; font-size:0.95rem;"><strong>Public Transit Score:</strong> <span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-weight:600;"><?php echo esc_html($transit); ?></span></p>
                    <?php endif; ?>
                    <?php if ($train): ?>
                        <p style="margin:0 0 10px 0; font-size:0.95rem;"><strong>Nearest Train:</strong> <?php echo esc_html($train); ?></p>
                    <?php endif; ?>
                    <?php if ($airport): ?>
                        <p style="margin:0; font-size:0.95rem;"><strong>Nearest Airport:</strong> <?php echo esc_html($airport); ?></p>
                    <?php endif; ?>
                </div>

                <!-- LINKS & CONTACT -->
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:20px; text-align:center;">
                    <?php if ($website): ?>
                        <a href="<?php echo esc_url($website); ?>" target="_blank" rel="noopener noreferrer" style="display:block; background:#0f172a; color:#fff; font-weight:700; text-decoration:none; padding:12px; border-radius:6px; margin-bottom:10px;">Official Website ↗</a>
                    <?php endif; ?>
                    <?php if ($insta): ?>
                        <div style="font-size:0.95rem; color:#475569;">Instagram: <strong style="color:#e1306c;"><?php echo esc_html($insta); ?></strong></div>
                    <?php endif; ?>
                </div>
            </div>

        </div>

    </div>
    <style>
    @media(max-width: 850px) {
        .wsf-snowpark-template > div:nth-child(3) {
            grid-template-columns: 1fr !important;
        }
    }
    </style>
    <?php
}
