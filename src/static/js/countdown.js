document.addEventListener('DOMContentLoaded', function() {
    const endDate = new Date("July 26, 2024 20:24:00").getTime();

    const timer = setInterval(function() {
        let now = new Date().getTime();
        let distance = endDate - now;

        let days = Math.floor(distance / (1000 * 60 * 60 * 24));
        let hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);

        document.getElementById("countdown").innerHTML = days + "j " + hours + "h "
        + minutes + "m " + seconds + "s ";

        if (distance < 0) {
            clearInterval(timer);
            document.getElementById("countdown").innerHTML = "C'est parti pour la fête !";
        }
    }, 1000);
});
