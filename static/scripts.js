function openModal(src) {
    // Set the source of the modal content to the clicked image
    document.getElementById('modalContent').src = src;
    // Display the modal
    document.getElementById('imageModal').style.display = "block";
}

function closeModal() {
    // Hide the modal when clicked
    document.getElementById('imageModal').style.display = "none";
}

// Optionally, close modal if clicked outside the image
window.onclick = function(event) {
    if (event.target === document.getElementById('imageModal')) {
        closeModal();
    }
}


//script for the dropdowns used in the "collection.html" file
document.addEventListener("DOMContentLoaded", function() {
    const select = document.getElementById("inputSheets");
    const start = 1; //start of the range
    const end = 30; //end of range as defined in the database
    
    //for loop to dynamically generate the input for the select dropdown
    for(let i = start; i <= end; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        select.appendChild(option);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const select = document.getElementById("inputRows");
    const start = 1; //start of the range
    const end = 5; //end of range as defined in the database
    
    //for loop to dynamically generate the input for the select dropdown
    for(let i = start; i <= end; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        select.appendChild(option);
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const select = document.getElementById("inputCols");
    const start = 1; //start of the range
    const end = 7; //end of range as defined in the database
    
    //for loop to dynamically generate the input for the select dropdown
    for(let i = start; i <= end; i++) {
        let option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        select.appendChild(option);
    }
});




