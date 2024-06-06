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