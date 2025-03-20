function populateMonthDropdown() {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];
    const currentDate = new Date();
    const currentMonth = currentDate.getMonth();
    const currentYear = currentDate.getFullYear();
    let html = '';

    for (let i = 0; i < 3; i++) {
        let month = (currentMonth + i) % 12;
        let year = currentYear + Math.floor((currentMonth + i) / 12);
        html += `<option value="${month + 1},${year}">${months[month]} ${year}</option>`;
    }

    document.getElementById('month-select').innerHTML = html;
}

function updateCalendar() {
    const [month, year] = document.getElementById('month-select').value.split(',');
    generateCalendar(parseInt(month), parseInt(year));
}

function generateCalendar(month, year) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'];
    const daysInMonth = new Date(year, month, 0).getDate();
    const firstDay = new Date(year, month - 1, 1).getDay();

    let html = `<h2>${months[month - 1]} ${year}</h2><table><tr>`;
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    days.forEach(day => html += `<th>${day}</th>`);
    html += '</tr><tr>';

    for (let i = 0; i < firstDay; i++) {
        html += '<td></td>';
    }

    for (let day = 1; day <= daysInMonth; day++) {
        if ((day + firstDay - 1) % 7 === 0 && day !== 1) {
            html += '</tr><tr>';
        }
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        html += `<td class="day" data-date="${dateStr}" onclick="window.location.href='/event_form?date=${dateStr}'">${day}</td>`;
    }

    html += '</tr></table>';
    document.getElementById('calendar').innerHTML = html;

    fetch(`/get_events?month=${month}&year=${year}`)
        .then(response => response.json())
        .then(events => {
            const eventList = document.getElementById('events-list');
            let eventHtml = '<h3>Events</h3>';
            const dayCells = document.querySelectorAll('.day');

            const eventsByDate = {};
            events.forEach(event => {
                if (!eventsByDate[event.date]) {
                    eventsByDate[event.date] = [];
                }
                eventsByDate[event.date].push(event);
            });

            dayCells.forEach(cell => {
                const date = cell.dataset.date;
                if (eventsByDate[date]) {
                    cell.classList.add('has-event');
                    let titles = eventsByDate[date].map(event => event.title).join('<br>');
                    cell.innerHTML = `${cell.textContent}<br><span class="event-title">${titles}</span>`;
                }
            });

            for (let date in eventsByDate) {
                eventsByDate[date].forEach(event => {
                    eventHtml += `<div class="event-item">${event.date}: ${event.title}</div>`;
                });
            }

            eventList.innerHTML = eventHtml;
        });
}