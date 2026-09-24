document.addEventListener("DOMContentLoaded", function () {

    // Automatically close Bootstrap alerts after 5 seconds
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach(function (alert) {

        setTimeout(function () {

            const closeButton = alert.querySelector(".btn-close");

            if (closeButton) {
                closeButton.click();
            }

        }, 5000);

    });


    // Add active navigation state
    const currentPage = window.location.pathname;

    document.querySelectorAll(".navbar-nav .nav-link").forEach(function (link) {

        if (link.getAttribute("href") === currentPage) {
            link.classList.add("active");
        }

    });

});