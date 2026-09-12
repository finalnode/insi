if (!window.pykimParsonsPointerReady) {
    window.pykimParsonsPointerReady = true;
    let drag = null;

    const moveParsons = event => {
        if (!drag || event.pointerId !== drag.pointerId) return;
        event.preventDefault();
        drag.card.style.top = `${event.clientY - drag.offsetY}px`;
        const cards = [...drag.list.querySelectorAll(
            ':scope > .pykim-parsons-block'
        )];
        const successor = cards.find(card => {
            const bounds = card.getBoundingClientRect();
            return event.clientY < bounds.top + bounds.height / 2;
        });
        drag.list.insertBefore(drag.placeholder, successor || null);
    };

    const stopParsons = event => {
        if (!drag || (event.pointerId !== undefined &&
            event.pointerId !== drag.pointerId)) return;
        const {card, list, placeholder} = drag;
        list.insertBefore(card, placeholder);
        placeholder.remove();
        card.removeAttribute('style');
        card.classList.remove('pykim-parsons-dragging');
        card.removeAttribute('aria-grabbed');
        drag = null;
    };

    document.addEventListener('pointerdown', event => {
        const card = event.target.closest('.pykim-parsons-block');
        if (!card || event.target.closest('button') || event.button !== 0) return;
        const list = card.closest('.pykim-parsons-list');
        if (!list) return;
        event.preventDefault();
        const bounds = card.getBoundingClientRect();
        const placeholder = document.createElement('div');
        placeholder.className = 'pykim-parsons-placeholder';
        placeholder.style.height = `${bounds.height}px`;
        list.insertBefore(placeholder, card);
        document.body.appendChild(card);
        Object.assign(card.style, {
            position: 'fixed',
            zIndex: '5000',
            left: `${bounds.left}px`,
            top: `${bounds.top}px`,
            width: `${bounds.width}px`,
            margin: '0',
            pointerEvents: 'none',
        });
        card.classList.add('pykim-parsons-dragging');
        card.setAttribute('aria-grabbed', 'true');
        drag = {
            card,
            list,
            placeholder,
            pointerId: event.pointerId,
            offsetY: event.clientY - bounds.top,
        };
    }, {passive: false});
    window.addEventListener('pointermove', moveParsons, {passive: false});
    window.addEventListener('pointerup', stopParsons);
    window.addEventListener('pointercancel', stopParsons);
    window.addEventListener('blur', stopParsons);
}
window.pykimMoveParsons = function(button, direction) {
    const card = button.closest('.pykim-parsons-block');
    const sibling = direction < 0
        ? card.previousElementSibling : card.nextElementSibling;
    if (!sibling) return;
    if (direction < 0) card.parentElement.insertBefore(card, sibling);
    else card.parentElement.insertBefore(sibling, card);
};
