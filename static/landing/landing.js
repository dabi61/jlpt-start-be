document.addEventListener("DOMContentLoaded", () => {
    const nav = document.querySelector(".site-nav");
    const toggle = document.querySelector(".menu-toggle");

    if (nav && toggle) {
        toggle.addEventListener("click", () => {
            const isOpen = nav.classList.toggle("site-nav-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });

        nav.querySelectorAll("a").forEach((item) => {
            item.addEventListener("click", () => {
                nav.classList.remove("site-nav-open");
                toggle.setAttribute("aria-expanded", "false");
            });
        });
    }

    const revealItems = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window) || revealItems.length === 0) {
        revealItems.forEach((item) => item.classList.add("is-visible"));
        return;
    }

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15, rootMargin: "0px 0px -20px 0px" }
    );

    revealItems.forEach((item) => observer.observe(item));
});
