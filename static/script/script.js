// script.js - Adds interactivity to Resume Analyzer

document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("uploadForm");
    
    if (uploadForm) {
        uploadForm.addEventListener("submit", function (event) {
            const resumeInput = document.getElementById("resume");
            const file = resumeInput.files[0];
            const allowedExtensions = ["pdf", "docx"];
            const fileExtension = file.name.split(".").pop().toLowerCase();
            
            if (!allowedExtensions.includes(fileExtension)) {
                alert("Invalid file type! Please upload a PDF or DOCX file.");
                event.preventDefault();
            }
        });
    }
    
    // Dark mode toggle (optional feature)
    const darkModeToggle = document.getElementById("darkModeToggle");
    if (darkModeToggle) {
        darkModeToggle.addEventListener("click", function () {
            document.body.classList.toggle("dark-mode");
        });
    }
});
