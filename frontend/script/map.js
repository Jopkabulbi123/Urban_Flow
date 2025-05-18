document.addEventListener('DOMContentLoaded', function() {
    // Ініціалізація мапи
    const map = L.map('map-container').setView([50.4501, 30.5234], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    let rectangle = null;
    let startPoint = null;
    let endPoint = null;

    // Обробник кліку на мапі
    map.on('click', function(e) {
        if (!startPoint) {
            startPoint = e.latlng;
            updateCoordinatesDisplay();
        } else if (!endPoint) {
            endPoint = e.latlng;
            drawRectangle();
            updateCoordinatesDisplay();
        } else {
            // Якщо обидві точки вже є, скидаємо вибір
            resetSelection();
            startPoint = e.latlng;
            updateCoordinatesDisplay();
        }
    });

    function drawRectangle() {
        if (rectangle) {
            map.removeLayer(rectangle);
        }
        
        const bounds = L.latLngBounds(startPoint, endPoint);
        rectangle = L.rectangle(bounds, {
            color: "#ff7800",
            weight: 2,
            fillOpacity: 0.2
        }).addTo(map);
        
        map.fitBounds(bounds);
    }

    function updateCoordinatesDisplay() {
        document.getElementById('nw-coords').textContent = startPoint 
            ? `${startPoint.lat.toFixed(4)}, ${startPoint.lng.toFixed(4)}` 
            : "Не вибрано";
        
        document.getElementById('se-coords').textContent = endPoint 
            ? `${endPoint.lat.toFixed(4)}, ${endPoint.lng.toFixed(4)}` 
            : "Не вибрано";
    }

    function resetSelection() {
        if (rectangle) {
            map.removeLayer(rectangle);
            rectangle = null;
        }
        startPoint = null;
        endPoint = null;
    }

    // Обробник кнопки аналізу
    document.getElementById('analyze-btn').addEventListener('click', async function() {
    if (!startPoint || !endPoint) {
        alert('Будь ласка, виберіть область на мапі');
        return;
    }

    try {
        const response = await fetch('http://127.0.0.1:8000/api/analyze/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                'nw_lat': startPoint.lat,
                'nw_lng': startPoint.lng,
                'se_lat': endPoint.lat,
                'se_lng': endPoint.lng
            })
        });

        // Додаткова перевірка на тип відповіді
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();
            throw new Error(`Очікувався JSON, а отримано: ${text.substring(0, 100)}...`);
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Невідома помилка сервера');
        }

        if (data.status === 'success') {
            displayResults(data.results);
        } else {
            alert('Помилка: ' + (data.message || 'Невідома помилка'));
        }
    } catch (error) {
        console.error('Помилка запиту:', error);
        alert('Сталася помилка: ' + error.message);
    }
});

    function displayResults(results) {
        const resultsContainer = document.getElementById('analysis-results');
        resultsContainer.innerHTML = `
            <div class="result-item">
                <span class="result-label">Площа:</span>
                <span class="result-value">${results.area} км²</span>
            </div>
            <div class="result-item">
                <span class="result-label">Кількість доріг:</span>
                <span class="result-value">${results.road_count}</span>
            </div>
            <div class="result-item">
                <span class="result-label">Найдовша вулиця:</span>
                <span class="result-value">${results.longest_road.name} (${results.longest_road.length} км)</span>
            </div>
            <div class="result-item">
                <span class="result-label">Рівень заторів:</span>
                <span class="result-value">${results.congestion}%</span>
            </div>
            <div class="result-item">
                <span class="result-label">Екологічність:</span>
                <span class="result-value">${results.ecology}%</span>
            </div>
        `;
    }
});