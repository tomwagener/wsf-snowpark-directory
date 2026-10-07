<?php
/**
 * Single Snowpark Template
 */

get_header();

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

<div id="primary" class="content-area site-main" style="padding: 40px 20px; background:#f8fafc;">
    <div class="site-container" style="max-width: 1200px; margin: 0 auto;">
        
        <!-- BACK LINK -->
        <div style="margin-bottom:20px;">
            <a href="<?php echo home_url('/snowparks/'); ?>" style="color:#2563eb; font-weight:700; text-decoration:none; font-size:0.95rem;">← Back to Snowpark Directory</a>
        </div>

        <!-- HERO BANNER -->
        <div style="background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color:#fff; border-radius:14px; padding:40px 35px; margin-bottom:30px; box-shadow:0 10px 25px -5px rgba(0,0,0,0.12);">
            <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:15px; align-items:center;">
                <?php if ($verified): ?>
                    <span style="background:#fbbf24; color:#78350f; font-weight:700; font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; padding:5px 12px; border-radius:9999px;">✓ WSF Verified</span>
                <?php endif; ?>
                <?php if ($location_str): ?>
                    <span style="background:rgba(255,255,255,0.15); color:#fff; font-size:0.9rem; padding:5px 14px; border-radius:9999px;">📍 <?php echo esc_html($location_str); ?></span>
                <?php endif; ?>
                <?php if ($elev): ?>
                    <span style="background:rgba(255,255,255,0.15); color:#fff; font-size:0.9rem; padding:5px 14px; border-radius:9999px;">⛰️ <?php echo esc_html($elev); ?></span>
                <?php endif; ?>
            </div>
            
            <h1 style="color:#fff; font-size:2.6rem; margin:0 0 10px 0; font-weight:800; line-height:1.2;"><?php echo esc_html($title); ?></h1>
            <p style="color:#94a3b8; font-size:1.15rem; margin:0 0 15px 0;">Home Resort: <strong style="color:#e2e8f0;"><?php echo esc_html($resort); ?></strong></p>
            
            <?php if ($stars): ?>
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="font-size:1rem; color:#cbd5e1;">WSPL Overall Rating:</span>
                    <?php echo $star_html($stars); ?>
                    <span style="font-weight:700; color:#fbbf24; font-size:1.1rem;"><?php echo esc_html($stars); ?> / 5</span>
                </div>
            <?php endif; ?>
        </div>

        <!-- QUICK STATS BAR -->
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:18px; margin-bottom:35px;">
            <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:22px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:0.05em;">Total Obstacles</div>
                <div style="font-size:2.2rem; font-weight:800; color:#0f172a; margin-top:5px;"><?php echo esc_html($total_obst ?: '—'); ?></div>
            </div>
            <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:22px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:0.05em;">Jumps / Kicker</div>
                <div style="font-size:2.2rem; font-weight:800; color:#2563eb; margin-top:5px;"><?php echo esc_html($jumps ?: '—'); ?></div>
            </div>
            <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:22px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:0.05em;">Jibs, Rails & Tubes</div>
                <div style="font-size:2.2rem; font-weight:800; color:#0891b2; margin-top:5px;"><?php echo esc_html($jibs ?: '—'); ?></div>
            </div>
            <div style="background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:22px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:0.05em;">Shaper Crew</div>
                <div style="font-size:1.15rem; font-weight:700; color:#0f172a; margin-top:12px;"><?php echo esc_html($crew ?: 'Local Crew'); ?></div>
            </div>
        </div>

        <!-- TWO COLUMN DETAILS -->
        <div style="display:grid; grid-template-columns: 1fr 360px; gap:30px;">
            
            <!-- LEFT COLUMN -->
            <div>
                <!-- RATINGS -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:28px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.3rem; margin-top:0; margin-bottom:18px; border-bottom:2px solid #f1f5f9; padding-bottom:12px; font-weight:800; color:#0f172a;">🎯 Difficulty Level Breakdown</h3>
                    <div style="display:flex; flex-direction:column; gap:14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; font-size:1rem;">Beginner / Easy Lines:</span>
                            <div><?php echo $star_html($rate_beg); ?></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; font-size:1rem;">Intermediate / Medium Lines:</span>
                            <div><?php echo $star_html($rate_int); ?></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span style="font-weight:600; font-size:1rem;">Advanced / Pro / XL Lines:</span>
                            <div><?php echo $star_html($rate_pro); ?></div>
                        </div>
                    </div>
                </div>

                <!-- PIPE DETAILS -->
                <?php if ($has_pipe && $pipe_type && $pipe_type !== 'None'): ?>
                    <div style="background:#eff6ff; border:1px solid #bfdbfe; border-radius:12px; padding:22px; margin-bottom:25px;">
                        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
                            <span style="font-size:1.6rem;">🏂</span>
                            <h3 style="font-size:1.25rem; margin:0; color:#1e40af; font-weight:800;">Pipe Specifications</h3>
                        </div>
                        <p style="margin:0; font-size:1.1rem; color:#1e3a8a;"><strong>Pipe Setup:</strong> <?php echo esc_html($pipe_type); ?></p>
                    </div>
                <?php endif; ?>

                <!-- SEASON & EVENTS -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:28px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.3rem; margin-top:0; margin-bottom:18px; border-bottom:2px solid #f1f5f9; padding-bottom:12px; font-weight:800; color:#0f172a;">📅 Season & Events</h3>
                    <p style="margin:0 0 18px 0; font-size:1.05rem;"><strong>Operating Window:</strong> <?php echo esc_html($season ?: 'Winter Season'); ?></p>
                    <?php if ($events): ?>
                        <a href="<?php echo esc_url($events); ?>" target="_blank" rel="noopener noreferrer" style="display:inline-block; background:#2563eb; color:#fff; font-weight:700; text-decoration:none; padding:12px 22px; border-radius:8px; font-size:0.95rem;">View Event Calendar & Contests ↗</a>
                    <?php endif; ?>
                </div>
            </div>

            <!-- RIGHT COLUMN -->
            <div>
                <!-- INFRASTRUCTURE -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:25px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.2rem; margin-top:0; margin-bottom:18px; border-bottom:2px solid #f1f5f9; padding-bottom:12px; font-weight:800; color:#0f172a;">⚡ Infrastructure</h3>
                    <ul style="list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:12px; font-size:0.95rem;">
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Park Lift:</span>
                            <strong style="color:<?php echo $has_lift ? '#059669' : '#64748b'; ?>"><?php echo $has_lift ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Daily Shape:</span>
                            <strong style="color:<?php echo $daily_shape ? '#059669' : '#64748b'; ?>"><?php echo $daily_shape ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Snowmaking:</span>
                            <strong style="color:<?php echo $snowmaking ? '#059669' : '#64748b'; ?>"><?php echo $snowmaking ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Dedicated Groomer:</span>
                            <strong style="color:<?php echo $groomer ? '#059669' : '#64748b'; ?>"><?php echo $groomer ? '✓ Yes' : '—'; ?></strong>
                        </li>
                        <li style="display:flex; justify-content:space-between;">
                            <span>Night Sessions / Floodlight:</span>
                            <strong style="color:<?php echo $nightpark ? '#059669' : '#64748b'; ?>"><?php echo $nightpark ? '✓ Yes' : '—'; ?></strong>
                        </li>
                    </ul>
                </div>

                <!-- TRAVEL & ARRIVAL -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:25px; margin-bottom:25px; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <h3 style="font-size:1.2rem; margin-top:0; margin-bottom:18px; border-bottom:2px solid #f1f5f9; padding-bottom:12px; font-weight:800; color:#0f172a;">🚆 Travel & Arrival</h3>
                    <?php if ($transit): ?>
                        <p style="margin:0 0 10px 0; font-size:0.95rem;"><strong>Public Transit:</strong> <span style="background:#e0f2fe; color:#0369a1; padding:2px 8px; border-radius:4px; font-weight:700;"><?php echo esc_html($transit); ?></span></p>
                    <?php endif; ?>
                    <?php if ($train): ?>
                        <p style="margin:0 0 10px 0; font-size:0.95rem;"><strong>Nearest Train:</strong> <?php echo esc_html($train); ?></p>
                    <?php endif; ?>
                    <?php if ($airport): ?>
                        <p style="margin:0; font-size:0.95rem;"><strong>Nearest Airport:</strong> <?php echo esc_html($airport); ?></p>
                    <?php endif; ?>
                </div>

                <!-- LINKS & CONTACT -->
                <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:25px; text-align:center; box-shadow:0 2px 4px rgba(0,0,0,0.02);">
                    <?php if ($website): ?>
                        <a href="<?php echo esc_url($website); ?>" target="_blank" rel="noopener noreferrer" style="display:block; background:#0f172a; color:#fff; font-weight:700; text-decoration:none; padding:12px; border-radius:8px; margin-bottom:12px; font-size:0.95rem;">Official Website ↗</a>
                    <?php endif; ?>
                    <?php if ($insta): ?>
                        <div style="font-size:0.95rem; color:#475569;">Instagram: <strong style="color:#e1306c;"><?php echo esc_html($insta); ?></strong></div>
                    <?php endif; ?>
                </div>
            </div>

        </div>

    </div>
</div>

<style>
@media(max-width: 850px) {
    .site-container > div:last-child {
        grid-template-columns: 1fr !important;
    }
}
</style>

<?php
get_footer();
