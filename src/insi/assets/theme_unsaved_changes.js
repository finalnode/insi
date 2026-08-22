window.pykimHasUnsavedChanges = false;
window.addEventListener('beforeunload', event => {
    if (window.pykimHasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '';
    }
});
