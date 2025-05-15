const fileDropArea = document.getElementById('fileDropArea');
const fileInput = document.getElementById('fileInput');

fileDropArea.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length) {
        handleFiles(fileInput.files);
    }
});

fileDropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileDropArea.classList.add('dragover');
});

fileDropArea.addEventListener('dragleave', () => {
    fileDropArea.classList.remove('dragover');
});

fileDropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileDropArea.classList.remove('dragover');

    if (e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFiles(e.dataTransfer.files);
    }
});

function handleFiles(files) {
    const file = files[0];
    const validTypes = ['image/jpeg', 'image/png', 'application/pdf', 'image/svg+xml'];

    if (!validTypes.includes(file.type)) {
        alert('Будь ласка, виберіть файл у підтримуваному форматі (JPG, PNG, PDF, SVG)');
        return;
    }
    console.log('Файл завантажено:', file.name);

    fileDropArea.querySelector('p').textContent = `Файл: ${file.name}`;

}