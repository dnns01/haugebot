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

function wusstestDuSchonSetActive(checkbox, id, field) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let payload = {
        id: id,
        field: field,
        active: checkbox.checked
    };

    fetch('/wusstest_du_schon/active', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
    }).then(response => response.json()).then(data => checkbox.checked = data.active);
}

function wusstestDuSchonRemove(id) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    let payload = {
        id: id
    };

    fetch('/wusstest_du_schon/remove', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        credentials: 'same-origin',
        body: JSON.stringify(payload)
    })
}