document.addEventListener('DOMContentLoaded', function () {
    const confirmTargets = document.querySelectorAll('[data-confirm]');
    confirmTargets.forEach(function (target) {
        const eventName = target.tagName === 'FORM' ? 'submit' : 'click';
        target.addEventListener(eventName, function (event) {
            const text = target.getAttribute('data-confirm') || 'Подтвердить действие?';
            if (!window.confirm(text)) {
                event.preventDefault();
            }
        });
    });
});
