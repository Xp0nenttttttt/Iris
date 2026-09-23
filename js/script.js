
/* =========================================================
   SPLEEN STATS — V1
========================================================= */


/* =========================================================
   THEME
========================================================= */

const themeButton = document.getElementById("themeButton");

themeButton.addEventListener("click", () => {

    document.body.classList.toggle("light");

    const isLight =
        document.body.classList.contains("light");

    localStorage.setItem(
        "theme",
        isLight ? "light" : "dark"
    );

    themeButton.textContent =
        isLight ? "☀" : "◐";
});


/* =========================================================
   LOAD SAVED THEME
========================================================= */

const savedTheme =
    localStorage.getItem("theme");

if (savedTheme === "light") {

    document.body.classList.add("light");

    themeButton.textContent = "☀";
}


/* =========================================================
   NAVIGATION ACTIVE STATE
========================================================= */

const sections =
    document.querySelectorAll("section[id]");

const navLinks =
    document.querySelectorAll(".navbar nav a");


window.addEventListener("scroll", () => {

    let current = "";

    sections.forEach(section => {

        const sectionTop =
            section.offsetTop - 150;

        if (window.scrollY >= sectionTop) {
            current = section.id;
        }

    });


    navLinks.forEach(link => {

        link.classList.remove("active");

        if (
            link.getAttribute("href") ===
            `#${current}`
        ) {
            link.classList.add("active");
        }

    });

});


/* =========================================================
   LAST UPDATE
========================================================= */

const lastUpdate =
    document.getElementById("lastUpdate");

const now = new Date();

lastUpdate.textContent =
    now.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });


/* =========================================================
   CARD ANIMATION
========================================================= */

const cards =
    document.querySelectorAll(
        ".stat-card, .wide-card"
    );


const observer =
    new IntersectionObserver(
        entries => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.style.opacity = "1";
                    entry.target.style.transform =
                        "translateY(0)";

                    observer.unobserve(
                        entry.target
                    );
                }

            });

        },
        {
            threshold: 0.15
        }
    );


cards.forEach(card => {

    card.style.opacity = "0";

    card.style.transform =
        "translateY(20px)";

    card.style.transition =
        "opacity 0.6s ease, transform 0.6s ease";

    observer.observe(card);

});

async function loadExcel() {

    // Charger le fichier Excel
    const response = await fetch("stats_clan_test.xlsx");
    const buffer = await response.arrayBuffer();

    // Lire le fichier
    const workbook = XLSX.read(buffer, {
        type: "array"
    });

    // Récupérer la première feuille
    const sheet = workbook.Sheets[workbook.SheetNames[0]];

    // Transformer Excel en tableau JavaScript
    const data = XLSX.utils.sheet_to_json(sheet);

    console.log("Données Excel :", data);

    // On récupère uniquement Spleen
    const spleenData = data.filter(
        player => player.Joueur === "Spleen"
    );

    // Labels du graphique
    const months = spleenData.map(
        player => player.Mois
    );

    // Rang AREDL
    const ranks = spleenData.map(
        player => player.AREDl
    );

    // Création du graphique
    const ctx = document
        .getElementById("aredlChart");

    new Chart(ctx, {

        type: "line",

        data: {
            labels: months,

            datasets: [{
                label: "Rang AREDL",

                data: ranks,

                borderWidth: 3,

                tension: 0.35,

                pointRadius: 5
            }]
        },

        options: {

            responsive: true,

            scales: {

                y: {
                    reverse: true,

                    title: {
                        display: true,
                        text: "Classement AREDL"
                    }
                },

                x: {
                    title: {
                        display: true,
                        text: "Mois"
                    }
                }
            }
        }
    });
}

loadExcel();