const mapLocationNameEl = document.getElementById('map-location-name');
const mapDescriptionEl = document.getElementById('map-description');

export function updateMap(locationName, description) {
    if (mapLocationNameEl) {
        mapLocationNameEl.textContent = locationName || "Unknown Location";
    }
    if (mapDescriptionEl) {
        mapDescriptionEl.textContent = description || "";
    }
}