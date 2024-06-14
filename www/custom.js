function toggleCheckboxes(UIObjectIds) {
    console.log("Hiding checkboxes after lib upload");
    UIObjectIds.forEach(function(UIObjectId) {
        var UIObject = document.getElementById(UIObjectId);
        if (UIObject) {
            UIObject.disabled = true;  // Disable the checkbox
        } else {
            console.error('Checkbox element not found:', UIObjectId);
        }
    });
}

// Register the handler for the custom message
Shiny.addCustomMessageHandler("disableUIList", function(message) {
    toggleCheckboxes(message.UIObjectIds);
});



function toggleUI(UIObjectId, action) {
    var UIobject = document.getElementById(UIObjectId);
    if (UIobject) {
        if (action === 'disable') {
            UIobject.disabled = true;  // Disable the UI
        } else {
            UIobject.disabled = false; // Enable the UI
        }
    } else {
        console.error('UI element not found:', UIObjectId);
    }
}

// Register the handler for the custom message
Shiny.addCustomMessageHandler("toggleUIHandler", function(message) {
    toggleUI(message.UIObjectId, message.action);
});
