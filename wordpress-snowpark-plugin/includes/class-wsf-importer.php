<?php
/**
 * Native WSF Snowpark CSV / Google Sheets Importer & Auto-Sync Engine
 */

if (!defined('ABSPATH')) exit;

class WSF_Snowpark_Importer {

    public function __construct() {
        add_action('admin_menu', [$this, 'add_admin_menu']);
        add_action('admin_init', [$this, 'handle_manual_sync']);
        add_action('wsf_daily_snowpark_sync_event', [$this, 'run_cron_sync']);

        // Schedule daily cron if not scheduled
        if (!wp_next_scheduled('wsf_daily_snowpark_sync_event')) {
            wp_schedule_event(time(), 'daily', 'wsf_daily_snowpark_sync_event');
        }
    }

    public function add_admin_menu() {
        add_submenu_page(
            'edit.php?post_type=snowpark',
            __('Sync & Import', 'wsf-guide'),
            __('Sync / Import CSV', 'wsf-guide'),
            'manage_options',
            'wsf-snowpark-sync',
            [$this, 'render_admin_page']
        );
    }

    public function render_admin_page() {
        $sheet_url = get_option('wsf_snowpark_sheet_url', '');
        ?>
        <div class="wrap">
            <h1><?php _e('WSF Snowpark Guide: Data Sync & Import', 'wsf-guide'); ?></h1>
            <p><?php _e('Import or synchronize all 175+ Snowparks directly from a local CSV upload or published Google Sheets URL.', 'wsf-guide'); ?></p>

            <?php if (isset($_GET['imported'])): ?>
                <div class="notice notice-success is-dismissible">
                    <p><strong><?php echo sprintf(__('Success! Processed %d snowparks.', 'wsf-guide'), intval($_GET['imported'])); ?></strong></p>
                </div>
            <?php endif; ?>

            <div style="background:#fff; padding:20px; border:1px solid #ccd0d4; border-radius:4px; max-width:800px; margin-top:20px;">
                <h2><?php _e('Option A: Upload Local Master CSV', 'wsf-guide'); ?></h2>
                <form method="post" enctype="multipart/form-data" action="<?php echo admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync'); ?>">
                    <?php wp_nonce_field('wsf_import_nonce', 'wsf_nonce'); ?>
                    <input type="hidden" name="wsf_action" value="upload_csv">
                    <p>
                        <input type="file" name="wsf_csv_file" accept=".csv" required>
                    </p>
                    <p>
                        <button type="submit" class="button button-primary button-large"><?php _e('Upload & Import Snowparks', 'wsf-guide'); ?></button>
                    </p>
                </form>

                <hr style="margin:25px 0;">

                <h2><?php _e('Option B: Google Sheets Live Sync (Automated)', 'wsf-guide'); ?></h2>
                <form method="post" action="<?php echo admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync'); ?>">
                    <?php wp_nonce_field('wsf_import_nonce', 'wsf_nonce'); ?>
                    <input type="hidden" name="wsf_action" value="save_sheet_url">
                    <table class="form-table">
                        <tr>
                            <th scope="row"><label for="wsf_sheet_url"><?php _e('Google Sheets CSV URL', 'wsf-guide'); ?></label></th>
                            <td>
                                <input type="url" name="wsf_sheet_url" id="wsf_sheet_url" value="<?php echo esc_attr($sheet_url); ?>" class="regular-text" style="width:100%;" placeholder="https://docs.google.com/spreadsheets/d/e/.../pub?output=csv">
                                <p class="description"><?php _e('Google Sheet -> File > Share > Publish to web > Format: CSV.', 'wsf-guide'); ?></p>
                            </td>
                        </tr>
                    </table>
                    <p>
                        <button type="submit" class="button button-secondary"><?php _e('Save Google Sheets URL', 'wsf-guide'); ?></button>
                        <?php if ($sheet_url): ?>
                            <a href="<?php echo wp_nonce_url(admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync&wsf_action=sync_now'), 'wsf_import_nonce', 'wsf_nonce'); ?>" class="button button-primary"><?php _e('Sync Now From Google Sheets', 'wsf-guide'); ?></a>
                        <?php endif; ?>
                    </p>
                </form>
            </div>
        </div>
        <?php
    }

    public function handle_manual_sync() {
        if (!isset($_REQUEST['wsf_nonce']) || !wp_verify_nonce($_REQUEST['wsf_nonce'], 'wsf_import_nonce')) {
            return;
        }

        if (!current_user_can('manage_options')) {
            return;
        }

        // Action 1: Upload CSV
        if (isset($_POST['wsf_action']) && $_POST['wsf_action'] === 'upload_csv' && !empty($_FILES['wsf_csv_file']['tmp_name'])) {
            $count = $this->process_csv_file($_FILES['wsf_csv_file']['tmp_name']);
            wp_redirect(admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync&imported=' . $count));
            exit;
        }

        // Action 2: Save Google Sheet URL
        if (isset($_POST['wsf_action']) && $_POST['wsf_action'] === 'save_sheet_url') {
            update_option('wsf_snowpark_sheet_url', esc_url_raw($_POST['wsf_sheet_url']));
            wp_redirect(admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync'));
            exit;
        }

        // Action 3: Sync from Google Sheet Now
        if (isset($_GET['wsf_action']) && $_GET['wsf_action'] === 'sync_now') {
            $sheet_url = get_option('wsf_snowpark_sheet_url');
            if ($sheet_url) {
                $response = wp_remote_get($sheet_url, [
                    'timeout'    => 60,
                    'sslverify'  => false,
                    'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                ]);
                if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
                    $body = wp_remote_retrieve_body($response);
                    $tmp = tempnam(sys_get_temp_dir(), 'wsf_');
                    file_put_contents($tmp, $body);
                    $count = $this->process_csv_file($tmp);
                    @unlink($tmp);
                    wp_redirect(admin_url('edit.php?post_type=snowpark&page=wsf-snowpark-sync&imported=' . $count));
                    exit;
                }
            }
        }
    }

    public function run_cron_sync() {
        $sheet_url = get_option('wsf_snowpark_sheet_url');
        if ($sheet_url) {
            $response = wp_remote_get($sheet_url, [
                'timeout'    => 60,
                'sslverify'  => false,
                'user-agent' => 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]);
            if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
                $body = wp_remote_retrieve_body($response);
                $tmp = tempnam(sys_get_temp_dir(), 'wsf_');
                file_put_contents($tmp, $body);
                $this->process_csv_file($tmp);
                @unlink($tmp);
            }
        }
    }

    public function process_csv_file($file_path) {
        if (!file_exists($file_path) || !is_readable($file_path)) {
            return 0;
        }

        $handle = fopen($file_path, 'r');
        if (!$handle) return 0;

        $header = null;
        $processed = 0;

        while (($row = fgetcsv($handle, 4096, ',')) !== false) {
            // Skip empty rows or potential metadata lines
            if (empty(array_filter($row)) || (isset($row[0]) && strpos($row[0], 'wsf_park_guide_master') !== false)) {
                continue;
            }

            if (!$header) {
                $header = array_map('trim', $row);
                continue;
            }

            if (count($header) > count($row)) {
                $row = array_pad($row, count($header), '');
            }

            $data = array_combine($header, array_slice($row, 0, count($header)));
            $this->import_single_snowpark($data);
            $processed++;
        }

        fclose($handle);
        return $processed;
    }

    private function import_single_snowpark($data) {
        $park_id   = sanitize_title(trim($data['park_id'] ?? ''));
        $park_name = sanitize_text_field(trim($data['park_name'] ?? ''));

        if (empty($park_id) || empty($park_name)) {
            return;
        }

        // 1. Find existing post by park_id meta or post_name
        $existing = get_posts([
            'post_type'      => 'snowpark',
            'meta_key'       => 'park_id',
            'meta_value'     => $park_id,
            'posts_per_page' => 1,
            'post_status'    => 'any',
        ]);

        $post_id = 0;
        if (!empty($existing)) {
            $post_id = $existing[0]->ID;
            wp_update_post([
                'ID'         => $post_id,
                'post_title' => $park_name,
            ]);
        } else {
            $post_id = wp_insert_post([
                'post_type'   => 'snowpark',
                'post_title'  => $park_name,
                'post_name'   => $park_id,
                'post_status' => 'publish',
            ]);
        }

        if (!$post_id || is_wp_error($post_id)) {
            return;
        }

        // 2. Taxonomies
        // Location (Hierarchical: Country > Region)
        $country = sanitize_text_field(trim($data['country'] ?? ''));
        $region  = sanitize_text_field(trim($data['region'] ?? ''));

        if (!empty($country)) {
            $country_term = term_exists($country, 'snowpark_location');
            if (!$country_term) {
                $country_term = wp_insert_term($country, 'snowpark_location');
            }
            $parent_id = is_array($country_term) ? (int)$country_term['term_id'] : (int)$country_term;

            $term_ids = [$parent_id];
            if (!empty($region)) {
                $region_term = term_exists($region, 'snowpark_location', $parent_id);
                if (!$region_term) {
                    $region_term = wp_insert_term($region, 'snowpark_location', ['parent' => $parent_id]);
                }
                $child_id = is_array($region_term) ? (int)$region_term['term_id'] : (int)$region_term;
                $term_ids[] = $child_id;
            }
            wp_set_object_terms($post_id, $term_ids, 'snowpark_location');
        }

        // Facility Type
        $facility_type = sanitize_text_field(trim($data['facility_type'] ?? ''));
        if (!empty($facility_type)) {
            wp_set_object_terms($post_id, [$facility_type], 'facility_type');
        }

        // 3. Helper for Boolean / Coordinates
        $parse_bool = function($val) {
            $val = strtolower(trim((string)$val));
            return in_array($val, ['yes', '1', 'true'], true) ? 1 : 0;
        };

        $parse_coord = function($val) {
            if (!$val) return '';
            $val = trim((string)$val);
            if (strpos($val, '.') !== false) return (float)$val;
            if (strpos($val, '-') === 0) {
                return (float)(substr($val, 0, 3) . '.' . substr($val, 3));
            }
            return (float)(substr($val, 0, 2) . '.' . substr($val, 2));
        };

        // 4. Save Custom Fields / ACF
        $fields = [
            'park_id'                => $park_id,
            'resort_name'            => sanitize_text_field($data['resort_name'] ?? ''),
            'elevation_masl'         => sanitize_text_field($data['elevation_masl'] ?? ''),
            'size_category'          => sanitize_text_field($data['size_category'] ?? ''),
            'total_obstacles'        => intval($data['total_obstacles'] ?? 0),
            'jump_count'             => intval($data['jump_count'] ?? 0),
            'jib_count'              => intval($data['jib_count'] ?? 0),
            'has_pipe'               => $parse_bool($data['has_pipe'] ?? ''),
            'pipe_type'              => sanitize_text_field($data['pipe_type'] ?? ''),
            'progression_features'   => $parse_bool($data['progression_features'] ?? ''),
            'overall_wspl_stars'     => intval($data['overall_wspl_stars'] ?? 0),
            'rating_beginner'        => intval($data['rating_beginner'] ?? 0),
            'rating_intermediate'    => intval($data['rating_intermediate'] ?? 0),
            'rating_advanced'        => intval($data['rating_advanced'] ?? ($data['rating_advanced_pro'] ?? 0)),
            'rating_pro_xl'          => intval($data['rating_pro_xl'] ?? ($data['rating_advanced_pro'] ?? 0)),
            'rating_advanced_pro'    => intval($data['rating_advanced'] ?? ($data['rating_advanced_pro'] ?? 0)),
            'shaper_crew'            => sanitize_text_field($data['shaper_crew'] ?? ''),
            'daily_shape'            => $parse_bool($data['daily_shape'] ?? ''),
            'dedicated_groomer'      => $parse_bool($data['dedicated_groomer'] ?? ''),
            'dedicated_snowmaking'   => $parse_bool($data['dedicated_snowmaking'] ?? ''),
            'has_park_lift'          => $parse_bool($data['has_park_lift'] ?? ''),
            'has_nightpark'          => $parse_bool($data['has_nightpark'] ?? ''),
            'season_window'          => sanitize_text_field($data['season_window'] ?? ''),
            'public_transit_score'   => sanitize_text_field($data['public_transit_score'] ?? ''),
            'nearest_train_station'  => sanitize_text_field($data['nearest_train_station'] ?? ''),
            'nearest_airport'        => sanitize_text_field($data['nearest_airport'] ?? ''),
            'latitude'               => $parse_coord($data['latitude'] ?? ''),
            'longitude'              => $parse_coord($data['longitude'] ?? ''),
            'instagram_handle'       => sanitize_text_field($data['instagram_handle'] ?? ''),
            'website_url'            => esc_url_raw($data['website_url'] ?? ''),
            'event_calendar_url'     => esc_url_raw($data['event_calendar_url'] ?? ''),
            'wsf_verified'           => $parse_bool($data['wsf_verified'] ?? ''),
        ];

        foreach ($fields as $key => $val) {
            update_post_meta($post_id, $key, $val);
            if (function_exists('update_field')) {
                update_field($key, $val, $post_id);
            }
        }
    }
}

new WSF_Snowpark_Importer();
