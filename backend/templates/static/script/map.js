document.addEventListener('DOMContentLoaded', function() {
    const map = L.map('map-container').setView([50.4501, 30.5234], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    let rectangle = null;
    let startPoint = null;
    let endPoint = null;

    map.on('click', function(e) {
        if (!startPoint) {
            startPoint = e.latlng;
        } else if (!endPoint) {
            endPoint = e.latlng;
            drawRectangle();
        } else {
            resetSelection();
            startPoint = e.latlng;
        }
        updateCoordinatesDisplay();
    });

    function drawRectangle() {
        if (rectangle) map.removeLayer(rectangle);

        rectangle = L.rectangle(L.latLngBounds(startPoint, endPoint), {
            color: "#ff7800",
            weight: 2,
            fillOpacity: 0.2
        }).addTo(map);

        map.fitBounds(rectangle.getBounds());
    }

    function updateCoordinatesDisplay() {
        document.getElementById('nw-coords').textContent =
            startPoint ? `${startPoint.lat.toFixed(4)}, ${startPoint.lng.toFixed(4)}` : "Не вибрано";

        document.getElementById('se-coords').textContent =
            endPoint ? `${endPoint.lat.toFixed(4)}, ${endPoint.lng.toFixed(4)}` : "Не вибрано";
    }

    function resetSelection() {
        if (rectangle) {
            map.removeLayer(rectangle);
            rectangle = null;
        }
        startPoint = null;
        endPoint = null;
    }

    document.getElementById('analyze-btn').addEventListener('click', analyzeArea);

    async function analyzeArea() {
        if (!startPoint || !endPoint) {
            alert('Будь ласка, виберіть область на мапі (два кліки)');
            return;
        }

        try {
            const response = await fetch('/api/analyze/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify({
                    nw_lat: startPoint.lat,
                    nw_lng: startPoint.lng,
                    se_lat: endPoint.lat,
                    se_lng: endPoint.lng
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Помилка сервера');
            }

            displayResults(data.results);

        } catch (error) {
            console.error('Помилка:', error);
            alert(`Помилка: ${error.message}`);
        }
    }

    function displayResults(results) {
        const container = document.getElementById('analysis-results');

        const formatScore = (score) => {
            const color = score > 70 ? 'positive' : score < 30 ? 'negative' : '';
            return `<span class="result-value ${color}">${score}%</span>`;
        };

        container.innerHTML = `
            <div class="result-item">
                <span class="result-label">Площа:</span>
                <span class="result-value">${results.area} км²</span>
            </div>
            <div class="result-item">
                <span class="result-label">Дороги:</span>
                <span class="result-value">${results.road_count} (${Object.entries(results.road_types)
                    .map(([type, count]) => `${type}: ${count}`)
                    .join(', ')})</span>
            </div>
            <div class="result-item">
                <span class="result-label">Найдовша:</span>
                <span class="result-value">${results.longest_road.name} (${results.longest_road.length} км)</span>
            </div>
            <div class="result-item">
                <span class="result-label">Затори:</span>
                ${formatScore(results.congestion)}
            </div>
            <div class="result-item">
                <span class="result-label">Екологія:</span>
                ${formatScore(results.ecology)}
            </div>
            <div class="result-item">
                <span class="result-label">Пішохідність:</span>
                ${formatScore(results.pedestrian_friendly)}
            </div>
            <div class="result-item">
                <span class="result-label">Транспорт:</span>
                ${formatScore(results.public_transport)}
            </div>
        `;
    }

    function getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
});