const { invoke } = window.__TAURI__.core;

let enabledCheckbox;
let speedSlider;
let speedText;
let saveButton;

const speedLabels = ['Slow', 'Normal', 'Fast'];

async function loadConfig() {
    try {
        const config = await invoke('get_config');
        enabledCheckbox.checked = config.enabled;
        
        // Convert typing speed to slider value
        const speedValue = config.typing_speed === 'Slow' ? 0 : 
                          config.typing_speed === 'Normal' ? 1 : 2;
        speedSlider.value = speedValue;
        updateSpeedText(speedValue);
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function saveConfig() {
    try {
        const enabled = enabledCheckbox.checked;
        const speedValue = parseInt(speedSlider.value);
        const typing_speed = speedLabels[speedValue];
        
        await invoke('save_config', { enabled, typing_speed });
        
        // Show save feedback
        showSavedIndicator();
    } catch (error) {
        console.error('Failed to save config:', error);
        saveButton.textContent = 'Error!';
        setTimeout(() => {
            saveButton.textContent = 'Save Settings';
        }, 2000);
    }
}

function showSavedIndicator() {
    const indicator = document.getElementById('saved-indicator');
    indicator.classList.add('show');
    
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 2000);
}

function updateSpeedText(value) {
    speedText.textContent = speedLabels[value];
}

window.addEventListener('DOMContentLoaded', () => {
    enabledCheckbox = document.getElementById('enabled-checkbox');
    speedSlider = document.getElementById('speed-slider');
    speedText = document.getElementById('speed-text');
    saveButton = document.getElementById('save-button');
    
    // Load current config
    loadConfig();
    
    // Setup event listeners
    speedSlider.addEventListener('input', (e) => {
        updateSpeedText(e.target.value);
    });
    
    saveButton.addEventListener('click', saveConfig);
    
    // Also save on Enter key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            saveConfig();
        }
    });
});