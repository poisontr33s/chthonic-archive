use serde::Deserialize;
use std::fs;
use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime};
use log::{info, warn};

#[derive(Deserialize, Debug, Clone)]
pub struct IslandWeather {
    pub isle: String,
    pub wind_dir: f32,
    pub wind_speed: f32,
}

#[derive(Deserialize, Debug, Clone)]
pub struct LiveBoundary {
    pub islands: Vec<IslandWeather>,
}

#[derive(Clone, Copy, Debug)]
pub struct WeatherState {
    pub wind_dir: f32,
    pub wind_speed: f32,
}

impl Default for WeatherState {
    fn default() -> Self {
        Self { wind_dir: 90.0, wind_speed: 3.8 } // Default fallback
    }
}

pub struct WeatherSpine {
    current_state: Arc<Mutex<WeatherState>>,
}

impl WeatherSpine {
    pub fn new(path: &'static str) -> Self {
        let current_state = Arc::new(Mutex::new(WeatherState::default()));
        let state_clone = Arc::clone(&current_state);
        
        std::thread::spawn(move || {
            let mut last_modified = SystemTime::UNIX_EPOCH;
            loop {
                if let Ok(metadata) = fs::metadata(path) {
                    if let Ok(modified) = metadata.modified() {
                        if modified > last_modified {
                            last_modified = modified;
                            if let Ok(content) = fs::read_to_string(path) {
                                if let Ok(boundary) = serde_json::from_str::<LiveBoundary>(&content) {
                                    // Use New-Providence as the anchor, matching the celestial sun tracking
                                    if let Some(np) = boundary.islands.iter().find(|i| i.isle == "New-Providence") {
                                        let mut state = state_clone.lock().unwrap();
                                        state.wind_dir = np.wind_dir;
                                        state.wind_speed = np.wind_speed;
                                        info!("🌬️ Weather Spine updated (New-Providence): wind = {} m/s at {}°", np.wind_speed, np.wind_dir);
                                    }
                                } else {
                                    warn!("⚠️ Failed to parse {path}");
                                }
                            }
                        }
                    }
                }
                std::thread::sleep(Duration::from_millis(1000));
            }
        });

        Self { current_state }
    }
    
    pub fn get_state(&self) -> WeatherState {
        *self.current_state.lock().unwrap()
    }
}
