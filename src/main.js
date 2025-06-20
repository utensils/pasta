const { invoke } = window.__TAURI__.core;

let speedSlider;
let speedText;
let saveButton;
let leftClickPasteCheckbox;

const speedLabels = ['Slow', 'Normal', 'Fast'];

async function loadConfig() {
    try {
        const config = await invoke('get_config');
        
        // Convert typing speed to slider value
        const speedValue = config.typing_speed === 'Slow' ? 0 : 
                          config.typing_speed === 'Normal' ? 1 : 2;
        speedSlider.value = speedValue;
        updateSpeedText(speedValue);
        
        // Set left-click paste checkbox
        leftClickPasteCheckbox.checked = config.left_click_paste || false;
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

async function saveConfig() {
    try {
        const speedValue = parseInt(speedSlider.value);
        const typing_speed = speedLabels[speedValue];
        const left_click_paste = leftClickPasteCheckbox.checked;
        
        await invoke('save_config', { typing_speed, left_click_paste });
        
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
    speedSlider = document.getElementById('speed-slider');
    speedText = document.getElementById('speed-text');
    saveButton = document.getElementById('save-button');
    leftClickPasteCheckbox = document.getElementById('left-click-paste');
    
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