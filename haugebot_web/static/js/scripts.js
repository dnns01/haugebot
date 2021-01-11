document.querySelectorAll(".tablink").forEach(value => {
    value.addEventListener("click", evt => {
        var i, x, tablinks;
        var cityName = value.getAttribute("id").replace("tablink_", "");
        x = document.getElementsByClassName("form");
        for (i = 0; i < x.length; i++) {
            x[i].style.display = "none";
        }
        tablinks = document.getElementsByClassName("tablink");
        for (i = 0; i < x.length; i++) {
            tablinks[i].className = tablinks[i].className.replace(" active", "");
        }
        document.getElementById(cityName).style.display = "block";
        value.className += " active";
    })
});

document.querySelectorAll(".color-select option").forEach(option => {
    option.setAttribute("style", "background: " + option.getAttribute("value") + ";");
});