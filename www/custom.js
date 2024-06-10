function toggleCheckboxes(checkboxIds) {
    console.log("Hiding checkboxes after lib upload");
    checkboxIds.forEach(function(checkboxId) {
        var checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.disabled = true;  // Disable the checkbox
        } else {
            console.error('Checkbox element not found:', checkboxId);
        }
    });
}

// Register the handler for the custom message
Shiny.addCustomMessageHandler("toggleCheckboxHandler", function(message) {
    toggleCheckboxes(message.checkboxIds);
});



function toggleButton(buttonId, action) {
    var button = document.getElementById(buttonId);
    if (button) {
        if (action === 'disable') {
            button.disabled = true;  // Disable the button
        } else {
            button.disabled = false; // Enable the button
        }
    } else {
        console.error('Button element not found:', buttonId);
    }
}

// Register the handler for the custom message
Shiny.addCustomMessageHandler("toggleButtonHandler", function(message) {
    toggleButton(message.buttonId, message.action);
});
