document.addEventListener('DOMContentLoaded', function () {
    const dangerLinks = document.querySelectorAll('[data-confirm]');
    dangerLinks.forEach(function (link) {
        link.addEventListener('click', function (event) {
            const text = link.getAttribute('data-confirm') || 'Подтвердить действие?';
            if (!window.confirm(text)) {
                event.preventDefault();
            }
        });
    });
});
