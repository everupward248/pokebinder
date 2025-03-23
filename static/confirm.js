//function for confirm delete on buttons
// Script for delete button on the collection page
// Select all buttons with the 'deleteButton' class
document.querySelectorAll('.deleteButton').forEach(function(button) {
    button.addEventListener('click', function(event) {
        // Prevent the form submission or default behavior of the button
        event.preventDefault();

        // Get the binder_id from the data attribute
        const binder_id = this.getAttribute('data-binder-id');

        // Show the confirmation alert
        const userConfirmed = confirm("Are you sure you want to delete this binder?");

        if (userConfirmed) {
            // If user confirms, send the POST request
            fetch('/collection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json', //ensure correct content type
                },
                body: JSON.stringify({ binder_id: binder_id }) // Send binder_id in the body
            })
            .then(response => response.json())
            .then(data => {
                // Handle the server's response here
                console.log('Success:', data);
                alert("Item deleted successfully!");
            })
            .catch(error => {
                // Handle any errors
                console.error('Error:', error);
            });
        } else {
            // If the user cancels, do nothing
            console.log("Delete action canceled.");
        }
    });
});