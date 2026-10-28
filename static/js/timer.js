let minutes = 25;
let seconds = 0;
let timer;
let running = false;
let currentMode = "focus";

const timerDisplay =
    document.getElementById("timerDisplay");

const statusLabel =
    document.getElementById("statusLabel");


/* ---------- Saving each timer run (so the admin can see the mode) ---------- */

const startUrl = document.body.dataset.startUrl;
const finishUrl = document.body.dataset.finishUrl;
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// Button name used on this page -> name saved in the database
const MODE_NAMES = {
    focus: "focus",
    break: "short_break",
    long: "long_break"
};

let sessionId = null;       // id of the run saved on the server
let sessionPending = null;  // waits for the server to answer the "start" request
let secondsRun = 0;         // seconds really counted down in this run


function sendToServer(url, data, useBeacon = false) {

    const body = new FormData();

    Object.entries(data).forEach(([key, value]) => body.append(key, value));

    body.append("csrfmiddlewaretoken", csrfToken);

    // sendBeacon still works while the page is closing
    if (useBeacon && navigator.sendBeacon) {
        navigator.sendBeacon(url, body);
        return Promise.resolve(null);
    }

    return fetch(url, {
        method: "POST",
        body: body,
        credentials: "same-origin"
    });

}


function startSession() {

    secondsRun = 0;

    sessionId = null;

    sessionPending = sendToServer(startUrl, { mode: MODE_NAMES[currentMode] })
        .then(response => response.json())
        .then(data => {
            sessionId = data.id;
            return data.id;
        })
        .catch(() => null);

}


// completed = true when the timer reached 00:00, false when it was stopped early
function finishSession(completed, useBeacon = false) {

    if (!sessionPending) {
        return;
    }

    const pending = sessionPending;
    const seconds = secondsRun;
    const knownId = sessionId;

    sessionPending = null;
    sessionId = null;

    const send = id => {
        if (id) {
            sendToServer(finishUrl, {
                session_id: id,
                seconds: seconds,
                completed: completed ? 1 : 0
            }, useBeacon);
        }
    };

    if (knownId) {
        send(knownId);
    } else {
        pending.then(send);
    }

}


/* ---------- Timer ---------- */

function updateDisplay() {

    timerDisplay.textContent =
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

}


function setMode(mode) {

    if (running) {

        if (!confirm(
            "Timer is running. Are you sure you want to switch modes and reset?"
        )) {
            return;
        }

    }

    clearInterval(timer);

    running = false;

    // The run that was in progress (running or paused) stops here
    finishSession(false);

    currentMode = mode;


    document
        .querySelectorAll('.mode-buttons button')
        .forEach(btn => btn.classList.remove('active'));


    if (mode === "focus") {

        minutes = 25;

        statusLabel.textContent = "Focus Mode";

        document
            .getElementById("focusBtn")
            .classList.add("active");

    }

    else if (mode === "break") {

        minutes = 5;

        statusLabel.textContent = "Short Break";

        document
            .getElementById("breakBtn")
            .classList.add("active");

    }

    else {

        minutes = 15;

        statusLabel.textContent = "Long Break";

        document
            .getElementById("longBtn")
            .classList.add("active");

    }

    seconds = 0;

    updateDisplay();

}


function startTimer() {

    if (!running) {

        running = true;

        // Resuming after Pause keeps the same run; a fresh start creates a new one
        if (!sessionPending) {
            startSession();
        }

        timer = setInterval(() => {

            if (seconds === 0) {

                if (minutes === 0) {

                    clearInterval(timer);

                    running = false;

                    finishSession(true);

                    alert(
                        `${statusLabel.textContent} complete!`
                    );

                    resetTimer();

                    return;
                }

                minutes--;

                seconds = 59;

            }

            else {

                seconds--;

            }

            secondsRun++;

            updateDisplay();

        }, 1000);

    }

}


function pauseTimer() {

    clearInterval(timer);

    running = false;

}


function resetTimer() {

    setMode(currentMode);

}


document
    .getElementById('hamburger-btn')
    .addEventListener('click', function() {

        document
            .getElementById('dropdown-menu')
            .classList.toggle('show');

    });


window.onclick = function(event) {

    if (!event.target.matches('#hamburger-btn')) {

        document
            .getElementById('dropdown-menu')
            .classList.remove('show');

    }

};


// If the user closes the tab, logs out or ends the task, save the run as stopped early
window.addEventListener('pagehide', function() {

    finishSession(false, true);

});


// End Current Task: ask first, then send the form (POST) to save end time and duration
const endTaskBtn = document.getElementById('endTaskBtn');

if (endTaskBtn) {
    endTaskBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to end the current task and stop time tracking?')) {
            document.getElementById('endTaskForm').submit();
        }
    });
}


updateDisplay();
