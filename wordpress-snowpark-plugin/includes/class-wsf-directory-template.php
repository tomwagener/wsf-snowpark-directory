<?php
/**
 * Render Interactive Snowpark Directory & Faceted Filter Grid
 * Usage via Shortcode: [wsf_snowpark_directory]
 */

if (!defined('ABSPATH')) exit;

add_shortcode('wsf_snowpark_directory', 'wsf_render_snowpark_directory_shortcode');

function wsf_render_snowpark_directory_shortcode() {
    $countries = get_terms(['taxonomy' => 'snowpark_location', 'parent' => 0, 'hide_empty' => true]);
    $facilities = get_terms(['taxonomy' => 'facility_type', 'hide_empty' => true]);

    $all_parks = get_posts([
        'post_type'      => 'snowpark',
        'posts_per_page' => -1,
        'post_status'    => 'publish',
        'orderby'        => 'title',
        'order'          => 'ASC',
    ]);

    ob_start();
    ?>
    <div id="wsf-directory-app" style="font-family:inherit; color:#1e293b; max-width:1200px; margin:0 auto; padding:10px 0;">
        
        <!-- FILTER BAR -->
        <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:12px; padding:25px; margin-bottom:30px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.05);">
            <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:15px; margin-bottom:20px;">
                
                <!-- Search input -->
                <div>
                    <label style="display:block; font-size:0.85rem; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:5px;">Search Park / Resort</label>
                    <input type="text" id="wsf-search" placeholder="Type park or resort..." style="width:100%; padding:10px 14px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.95rem; box-sizing:border-box;">
                </div>

                <!-- Country Dropdown -->
                <div>
                    <label style="display:block; font-size:0.85rem; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:5px;">Country / Location</label>
                    <select id="wsf-country-filter" style="width:100%; padding:10px 14px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.95rem; background:#fff; box-sizing:border-box;">
                        <option value="">All Countries (Worldwide)</option>
                        <?php foreach ($countries as $c): ?>
                            <option value="<?php echo esc_attr(strtolower($c->name)); ?>"><?php echo esc_html($c->name); ?> (<?php echo $c->count; ?>)</option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <!-- Facility Type Dropdown -->
                <div>
                    <label style="display:block; font-size:0.85rem; font-weight:700; text-transform:uppercase; color:#64748b; margin-bottom:5px;">Facility Type</label>
                    <select id="wsf-facility-filter" style="width:100%; padding:10px 14px; border:1px solid #cbd5e1; border-radius:6px; font-size:0.95rem; background:#fff; box-sizing:border-box;">
                        <option value="">All Facility Types</option>
                        <?php foreach ($facilities as $f): ?>
                            <option value="<?php echo esc_attr(strtolower($f->name)); ?>"><?php echo esc_html($f->name); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>

            </div>

            <!-- Feature Checkboxes -->
            <div style="display:flex; gap:20px; flex-wrap:wrap; border-top:1px solid #e2e8f0; padding-top:15px; font-size:0.95rem; align-items:center;">
                <span style="font-weight:700; color:#475569; font-size:0.85rem; text-transform:uppercase;">Quick Filters:</span>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
                    <input type="checkbox" id="wsf-pipe-filter" value="1"> 🏂 Has Superpipe / Pipe
                </label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
                    <input type="checkbox" id="wsf-night-filter" value="1"> 🌙 Nightpark / Floodlight
                </label>
                <label style="cursor:pointer; display:inline-flex; align-items:center; gap:6px;">
                    <input type="checkbox" id="wsf-verified-filter" value="1"> ⭐ WSF Verified Only
                </label>
            </div>
        </div>

        <!-- RESULTS COUNT -->
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
            <div id="wsf-results-count" style="font-size:1.1rem; font-weight:700; color:#0f172a;">Showing <?php echo count($all_parks); ?> Snowparks</div>
        </div>

        <!-- PARKS GRID -->
        <div id="wsf-parks-grid" style="display:grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap:25px;">
            <?php foreach ($all_parks as $p): 
                $pid = $p->ID;
                $resort = get_field('resort_name', $pid) ?: $p->post_title;
                $stars = get_field('overall_wspl_stars', $pid);
                $obst = get_field('total_obstacles', $pid);
                $pipe = get_field('has_pipe', $pid);
                $pipe_type = get_field('pipe_type', $pid);
                $night = get_field('has_nightpark', $pid);
                $verified = get_field('wsf_verified', $pid);
                $elev = get_field('elevation_masl', $pid);
                
                // Location terms
                $l_terms = get_the_terms($pid, 'snowpark_location');
                $country_name = '';
                if ($l_terms && !is_wp_error($l_terms)) {
                    foreach ($l_terms as $lt) {
                        if ($lt->parent == 0) {
                            $country_name = $lt->name;
                            break;
                        }
                    }
                }

                // Facility terms
                $f_terms = get_the_terms($pid, 'facility_type');
                $facility_name = ($f_terms && !is_wp_error($f_terms)) ? $f_terms[0]->name : 'Resort';
            ?>
                <div class="wsf-park-card" 
                     data-name="<?php echo esc_attr(strtolower($p->post_title . ' ' . $resort)); ?>"
                     data-country="<?php echo esc_attr(strtolower($country_name)); ?>"
                     data-facility="<?php echo esc_attr(strtolower($facility_name)); ?>"
                     data-pipe="<?php echo $pipe ? '1' : '0'; ?>"
                     data-night="<?php echo $night ? '1' : '0'; ?>"
                     data-verified="<?php echo $verified ? '1' : '0'; ?>"
                     style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:22px; display:flex; flex-direction:column; justify-content:space-between; box-shadow:0 2px 4px rgba(0,0,0,0.03); transition: transform 0.2s, box-shadow 0.2s;">
                    
                    <div>
                        <!-- Badges -->
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                            <span style="font-size:0.8rem; font-weight:700; color:#2563eb; background:#eff6ff; padding:3px 8px; border-radius:4px; text-transform:uppercase;">
                                📍 <?php echo esc_html($country_name ?: 'Resort'); ?>
                            </span>
                            <?php if ($verified): ?>
                                <span style="background:#fef3c7; color:#92400e; font-size:0.75rem; font-weight:700; padding:3px 8px; border-radius:9999px;">✓ WSF Verified</span>
                            <?php endif; ?>
                        </div>

                        <!-- Title & Resort -->
                        <h3 style="font-size:1.25rem; font-weight:800; margin:0 0 6px 0; line-height:1.3;">
                            <a href="<?php echo get_permalink($pid); ?>" style="color:#0f172a; text-decoration:none;"><?php echo esc_html($p->post_title); ?></a>
                        </h3>
                        <div style="font-size:0.95rem; color:#64748b; margin-bottom:15px;"><?php echo esc_html($resort); ?></div>

                        <!-- Stats Pills -->
                        <div style="display:flex; gap:8px; flex-wrap:wrap; margin-bottom:15px;">
                            <span style="background:#f1f5f9; color:#334155; font-size:0.85rem; font-weight:600; padding:4px 9px; border-radius:6px;">
                                ⚡ <?php echo esc_html($obst ? $obst . ' Features' : 'Terrain Park'); ?>
                            </span>
                            <?php if ($pipe && $pipe_type && $pipe_type !== 'None'): ?>
                                <span style="background:#ecfdf5; color:#065f46; font-size:0.85rem; font-weight:600; padding:4px 9px; border-radius:6px;">
                                    🏂 <?php echo esc_html($pipe_type); ?>
                                </span>
                            <?php endif; ?>
                            <?php if ($elev): ?>
                                <span style="background:#f8fafc; color:#64748b; font-size:0.85rem; padding:4px 9px; border-radius:6px;">
                                    ⛰️ <?php echo esc_html($elev); ?>
                                </span>
                            <?php endif; ?>
                        </div>
                    </div>

                    <!-- Bottom Link & Stars -->
                    <div style="border-top:1px solid #f1f5f9; padding-top:15px; display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <?php if ($stars): ?>
                                <span style="color:#f59e0b; font-size:0.95rem;">
                                    <?php for ($s = 1; $s <= 5; $s++) echo ($s <= $stars) ? '★' : '☆'; ?>
                                </span>
                            <?php endif; ?>
                        </div>
                        <a href="<?php echo get_permalink($pid); ?>" style="color:#2563eb; font-weight:700; font-size:0.9rem; text-decoration:none;">View Setup →</a>
                    </div>

                </div>
            <?php endforeach; ?>
        </div>

    </div>

    <!-- LIVE FILTER JAVASCRIPT -->
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const searchInput = document.getElementById('wsf-search');
        const countryFilter = document.getElementById('wsf-country-filter');
        const facilityFilter = document.getElementById('wsf-facility-filter');
        const pipeFilter = document.getElementById('wsf-pipe-filter');
        const nightFilter = document.getElementById('wsf-night-filter');
        const verifiedFilter = document.getElementById('wsf-verified-filter');
        const cards = document.querySelectorAll('.wsf-park-card');
        const countDisplay = document.getElementById('wsf-results-count');

        function filterParks() {
            const query = searchInput.value.toLowerCase().trim();
            const country = countryFilter.value.toLowerCase();
            const facility = facilityFilter.value.toLowerCase();
            const requirePipe = pipeFilter.checked;
            const requireNight = nightFilter.checked;
            const requireVerified = verifiedFilter.checked;

            let visibleCount = 0;

            cards.forEach(card => {
                const name = card.dataset.name;
                const cCountry = card.dataset.country;
                const cFacility = card.dataset.facility;
                const hasPipe = card.dataset.pipe === '1';
                const hasNight = card.dataset.night === '1';
                const isVerified = card.dataset.verified === '1';

                const matchesSearch = !query || name.includes(query);
                const matchesCountry = !country || cCountry.includes(country);
                const matchesFacility = !facility || cFacility.includes(facility);
                const matchesPipe = !requirePipe || hasPipe;
                const matchesNight = !requireNight || hasNight;
                const matchesVerified = !requireVerified || isVerified;

                if (matchesSearch && matchesCountry && matchesFacility && matchesPipe && matchesNight && matchesVerified) {
                    card.style.display = 'flex';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            countDisplay.innerText = `Showing ${visibleCount} Snowparks`;
        }

        searchInput.addEventListener('input', filterParks);
        countryFilter.addEventListener('change', filterParks);
        facilityFilter.addEventListener('change', filterParks);
        pipeFilter.addEventListener('change', filterParks);
        nightFilter.addEventListener('change', filterParks);
        verifiedFilter.addEventListener('change', filterParks);
    });
    </script>
    <?php
    return ob_get_clean();
}
