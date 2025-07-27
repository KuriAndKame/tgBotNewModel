document.addEventListener('DOMContentLoaded', function() {
    // Первоначальная загрузка новостей
    loadNews();

    // Обновление новостей каждые 30 секунд
    setInterval(loadNews, 30000);
});

function loadNews() {
    fetch('/get_news')
        .then(response => response.json())
        .then(news => {
            const container = document.getElementById('news-container');
            container.innerHTML = '';

            if (news.length === 0) {
                container.innerHTML = '<p>Новостей пока нет</p>';
                return;
            }

            news.forEach(item => {
                const newsElement = document.createElement('div');
                newsElement.className = 'card mb-3';
                newsElement.innerHTML = `
                    <div class="card-body">
                        <h3 class="card-title">${item.refactoredTitle}</h3>
                        <p class="card-text">${item.resume}</p>
                        <a href="/news/${item.id}" class="btn btn-primary">Читать полностью</a>
                    </div>
                `;
                container.appendChild(newsElement);
            });
        })
        .catch(error => {
            console.error('Ошибка при загрузке новостей:', error);
            document.getElementById('news-container').innerHTML =
                '<div class="alert alert-danger">Не удалось загрузить новости. Попробуйте обновить страницу.</div>';
        });
}