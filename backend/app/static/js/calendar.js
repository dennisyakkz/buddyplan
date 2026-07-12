class CalendarView {
    constructor(container, options = {}) {
        this.container = container;
        this.view = "week";
        this.currentDate = new Date();
        this.currentDate.setHours(0, 0, 0, 0);
        this.onDateClick = options.onDateClick || (() => {});
        this.renderDay = options.renderDay || (() => "");
        this.draggable = options.draggable || false;
        this.onReorder = options.onReorder || (() => {});
        this.onMove = options.onMove || null;
        this.draggedTaskId = null;
        this.dragSourceDate = null;
    }

    setView(view) {
        this.view = view;
        this.render();
    }

    navigate(delta) {
        const d = new Date(this.currentDate);
        if (this.view === "day") {
            d.setDate(d.getDate() + delta);
        } else if (this.view === "week") {
            d.setDate(d.getDate() + delta * 7);
        } else {
            d.setMonth(d.getMonth() + delta);
        }
        this.currentDate = d;
        this.render();
    }

    goToday() {
        this.currentDate = new Date();
        this.currentDate.setHours(0, 0, 0, 0);
        this.render();
    }

    getPeriodLabel() {
        if (this.view === "day") {
            return `${formatDayNL(this.currentDate)} ${formatDateNL(this.currentDate)}`;
        }
        if (this.view === "week") {
            const mon = mondayOf(this.currentDate);
            const sun = new Date(mon);
            sun.setDate(sun.getDate() + 6);
            return `${formatDateNL(mon)} – ${formatDateNL(sun)}`;
        }
        return `${DUTCH_MONTHS[this.currentDate.getMonth() + 1]} ${this.currentDate.getFullYear()}`;
    }

    getVisibleDates() {
        if (this.view === "day") return [new Date(this.currentDate)];
        if (this.view === "week") {
            const mon = mondayOf(this.currentDate);
            return Array.from({ length: 7 }, (_, i) => {
                const d = new Date(mon);
                d.setDate(d.getDate() + i);
                return d;
            });
        }
        return this._monthDates();
    }

    _monthDates() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const first = new Date(year, month, 1);
        const start = mondayOf(first);
        const dates = [];
        for (let i = 0; i < 42; i++) {
            const d = new Date(start);
            d.setDate(d.getDate() + i);
            dates.push(d);
        }
        return dates;
    }

    async render() {
        const label = document.getElementById("current-period");
        if (label) label.textContent = this.getPeriodLabel();

        if (this.view === "month") {
            this._renderMonth();
        } else if (this.view === "week") {
            await this._renderWeek();
        } else {
            await this._renderDay();
        }
    }

    async _renderDay() {
        const date = this.currentDate;
        const content = await this.renderDay(date);
        this.container.innerHTML = `
            <div class="day-view">
                <div class="task-list drop-zone" data-date="${toISODate(date)}">
                    ${content}
                </div>
            </div>`;
        if (this.draggable) this._setupDragDrop(this.container.querySelector(".drop-zone"));
    }

    async _renderWeek() {
        const dates = this.getVisibleDates();
        const contents = await Promise.all(dates.map(d => this.renderDay(d)));
        const days = dates.map((d, i) => `
            <div class="week-day ${isToday(d) ? "today" : ""}">
                <div class="week-day-header">
                    ${formatDayNL(d)}
                    <div class="date">${formatDateNL(d)}</div>
                </div>
                <div class="week-day-body drop-zone" data-date="${toISODate(d)}">
                    ${contents[i]}
                </div>
            </div>
        `).join("");

        this.container.innerHTML = `<div class="week-view">${days}</div>`;
        if (this.draggable) {
            this.container.querySelectorAll(".drop-zone").forEach(z => this._setupDragDrop(z));
        }
    }

    async _renderMonth() {
        const dates = this._monthDates();
        const month = this.currentDate.getMonth();
        const headers = DUTCH_DAYS.map(d => `<div class="month-header">${d.slice(0, 2)}</div>`).join("");

        const dayContents = await Promise.all(dates.map(d => this.renderDay(d)));

        const cells = dates.map((d, i) => {
            const other = d.getMonth() !== month ? "other-month" : "";
            const today = isToday(d) ? "today" : "";
            const items = dayContents[i];
            const miniItems = typeof items === "string"
                ? (items.match(/task-title|agenda-card/g) || []).length
                : 0;
            return `
                <div class="month-cell ${other} ${today}" data-date="${toISODate(d)}">
                    <div class="day-num">${d.getDate()}</div>
                    ${items}
                </div>`;
        }).join("");

        this.container.innerHTML = `
            <div class="month-view">
                <div class="month-grid">${headers}${cells}</div>
            </div>`;

        this.container.querySelectorAll(".month-cell").forEach(cell => {
            cell.addEventListener("click", () => {
                this.onDateClick(new Date(cell.dataset.date + "T00:00:00"));
            });
        });
    }

    _setupDragDrop(zone) {
        zone.addEventListener("dragover", e => {
            e.preventDefault();
            zone.classList.add("drag-over");
            const after = this._dragAfterElement(zone, e.clientY);
            const dragging = document.querySelector(".dragging");
            if (dragging && after == null) {
                zone.appendChild(dragging);
            } else if (dragging && after) {
                zone.insertBefore(dragging, after);
            }
        });

        zone.addEventListener("dragleave", () => zone.classList.remove("drag-over"));

        zone.addEventListener("drop", e => {
            e.preventDefault();
            zone.classList.remove("drag-over");
            const targetDate = zone.dataset.date;
            const dragging = document.querySelector(".task-card.dragging");
            const taskId = dragging
                ? parseInt(dragging.dataset.id)
                : this.draggedTaskId;
            const sourceDate = this.dragSourceDate;
            const ids = Array.from(zone.querySelectorAll(".task-card"))
                .map(el => parseInt(el.dataset.id));

            const moved = sourceDate
                && sourceDate !== targetDate
                && taskId
                && this.onMove;

            if (moved) {
                this.onMove(taskId, sourceDate, targetDate, ids);
            } else {
                this.onReorder(targetDate, ids);
            }
        });
    }

    _dragAfterElement(container, y) {
        const els = [...container.querySelectorAll(".task-card:not(.dragging)")];
        return els.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) {
                return { offset, element: child };
            }
            return closest;
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }

    makeDraggable(el) {
        el.draggable = true;
        el.addEventListener("dragstart", () => {
            el.classList.add("dragging");
            this.draggedTaskId = parseInt(el.dataset.id);
            const zone = el.closest(".drop-zone");
            this.dragSourceDate = zone ? zone.dataset.date : null;
        });
        el.addEventListener("dragend", () => {
            el.classList.remove("dragging");
            this.draggedTaskId = null;
            this.dragSourceDate = null;
        });
    }
}
